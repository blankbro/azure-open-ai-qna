import os

from dotenv import load_dotenv
from langchain import SQLDatabase, SQLDatabaseChain
from langchain.chat_models import AzureChatOpenAI

load_dotenv()

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API_BASE")


class DatabaseLLMHelper:

    def __init__(self):
        self.llm = AzureChatOpenAI(
            temperature=0.1,
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_MODEL_DEPLOYMENT_NAME"),
        )

        self.db = SQLDatabase.from_uri(
            database_uri=f"mysql+pymysql://{os.getenv('MYSQL_USERNAME')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_ADDRESS')}/{os.getenv('MYSQL_DATABASE')}",
        )

        self.db_chain = SQLDatabaseChain.from_llm(
            llm=self.llm, db=self.db, verbose=False,
            return_intermediate_steps=True
        )

    def get_response(self, prompt: str):
        question = f"{prompt} reply in 中文"
        result = self.db_chain(question)
        if len(result["intermediate_steps"]) == 6:
            return result["result"], result["intermediate_steps"][1], result["intermediate_steps"][3]
        return result


if __name__ == "__main__":
    llmHelper = DatabaseLLMHelper()
    result = llmHelper.get_response("现在一共有多少台设备？")
    print(result)
