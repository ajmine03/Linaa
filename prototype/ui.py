import uuid

import requests
import streamlit as st


DEFAULT_API_URL = (
    "http://127.0.0.1:8000"
)


st.set_page_config(
    page_title=(
        "Local Pentest AI Prototype"
    ),
    page_icon="🔐",
    layout="wide",
)


if "session_id" not in st.session_state:
    st.session_state.session_id = str(
        uuid.uuid4()
    )


if "messages" not in st.session_state:
    st.session_state.messages = []


st.title(
    "Local Pentest AI Prototype"
)

st.caption(
    "For authorized security testing, "
    "CTFs, labs, and systems you have "
    "permission to assess."
)


with st.sidebar:
    st.header("Session")

    api_url = st.text_input(
        "API URL",
        value=DEFAULT_API_URL,
    )

    target = st.text_input(
        "Authorized target",
        placeholder=(
            "192.168.56.101 or "
            "http://lab.local"
        ),
    )

    st.text_input(
        "Session ID",
        value=(
            st.session_state.session_id
        ),
        disabled=True,
    )

    if st.button(
        "New Session",
        use_container_width=True,
    ):
        st.session_state.session_id = str(
            uuid.uuid4()
        )

        st.session_state.messages = []

        st.rerun()

    if st.button(
        "Generate Markdown Report",
        use_container_width=True,
    ):
        if not target:
            st.error(
                "Enter an authorized target."
            )

        else:
            try:
                response = requests.post(
                    (
                        f"{api_url}"
                        "/report"
                    ),
                    json={
                        "session_id": (
                            st.session_state
                            .session_id
                        ),
                        "target": target,
                    },
                    timeout=600,
                )

                response.raise_for_status()

                data = response.json()

                st.success(
                    "Report generated."
                )

                st.code(
                    data["report"]
                )

            except Exception as exc:
                st.error(
                    str(exc)
                )


for message in (
    st.session_state.messages
):
    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )


prompt = st.chat_input(
    "Ask the assistant to assess "
    "your authorized target..."
)


if prompt:
    if not target:
        st.error(
            "Enter an authorized target "
            "in the sidebar first."
        )

        st.stop()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message(
        "assistant"
    ):
        with st.spinner(
            "Analyzing target..."
        ):
            try:
                response = requests.post(
                    f"{api_url}/chat",
                    json={
                        "session_id": (
                            st.session_state
                            .session_id
                        ),
                        "target": target,
                        "message": prompt,
                    },
                    timeout=1200,
                )

                response.raise_for_status()

                data = response.json()

                answer = data[
                    "response"
                ]

                st.markdown(answer)

                steps = data.get(
                    "steps",
                    [],
                )

                if steps:
                    with st.expander(
                        "Execution trace"
                    ):
                        for step in steps:
                            st.write(
                                "Reason:",
                                step.get(
                                    "reasoning",
                                    "",
                                ),
                            )

                            result = step.get(
                                "tool_result",
                                {},
                            )

                            st.code(
                                " ".join(
                                    result.get(
                                        "command",
                                        [],
                                    )
                                )
                            )

                            output = result.get(
                                "stdout",
                                "",
                            )

                            if output:
                                st.text(
                                    output
                                )

                            error = result.get(
                                "error"
                            )

                            if error:
                                st.error(
                                    error
                                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as exc:
                st.error(
                    f"Request failed: {exc}"
                )