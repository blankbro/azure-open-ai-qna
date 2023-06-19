import hashlib
import logging
import os
import re

from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chat_models import AzureChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings.openai import OpenAIEmbeddings

from server.file_storage.azure_blob_storage import AzureBlobStorageClient
from server.model.custom_handler import LLMChainCallbackHandler
from server.model.custom_prompt import COMPLETION_PROMPT
from server.model.document_util import document_to_markdown_link
from server.text_loader.azure_form_recognizer import AzureFormRecognizerClient
from server.text_splitter.custom_text_splitter import CustomTextSplitter
from server.vector_storage.redis import RedisExtended

load_dotenv()

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API_BASE")


class DocumentLLMHelper:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            temperature=0.2,
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_MODEL_DEPLOYMENT_NAME"),
        )

        self.embedding_model = OpenAIEmbeddings(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_DEPLOYMENT_NAME"),
            chunk_size=1
        )

        self.vector_store = RedisExtended(
            embedding_function=self.embedding_model.embed_query
        )

        self.blob_storage_client = AzureBlobStorageClient()

        self.pdf_parser = AzureFormRecognizerClient()

        self.text_splitter = CustomTextSplitter()

    def get_response(self, question, chat_history):
        llm_chain_custom_handler = LLMChainCallbackHandler()

        question_generator = LLMChain(
            llm=self.llm,
            prompt=CONDENSE_QUESTION_PROMPT,
            # verbose=True,
            callbacks=[llm_chain_custom_handler],
        )

        doc_chain = load_qa_with_sources_chain(
            self.llm,
            chain_type="stuff",
            # verbose=True,
            prompt=COMPLETION_PROMPT
        )

        chain = ConversationalRetrievalChain(
            retriever=self.vector_store.as_retriever(
                # k=self.k,
                # score_threshold=self.score_threshold,
                search_type="similarity_limit"
            ),
            question_generator=question_generator,
            combine_docs_chain=doc_chain,
            return_source_documents=True,
        )

        result = chain({"question": question, "chat_history": chat_history})

        context = "\n\n".join(list(map(lambda x: x.page_content, result['source_documents'])))
        sources = "\n\n".join(set(map(lambda x: document_to_markdown_link(x), result['source_documents'])))
        sources = sources.replace('_SAS_TOKEN_PLACEHOLDER_', self.blob_storage_client.get_container_sas())

        return result['answer'], sources, llm_chain_custom_handler.get_new_question()

    def convert_file_and_add_embeddings(self, source_file_bytes: bytes = None, source_file_url: str = None, filename: str = None):
        assert source_file_bytes or source_file_url
        assert filename

        # Extract the text from the file
        text = self.pdf_parser.analyze_read(source_file_bytes, source_file_url)

        # Upload the text to Azure Blob Storage
        converted_filename = f"converted/{filename}.txt"
        convert_file_url = self.blob_storage_client.upload_file("\n".join(text), f"converted/{filename}.txt", content_type='text/plain; charset=utf-8')

        print(f"Converted file uploaded to {convert_file_url} with filename {filename}")
        # Update the metadata to indicate that the file has been converted
        self.blob_storage_client.update_metadata(filename, {"converted": "true"})

        self.add_embeddings_lc(source_url=convert_file_url)

        return converted_filename

    def add_embeddings_lc(self, source_url):
        try:
            documents = WebBaseLoader(source_url).load()

            # Convert to UTF-8 encoding for non-ascii text
            for (document) in documents:
                try:
                    if document.page_content.encode("iso-8859-1") == document.page_content.encode("latin-1"):
                        document.page_content = document.page_content.encode("iso-8859-1").decode("utf-8", errors="ignore")
                except:
                    pass

            docs = self.text_splitter.split_documents(documents)

            # Remove half non-ascii character from start/end of doc content (langchain TokenTextSplitter may split a non-ascii character in half)
            pattern = re.compile(r'[\x00-\x1f\x7f\u0080-\u00a0\u2000-\u3000\ufff0-\uffff]')
            for (doc) in docs:
                doc.page_content = re.sub(pattern, '', doc.page_content)
                if doc.page_content == '':
                    docs.remove(doc)

            keys = []
            filenames = set()
            for i, doc in enumerate(docs):
                # Create a unique key for the document
                source_url = source_url.split('?')[0]
                filename = "/".join(source_url.split('/')[4:])
                hash_key = hashlib.sha1(f"{source_url}_{i}".encode('utf-8')).hexdigest()
                hash_key = f"doc:{self.vector_store.index_name}:{hash_key}"
                keys.append(hash_key)
                doc.metadata = {"source": f"[{source_url}]({source_url}_SAS_TOKEN_PLACEHOLDER_)", "chunk": i, "key": hash_key, "filename": filename}
                filenames.add(filename)
                self.vector_store.add_documents(documents=docs, redis_url=self.vector_store.redis_url, index_name=self.vector_store.index_name, keys=keys)

        except Exception as e:
            logging.error(f"Error adding embeddings for {source_url}: {e}")
            raise e


if __name__ == "__main__":
    llmHelper = DocumentLLMHelper()
    print(llmHelper.get_response("你是谁？", {}))
