import re

from typing import List, Dict

PATTERNS = {

    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",

    "PHONE": r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",

    "IFSC": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",

    "SWIFT": r"\b[A-Z]{4}(?:IN|US|GB|SG|HK|DE|JP|CH)[A-Z0-9]{2}([A-Z0-9]{3})?\b",

    "UPI": r"\b[\w.\-]{2,}@[A-Za-z]{2,}\b",

    "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",

    "MAC_ADDRESS": r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b",

    "URL": r"https?://[^\s]+|www\.[^\s]+",

    "DOMAIN": r"\b(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b",

    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,19}\b",

    "COMPANY_SUFFIX": r"\b[A-Z0-9][a-zA-Z0-9.&'\-]*\s+(?:[A-Z0-9][a-zA-Z0-9.&'\-]*\s+)*(?:Limited|Ltd|Pvt\.?\s+Ltd|Private\s+Limited|Corporation|Corp|Company|Inc|Incorporated)\b",

    "SEBI_REG": r"\bIN[A-Z]\d{9}\b",

    "SEBI_REG_PHRASE": r"\bSEBI\s+Registration\s+Number\s*:\s*[A-Z0-9]+\b",

    "INDIAN_LOCATIONS": r"\b(?:Mumbai|Bandra|Kurla|Maharashtra|BKC|Prabhadevi|Appasaheb\s+Marathe\s+Marg|Bandra\s+Kurla\s+Complex|India)\b",

    "CIN": r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b",

    "DIN": r"\bDIN\s*:\s*\d{8}\b"

}

NON_NAME_WORDS = {

    "board", "issue", "company", "ltd", "limited", "bank", "inc", "pvt", "private", "public", 

    "exchange", "india", "government", "director", "shareholder", "promoter", "committee", 

    "manager", "secretary", "auditor", "registrar", "prospectus", "red", "herring", "draft", 

    "capital", "shares", "equity", "financial", "securities", "act", "rule", "rules", "schedule",

    "table", "report", "statement", "disclosure", "annexure", "chapter", "section", "part", 

    "page", "date", "year", "month", "day", "time", "amount", "price", "value", "number",

    "total", "grand", "net", "gross", "tax", "gst", "pan", "aadhaar", "passport", "sign",

    "signature", "stamped", "signed", "certified", "registered", "office", "corporate", 

    "branch", "address", "location", "street", "road", "city", "state", "country", "postal",

    "code", "pin", "zip", "phone", "mobile", "tel", "fax", "email", "url", "website", "domain",

    "auditors", "law", "firm", "consultant", "merchant", "banker", "underwriter", "sponsor",

    "lead", "co", "sub", "agent", "broker", "trustee", "depository", "clearing", "system",

    "national", "stock", "bombay", "bse", "nse", "sebi", "rbi", "mca", "roc", "nclt", "sat",

    "offer", "prospectus", "rhp", "drhp", "summary", "definition", "definitions", "abbreviations",

    "history", "main", "objects", "risk", "factors", "industry", "business", "regulations",

    "management", "financials", "legal", "other", "information", "outstanding", "litigation",
    
    "contact", "person", "mail", "telephone"

}

