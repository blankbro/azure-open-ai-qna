from typing import List, Optional

from langchain.docstore.document import Document
from langchain.document_loaders import ConfluenceLoader

import utils.env as env


class ConfluenceLoaderHelper:

    def __init__(self):
        self.loader = ConfluenceLoader(
            url=env.CONFLUENCE_URL,
            username=env.CONFLUENCE_USERNAME,
            api_key=env.CONFLUENCE_PASSWORD,
        )

    def confluence_load(
            self,
            space_key: Optional[str] = None,
            page_ids: Optional[List[str]] = None,
            limit: Optional[int] = 50,
            max_pages: Optional[int] = 1000,
    ) -> List[Document]:
        return self.loader.load(
            space_key=space_key,
            page_ids=page_ids,
            include_attachments=True,
            limit=limit,
            max_pages=max_pages
        )
