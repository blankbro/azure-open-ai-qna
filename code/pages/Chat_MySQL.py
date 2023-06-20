import streamlit as st
from streamlit_chat import message

from pages.common.page_config import load_page_config
from server.model.mysql_llm_helper import DatabaseLLMHelper

load_page_config()


def clear_chat_data():
    st.session_state['chat_mysql_input'] = ""
    st.session_state['chat_mysql_history'] = []
    st.session_state['chat_mysql_sql'] = []


def send_msg():
    if st.session_state['chat_mysql_input']:
        result, sql_query, sql_result = llm_helper.get_response(st.session_state['chat_mysql_input'])
        st.session_state['chat_mysql_history'].append((st.session_state['chat_mysql_input'], result))
        st.session_state['chat_mysql_sql'].append((sql_query, sql_result.lstrip('[(').rstrip(',)]')))
        st.session_state['chat_mysql_input'] = ""


if 'chat_mysql_history' not in st.session_state:
    st.session_state['chat_mysql_history'] = []
if 'chat_mysql_sql' not in st.session_state:
    st.session_state['chat_mysql_sql'] = []

llm_helper = DatabaseLLMHelper()

col1, col2 = st.columns([8, 2])

with col1:
    st.text_input("You: ", placeholder="type your question", key="chat_mysql_input")

with col2:
    st.text("")
    st.text("")
    st.button("Send", on_click=send_msg)

col1, col2 = st.columns([1, 1])

with col1:
    clear_chat = st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)

if st.session_state['chat_mysql_history']:
    for i in range(len(st.session_state['chat_mysql_history']) - 1, -1, -1):
        message(st.session_state['chat_mysql_history'][i][1], key=str(i))
        if st.session_state["chat_mysql_sql"][i]:
            st.markdown(f"SQL Query: `{st.session_state['chat_mysql_sql'][i][0]}`")
            st.markdown(f"SQL Result: `{st.session_state['chat_mysql_sql'][i][1]}`")
        message(st.session_state['chat_mysql_history'][i][0], is_user=True, key=str(i) + '_user')
