from datetime import datetime
from typing import List, Optional

from atlassian import Confluence
from langchain.docstore.document import Document
from langchain.document_loaders import ConfluenceLoader

import utils.env as env


class ConfluenceLoaderHelper:

    def __init__(self):
        self.confluenceLoader = ConfluenceLoader(
            url=env.CONFLUENCE_URL,
            username=env.CONFLUENCE_USERNAME,
            api_key=env.CONFLUENCE_PASSWORD,
        )

        self.confluence = Confluence(
            url=env.CONFLUENCE_URL,
            username=env.CONFLUENCE_USERNAME,
            password=env.CONFLUENCE_PASSWORD,
        )

    # 默认的load方式，有一些局限
    def load(
            self,
            space_key: Optional[str] = None,
            page_ids: Optional[List[str]] = None,
            limit: Optional[int] = 50,
            max_pages: Optional[int] = 1000,
    ) -> List[Document]:
        return self.confluenceLoader.load(
            space_key=space_key,
            page_ids=page_ids,
            include_attachments=True,
            limit=limit,
            max_pages=max_pages,
            ocr_languages="eng+chi_sim"
        )

    def get_all_spaces(self):
        response = self.confluence.get_all_spaces(space_type="global")
        results = response["results"]
        spaces = []

        for result in results:
            space = {
                "name": result["name"],
                "id": result["id"],
                "key": result["key"],
                "source": response["_links"]["base"] + result["_links"]["webui"],
            }
            spaces.append(space)
        return spaces

    def get_all_pages_from_space(self, space_key: str, max_pages: Optional[int] = None):
        start = 0
        limit = 50 if max_pages is None or max_pages <= 0 else min(50, max_pages)
        pages = []
        while True:
            result = self.confluence.get_all_pages_from_space(
                space=space_key, start=start, limit=limit, expand="body.storage.value,version,history.lastUpdated"
            )
            pages += result
            if len(result) < limit:
                break
            start += limit
            if max_pages and max_pages > 0 and len(pages) >= max_pages.numerator:
                break
        return pages

    def load_single_page(self, page: dict):
        doc = self.confluenceLoader.process_page(page, include_attachments=False, include_comments=False, ocr_languages="eng+chi_sim")
        if not doc.page_content:
            return None
        doc.metadata["version"] = page["version"]["number"]
        dt = datetime.fromisoformat(page["history"]["lastUpdated"]["when"]).astimezone()
        doc.metadata["last_edit_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        return doc

    def load_all_pages_from_space(self, space_key: str, max_pages: Optional[int] = -1) -> List[Document]:
        docs = []
        pages = self.get_all_pages_from_space(space_key=space_key, max_pages=max_pages)
        for page in pages:
            doc = self.load_single_page(page)
            if doc:
                docs.append(doc)
        return docs
