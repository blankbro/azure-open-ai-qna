import traceback

import streamlit as st
from streamlit_chat import message

from pages.common.page_config import load_page_config
from server.model.custom_prompt import completion_prompt_template
from server.model.document_llm_helper import DocumentLLMHelper

load_page_config()


def clear_chat_data():
    st.session_state['00_input'] = ""
    st.session_state['00_chat_history'] = []


def send_msg():
    if st.session_state['00_input']:
        new_question, answer, sources, contents = llm_helper.get_response(st.session_state['00_input'], st.session_state['00_chat_history'])
        st.session_state['00_chat_history'].append((st.session_state['00_input'], answer, sources, new_question, contents))
        st.session_state['00_input'] = ""


def check_completion_prompt():
    # Check if "summaries" is present in the string completion_prompt
    if "{summaries}" not in st.session_state.completion_prompt:
        st.warning("""Your completion prompt doesn't contain the variable "{summaries}".  
        This variable is used to add the content of the documents retrieved from the VectorStore to the prompt.  
        Please add it to your completion prompt to use the app.  
        Reverting to default prompt.
        """)
        st.session_state.completion_prompt = None
    if "{question}" not in st.session_state.completion_prompt:
        st.warning("""Your completion prompt doesn't contain the variable "{question}".  
        This variable is used to add the user's question to the prompt.  
        Please add it to your completion prompt to use the app.  
        Reverting to default prompt.  
        """)
        st.session_state.completion_prompt = None


try:
    if '00_chat_history' not in st.session_state:
        st.session_state['00_chat_history'] = []

    with st.expander("Settings"):
        st.slider("Temperature", key='temperature', min_value=0.0, max_value=1.0, step=0.1, value=0.2)
        st.text_area(
            "Prompt", key='completion_prompt', height=150,
            on_change=check_completion_prompt,
            value=completion_prompt_template,
            help="""You can configure a completion prompt by adding the variables {summaries} and {question} to the prompt.  
                {summaries} will be replaced with the content of the documents retrieved from the VectorStore.  
                {question} will be replaced with the user's question."""
        )
        st.number_input("Redisearch Top k", key='redisearch_topk', min_value=1, step=1, value=4, help="限制从Redis搜索到的最大Chunk数")
        st.slider("Redisearch similarity score", key='redisearch_similarity_score', min_value=0.0, step=0.1, max_value=1.0, value=0.4, help="向量相似性：数值越小相似性越高")
        st.selectbox("Redisearch type", key='redisearch_type', options=("similarity_limit", "similarity"), help="similarity_limit 模式下，会根据 Redisearch similarity score 对搜索结果进行过滤")

    llm_helper = DocumentLLMHelper(
        completion_prompt=st.session_state.completion_prompt,
        temperature=st.session_state.temperature,
        redisearch_topk=st.session_state.redisearch_topk,
        redisearch_similarity_score=st.session_state.redisearch_similarity_score,
        redisearch_type=st.session_state.redisearch_type
    )

    col1, col2 = st.columns([8, 2])

    with col1:
        st.text_input("You: ", placeholder="type your question", key="00_input")

    with col2:
        st.text("")
        st.text("")
        st.button("Send", on_click=send_msg)

    col1, col2 = st.columns([1, 1])

    with col1:
        clear_chat = st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)

    if st.session_state['00_chat_history']:
        for i in range(len(st.session_state['00_chat_history']) - 1, -1, -1):
            message(st.session_state['00_chat_history'][i][1], key=str(i))
            if st.session_state["00_chat_history"][i][2]:
                st.markdown(f'Sources: {st.session_state["00_chat_history"][i][2]}')
            with st.expander("Debug"):
                if st.session_state["00_chat_history"][i][3]:
                    st.markdown(f'New Question: {st.session_state["00_chat_history"][i][3]}')
                if st.session_state["00_chat_history"][i][4]:
                    st.markdown(f'Similarity chunk: {st.session_state["00_chat_history"][i][4]}')
            message(st.session_state['00_chat_history'][i][0], is_user=True, key=str(i) + '_user')
except Exception:
    traceback.print_exc()
    st.error(traceback.format_exc())
