from typing import List, Dict

from replacers.text_replacer import TextReplacer

class TextRedactor:

    def __init__(self):

        self.replacer = TextReplacer()

    def redact(self, text: str, entities: List[Dict]) -> str:

        return self.replacer.replace(text, entities)
