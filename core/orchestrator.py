from typing import List, Dict
import json
import re
from pathlib import Path
from detectors.regex_detector import RegexDetector
from detectors.presidio_detector import PresidioDetector
from detectors.merger import EntityMerger

LABEL_TO_CATEGORY = {
    "PERSON": "names",
    "PERSON_NAME": "names",
    "DIRECTOR": "names",
    "PROMOTER": "names",
    "SHAREHOLDER": "names",
    "CONTACT_PERSON": "names",
    "EMAIL": "emails",
    "EMAIL_ADDRESS": "emails",
    "PHONE": "phones",
    "PHONE_NUMBER": "phones",
    "MOBILE_NUMBER": "phones",
    "ADDRESS": "addresses",
    "LOCATION": "addresses",
    "RESIDENTIAL_ADDRESS": "addresses",
    "MAILING_ADDRESS": "addresses",
    "CORPORATE_OFFICE": "addresses",
    "BRANCH_OFFICE": "addresses",
    "FACTORY_ADDRESS": "addresses",
    "GPE": "addresses",
    "COMPANY": "organizations",
    "ORGANIZATION": "organizations",
    "ORG": "organizations",
    "TRUST": "organizations",
    "PARTNERSHIP": "organizations",
    "HUF": "organizations",
    "REGISTRAR": "organizations",
    "MERCHANT_BANKER": "organizations",
    "AUDITOR": "organizations",
    "LAW_FIRM": "organizations",
    "CONSULTANT": "organizations"
}

