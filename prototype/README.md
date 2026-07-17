# Local Pentest AI Prototype

A small proof-of-concept for testing whether
a local LLM can orchestrate authorized security
reconnaissance and vulnerability-scanning
workflows.

## Scope

The prototype supports:

- Chat
- Local Ollama LLM
- SQLite conversation memory
- LLM planning loop
- Nmap
- httpx
- WhatWeb
- Nuclei
- ffuf
- Markdown reports
- FastAPI API
- Streamlit UI
- Typer CLI

It intentionally does not implement an
autonomous exploitation engine.

Use only against systems you own or have
explicit permission to test.

## Requirements

- Python 3.12
- Ollama
- qwen2.5-coder:7b
- nmap
- httpx
- whatweb
- nuclei
- ffuf

## Setup

Create a virtual environment:

    python3.12 -m venv .venv

Activate it:

    source .venv/bin/activate

Install Python dependencies:

    pip install -r requirements.txt

Copy environment configuration:

    cp .env.example .env

Make sure the Ollama model is available:

    ollama pull qwen2.5-coder:7b

## Start API

Run:

    python main.py serve

The API will listen on:

    http://127.0.0.1:8000

## Start Streamlit

In another terminal:

    streamlit run ui.py

## CLI

Start an interactive session:

    python main.py chat-cli \
        --target 192.168.56.101

Generate a report:

    python main.py report \
        --target 192.168.56.101 \
        --session cli-session

Check Ollama:

    python main.py check

## Example

Start a deliberately vulnerable lab machine.

Set its IP as the authorized target.

Then ask:

    Perform initial reconnaissance and identify
    exposed services.

The planner may select Nmap.

After receiving the Nmap output, it may identify
an HTTP service and choose httpx or WhatWeb.

For an authorized web application it may then
choose ffuf or Nuclei.

The results are stored in SQLite and can later
be converted into a Markdown report.

## Current Limitations

This is intentionally a prototype.

The LLM planner may make poor decisions.

Tool output parsing is currently LLM-based rather
than using structured parsers.

Long command output is truncated.

There is no authentication because the API is
intended to run locally.

There is no distributed execution.

There is no plugin architecture.

There is no multi-agent architecture.

There is no arbitrary shell execution.

The authorized target is supplied separately from
the LLM's generated tool arguments.