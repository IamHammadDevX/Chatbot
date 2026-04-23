import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIError, AuthenticationError, RateLimitError

# Local only (.env)
load_dotenv()

st.set_page_config(
    page_title="ChatBot",
    page_icon="💬",
    layout="centered"
)

st.title("💬 ChatBot")
st.caption("Ask anything — powered by OpenRouter")

MODEL = "openai/gpt-4o-mini"
SYSTEM_PROMPT = "You are a helpful, concise assistant."


@st.cache_resource
def get_client():
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


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Settings")

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Model:** `{MODEL}`")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")


client = get_client()

if client is None:
    st.error(
        "OPENROUTER_API_KEY not found.\n\n"
        "Add it in Streamlit Cloud → App Settings → Secrets"
    )
    st.stop()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


prompt = st.chat_input("Type your message...")


if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            api_messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

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

            placeholder.markdown(full_response)

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

        except AuthenticationError:
            placeholder.error("Invalid API key.")

        except RateLimitError:
            placeholder.error("Rate limit exceeded.")

        except APIConnectionError:
            placeholder.error("Connection failed.")

        except APIError as e:
            placeholder.error(f"API Error: {str(e)}")

        except Exception as e:
            placeholder.error(f"Error: {str(e)}")