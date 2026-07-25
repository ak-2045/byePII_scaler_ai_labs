from pathlib import Path

from typing import List, Dict

def get_file_extension(file_path: str) -> str:

    return Path(file_path).suffix.lower()

def is_image(file_path: str, image_extensions: set) -> bool:

    return get_file_extension(file_path) in image_extensions

def is_document(file_path: str, document_extensions: set) -> bool:

    return get_file_extension(file_path) in document_extensions

def load_text(file_path: str) -> str:

    return Path(file_path).read_text(encoding="utf-8")

def save_text(file_path: str, text: str) -> None:

    Path(file_path).write_text(text, encoding="utf-8")

def sort_entities(entities: List[Dict]) -> List[Dict]:

    return sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))

def remove_overlaps(entities: List[Dict]) -> List[Dict]:

    entities = sort_entities(entities)

    merged = []

    last_end = -1

    for entity in entities:

        if entity["start"] >= last_end:

            merged.append(entity)

            last_end = entity["end"]

    return merged

def mask_text(text: str, entities: List[Dict], token: str) -> str:

    entities = sorted(entities, key=lambda x: x["start"], reverse=True)

    for entity in entities:

        text = (

            text[:entity["start"]]

            + token

            + text[entity["end"]:]

        )

    return text
