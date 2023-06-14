import os

from langchain import SQLDatabase, SQLDatabaseChain
from langchain.chat_models import AzureChatOpenAI

import utils.env as env

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_KEY"] = env.AZURE_OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = env.AZURE_OPENAI_API_BASE


class DatabaseLLMHelper:

    def __init__(self):
        self.llm = AzureChatOpenAI(
            temperature=0.1,
            deployment_name=env.AZURE_OPENAI_CHAT_MODEL_DEPLOYMENT_NAME,
        )

        self.db = SQLDatabase.from_uri(
            database_uri=f"mysql+pymysql://{env.MYSQL_USERNAME}:{env.MYSQL_PASSWORD}@{env.MYSQL_ADDRESS}/{env.MYSQL_DATABASE}",
        )

        self.db_chain = SQLDatabaseChain.from_llm(llm=self.llm, db=self.db, verbose=False,
                                                  return_intermediate_steps=True)

    def get_response(self, prompt: str):
        question = prompt
        result = self.db_chain(question)
        if len(result["intermediate_steps"]) == 6:
            return result["result"], result["intermediate_steps"][1], result["intermediate_steps"][3]
        return result


if __name__ == "__main__":
    llmHelper = DatabaseLLMHelper()
    result = llmHelper.get_response("现在一共有多少台设备？")
    print(result)
