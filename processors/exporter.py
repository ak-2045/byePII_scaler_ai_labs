from pathlib import Path

from typing import Dict, List

import fitz

import pandas as pd

from docx import Document

class Exporter:

    @staticmethod

    def export_json(entities: List[Dict], output_path: str | Path):

        df = pd.DataFrame(entities)

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        df.to_json(

            output_path,

            orient="records",

            indent=4,

            force_ascii=False

        )

    @staticmethod

    def export_excel(entities: List[Dict], output_path: str | Path):

        df = pd.DataFrame(entities)

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        df.to_excel(

            output_path,

            index=False

        )

    @staticmethod

    def export_docx(

        paragraphs: List[str],

        output_path: str | Path

    ):

        document = Document()

        for paragraph in paragraphs:

            document.add_paragraph(paragraph)

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        document.save(output_path)

    @staticmethod

    def export_pdf(

        pages: List[str],

        output_path: str | Path

    ):

        document = fitz.open()

        for text in pages:

            page = document.new_page()

            page.insert_textbox(

                fitz.Rect(

                    50,

                    50,

                    545,

                    792

                ),

                text,

                fontsize=11

            )

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        document.save(output_path)

        document.close()

    @staticmethod

    def summary(entities: List[Dict]) -> Dict:

        summary = {}

        for entity in entities:

            label = entity["label"]

            summary[label] = summary.get(

                label,

                0

            ) + 1

        return dict(

            sorted(summary.items())

        )
