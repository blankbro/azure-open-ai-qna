from utils.document_loader import ConfluenceLoaderHelper

if __name__ == "__main__":
    clh = ConfluenceLoaderHelper()
    documents = clh.confluence_load(space_key="9CK", max_pages=1000)
    # documents = clh.confluence_load(page_ids=["90143794"], max_pages=1)

    for document in documents:
        if not document.page_content:
            print(document.metadata["title"] + " page content is empty")
        else:
            print(document)
