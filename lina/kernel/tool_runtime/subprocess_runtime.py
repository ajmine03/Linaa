"""Subprocess-based ToolRuntimePort implementation.

Handlers registered against this runtime are plain async callables (see
ToolHandler protocol) — this runtime does not itself spawn subprocesses;
that responsibility belongs to each plugin's tool handler (e.g. wrapping
nmap, a Metasploit RPC client, etc.). What this runtime DOES provide
uniformly for every handler:
  - timeout enforcement via asyncio.wait_for
  - cancellation tracking/registry so in-flight executions can be cancelled
  - centralized error normalization (handler exceptions -> ToolRuntimeError)
  - structured logging of every execution's lifecycle

A separate helper, `run_subprocess`, is exposed for plugin tool handlers
that need to shell out to a real CLI (nmap, etc.) with bounded output
capture and timeout — this is the low-level primitive plugins build on.
"""

from __future__ import annotations

import asyncio
import time

import structlog

from kernel.entities.tool_execution import ToolExecution
from kernel.ports.exceptions import ToolRuntimeError
from kernel.ports.tool_runtime import ToolHandler, ToolResult, ToolRuntimePort, ToolSpec
from kernel.tool_runtime.output_capture import BoundedBuffer
from kernel.tool_runtime.registry import ToolRegistry

logger = structlog.get_logger(__name__)


async def run_subprocess(
    command: list[str],
    *,
    timeout_seconds: int,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> ToolResult:
    """Low-level primitive: run an external command with bounded output capture
    and hard timeout enforcement. Intended for plugin tool handlers that wrap
    real CLI security tools (nmap, subfinder, etc.).

    Raises ToolRuntimeError only for infrastructure failures (e.g. binary not
    found). A non-zero exit code is returned normally in ToolResult.exit_code.
    """
    start = time.monotonic()
    stdout_buf = BoundedBuffer()
    stderr_buf = BoundedBuffer()

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
    except FileNotFoundError as exc:
        raise ToolRuntimeError(f"Command binary not found: {command[0]}") from exc
    except OSError as exc:
        raise ToolRuntimeError(f"Failed to spawn process: {exc}") from exc

    async def _drain_stream(stream: asyncio.StreamReader, buf: BoundedBuffer) -> None:
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                break
            buf.write(chunk)

    assert process.stdout is not None
    assert process.stderr is not None

    try:
        await asyncio.wait_for(
            asyncio.gather(
                _drain_stream(process.stdout, stdout_buf),
                _drain_stream(process.stderr, stderr_buf),
                process.wait(),
            ),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        duration = time.monotonic() - start
        return ToolResult(
            exit_code=-1,
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue() + "\n[LINA] Process killed: timeout exceeded.",
            duration_seconds=duration,
            truncated=stdout_buf.truncated or stderr_buf.truncated,
        )

    duration = time.monotonic() - start
    return ToolResult(
        exit_code=process.returncode if process.returncode is not None else -1,
        stdout=stdout_buf.getvalue(),
        stderr=stderr_buf.getvalue(),
        duration_seconds=duration,
        truncated=stdout_buf.truncated or stderr_buf.truncated,
    )


class SubprocessToolRuntime(ToolRuntimePort):
    """Default LINA Tool Runtime. Delegates actual execution to registered
    handlers (which may or may not shell out to a subprocess internally),
    while uniformly enforcing timeouts and tracking cancellable tasks.
    """

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()
        self._in_flight: dict[str, asyncio.Task[ToolResult]] = {}

    def register_handler(self, tool_name: str, handler: ToolHandler) -> None:
        spec = self._registry.get_spec(tool_name)
        if spec is None:
            raise ToolRuntimeError(
                f"Cannot register handler for unknown tool '{tool_name}'; "
                "register the ToolSpec first via registry.register()."
            )
        self._registry.register(spec, handler)

    def register_tool(self, spec: ToolSpec, handler: ToolHandler) -> None:
        """Convenience: register spec + handler together (typical plugin usage)."""
        self._registry.register(spec, handler)

    def get_spec(self, tool_name: str) -> ToolSpec | None:
        return self._registry.get_spec(tool_name)

    def list_specs(self, *, plugin_name: str | None = None) -> list[ToolSpec]:
        return self._registry.list_specs(plugin_name=plugin_name)

    async def execute(self, spec: ToolSpec, execution: ToolExecution) -> ToolResult:
        handler = self._registry.get_handler(spec.name)
        if handler is None:
            raise ToolRuntimeError(f"No handler registered for tool '{spec.name}'.")

        logger.info(
            "tool_runtime.execution_starting",
            tool_name=spec.name,
            execution_id=execution.id,
            engagement_id=execution.engagement_id,
            timeout_seconds=spec.timeout_seconds,
        )

        task: asyncio.Task[ToolResult] = asyncio.ensure_future(
            self._run_with_timeout(handler, execution, spec.timeout_seconds)
        )
        self._in_flight[execution.id] = task

        try:
            result = await task
            logger.info(
                "tool_runtime.execution_finished",
                tool_name=spec.name,
                execution_id=execution.id,
                exit_code=result.exit_code,
                duration_seconds=round(result.duration_seconds, 3),
            )
            return result
        finally:
            self._in_flight.pop(execution.id, None)

    async def _run_with_timeout(
        self, handler: ToolHandler, execution: ToolExecution, timeout_seconds: int
    ) -> ToolResult:
        start = time.monotonic()
        try:
            result = await asyncio.wait_for(
                handler(execution.parameters),
                timeout=timeout_seconds,
            )
            return result
        except TimeoutError:
            duration = time.monotonic() - start
            logger.warning(
                "tool_runtime.execution_timed_out",
                execution_id=execution.id,
                timeout_seconds=timeout_seconds,
            )
            return ToolResult(
                exit_code=-1,
                stdout="",
                stderr=f"[LINA] Handler timed out after {timeout_seconds}s.",
                duration_seconds=duration,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 — normalize into ToolRuntimeError
            logger.exception("tool_runtime.handler_raised", execution_id=execution.id)
            raise ToolRuntimeError(f"Tool handler raised an exception: {exc}") from exc

    async def cancel(self, execution_id: str) -> bool:
        task = self._in_flight.get(execution_id)
        if task is None or task.done():
            return False
        task.cancel()
        logger.info("tool_runtime.execution_cancelled", execution_id=execution_id)
        return True