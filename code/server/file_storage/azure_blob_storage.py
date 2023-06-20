import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

from azure.storage.blob import BlobServiceClient, ContentSettings, generate_container_sas
from langchain.docstore.document import Document


def chinese_encode(chinese_str: str) -> str:
    return base64.b64encode(chinese_str.encode('UTF-8')).decode('UTF-8')


def chinese_decode(encode_str) -> str:
    return base64.b64decode(encode_str).decode("UTF-8")


class AzureBlobStorageClient:
    def __init__(self, account_name: str = None, account_key: str = None, container_name: str = None):
        self.account_name: str = account_name if account_name else os.getenv("AZURE_BLOB_STORAGE_ACCOUNT_NAME")
        self.account_key: str = account_key if account_key else os.getenv("AZURE_BLOB_STORAGE_ACCOUNT_KEY")
        self.connect_str: str = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.account_key};EndpointSuffix=core.windows.net"
        self.container_name: str = container_name if container_name else os.getenv("AZURE_BLOB_STORAGE_CONTAINER_NAME")
        self.blob_service_client: BlobServiceClient = BlobServiceClient.from_connection_string(self.connect_str)

    def upload_confluence_text(self, doc: Document, confluence_space_name: str) -> str:
        return self.upload_blob(
            data=doc.metadata["title"] + " " + doc.page_content,
            file_name=f"confluence/{confluence_space_name}/{doc.metadata['id']}/v{doc.metadata['version']}/{doc.metadata['title']}.txt",
            content_type='text/plain; charset=utf-8',
            metadata={
                "confluence_url": doc.metadata["source"]
            }
        )

    def upload_blob(self, data, file_name, content_type, metadata: Optional[Dict[str, str]] = None) -> str:
        """
            content_type:
                txt ==> text/plain; charset=utf-8
                pdf ==> application/pdf
        """
        # Create a blob client using the local file name as the name for the blob
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        # Upload the created file
        blob_client.upload_blob(
            data, overwrite=True, content_settings=ContentSettings(content_type=content_type), metadata=metadata
        )
        # Generate a SAS URL to the blob and return it
        return blob_client.url + '?' + self.get_container_sas()

    def update_metadata(self, file_name, metadata):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        # Read metadata from the blob
        blob_metadata = blob_client.get_blob_properties().metadata
        # Update metadata
        blob_metadata.update(metadata)
        # Add metadata to the blob
        blob_client.set_blob_metadata(metadata=blob_metadata)

    def get_container_sas(self):
        return generate_container_sas(self.account_name, self.container_name, account_key=self.account_key, permission="r", expiry=datetime.utcnow() + timedelta(hours=3))

    def get_blob_sas(self, file_name, sas):
        # Generate a SAS URL to the blob and return it
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{file_name}?{sas}"

    def get_files(self, name_starts_with: str = None):
        # 获取文件列表
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_list = container_client.list_blobs(name_starts_with=name_starts_with, include='metadata')
        sas = self.get_container_sas()

        # 组装信息
        files = []
        converted_files = {}
        for blob in blob_list:
            if blob.name.startswith('converted/'):
                converted_files[blob.name] = self.get_blob_sas(blob.name, sas)
            else:
                files.append({
                    "source_file_name": blob.name.split("/")[-1],
                    "source_file_url": blob.metadata.get('confluence_url', self.get_blob_sas(blob.name, sas)),
                    "source_file_key": blob.name,
                    "embeddings_added": blob.metadata.get('embeddings_added', 'false') == 'true' if blob.metadata else False,
                })

        # 补充 converted_path
        for file in files:
            if file["source_file_name"].endswith('.txt'):
                file['converted'] = True
                file['converted_file_name'] = file['source_file_name']
                file['converted_file_url'] = self.get_blob_sas(file['source_file_key'], sas)
                continue
            converted_filename = f"converted/{file.get('source_file_key')}.txt"
            if converted_filename in converted_files:
                file['converted'] = True
                file['converted_file_name'] = converted_filename
                file['converted_file_url'] = converted_files[converted_filename]
            else:
                file['converted'] = False
                file['converted_file_name'] = ""
                file['converted_file_url'] = ""

        return files

    def delete_files(self, name_starts_with):
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_name_list = container_client.list_blob_names(name_starts_with=name_starts_with)
        container_client.delete_blobs(*blob_name_list)

    def delete_file(self, file_name):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        blob_client.delete_blob()
