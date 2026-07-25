from pathlib import Path

from typing import Dict, List

import fitz

from PIL import Image

class PDFProcessor:

    def __init__(self, pdf_path: str | Path):

        self.pdf_path = str(pdf_path)

        self.document = fitz.open(self.pdf_path)

    def extract_text(self) -> List[Dict]:

        pages = []

        for page_number, page in enumerate(self.document):

            pages.append(

                {

                    "page": page_number + 1,

                    "text": page.get_text("text")

                }

            )

        return pages

    def extract_words(self) -> List[Dict]:

        words = []

        for page_number, page in enumerate(self.document):

            for word in page.get_text("words"):

                x0, y0, x1, y1, text, *_ = word

                words.append(

                    {

                        "page": page_number + 1,

                        "text": text,

                        "bbox": [x0, y0, x1, y1]

                    }

                )

        return words

    def extract_images(self) -> List[Dict]:

        images = []

        for page_number, page in enumerate(self.document):

            for image_index, image in enumerate(page.get_images(full=True)):

                xref = image[0]

                image_data = self.document.extract_image(xref)

                images.append(

                    {

                        "page": page_number + 1,

                        "index": image_index,

                        "bytes": image_data["image"],

                        "extension": image_data["ext"]

                    }

                )

        return images

    def render_pages(self, dpi: int = 200) -> List[Image.Image]:

        rendered = []

        zoom = dpi / 72

        matrix = fitz.Matrix(zoom, zoom)

        for page in self.document:

            pixmap = page.get_pixmap(matrix=matrix)

            image = Image.frombytes(

                "RGB",

                [pixmap.width, pixmap.height],

                pixmap.samples

            )

            rendered.append(image)

        return rendered

    def page_count(self) -> int:

        return len(self.document)

    def close(self):

        self.document.close()
