from typing import List, Dict

from presidio_analyzer import AnalyzerEngine

from presidio_analyzer.nlp_engine import NlpEngineProvider

class PresidioDetector:

    def __init__(self):

        try:

            import spacy

            spacy.load("en_core_web_sm")

        except OSError:

            import subprocess

            import sys

            logging_logger = __import__("logging").getLogger("byepii")

            logging_logger.info("spaCy model 'en_core_web_sm' not found. Downloading...")

            try:

                subprocess.run(

                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],

                    stdout=subprocess.PIPE,

                    stderr=subprocess.PIPE,

                    check=True

                )

            except Exception as e:

                logging_logger.error(f"Failed to download spaCy model: {str(e)}")

        configuration = {

            "nlp_engine_name": "spacy",

            "models": [

                {

                    "lang_code": "en",

                    "model_name": "en_core_web_sm"

                }

            ]

        }

        provider = NlpEngineProvider(nlp_configuration=configuration)

        nlp_engine = provider.create_engine()

        import logging as py_logging

        py_logging.getLogger("presidio-analyzer").setLevel(py_logging.ERROR)

        self.analyzer = AnalyzerEngine(

            nlp_engine=nlp_engine,

            supported_languages=["en"]

        )

    def detect(self, text: str) -> List[Dict]:

        results = self.analyzer.analyze(

            text=text,

            language="en"

        )

        entities = []

        for result in results:

            if result.entity_type == "DATE_TIME":

                start_win = max(0, result.start - 50)

                end_win = min(len(text), result.end + 50)

                context = text[start_win:end_win].lower()

                if not any(k in context for k in ("birth", "dob", "born")):

                    continue

            entities.append(

                {

                    "text": text[result.start:result.end],

                    "label": result.entity_type,

                    "start": result.start,

                    "end": result.end,

                    "confidence": float(result.score),

                    "source": "presidio"

                }

            )

        entities.sort(key=lambda x: x["start"])

        return entities
