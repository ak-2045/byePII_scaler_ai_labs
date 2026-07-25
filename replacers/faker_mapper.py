from typing import Dict

from faker import Faker

class FakerMapper:

    def __init__(self):

        self.faker = Faker("en_US")

        self.cache: Dict[str, str] = {}

        self.phone_counter = 0

    def _cached(self, key: str, generator):

        if key not in self.cache:

            self.cache[key] = generator()

        return self.cache[key]

    def replace(self, text: str, label: str) -> str:

        key = f"{label}:{text}"

        label = label.upper()

        if key in self.cache:

            return self.cache[key]

        val = ""

        if label in {"PERSON", "FULL_NAME", "NAME"}:

            val = self._cached(key, lambda: self.faker.name().upper())

        elif label in {"EMAIL", "EMAIL_ADDRESS"}:

            val = self._cached(key, lambda: self.faker.email().upper())

        elif label in {"PHONE", "PHONE_NUMBER", "MOBILE_NUMBER"}:

            digit = str(9 - (self.phone_counter % 3))

            self.phone_counter += 1

            val = digit * 10

        elif label in {"ADDRESS", "RESIDENTIAL_ADDRESS", "LOCATION"}:

            val = self._cached(key, lambda: self.faker.address().upper())

            val = val.replace("\n", ", ")

        elif label in {"ORG", "ORGANIZATION", "COMPANY"}:

            val = self._cached(key, lambda: self.faker.company().upper())

        elif label in {"URL", "WEBSITE"}:

            val = self._cached(key, lambda: self.faker.url().upper())

        elif label == "DOMAIN":

            val = self._cached(key, lambda: self.faker.domain_name().upper())

        elif label in {"DATE_TIME", "DATE", "TIME"}:

            val = "01-01-2024"

        elif label == "IFSC":

            val = "ABCD0123456"

        elif label == "UPI":

            val = "USER@BANK"

        elif label == "SWIFT":

            val = "AAAABBCCDDD"

        elif label == "IP_ADDRESS":

            val = self._cached(key, lambda: self.faker.ipv4().upper())

        elif label == "CREDIT_CARD":

            val = "1111-2222-3333-4444"

        elif label == "SEBI_REG":

            val = "INM000011179"

        elif label == "CIN":

            val = "L12345MH2000PLC123456"

        elif label == "DIN":

            val = "DIN: 00000000"

        else:

            val = f"DUMMY_{label}"

        val = val.upper()

        self.cache[key] = val

        return val