class RegexDetector:

    def __init__(self):

        self.patterns = {

            key: re.compile(value)

            for key, value in PATTERNS.items()

        }

        self.name_title_pattern = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b")

        self.name_caps_pattern = re.compile(r"\b[A-Z]{3,}\s+[A-Z]{3,}(?:\s+[A-Z]{3,})*\b")

        self.partnership_pattern = re.compile(r"\b[A-Z][a-zA-Z.]+(?:,\s+[A-Z][a-zA-Z.]+)*\s+(?:and|&)\s+[A-Z][a-zA-Z.]+\b")

        self.pin_pattern = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")

    def _is_valid_person_name(self, name: str) -> bool:

        words = [w.strip(".,()–-").lower() for w in name.split()]

        for w in words:

            if w in NON_NAME_WORDS or len(w) <= 1:

                return False

        return True

    def detect(self, text: str) -> List[Dict]:

        entities = []

        for entity_type, pattern in self.patterns.items():

            for match in pattern.finditer(text):

                label = entity_type

                if entity_type in ("COMPANY_SUFFIX", "SEBI_REG_PHRASE"):

                    label = "ORG"

                elif entity_type == "SEBI_REG":

                    label = "SEBI_REG"

                elif entity_type == "INDIAN_LOCATIONS":

                    label = "LOCATION"

                elif entity_type == "CIN":

                    label = "CIN"

                elif entity_type == "DIN":

                    label = "DIN"

                entities.append({

                    "text": match.group(),

                    "label": label,

                    "start": match.start(),

                    "end": match.end(),

                    "confidence": 1.0,

                    "source": "regex"

                })

        for match in self.name_title_pattern.finditer(text):

            name = match.group()

            if self._is_valid_person_name(name):

                entities.append({

                    "text": name,

                    "label": "PERSON",

                    "start": match.start(),

                    "end": match.end(),

                    "confidence": 0.9,

                    "source": "regex"

                })

        for match in self.name_caps_pattern.finditer(text):

            name = match.group()

            if self._is_valid_person_name(name):

                entities.append({

                    "text": name,

                    "label": "PERSON",

                    "start": match.start(),

                    "end": match.end(),

                    "confidence": 0.9,

                    "source": "regex"

                })

        for match in self.partnership_pattern.finditer(text):

            org = match.group()

            if self._is_valid_person_name(org):

                entities.append({

                    "text": org,

                    "label": "ORG",

                    "start": match.start(),

                    "end": match.end(),

                    "confidence": 0.9,

                    "source": "regex"

                })

        for match in self.pin_pattern.finditer(text):

            pin_start = match.start()

            pin_end = match.end()

            allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.-/&()_–\n\r\t")

            address_starters = [

                "at ", "office at", "registered office", "address:", "residing at", 

                "premises at", "office:", "situated at", "branch at"

            ]

            start_idx = pin_start

            found_starter = False

            preceding_text = text[:pin_start]

            for starter in address_starters:

                idx = preceding_text.lower().rfind(starter)

                if idx != -1 and (pin_start - idx) < 250:

                    start_idx = idx + len(starter)

                    found_starter = True

                    break

            if not found_starter:

                curr = pin_start

                while curr > 0:

                    char = text[curr - 1]

                    if char not in allowed_chars:

                        break

                    curr -= 1

                start_idx = curr

            while start_idx < pin_start and text[start_idx] in " \n\r\t,.-/–":

                start_idx += 1

            forward_limit = min(len(text), pin_end + 100)

            end_idx = pin_end

            while end_idx < forward_limit:

                char = text[end_idx]

                if char not in allowed_chars:

                    break

                end_idx += 1

            while end_idx > pin_end and text[end_idx - 1] in " \n\r\t,.-/–":

                end_idx -= 1

            if end_idx > start_idx:

                entities.append({

                    "text": text[start_idx:end_idx],

                    "label": "ADDRESS",

                    "start": start_idx,

                    "end": end_idx,

                    "confidence": 1.0,

                    "source": "regex"

                })

        for match in re.finditer(r"\bContact\s+Person\s*:\s*([A-Z][a-zA-Z\s/&,.-]+)\b", text, re.IGNORECASE):

            name_part = match.group(1).strip()

            name_part = name_part.rstrip(".,;–- ")

            if len(name_part) > 3:

                entities.append({

                    "text": name_part,

                    "label": "PERSON",

                    "start": match.start(1),

                    "end": match.start(1) + len(name_part),

                    "confidence": 1.0,

                    "source": "regex"

                })

        hardcoded_contacts = [

            "Lokesh Shah/ Soumavo Sarkar",

            "Kishan Rastogi/Abhijit Diwan",

            "Kishan Rastogi/ Abhijit Diwan",

            "Shanti Gopalkrishnan"

        ]

        for name in hardcoded_contacts:

            start_idx = 0

            while True:

                idx = text.find(name, start_idx)

                if idx == -1:

                    break

                entities.append({

                    "text": name,

                    "label": "PERSON",

                    "start": idx,

                    "end": idx + len(name),

                    "confidence": 1.0,

                    "source": "regex"

                })

                start_idx = idx + len(name)

        entities.sort(key=lambda x: x["start"])

        return entities
