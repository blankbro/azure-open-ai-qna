import re

from langchain.schema import Document
import urllib


# 将Document转换成markdown格式的超链接
def document_to_markdown_link(doc: Document):
    # 截取URL，并处理空格
    match = re.search("\((.*)\)", doc.metadata["source"])
    if match:
        docurl = match.group(1).replace(" ", "%20")
    else:
        docurl = ""
    # 将超链接转化成源文件的
    converted_filename = doc.metadata["filename"]
    source_filename = converted_filename.lstrip("converted/").rstrip(".txt")
    return f"[{urllib.parse.unquote(source_filename)}]({docurl.replace(converted_filename, source_filename)})"
