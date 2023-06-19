import os

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv


class AzureFormRecognizerClient:
    def __init__(self, form_recognizer_endpoint: str = None, form_recognizer_key: str = None):

        load_dotenv()

        self.pages_per_embeddings = int(os.getenv('PAGES_PER_EMBEDDINGS', 2))
        self.section_to_exclude = ['footnote', 'pageHeader', 'pageFooter', 'pageNumber']

        self.form_recognizer_endpoint: str = form_recognizer_endpoint if form_recognizer_endpoint else os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
        self.form_recognizer_key: str = form_recognizer_key if form_recognizer_key else os.getenv('AZURE_FORM_RECOGNIZER_KEY')

        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=self.form_recognizer_endpoint, credential=AzureKeyCredential(self.form_recognizer_key)
        )

    def analyze_read(self, file_bytes: bytes = None, file_url: str = None):
        assert file_bytes or file_url

        if file_bytes:
            poller = self.document_analysis_client.begin_analyze_document("prebuilt-layout", file_bytes)
        else:
            poller = self.document_analysis_client.begin_analyze_document_from_url("prebuilt-layout", file_url)

        layout = poller.result()
        results = []
        page_result = ''
        for p in layout.paragraphs:
            page_number = p.bounding_regions[0].page_number
            output_file_id = int((page_number - 1) / self.pages_per_embeddings)

            if len(results) < output_file_id + 1:
                results.append('')

            if p.role not in self.section_to_exclude:
                results[output_file_id] += f"{p.content}\n"

        for t in layout.tables:
            page_number = t.bounding_regions[0].page_number
            output_file_id = int((page_number - 1) / self.pages_per_embeddings)

            if len(results) < output_file_id + 1:
                results.append('')
            previous_cell_row = 0
            row_content = '| '
            table_content = ''
            for c in t.cells:
                if c.row_index == previous_cell_row:
                    row_content += c.content + " | "
                else:
                    table_content += row_content + "\n"
                    row_content = '|'
                    row_content += c.content + " | "
                    previous_cell_row += 1
            results[output_file_id] += f"{table_content}|"
        return results
