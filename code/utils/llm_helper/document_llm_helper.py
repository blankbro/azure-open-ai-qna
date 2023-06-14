import os

from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings

import utils.env as env
from custom_handler import LLMChainCallbackHandler
from custom_prompt import COMPLETION_PROMPT
from document_util import document_to_markdown_link
from utils.document_storage.azure_blob_storage import AzureBlobStorageClient
from utils.vector_db.redis import RedisExtended

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_KEY"] = env.AZURE_OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = env.AZURE_OPENAI_API_BASE


class DocumentLLMHelper:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            temperature=0.2,
            deployment_name=env.AZURE_OPENAI_CHAT_MODEL_DEPLOYMENT_NAME,
        )

        self.embedding_model = OpenAIEmbeddings(
            model=env.AZURE_OPENAI_EMBEDDING_MODEL_DEPLOYMENT_NAME,
            chunk_size=1
        )

        self.vector_store = RedisExtended(
            redis_url=f"redis://:{env.REDIS_PASSWORD}@{env.REDIS_ADDRESS}:{env.REDIS_PORT}",
            index_name="embeddings",
            embedding_function=self.embedding_model.embed_query
        )

        self.blob_client = AzureBlobStorageClient()

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
        sources = sources.replace('_SAS_TOKEN_PLACEHOLDER_', self.blob_client.get_container_sas())

        return result['answer'], sources, llm_chain_custom_handler.get_new_question()


if __name__ == "__main__":
    llmHelper = DocumentLLMHelper()
    print(llmHelper.get_response("你是谁？", {}))
