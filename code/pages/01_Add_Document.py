import sys

import streamlit as st

from utils.document_loader import ConfluenceLoaderHelper
from utils.document_storage import AzureBlobStorageClient

st.set_page_config(layout="wide")

with st.expander("Add all confluence document to the knowledge base", expanded=False):
    confluenceLoaderHelper = ConfluenceLoaderHelper()
    # 获取所有空间
    spaces = confluenceLoaderHelper.get_all_spaces()
    space_names = ["None"]
    space_name_key_map = {}
    for space in spaces:
        space_names.append(space["name"])
        space_name_key_map[space["name"]] = space["key"]

    st.title("Add all confluence document to the knowledge base")
    st.selectbox("Confluence 空间列表", space_names, key="confluence_space_name", label_visibility="hidden")
    if st.button("Load confluence document"):
        confluence_space_name = st.session_state["confluence_space_name"]
        if confluence_space_name == "None":
            st.warning("请先选择空间")
            sys.exit()

        # 获取空间的所有页面
        confluence_space_key = space_name_key_map[confluence_space_name]
        pages = confluenceLoaderHelper.get_all_pages_from_space(confluence_space_key, max_pages=-1)
        st.write(f"共{len(pages)}个页面")
        placeholder = st.empty()

        azureBlobStorageClient = AzureBlobStorageClient()
        for i in range(len(pages)):
            page = pages[i]
            placeholder.write(f"当前进度: {i + 1}/{len(pages)}【{page['title']}】")

            # 提取页面的文本
            doc = confluenceLoaderHelper.load_single_page(page)
            if not doc:
                st.write(f"{i + 1}【{page['title']}】page content is empty")
                continue

            # 上传到 Azure Blob Storage
            azureBlobStorageClient.upload_confluence(doc)
            st.write(f"{i + 1}【{page['title']}】ok")
