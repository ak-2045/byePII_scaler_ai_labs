REGEX_PATTERNS = {

    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",

    "PHONE_NUMBER": r"(?:\+91[-\s]?)?[6-9]\d{9}\b",

    "IFSC_CODE": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",

    "BANK_ACCOUNT": r"\b\d{9,18}\b",

    "UPI_ID": r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b",

    "IPV4_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",

    "IPV6_ADDRESS": r"\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b",

    "MAC_ADDRESS": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",

    "URL": r"https?://[^\s]+",

    "PIN_CODE": r"\b[1-9][0-9]{5}\b",

    "DATE": r"\b(?:\d{1,2}[/-]){2}\d{2,4}\b",

    "TIME": r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b",

    "VEHICLE_NUMBER": r"\b[A-Z]{2}[ -]?\d{1,2}[ -]?[A-Z]{1,3}[ -]?\d{4}\b",

    "CREDIT_CARD": r"\b(?:\d[ -]?){13,19}\b",

    "CVV": r"\b\d{3,4}\b",

}
