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

    def upload_confluence(self, doc: Document, confluence_space_name: str) -> str:
        return self.upload_file(
            bytes_data=doc.metadata["title"] + " " + doc.page_content,
            file_name=f"confluence/{confluence_space_name}/{doc.metadata['id']}/v{doc.metadata['version']}/{doc.metadata['title']}.txt",
            content_type='text/plain; charset=utf-8',
            metadata={
                "link": f"{doc.metadata['source']}",
                # 由于底层组件的限制，header 中不允许出现中文。写入的时候通过base64编码，读取的时候再通过base64解码
                "title": chinese_encode(doc.metadata["title"]),
                "version": f"{doc.metadata['version']}",
                "last_edit_time": f"{doc.metadata['last_edit_time']}"
            }
        )

    def upload_file(self, bytes_data, file_name, content_type, metadata: Optional[Dict[str, str]] = None, ) -> str:
        """
            content_type:
                txt ==> text/plain; charset=utf-8
                pdf ==> application/pdf
        """
        # Create a blob client using the local file name as the name for the blob
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        # Upload the created file
        blob_client.upload_blob(
            bytes_data, overwrite=True, content_settings=ContentSettings(content_type=content_type), metadata=metadata
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
        blob_list = container_client.list_blobs(name_starts_with=name_starts_with)
        sas = self.get_container_sas()

        # 组装信息
        files = []
        converted_files = {}
        for blob in blob_list:
            if blob.name.startswith('converted/'):
                converted_files[blob.name] = self.get_blob_sas(blob.name, sas)
            else:
                files.append({
                    "filename": blob.name,
                    "converted": blob.metadata.get('converted', 'false') == 'true' if blob.metadata else False,
                    "embeddings_added": blob.metadata.get('embeddings_added', 'false') == 'true' if blob.metadata else False,
                    "fullpath": self.get_blob_sas(blob.name, sas),
                    "converted_filename": blob.metadata.get('converted_filename', '') if blob.metadata else '',
                    "converted_path": ""
                })

        # 补充 converted_path
        for file in files:
            converted_filename = "converted/" + file.get('filename', '') + ".txt"
            if converted_filename in converted_files:
                file['converted'] = True
                file['converted_filename'] = converted_filename
                file['converted_path'] = converted_files[converted_filename]
            else:
                file['converted'] = False
                file['converted_filename'] = ""
                file['converted_path'] = ""

        return files

    def delete_file(self, file_name):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
        blob_client.delete_blob()
