import base64
import os
from dotenv import load_dotenv

from server.text_loader.confluence_loader import ConfluenceLoaderHelper
from server.file_storage.azure_blob_storage import AzureBlobStorageClient

load_dotenv()


def delete_files():
    azureBlobStorageClient = AzureBlobStorageClient()
    files = azureBlobStorageClient.get_files("confluence")
    for file in files:
        print(file["filename"])
        azureBlobStorageClient.delete_file(file["filename"])


def load_confluence():
    confluenceHelper = ConfluenceLoaderHelper()
    docs = confluenceHelper.load(page_ids=["73138262"])
    print(docs)


def upload_confluence():
    confluenceHelper = ConfluenceLoaderHelper()
    docs = confluenceHelper.load_pages_from_space("9CK", max_pages=1)

    azureBlobStorageClient = AzureBlobStorageClient()
    source_url = azureBlobStorageClient.upload_confluence_text(docs[0], "9CK")
    print(source_url)


def chinese_str():
    encode_str = base64.b64encode("你好中国".encode('utf-8')).decode('utf-8')
    decode_str = base64.b64decode(encode_str).decode("utf-8")
    print(decode_str)


def list_env_var():
    mysql_list_str = os.getenv("MYSQL_URL_LIST")
    mysql_list = eval(mysql_list_str)
    print(mysql_list)


if __name__ == "__main__":
    # upload_file()
    # chinese_str()
    # load_confluence()
    list_env_var()
