import os
import traceback

import streamlit as st
from dotenv import load_dotenv

from server.file_storage.azure_blob_storage import AzureBlobStorageClient

load_dotenv()

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

    blob_client = AzureBlobStorageClient()

    col1, col2, col3 = st.columns([2, 1, 1])

    files_data = blob_client.get_files()

    st.dataframe(files_data, use_container_width=True)

except Exception as e:
    st.error(traceback.format_exc())
