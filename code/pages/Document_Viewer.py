import streamlit as st

from pages.common.page_config import load_page_config
from server.file_storage.azure_blob_storage import AzureBlobStorageClient

load_page_config()

blob_client = AzureBlobStorageClient()

col1, col2, col3 = st.columns([2, 1, 1])

files_data = blob_client.get_files()

st.dataframe(files_data, use_container_width=True)
