from utils.document_loader import ConfluenceLoaderHelper
from utils.document_storage import AzureBlobStorageClient

if __name__ == "__main__":
    confluenceHelper = ConfluenceLoaderHelper()
    docs = confluenceHelper.load_all_pages_from_space("9CK", max_pages=1)

    azureBlobStorageClient = AzureBlobStorageClient()
    source_url = azureBlobStorageClient.upload_confluence(docs[0])
    print(source_url)
