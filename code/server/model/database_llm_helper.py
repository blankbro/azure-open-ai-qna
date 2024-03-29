import os

from dotenv import load_dotenv
from langchain.chat_models import AzureChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

load_dotenv()

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API_BASE")


class DatabaseLLMHelper:

    def __init__(self, database_uri: str):
        self.llm = AzureChatOpenAI(
            temperature=0.1,
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_MODEL_DEPLOYMENT_NAME"),
        )

        self.db = SQLDatabase.from_uri(database_uri=database_uri)

        self.db_chain = SQLDatabaseChain.from_llm(
            llm=self.llm, db=self.db, verbose=False,
            return_intermediate_steps=True
        )

    def get_response(self, prompt: str):
        question = f"{prompt} reply in 中文"
        result = self.db_chain(question)
        if len(result["intermediate_steps"]) == 6:
            return result["result"], result["intermediate_steps"][1], result["intermediate_steps"][3].lstrip("[(").rstrip(",)]")
        return result


if __name__ == "__main__":
    llmHelper = DatabaseLLMHelper()
    result = llmHelper.get_response("现在一共有多少台设备？")
    print(result)
