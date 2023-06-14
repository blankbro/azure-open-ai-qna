from typing import Any, Dict, Union, List

from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentFinish, AgentAction, LLMResult


class LLMChainCallbackHandler(BaseCallbackHandler):

    def __init__(self):
        self.new_question = None

    def get_new_question(self):
        return self.new_question

    def always_verbose(self) -> bool:
        return True

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        print(f"[on_llm_start] serialized = {serialized}, prompts = {prompts}, kwargs = {kwargs}")

    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        print(f"[on_llm_new_token] token = {token}, kwargs = {kwargs}")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        print(f"[on_llm_end] response = {response}, kwargs = {kwargs}")

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        print(f"[on_llm_error] error = {error}, kwargs = {kwargs}")

    # 最初的输入
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> Any:
        print(f"[on_chain_start] serialized = {serialized}, inputs = {inputs}, kwargs = {kwargs}")

    # 返回的结果
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        print(f"[on_chain_end] outputs = {outputs}, kwargs = {kwargs}")
        self.new_question = outputs["text"]

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        print(f"[on_chain_error] error = {error}, kwargs = {kwargs}")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        print(f"[on_tool_start] serialized = {serialized}, input_str = {input_str}, kwargs = {kwargs}")

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        print(f"[on_tool_end] output = {output}, kwargs = {kwargs}")

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        print(f"[on_tool_error] error = {error}, kwargs = {kwargs}")

    # 完整prompt
    def on_text(self, text: str, **kwargs: Any) -> Any:
        print(f"[on_text] text = {text}, kwargs = {kwargs}")

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        print(f"[on_agent_action] action = {action}, kwargs = {kwargs}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        print(f"[on_agent_finish] finish = {finish}, kwargs = {kwargs}")
