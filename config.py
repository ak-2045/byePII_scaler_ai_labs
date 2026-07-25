from pathlib import Path

import os

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"

OUTPUT_DIR = BASE_DIR / "outputs"

CACHE_DIR = BASE_DIR / "cache"

ASSETS_DIR = BASE_DIR / "assets"

POLICY_PATH = BASE_DIR / "policy.json"

REPORTS_DIR = BASE_DIR / "reports"

UPLOAD_DIR.mkdir(exist_ok=True)

OUTPUT_DIR.mkdir(exist_ok=True)

CACHE_DIR.mkdir(exist_ok=True)

ENABLE_LLM = False

LLM_MODEL = ""

PRESERVE_CONSISTENCY = True

REDACT_IMAGES = True

SUPPORTED_DOCUMENTS = [

    "pdf",

    "docx",

    "txt"

]

DEFAULT_LABELS = [

    "Person",

    "Company",

    "Organization",

    "Director",

    "Promoter",

    "Shareholder",

    "Registrar",

    "Merchant Banker",

    "Auditor",

    "Law Firm",

    "Consultant",

    "Contact Person",

    "Registered Office",

    "Corporate Office",

    "Branch Office",

    "Factory Address",

    "Residential Address",

    "Mailing Address",

    "Trust",

    "Partnership",

    "HUF",

    "Signature",

    "Bank Account Number",

    "IFSC Code",

    "SWIFT Code",

    "UPI ID"

]

CONFIDENCE_THRESHOLDS = {

    "regex": 1.0,

    "presidio": 0.6,

}

REPLACEMENT_TYPES = {

    "PERSON": "name",

    "COMPANY": "company",

    "ORGANIZATION": "company",

    "EMAIL": "email",

    "PHONE": "phone",

    "ADDRESS": "address",

    "IFSC": "ifsc",

    "SWIFT": "swift",

    "UPI": "upi"

}
