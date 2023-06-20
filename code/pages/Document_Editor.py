import traceback

import requests
import streamlit as st

from pages.common.page_config import load_page_config
from server.model.document_llm_helper import DocumentLLMHelper

load_page_config()


def convert_file_and_add_embeddings():
    placeholder = st.empty()
    for i, file_data in enumerate(files_data):
        filename = file_data["filename"]
        placeholder.write(f"当前进度: {i + 1}/{len(files_data)}【{filename}】")
        if file_data.get("converted") is False and not filename.endswith('.txt'):
            llm_helper.convert_file_and_add_embeddings(source_file_bytes=requests.get(file_data["fullpath"]).content, filename=filename)
        elif file_data.get("embeddings_added") is False:
            llm_helper.add_embeddings(file_data["converted_path"], filename)
    placeholder.empty()


def delete_embeddings():
    placeholder = st.empty()
    for i in range(len(files_data)):
        file_data = files_data[i]
        filename = file_data["filename"]
        placeholder.write(f"当前进度: {i + 1}/{len(files_data)}【{filename}】")
        if file_data["embeddings_added"]:
            llm_helper.blob_storage_client.update_metadata(filename, {'embeddings_added': 'false'})
    llm_helper.delete_embeddings()
    placeholder.empty()


try:
    llm_helper = DocumentLLMHelper()

    files_data = llm_helper.get_files()

    st.dataframe(files_data, use_container_width=True)

    st.button("提取pdf中的文本，并生成embeddings向量", on_click=convert_file_and_add_embeddings)

    st.button("删除所有 embeddings 向量", on_click=delete_embeddings)

except Exception as e:
    traceback.print_exc()
    st.error(traceback.format_exc())
