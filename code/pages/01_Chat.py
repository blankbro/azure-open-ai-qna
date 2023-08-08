import streamlit as st

from pages.common.page_config import load_page_config
from server.model.document_llm_helper import DocumentLLMHelper

load_page_config()


def clear_chat_data():
    st.session_state.messages = []
    st.session_state.history = []


if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'history' not in st.session_state:
    st.session_state.history = []

llm_helper = DocumentLLMHelper()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.markdown(f'\n\nSources: {message["source"]}')

# Accept user input
if prompt := st.chat_input("type your question"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # ask openai
        new_question, answer, sources, contents = llm_helper.get_response(prompt, st.session_state.history)
        st.markdown(answer)
        st.markdown(f'\n\nSources: {sources}')
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer, "source": sources})
    st.session_state.history.append((prompt, answer))
    st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)
