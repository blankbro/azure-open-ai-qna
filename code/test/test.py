import base64

from utils.document_loader.confluence_loader_helper import ConfluenceLoaderHelper
from utils.document_storage import AzureBlobStorageClient


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
    docs = confluenceHelper.load_all_pages_from_space("9CK", max_pages=1)

    azureBlobStorageClient = AzureBlobStorageClient()
    source_url = azureBlobStorageClient.upload_confluence(docs[0], "9CK")
    print(source_url)


def chinese_str():
    encode_str = base64.b64encode("你好中国".encode('utf-8')).decode('utf-8')
    decode_str = base64.b64decode(encode_str).decode("utf-8")
    print(decode_str)


if __name__ == "__main__":
    # upload_file()
    # chinese_str()
    load_confluence()
