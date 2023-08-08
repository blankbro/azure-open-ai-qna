import traceback

import streamlit as st

from pages.common.page_config import load_page_config
from server.model.custom_prompt import completion_prompt_template
from server.model.document_llm_helper import DocumentLLMHelper

load_page_config()


def clear_chat_data():
    st.session_state.zero_messages = []


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
    if 'zero_messages' not in st.session_state:
        st.session_state.zero_messages = []
    if 'zero_history' not in st.session_state:
        st.session_state.zero_history = []

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

    # Display chat messages from history on app rerun
    for message in st.session_state.zero_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "source" in message and message["source"]:
                st.markdown(f'\n\nSources: {message["source"]}')
            if "new_question" in message and message["new_question"]:
                st.markdown(f'New question: {message["new_question"]}')
            if "similarity_chunk" in message and message["similarity_chunk"]:
                with st.expander("Similarity chunk"):
                    st.markdown(f'{message["similarity_chunk"]}')

    # Accept user input
    if prompt := st.chat_input("type your question"):
        # Add user message to chat history
        st.session_state.zero_messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # ask openai
            new_question, answer, sources, contents = llm_helper.get_response(prompt, st.session_state.zero_history)
            st.markdown(answer)
            st.markdown(f'\n\nSources: {sources}')
            if new_question:
                st.markdown(f'New question: {new_question}')
            if contents:
                with st.expander("Similarity chunk"):
                    st.markdown(f'{contents}')
        # Add assistant response to chat history
        st.session_state.zero_messages.append({
            "role": "assistant",
            "content": answer,
            "source": sources,
            "new_question": new_question,
            "similarity_chunk": contents,
        })
        st.session_state.zero_history.append((prompt, answer))
        st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)
except Exception:
    traceback.print_exc()
    st.error(traceback.format_exc())
