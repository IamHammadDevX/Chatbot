# ChatBot (Streamlit)

## Overview

A simple ChatGPT-like chatbot built with Python + Streamlit. Users type prompts and receive streamed responses from OpenAI. Clean UI with proper error handling (auth, rate limit, connection, API errors).

## Stack

- **Framework**: Streamlit
- **Language**: Python 3.11
- **LLM**: OpenRouter (model: `openai/gpt-4o-mini`) via the `openai` Python SDK with `base_url = https://openrouter.ai/api/v1`
- **Entry point**: `app.py`
- **Config**: `.streamlit/config.toml` (port 5000, headless, bound to 0.0.0.0)

## Environment Variables

- `OPENROUTER_API_KEY` — required secret; the app stops with a friendly error if missing.

## Running Locally

The `Start application` workflow runs `streamlit run app.py --server.port 5000` on port 5000.

## Features

- Streaming assistant responses with a live cursor (`▌`)
- Chat history kept in `st.session_state`
- Sidebar with "Clear chat" button and status info
- Graceful handling of `AuthenticationError`, `RateLimitError`, `APIConnectionError`, `APIError`, and generic exceptions
