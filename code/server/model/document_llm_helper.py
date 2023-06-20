import hashlib
import logging
import os
import re
import urllib

import requests
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chat_models import AzureChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate

from server.file_storage.azure_blob_storage import AzureBlobStorageClient
from server.model.custom_handler import LLMChainCallbackHandler
from server.model.custom_prompt import COMPLETION_PROMPT, DOCUMENT_FORMAT
from server.text_loader.azure_form_recognizer import AzureFormRecognizerClient
from server.text_splitter.custom_text_splitter import CustomTextSplitter
from server.vector_storage.redis import RedisExtended

load_dotenv()

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API_BASE")


def generate_md_superlink_by_document(doc):
    docurl = doc.metadata['source_file_url'].replace(" ", "%20")
    return f"[{doc.metadata['source_file_name']}]({docurl}?_SAS_TOKEN_PLACEHOLDER_)"


class DocumentLLMHelper:
    def __init__(
            self,
            completion_prompt: str = None,
            temperature: float = None,
            redisearch_topk: int = None,
            redisearch_similarity_score: float = None,
            redisearch_type: str = None,
    ):
        self.completion_prompt = COMPLETION_PROMPT if completion_prompt is None else PromptTemplate(template=completion_prompt, input_variables=["summaries", "question"])
        self.redisearch_topk = 4 if redisearch_topk is None else redisearch_topk
        self.redisearch_similarity_score = 0.4 if redisearch_similarity_score is None else redisearch_similarity_score
        self.redisearch_type = "similarity_limit" if redisearch_type is None else redisearch_type

        self.llm = AzureChatOpenAI(
            temperature=0.2 if temperature is None else temperature,
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

        self.text_splitter = CustomTextSplitter(chunk_size=500, chunk_overlap=100)

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
            prompt=self.completion_prompt,
            document_prompt=DOCUMENT_FORMAT
        )

        chain = ConversationalRetrievalChain(
            retriever=self.vector_store.as_retriever(
                k=self.redisearch_topk,
                score_threshold=self.redisearch_similarity_score,
                search_type=self.redisearch_type
            ),
            question_generator=question_generator,
            combine_docs_chain=doc_chain,
            return_source_documents=True,
        )

        result = chain({"question": question, "chat_history": chat_history})

        context = "\n\n".join(list(map(lambda x: x.page_content, result['source_documents'])))
        sources = "\n\n".join(set(map(lambda x: generate_md_superlink_by_document(x), result['source_documents'])))
        sources = sources.replace('_SAS_TOKEN_PLACEHOLDER_', self.blob_storage_client.get_container_sas())

        return llm_chain_custom_handler.get_new_question(), result['answer'], sources, context

    def convert_file_and_add_embeddings(self, source_file_url: str = None):
        source_url = source_file_url.split('?')[0]
        source_file_key = "/".join(source_url.split('/')[4:])
        source_file_name = source_file_key.split('/')[-1]

        source_file_bytes = requests.get(source_file_url).content

        # Extract the text from the file
        text = self.pdf_parser.analyze_read(source_file_bytes, source_file_url)

        # Upload the text to Azure Blob Storage
        converted_file_key = f"converted/{source_file_key}.txt"
        convert_file_url = self.blob_storage_client.upload_blob("\n".join(text), f"converted/{source_file_key}.txt", content_type='text/plain; charset=utf-8')

        print(f"Converted file uploaded to {convert_file_url} with source_file_key {source_file_key}")
        # Update the metadata to indicate that the file has been converted
        self.blob_storage_client.update_metadata(source_file_key, {"converted": "true", "converted_file_key": urllib.parse.quote(converted_file_key)})

        self.add_embeddings(
            converted_file_url=convert_file_url,
            source_file_name=source_file_name,
            source_file_key=source_file_key,
            source_file_url=source_file_url
        )

        return converted_file_key

    def add_embeddings(self, converted_file_url, source_file_name, source_file_key, source_file_url):
        try:
            documents = WebBaseLoader(converted_file_url).load()

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
            for i, doc in enumerate(docs):
                # Create a unique key for the document
                hash_key = hashlib.sha1(f"{source_file_key}".encode('utf-8')).hexdigest()
                keys.append(f"doc:{self.vector_store.index_name}:{hash_key}:{i}")
                doc.metadata = {
                    "source_file_name": source_file_name,
                    "source_file_key": source_file_key,
                    "source_file_url": source_file_url.split('?')[0],
                    "chunk": i
                }

            self.vector_store.add_documents(documents=docs, redis_url=self.vector_store.redis_url, index_name=self.vector_store.index_name, keys=keys)

            self.blob_storage_client.update_metadata(source_file_key, {'embeddings_added': 'true'})

        except Exception as e:
            logging.error(f"Error adding embeddings for {converted_file_url}: {e}")
            raise e

    def delete_embeddings(self):
        # self.vector_store.delete_keys_pattern()
        self.vector_store.delete_all()

    def get_files(self):
        return self.blob_storage_client.get_files()


if __name__ == "__main__":
    llmHelper = DocumentLLMHelper()
    print(llmHelper.get_response("你是谁？", {}))
