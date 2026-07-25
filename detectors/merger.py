from typing import Dict, List

class EntityMerger:

    def __init__(self, overlap_threshold: float = 0.5):

        self.overlap_threshold = overlap_threshold

    @staticmethod

    def _text_overlap(a: Dict, b: Dict) -> float:

        if "start" not in a or "start" not in b:

            return 0.0

        left = max(a["start"], b["start"])

        right = min(a["end"], b["end"])

        if right <= left:

            return 0.0

        overlap = right - left

        shortest = min(

            a["end"] - a["start"],

            b["end"] - b["start"]

        )

        return overlap / shortest

    @staticmethod

    def _bbox_overlap(a: Dict, b: Dict) -> float:

        if "bbox" not in a or "bbox" not in b:

            return 0.0

        ax1, ay1, ax2, ay2 = a["bbox"]

        bx1, by1, bx2, by2 = b["bbox"]

        x1 = max(ax1, bx1)

        y1 = max(ay1, by1)

        x2 = min(ax2, bx2)

        y2 = min(ay2, by2)

        if x2 <= x1 or y2 <= y1:

            return 0.0

        intersection = (x2 - x1) * (y2 - y1)

        area_a = (ax2 - ax1) * (ay2 - ay1)

        area_b = (bx2 - bx1) * (by2 - by1)

        return intersection / min(area_a, area_b)

    @staticmethod

    def _merge_sources(first: Dict, second: Dict) -> List[str]:

        sources = []

        for entity in (first, second):

            source = entity.get("source")

            if isinstance(source, list):

                sources.extend(source)

            elif source:

                sources.append(source)

        return sorted(set(sources))

    def merge(self, *entity_lists: List[Dict]) -> List[Dict]:

        entities = []

        for entity_list in entity_lists:

            entities.extend(entity_list)

        entities.sort(

            key=lambda x: (

                x.get("start", 0),

                -x.get("confidence", 0)

            )

        )

        merged = []

        for entity in entities:

            matched = False

            for existing in merged:

                text_overlap = self._text_overlap(existing, entity)

                bbox_overlap = self._bbox_overlap(existing, entity)

                overlap = max(text_overlap, bbox_overlap)

                if overlap >= self.overlap_threshold:

                    if entity["confidence"] > existing["confidence"]:

                        existing.update(entity)

                    existing["source"] = self._merge_sources(existing, entity)

                    matched = True

                    break

            if not matched:

                entity = entity.copy()

                if not isinstance(entity.get("source"), list):

                    entity["source"] = [entity["source"]]

                merged.append(entity)

        if not merged:

            return []

        merged.sort(key=lambda x: x["start"])

        adjacent_merged = []

        current = merged[0].copy()

        for next_ent in merged[1:]:

            if next_ent["start"] <= current["end"] + 5:

                current["end"] = max(current["end"], next_ent["end"])

                current["text"] = current["text"] + " " + next_ent["text"]

                if current["label"] != next_ent["label"]:

                    if next_ent["label"] in ("PERSON", "ADDRESS", "ORG", "ORGANIZATION"):

                        current["label"] = next_ent["label"]

                current["confidence"] = max(current["confidence"], next_ent["confidence"])

                src1 = current["source"] if isinstance(current["source"], list) else [current["source"]]

                src2 = next_ent["source"] if isinstance(next_ent["source"], list) else [next_ent["source"]]

                current["source"] = sorted(list(set(src1 + src2)))

            else:

                adjacent_merged.append(current)

                current = next_ent.copy()

        adjacent_merged.append(current)

        adjacent_merged.sort(

            key=lambda x: (

                x.get("start", 0),

                -x.get("confidence", 0)

            )

        )

        return adjacent_merged
