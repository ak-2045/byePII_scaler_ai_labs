from pathlib import Path

import config

from core.orchestrator import ByePIIOrchestrator

from redaction.text_redactor import TextRedactor

from redaction.pdf_redactor import PDFRedactor

from redaction.docx_redactor import DOCXRedactor

from utils.constants import SUPPORTED_DOCUMENT_EXTENSIONS

from utils.helpers import is_document, load_text, save_text

class ByePIIPipeline:

    def __init__(self, disabled_categories=None):

        self.orchestrator = ByePIIOrchestrator(disabled_categories=disabled_categories)

        self.text_redactor = TextRedactor()

        self.pdf_redactor = PDFRedactor()

        self.docx_redactor = DOCXRedactor()

    def process_text(self, text: str):

        entities = self.orchestrator.detect(text)

        from replacers.faker_mapper import FakerMapper

        mapper = FakerMapper()

        for ent in entities:

            ent["replacement"] = mapper.replace(ent["text"], ent["label"])

        redacted_text = self.text_redactor.redact(text, entities)

        return {

            "text": text,

            "redacted_text": redacted_text,

            "entities": entities,

        }

    def process_file(self, file_path: str):

        path = Path(file_path)

        if is_document(path, SUPPORTED_DOCUMENT_EXTENSIONS):

            if path.suffix.lower() == ".txt":

                text = load_text(path)

                res = self.process_text(text)

                output_txt_name = "output.txt"
                output_txt_path = config.OUTPUT_DIR / output_txt_name

                save_text(str(output_txt_path), res["redacted_text"])

                return {

                    "entities": res["entities"],

                    "original_pages": [res["text"]],

                    "redacted_pages": [res["redacted_text"]],

                    "redacted_file_path": str(output_txt_path)

                }

            if path.suffix.lower() == ".pdf":

                return self.pdf_redactor.redact_pdf(

                    file_path,

                    self.orchestrator,

                )

            if path.suffix.lower() == ".docx":

                return self.docx_redactor.redact_docx(

                    file_path,

                    self.orchestrator,

                )

        raise ValueError("Unsupported file type. Only PDF, DOCX, and TXT are supported.")
