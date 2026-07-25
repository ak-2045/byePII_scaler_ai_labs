from typing import Dict, List

from replacers.faker_mapper import FakerMapper

class TextReplacer:

    def __init__(self):

        self.mapper = FakerMapper()

    def replace(

        self,

        text: str,

        entities: List[Dict]

    ) -> str:

        entities = sorted(

            entities,

            key=lambda x: x["start"],

            reverse=True

        )

        output = text

        for entity in entities:

            replacement = self.mapper.replace(

                entity["text"],

                entity["label"]

            )

            output = (

                output[:entity["start"]]

                + replacement

                + output[entity["end"]:]

            )

        return output

    def replace_with_mapping(

        self,

        text: str,

        entities: List[Dict]

    ):

        entities = sorted(

            entities,

            key=lambda x: x["start"],

            reverse=True

        )

        mapping = {}

        output = text

        for entity in entities:

            replacement = self.mapper.replace(

                entity["text"],

                entity["label"]

            )

            mapping[entity["text"]] = replacement

            output = (

                output[:entity["start"]]

                + replacement

                + output[entity["end"]:]

            )

        return output, mapping
