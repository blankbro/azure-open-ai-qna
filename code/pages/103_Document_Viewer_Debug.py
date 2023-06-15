import requests
import streamlit as st
import os
import traceback
from core.llm_helper.document_llm_helper import DocumentLLMHelper
from core.document_storage.azure_blob_storage import AzureBlobStorageClient
import datetime
import urllib


def now_date_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


try:
    # Set page layout to wide screen and menu item
    menu_items = {
        'Get help': None,
        'Report a bug': None,
        'About': '''
            ## Embeddings App

            Document Reader Sample Demo.
        '''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    llm_helper = DocumentLLMHelper()
    bolb_client = AzureBlobStorageClient()

    files_data = bolb_client.get_files()

    # 待探索，新增多选框
    st.dataframe(files_data, use_container_width=True)

    if st.button("补充缺失的 converted文件 和 embeddings向量"):
        for i in range(len(files_data)):
            file_data = files_data[i]
            filename = file_data["filename"]
            if file_data.get("converted") is False and not filename.endswith('.txt'):
                st.write(f"{now_date_time()}【{i}】{filename} 开始生成 converted文件 和 embeddings向量")
                converted_filename = llm_helper.convert_file_and_add_embeddings(bytes_data=requests.get(file_data["fullpath"]).content, source_url=None, filename=filename, enable_translation=False)
                llm_helper.blob_client.upsert_blob_metadata(filename, {'converted': 'true', 'embeddings_added': 'true', 'converted_filename': urllib.parse.quote(converted_filename)})
                st.write(f"{now_date_time()}【{i}】{filename} 完成了")
            elif file_data.get("embeddings_added") is False:
                st.write(f"{now_date_time()}【{i}】{filename} 开始生成 embeddings向量")
                llm_helper.add_embeddings_lc(file_data["fullpath"])
                llm_helper.blob_client.upsert_blob_metadata(filename, {'embeddings_added': 'true'})
                st.write(f"{now_date_time()}【{i}】{filename} 完成了")
        st.write("所有文件已处理完成")
    if st.button("将所有文档 embeddings_added 状态置为 false"):
        for i in range(len(files_data)):
            file_data = files_data[i]
            filename = file_data["filename"]
            st.write(f"{now_date_time()}【{i}】{filename} 开始了")
            llm_helper.blob_client.upsert_blob_metadata(filename, {'embeddings_added': 'false'})
            st.write(f"{now_date_time()}【{i}】{filename} 完成了")
        st.write("所有文件已处理完成")
except Exception as e:
    traceback.print_exc()
    st.error(traceback.format_exc())
