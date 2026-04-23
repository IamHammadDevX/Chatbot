import os
from dotenv import load_dotenv
import streamlit as st
from openai import (
    OpenAI,
    APIConnectionError,
    APIError,
    AuthenticationError,
    RateLimitError,
)

# Load local .env for local development only
# Streamlit Cloud will use st.secrets instead
load_dotenv()

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="ChatBot",
    page_icon="💬",
    layout="centered",
)

st.title("💬 ChatBot")
st.caption("Ask anything — powered by OpenRouter")

# --------------------------------------------------
# Settings
# --------------------------------------------------
MODEL = "openai/gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. "
    "Answer clearly and accurately."
)

# --------------------------------------------------
# OpenRouter Client
# --------------------------------------------------
@st.cache_resource
def get_client():
    """
    Create OpenRouter client safely for:
    - Local development (.env)
    - Streamlit Cloud deployment (st.secrets)
    """

    # First try Streamlit Cloud secrets
    api_key = st.secrets.get("OPENROUTER_API_KEY")

    # Fallback to local .env
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


# --------------------------------------------------
# Session State
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.subheader("Settings")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Model:** `{MODEL}`")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")

# --------------------------------------------------
# Initialize Client
# --------------------------------------------------
client = get_client()

if client is None:
    st.error(
        "OPENROUTER_API_KEY not found.\n\n"
        "For local development:\n"
        "Create a `.env` file with:\n\n"
        "OPENROUTER_API_KEY=your_api_key_here\n\n"
        "For Streamlit Cloud:\n"
        "Add the key in:\n"
        "App Settings → Secrets"
    )
    st.stop()

# --------------------------------------------------
# Display Previous Messages
# --------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# Chat Input
# --------------------------------------------------
prompt = st.chat_input("Type your message...")

if prompt:
    prompt = prompt.strip()

    if not prompt:
        st.warning("Please enter a valid message.")
        st.stop()

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            # Build message history
            api_messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ] + [
                {
                    "role": m["role"],
                    "content": m["content"],
                }
                for m in st.session_state.messages
            ]

            # Stream response from OpenRouter
            stream = client.chat.completions.create(
                model=MODEL,
                messages=api_messages,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta.content

                    if delta:
                        full_response += delta
                        placeholder.markdown(full_response + "▌")

            # Handle empty response
            if not full_response.strip():
                raise Exception("Empty response from model.")

            # Final output
            placeholder.markdown(full_response)

            # Save assistant response
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                }
            )

        except AuthenticationError:
            placeholder.error(
                "Authentication failed.\n\n"
                "Please check your OpenRouter API key."
            )

        except RateLimitError:
            placeholder.error(
                "Rate limit exceeded.\n\n"
                "Please wait a moment and try again."
            )

        except APIConnectionError:
            placeholder.error(
                "Connection failed.\n\n"
                "Please check your internet connection."
            )

        except APIError as e:
            placeholder.error(f"API Error: {str(e)}")

        except Exception as e:
            placeholder.error(f"Something went wrong: {str(e)}")