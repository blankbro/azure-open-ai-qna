from langchain.prompts import PromptTemplate

completion_prompt_template = """{summaries}
Please reply to the question using only the information present in the text above. 
If you can't find it, reply politely that the information is not in the knowledge base.
Reply in 中文.
Question: {question}
Answer:"""

COMPLETION_PROMPT = PromptTemplate(
    template=completion_prompt_template,
    input_variables=["summaries", "question"]
)