class ByePIIOrchestrator:

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[,:;()\[\]{}]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def __init__(self, disabled_categories=None):
        self.regex_detector = RegexDetector()
        self.presidio_detector = PresidioDetector()
        self.merger = EntityMerger()
        self.disabled_categories = disabled_categories or set()
        self.false_positives = set()

        try:
            fp_path = Path("outputs/false_positive.json")
            if not fp_path.exists():
                fp_path = (
                    Path(__file__).resolve().parent.parent
                    / "outputs"
                    / "false_positive.json"
                )
            if fp_path.exists():
                with open(fp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        if text:
                            self.false_positives.add(
                                self.normalize_text(text)
                            )
        except Exception as e:
            print(f"Failed to load false positives: {e}")

    def _matches_false_positive(self, norm: str) -> bool:
        return norm in self.false_positives

    def _matches_heading(self, norm: str, headings) -> bool:
        for heading in headings:
            h = self.normalize_text(heading)
            if (
                norm == h
                or norm in h
                or h in norm
            ):
                return True
        return False

    def is_blacklisted(self, text: str) -> bool:
        # Protect header prefixes containing colons from being redacted
        if ":" in text:
            parts = text.split(":", 1)
            prefix = parts[0].strip().lower()
            if any(h in prefix for h in ("contact person", "registered office", "corporate office", "website")):
                return True

        norm = self.normalize_text(text)

        must_redact_substrings = {
            "lokesh shah", "soumavo sarkar", "kishan rastogi",
            "abhijit diwan", "shanti gopalkrishnan",
            "gerald welch", "sullivan", "rebekah hebert",
            "miguel allison", "gibsonjill", "kwilson",
            "laura white", "thomas and davis", "mcguire",
            "casey sellers", "tonycox", "sandoval",
            "robinsonmitchell", "mitchell and grant",
            "melissa hoover", "moore", "nathan harvey",
            "mercado", "rivas falls",
            "jeffreywashington", "edwards"
        }
        for sub in must_redact_substrings:
            if sub in norm:
                return False

        TABLE_HEADINGS = [
            "registered office corporate office contact person e-mail and telephone website",
            "registered office corporate office contact person email and telephone website",
            "type size of the fresh issue size of the offer for sale total offer size eligibility and share reservation among qibs niis and riis",
            "type size of the fresh issue size of the offer for sale total offer size eligibility and share reservation among qibs, niis and riis",
            "details of the promoter selling shareholders, offer for sale and weighted average cost of acquisition per equity share name of the promoter selling shareholder type aggregate amount of offer for sale (₹ in million) weighted average cost of acquisition per equity share of face value of ₹5 each (in ₹) *#",
            "details of the promoter selling shareholders offer for sale and weighted average cost of acquisition per equity share name of the promoter selling shareholder type aggregate amount of offer for sale (in million) weighted average cost of acquisition per equity share of face value of each (in) *#",
            "details of the promoter selling shareholders, offer for sale and weighted average cost of acquisition per equity share name of the promoter selling shareholder type aggregate amount of offer for sale (in million) weighted average cost of acquisition per equity share of face value of each (in ) *#",
            "risks in relation to the first offer general risks issuer’s and promoter selling shareholders’ absolute responsibility",
            "risks in relation to the first offer general risks issuer's and promoter selling shareholders' absolute responsibility"
        ]

        if self._matches_heading(norm, TABLE_HEADINGS):
            return True

        heading_parts = {
            "size of the fresh issue",
            "size of the offer for sale",
            "total offer size",
            "details of the promoter selling shareholders",
            "weighted average cost of acquisition",
            "promoter selling shareholder",
            "risks in relation to the first offer",
            "general risks",
            "absolute responsibility",
            "registered office",
            "corporate office",
            "contact person",
            "e-mail and telephone",
            "email and telephone",
            "email & telephone",
            "website",
            "reservation among qibs",
            "niis and riis",
            "selling shareholders",
            "selling shareholder"
        }

        if self._matches_heading(norm, heading_parts):
            return True

        if "offer" in norm:
            return True

        if any(
            x in norm
            for x in (
                "contact person",
                "registered office",
                "corporate office",
                "website"
            )
        ):
            return True

        if self._matches_false_positive(norm):
            return True

        parts = [
            self.normalize_text(p)
            for p in re.split(r'[\t\n]+', text)
            if p.strip()
        ]

        if len(parts) > 1:
            all_parts_blacklisted = True
            for part in parts:
                is_part_fp = (
                    self._matches_false_positive(part)
                    or self._matches_heading(part, heading_parts)
                    or "offer" in part
                )
                if not is_part_fp:
                    all_parts_blacklisted = False
                    break
            if all_parts_blacklisted:
                return True
        return False

    def detect_text(self, text: str) -> List[Dict]:
        regex_entities = self.regex_detector.detect(text)
        presidio_entities = self.presidio_detector.detect(text)

        regex_entities = [
            ent
            for ent in regex_entities
            if not self.is_blacklisted(ent["text"])
        ]
        presidio_entities = [
            ent
            for ent in presidio_entities
            if not self.is_blacklisted(ent["text"])
        ]

        custom_entities = []
        matches = re.finditer(
            r'(?i)\bcontact\s+person\s*:\s*([^\t\n\r]+)',
            text
        )
        for m in matches:
            val_raw = m.group(1)
            val_stripped = val_raw.strip()
            if val_stripped and not self.is_blacklisted(val_stripped):
                offset = val_raw.index(val_stripped)
                start_val = m.start(1) + offset
                end_val = start_val + len(val_stripped)
                custom_entities.append(
                    {
                        "start": start_val,
                        "end": end_val,
                        "text": val_stripped,
                        "label": "PERSON",
                        "confidence": 1.0,
                        "source": "custom_contact_person",
                    }
                )

        merged = self.merger.merge(
            regex_entities,
            presidio_entities,
            custom_entities,
        )

        filtered = [
            ent
            for ent in merged
            if not self.is_blacklisted(ent["text"])
        ]

        if self.disabled_categories:
            final_filtered = []
            for ent in filtered:
                lbl = ent.get("label", "PERSON").upper()
                cat = LABEL_TO_CATEGORY.get(lbl, lbl.lower())
                if cat in self.disabled_categories:
                    continue
                final_filtered.append(ent)
            return final_filtered
        return filtered

    def detect(self, data, image=False) -> List[Dict]:
        return self.detect_text(data)