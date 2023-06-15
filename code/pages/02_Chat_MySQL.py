import os

import streamlit as st
from streamlit_chat import message

import core.common.env as env
from core.llm_helper.database_llm_helper import DatabaseLLMHelper

st.set_page_config(
    layout="wide",
    page_title=env.PAGE_TITLE,
    page_icon=os.path.join('images', 'openai.ico'),
    menu_items={
        'Get help': None,
        'Report a bug': None,
        'About': None
    }
)

hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def clear_chat_data():
    st.session_state['input'] = ""
    st.session_state['chat_history'] = []


def send_msg():
    if st.session_state['input']:
        result, sql_query, sql_result = llm_helper.get_response(st.session_state['input'])
        st.session_state['chat_history'].append((
            st.session_state['input'],
            f"{result}\n\nSQL Query: {sql_query}\nSQL Result: {sql_result.lstrip('[(').rstrip(',)]')}"
        ))
        st.session_state['input'] = ""


# Initialize chat history
if 'question' not in st.session_state:
    st.session_state['question'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

llm_helper = DatabaseLLMHelper()

col1, col2 = st.columns([8, 2])
with col1:
    st.text_input("You: ", placeholder="type your question", key="input")
with col2:
    st.text("")
    st.text("")
    st.button("Send", on_click=send_msg)

col1, col2 = st.columns([1, 1])
with col1:
    clear_chat = st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)

if st.session_state['chat_history']:
    for i in range(len(st.session_state['chat_history']) - 1, -1, -1):
        message(st.session_state['chat_history'][i][1], key=str(i))
        message(st.session_state['chat_history'][i][0], is_user=True, key=str(i) + '_user')
