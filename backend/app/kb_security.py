import re


# ---------------------------------------------------------
# SENSITIVE DATA PATTERNS
# ---------------------------------------------------------

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
)

CARD_PATTERN = re.compile(
    r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"
)

CVV_PATTERN = re.compile(
    r"(?i)\b(cvv|cvc|security\s*code)\s*[:=-]?\s*\d{3,4}\b"
)

PIN_PATTERN = re.compile(
    r"(?i)\b(pin|upi\s*pin|atm\s*pin)\s*[:=-]?\s*\d{4,6}\b"
)

UPI_PATTERN = re.compile(
    r"\b[A-Za-z0-9._-]+@[A-Za-z]{2,}\b"
)

PASSWORD_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd)\s*[:=-]\s*\S+"
)

API_KEY_PATTERN = re.compile(
    r"(?i)\b(api[_ -]?key|access[_ -]?token|secret[_ -]?key)"
    r"\s*[:=-]\s*\S+"
)

AADHAAR_PATTERN = re.compile(
    r"(?i)\b(aadhaar|aadhar)\s*(?:number|no\.?|id)?"
    r"\s*[:=-]?\s*\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
)

BANK_ACCOUNT_PATTERN = re.compile(
    r"(?i)\b(bank\s*account|account\s*number|account\s*no\.?)"
    r"\s*[:=-]?\s*\d{8,18}\b"
)


# ---------------------------------------------------------
# MASK TEXT
# ---------------------------------------------------------

def mask_sensitive_data(text):
    """
    Mask common sensitive information in text.

    The original text is not modified on disk.
    This function only returns a masked copy.
    """

    if not isinstance(text, str):
        return text

    masked = text

    # Payment/security information first
    masked = CARD_PATTERN.sub("[CARD_REDACTED]", masked)

    masked = CVV_PATTERN.sub(
        lambda match: f"{match.group(1)}: [CVV_REDACTED]",
        masked
    )

    masked = PIN_PATTERN.sub(
        lambda match: f"{match.group(1)}: [PIN_REDACTED]",
        masked
    )

    masked = AADHAAR_PATTERN.sub(
        "[AADHAAR_REDACTED]",
        masked
    )

    masked = BANK_ACCOUNT_PATTERN.sub(
        lambda match: f"{match.group(1)}: [ACCOUNT_REDACTED]",
        masked
    )

    masked = PASSWORD_PATTERN.sub(
        lambda match: f"{match.group(1)}: [PASSWORD_REDACTED]",
        masked
    )

    masked = API_KEY_PATTERN.sub(
        lambda match: f"{match.group(1)}: [SECRET_REDACTED]",
        masked
    )

    # Personal contact information
    masked = EMAIL_PATTERN.sub(
        "[EMAIL_REDACTED]",
        masked
    )

    masked = PHONE_PATTERN.sub(
        "[PHONE_REDACTED]",
        masked
    )

    # UPI IDs
    masked = UPI_PATTERN.sub(
        "[UPI_REDACTED]",
        masked
    )

    return masked


# ---------------------------------------------------------
# MASK DICTIONARIES
# ---------------------------------------------------------

def mask_sensitive_dict(data):
    """
    Recursively mask sensitive information inside dictionaries
    and lists.
    """

    if isinstance(data, dict):
        return {
            key: mask_sensitive_dict(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            mask_sensitive_dict(item)
            for item in data
        ]

    if isinstance(data, tuple):
        return tuple(
            mask_sensitive_dict(item)
            for item in data
        )

    if isinstance(data, str):
        return mask_sensitive_data(data)

    return data


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print("SENSITIVE DATA MASKING TEST")
    print("---------------------------")

    test_text = """
    Customer email: test@example.com
    Phone: +91 9876543210
    Card: 4111 1111 1111 1111
    CVV: 123
    PIN: 4567
    UPI: customer@upi
    Password: MySecret123
    API_KEY: abc123xyz
    Aadhaar: 1234 5678 9012
    Bank Account: 123456789012
    """

    print("\nOriginal:")
    print(test_text)

    print("\nMasked:")
    print(mask_sensitive_data(test_text))