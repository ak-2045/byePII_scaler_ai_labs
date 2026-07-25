import logging

from pathlib import Path

from typing import Dict, Any

import fitz

import config

from processors.pdf_processor import PDFProcessor

from replacers.faker_mapper import FakerMapper

from redaction.image_blur import blur_logos_in_pdf_page

logger = logging.getLogger("byepii")

class PDFRedactor:

    def __init__(self):

        self.mapper = FakerMapper()

        self.mode = "black"

    def redact_pdf(self, file_path: str, orchestrator: Any) -> Dict[str, Any]:

        pdf_path = Path(file_path)

        processor = PDFProcessor(pdf_path)

        doc = processor.document

        all_detected_entities = []

        for page_number in range(len(doc)):

            page = doc[page_number]

            page_text = page.get_text("text")

            text_entities = orchestrator.detect_text(page_text)

            page_ents = []

            for ent in text_entities:

                ent["page"] = page_number + 1

                ent["replacement"] = self.mapper.replace(ent["text"], ent["label"])

                page_ents.append(ent)

            all_detected_entities.extend(page_ents)

            rects_to_draw = []

            for ent in page_ents:

                orig_text = ent["text"]

                rects = page.search_for(orig_text)

                for rect in rects:

                    rects_to_draw.append((rect, ent))

            for rect, ent in rects_to_draw:

                fill_color = (1, 1, 0)               

                page.add_redact_annot(rect, fill=fill_color)

            if rects_to_draw:

                page.apply_redactions()

                for rect, ent in rects_to_draw:

                    replacement = ent["replacement"]

                    font_color = (0, 0, 0)              

                    page.insert_textbox(

                        rect,

                        replacement,

                        fontname="cour",                

                        fontsize=max(6.0, rect.y1 - rect.y0 - 2.0),

                        color=font_color,

                        align=0

                    )

            if getattr(config, "REDACT_IMAGES", True):
                try:
                    n_blurred = blur_logos_in_pdf_page(page)
                    if n_blurred:
                        logger.info(f"Page {page_number + 1}: blurred {n_blurred} logo instance(s).")
                except Exception as e:
                    logger.warning(f"Image blur failed on page {page_number + 1}: {e}")

        output_pdf_name = "output.pdf"
        output_pdf_path = config.OUTPUT_DIR / output_pdf_name

        doc.save(str(output_pdf_path), garbage=4, deflate=True)

        doc.close()

        original_previews = processor.render_pages(dpi=100)

        redacted_processor = PDFProcessor(output_pdf_path)

        redacted_previews = redacted_processor.render_pages(dpi=100)

        redacted_processor.close()

        return {

            "entities": all_detected_entities,

            "original_pages": original_previews,

            "redacted_pages": redacted_previews,

            "redacted_file_path": str(output_pdf_path)

        }
