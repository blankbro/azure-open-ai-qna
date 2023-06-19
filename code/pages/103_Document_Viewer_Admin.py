import datetime
import os
import traceback
import urllib

import requests
import streamlit as st
from dotenv import load_dotenv

from server.file_storage.azure_blob_storage import AzureBlobStorageClient
from server.model.document_llm_helper import DocumentLLMHelper

load_dotenv()


def now_date_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


st.set_page_config(
    layout="wide",
    page_title=os.getenv("PAGE_TITLE"),
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

try:
    llm_helper = DocumentLLMHelper()
    bolb_client = AzureBlobStorageClient()

    files_data = bolb_client.get_files()

    # 待探索，新增多选框
    st.dataframe(files_data, use_container_width=True)

    if st.button("提取pdf中的文本，并生成embeddings向量"):
        for i in range(len(files_data)):
            file_data = files_data[i]
            filename = file_data["filename"]
            if file_data.get("converted") is False and not filename.endswith('.txt'):
                st.write(f"{now_date_time()}【{i}】{filename} 开始生成 converted文件 和 embeddings向量")
                converted_filename = llm_helper.convert_file_and_add_embeddings(
                    source_file_bytes=requests.get(file_data["fullpath"]).content,
                    filename=filename
                )
                llm_helper.blob_storage_client.upsert_blob_metadata(filename, {'converted': 'true', 'embeddings_added': 'true', 'converted_filename': urllib.parse.quote(converted_filename)})
                st.write(f"{now_date_time()}【{i}】{filename} 完成了")
            elif file_data.get("embeddings_added") is False:
                st.write(f"{now_date_time()}【{i}】{filename} 开始生成 embeddings向量")
                llm_helper.add_embeddings_lc(file_data["fullpath"])
                llm_helper.blob_storage_client.upsert_blob_metadata(filename, {'embeddings_added': 'true'})
                st.write(f"{now_date_time()}【{i}】{filename} 完成了")
        st.write("所有文件已处理完成")
    if st.button("删除所有文档的 embeddings 向量"):
        for i in range(len(files_data)):
            file_data = files_data[i]
            filename = file_data["filename"]
            st.write(f"{now_date_time()}【{i}】{filename} 开始了")
            llm_helper.blob_storage_client.upsert_blob_metadata(filename, {'embeddings_added': 'false'})
            st.write(f"{now_date_time()}【{i}】{filename} 完成了")
        st.write("所有文件已处理完成")
except Exception as e:
    traceback.print_exc()
    st.error(traceback.format_exc())
