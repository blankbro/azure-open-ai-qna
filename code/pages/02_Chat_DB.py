import os

import streamlit as st
from dotenv import load_dotenv

from pages.common.page_config import load_page_config
from server.model.database_llm_helper import DatabaseLLMHelper

load_dotenv()

load_page_config()


def clear_chat_data():
    st.session_state.chatdb_messages = []


if 'chatdb_messages' not in st.session_state:
    st.session_state.chatdb_messages = []

mysql_url_list = eval(os.getenv("MYSQL_URL_LIST"))
mysql_names = []
mysql_name_url_map = {}
for mysql_url in mysql_url_list:
    mysql_names.append(mysql_url[0])
    mysql_name_url_map[mysql_url[0]] = mysql_url[1]

col1, col2 = st.columns([2, 8])
with col1:
    st.selectbox("Select DB", mysql_names, key="mysql_name")

# Display chat messages from history on app rerun
for message in st.session_state.chatdb_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.markdown(f'SQL Query: {message["sql_query"]}')
            st.markdown(f'SQL Result: {message["sql_result"]}')

# Accept user input
if prompt := st.chat_input("type your question"):
    # Add user message to chat history
    st.session_state.chatdb_messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # ask openai
        result, sql_query, sql_result = DatabaseLLMHelper(mysql_name_url_map[st.session_state["mysql_name"]]).get_response(prompt)
        st.markdown(result)
        st.markdown(f'\nSQL Query: {sql_query}')
        st.markdown(f'SQL Result: {sql_result}')
    # Add assistant response to chat history
    st.session_state.chatdb_messages.append({"role": "assistant", "content": result, "sql_query": sql_query, "sql_result": sql_result})
    st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)
