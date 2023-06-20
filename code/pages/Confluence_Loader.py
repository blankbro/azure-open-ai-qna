import sys

import streamlit as st

from pages.common.page_config import load_page_config
from server.file_storage.azure_blob_storage import AzureBlobStorageClient
from server.text_loader.confluence_loader import ConfluenceLoaderHelper

load_page_config()


def load():
    confluence_space_name = st.session_state["confluence_space_name"]
    if confluence_space_name == "None":
        st.warning("请先选择空间")
        sys.exit()

    # 获取空间的所有页面
    confluence_space_key = space_name_key_map[confluence_space_name]
    pages = confluenceLoaderHelper.get_pages_from_space(confluence_space_key, max_pages=-1)
    st.write(f"共{len(pages)}个页面")
    placeholder = st.empty()

    azure_blob_storage_client = AzureBlobStorageClient()
    for i, page in enumerate(pages):
        placeholder.write(f"当前进度: {i + 1}/{len(pages)}【{page['title']}】")

        # 提取页面的文本
        doc = confluenceLoaderHelper.load_page(page)
        if not doc:
            st.write(f"{i + 1}【{page['title']}】page content is empty")
            continue

        # 上传到 Azure Blob Storage
        azure_blob_storage_client.upload_confluence(doc, confluence_space_name)
        st.write(f"{i + 1}【{page['title']}】ok")


st.title("Add all confluence document to the knowledge base")
confluenceLoaderHelper = ConfluenceLoaderHelper()

# 获取所有空间
spaces = confluenceLoaderHelper.get_spaces()
space_names = ["None"]
space_name_key_map = {}
for space in spaces:
    space_names.append(space["name"])
    space_name_key_map[space["name"]] = space["key"]

st.selectbox("Confluence 空间列表", space_names, key="confluence_space_name", label_visibility="hidden")

st.button("Load confluence document", on_click=load)
