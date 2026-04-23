import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI, APIConnectionError, APIError, AuthenticationError, RateLimitError

# Load environment variables from .env
load_dotenv()

# Streamlit page config
st.set_page_config(
    page_title="ChatBot",
    page_icon="💬",
    layout="centered"
)

st.title("💬 ChatBot")
st.caption("Ask anything — powered by OpenRouter")

# Configuration
MODEL = "openai/gpt-4o-mini"
SYSTEM_PROMPT = "You are a helpful, concise assistant. Answer clearly and accurately."


@st.cache_resource
def get_client():
    """
    Create and return OpenRouter client
    """
    api_key = os.getenv("OPENROUTER_API_KEY")

    # Do NOT print the API key in logs
    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Sidebar
with st.sidebar:
    st.subheader("Settings")

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Model:** `{MODEL}`")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")


# Create client
client = get_client()

if client is None:
    st.error(
        "OPENROUTER_API_KEY is not set.\n\n"
        "Please create a `.env` file in the same folder as `app.py` and add:\n\n"
        "OPENROUTER_API_KEY=your_api_key_here"
    )
    st.stop()


# Show previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# User input
prompt = st.chat_input("Type your message...")


if prompt:
    prompt = prompt.strip()

    if not prompt:
        st.warning("Please enter a non-empty message.")
        st.stop()

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            # Prepare conversation history
            api_messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + [
                {
                    "role": m["role"],
                    "content": m["content"]
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

            # Final display
            placeholder.markdown(full_response)

            # Save assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

        except AuthenticationError:
            placeholder.error(
                "Authentication failed.\n\n"
                "Please check that your OPENROUTER_API_KEY is valid."
            )
            st.session_state.messages.pop()

        except RateLimitError:
            placeholder.error(
                "Rate limit or quota exceeded.\n\n"
                "Please wait a moment and try again."
            )
            st.session_state.messages.pop()

        except APIConnectionError:
            placeholder.error(
                "Could not connect to OpenRouter.\n\n"
                "Please check your internet connection."
            )
            st.session_state.messages.pop()

        except APIError as e:
            placeholder.error(f"API Error: {str(e)}")
            st.session_state.messages.pop()

        except Exception as e:
            placeholder.error(f"Something went wrong: {str(e)}")
            st.session_state.messages.pop()