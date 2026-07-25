from pathlib import Path

from typing import Dict, List

import pandas as pd

class ReportGenerator:

    def __init__(self, entities: List[Dict]):

        self.entities = entities

    def summary(self) -> Dict:

        summary = {}

        for entity in self.entities:

            label = entity["label"]

            summary[label] = summary.get(label, 0) + 1

        return dict(sorted(summary.items()))

    def dataframe(self) -> pd.DataFrame:

        return pd.DataFrame(self.entities)

    def save_excel(self, output_path: str):

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        with pd.ExcelWriter(output_path) as writer:

            self.dataframe().to_excel(

                writer,

                sheet_name="Entities",

                index=False

            )

            pd.DataFrame(

                list(self.summary().items()),

                columns=["Entity", "Count"]

            ).to_excel(

                writer,

                sheet_name="Summary",

                index=False

            )

    def save_csv(self, output_path: str):

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        self.dataframe().to_csv(

            output_path,

            index=False

        )

    def save_json(self, output_path: str):

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        self.dataframe().to_json(

            output_path,

            orient="records",

            indent=4

        )

    def save_texts_only_json(self, output_path: str):

        Path(output_path).parent.mkdir(

            parents=True,

            exist_ok=True

        )

        texts_only = [{"text": ent["text"]} for ent in self.entities if "text" in ent]

        import json

        with open(output_path, "w", encoding="utf-8") as f:

            json.dump(texts_only, f, indent=4, ensure_ascii=False)
