import sys

import streamlit as st
import pandas as pd

from pages.common.page_config import load_page_config
from server.file_storage.azure_blob_storage import AzureBlobStorageClient
from server.model.document_llm_helper import DocumentLLMHelper
from server.text_loader.confluence_loader import ConfluenceLoaderHelper

load_page_config()

llm_helper = DocumentLLMHelper()
confluence_loader_helper = ConfluenceLoaderHelper()
azure_blob_storage_client = AzureBlobStorageClient()

placeholder = st.empty()
with st.expander("Convert file and add embeddings", expanded=False):
    files_data = llm_helper.get_files()
    file_count = len(files_data)
    st.dataframe(files_data, hide_index=False, column_order=("source_file_name", "converted", "embeddings_added", "source_file_url", "converted_file_url"))
    if st.button("提取pdf中的文本，并生成embeddings向量"):
        for i, file_data in enumerate(files_data):
            source_file_name = file_data["source_file_name"]
            source_file_key = file_data["source_file_key"]
            source_file_url = file_data["source_file_url"]
            converted_file_url = file_data["converted_file_url"]
            placeholder.write(f"当前进度: {i + 1}/{file_count}【{source_file_name}】")
            if file_data.get("converted") is False and not source_file_name.endswith('.txt'):
                llm_helper.convert_file_and_add_embeddings(source_file_url=source_file_url)
            elif file_data.get("embeddings_added") is False:
                llm_helper.add_embeddings(
                    converted_file_url=converted_file_url,
                    source_file_name=source_file_name,
                    source_file_key=source_file_key,
                    source_file_url=source_file_url
                )
        placeholder.write("all is ok")
    if st.button("删除所有 embeddings 向量"):
        for i, file_data in enumerate(files_data):
            source_file_name = file_data["source_file_name"]
            source_file_key = file_data["source_file_key"]
            placeholder.write(f"当前进度: {i + 1}/{len(files_data)}【{source_file_name}】")
            if file_data["embeddings_added"]:
                llm_helper.blob_storage_client.update_metadata(source_file_key, {'embeddings_added': 'false'})
        llm_helper.delete_embeddings()
        placeholder.write("all is ok")

with st.expander("Edit confluence document"):
    # 获取所有空间
    spaces = confluence_loader_helper.get_spaces()
    space_names = ["None"]
    space_name_key_map = {}
    for space in spaces:
        space_names.append(space["name"])
        space_name_key_map[space["name"]] = space["key"]

    st.selectbox("Select confluence space", space_names, key="confluence_space_name")

    if st.button("Convert confluence"):
        confluence_space_name = st.session_state["confluence_space_name"]
        if confluence_space_name == "None":
            st.warning("请先选择空间")
            sys.exit()

        # 获取空间的所有页面
        confluence_space_key = space_name_key_map[confluence_space_name]
        pages = confluence_loader_helper.get_pages_from_space(confluence_space_key, max_pages=-1)

        for i, page in enumerate(pages):
            placeholder.write(f"当前进度: {i + 1}/{len(pages)}【{page['title']}】")

            # 提取页面的文本
            doc = confluence_loader_helper.load_page(page)
            if not doc:
                continue

            # 上传到 Azure Blob Storage
            azure_blob_storage_client.upload_confluence_text(doc, confluence_space_name)

        placeholder.write("all is ok")
    if st.button("Delete confluence from the knowledge base"):
        confluence_space_name = st.session_state["confluence_space_name"]
        if confluence_space_name == "None":
            st.warning("请先选择空间")
            sys.exit()

        azure_blob_storage_client.delete_files(f"confluence/{confluence_space_name}")
        placeholder.write("all is ok")
