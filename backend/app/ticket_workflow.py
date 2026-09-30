import re
from datetime import datetime


# ==================================================
# Support Ticket Extraction
# ==================================================

ORDER_ID_PATTERN = re.compile(
    r"\b(?:ORD|ORDER)[-_]?[A-Z0-9]{4,}\b",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)"
)

DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|"
    r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"
    r")\b"
)

PRODUCT_CODE_PATTERN = re.compile(
    r"\b(?:SKU|PRODUCT|ITEM)[-_ ]?[A-Z0-9-]{3,}\b",
    re.IGNORECASE,
)


# ==================================================
# Basic Information Extraction
# ==================================================

def extract_order_id(text):
    match = ORDER_ID_PATTERN.search(text)

    if match:
        return match.group(0).upper()

    return None


def extract_email(text):
    match = EMAIL_PATTERN.search(text)

    if match:
        return match.group(0)

    return None


def extract_phone(text):
    match = PHONE_PATTERN.search(text)

    if match:
        return match.group(0)

    return None


def extract_date(text):
    match = DATE_PATTERN.search(text)

    if match:
        return match.group(0)

    return None


def extract_product_code(text):
    match = PRODUCT_CODE_PATTERN.search(text)

    if match:
        return match.group(0).upper()

    return None


# ==================================================
# Issue Detection
# ==================================================

def detect_issue(text):
    text_lower = text.lower()

    issue_patterns = [
        # Delivery
        (
            [
                "not delivered",
                "not arrived",
                "hasn't arrived",
                "has not arrived",
                "delivery is late",
                "delivery late",
                "order is late",
                "package is late",
                "order hasn't arrived",
                "order has not arrived",
            ],
            "delivery_delay",
        ),

        # Payment
        (
            [
                "payment failed",
                "payment failure",
                "card declined",
                "payment not working",
                "payment issue",
                "payment problem",
                "charged but order failed",
            ],
            "payment_issue",
        ),

        # Refund
        (
            [
                "refund not received",
                "refund pending",
                "need a refund",
                "want a refund",
                "refund",
                "money back",
            ],
            "refund_issue",
        ),

        # Return
        (
            [
                "want to return",
                "return product",
                "return order",
                "return this",
                "return the product",
                "return the order",
            ],
            "return_request",
        ),

        # Damaged product
        (
            [
                "damaged product",
                "product damaged",
                "package damaged",
                "item damaged",
                "order damaged",
                "is damaged",
                "was damaged",
                "arrived damaged",
                "arrived broken",
                "received damaged",
                "received broken",
                "broken product",
                "broken item",
                "broken",
                "damaged",
            ],
            "damaged_product",
        ),

        # Wrong product
        (
            [
                "wrong product",
                "wrong item",
                "incorrect product",
                "incorrect item",
                "received wrong",
                "wrong product received",
            ],
            "wrong_product",
        ),

        # Product not working
        (
            [
                "not working",
                "doesn't work",
                "does not work",
                "stopped working",
                "not functioning",
                "not functioning properly",
            ],
            "product_not_working",
        ),
    ]

    for keywords, issue_type in issue_patterns:

        if any(
            keyword in text_lower
            for keyword in keywords
        ):
            return issue_type

    return "general_support_issue"


# ==================================================
# Product Extraction
# ==================================================

def extract_product(text):
    text_lower = text.lower()

    # Product after ordered / bought / purchased
    match = re.search(
        r"(?:ordered|bought|purchased)\s+"
        r"(?:a|an|the)\s+"
        r"([a-zA-Z0-9][a-zA-Z0-9 _-]*?)"
        r"(?=\s+(?:and|on|for|with|from|because|"
        r"the expected|the delivery|was|is)\b|[.,\n]|$)",
        text_lower,
    )

    if match:
        product = match.group(1).strip()

        if product:
            return product

    # Product after "product" or "item"
    match = re.search(
        r"(?:product|item)\s*"
        r"(?:is|:)\s*"
        r"([^.,\n]+)",
        text_lower,
    )

    if match:
        product = match.group(1).strip()

        if product:
            return product

    # Common product names
    common_products = [
        "laptop",
        "phone",
        "mobile",
        "smartphone",
        "tablet",
        "headphones",
        "earphones",
        "earbuds",
        "watch",
        "smartwatch",
        "keyboard",
        "mouse",
        "monitor",
        "camera",
        "printer",
        "speaker",
        "television",
        "tv",
        "charger",
        "power bank",
    ]

    for product in common_products:

        if re.search(
            rf"\b{re.escape(product)}\b",
            text_lower,
        ):
            return product

    return None


# ==================================================
# Evidence Extraction
# ==================================================

def extract_evidence(text):
    evidence = []

    evidence_patterns = [
        r"expected delivery[^.]*",
        r"delivery date[^.]*",
        r"error code[^.]*",
        r"payment[^.]*failed[^.]*",
        r"charged[^.]*",
        r"received[^.]*",
        r"ordered[^.]*",
        r"damaged[^.]*",
        r"broken[^.]*",
    ]

    for pattern in evidence_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:

            cleaned = match.strip()

            if (
                cleaned
                and cleaned not in evidence
            ):
                evidence.append(cleaned)

    return evidence


# ==================================================
# Conversation Summary
# ==================================================

def create_conversation_summary(
    conversation,
):
    if not conversation:
        return None

    cleaned = " ".join(
        conversation.split()
    )

    if len(cleaned) <= 300:
        return cleaned

    return cleaned[:297] + "..."


# ==================================================
# Missing Information Detection
# ==================================================

def find_missing_information(
    order_id,
    product,
    email,
    phone,
    issue,
):
    missing_information = []

    if not order_id:
        missing_information.append(
            "order_id"
        )

    if not product:
        missing_information.append(
            "product"
        )

    if not email and not phone:
        missing_information.append(
            "customer_contact"
        )

    if issue == "general_support_issue":
        missing_information.append(
            "issue_details"
        )

    return missing_information


# ==================================================
# Create Support Ticket
# ==================================================

def create_support_ticket(
    conversation,
    customer_name=None,
):
    """
    Convert a customer conversation into
    a structured support ticket.

    The function does not invent missing
    customer or order information.
    """

    if not conversation:
        conversation = ""

    conversation = conversation.strip()

    order_id = extract_order_id(
        conversation
    )

    email = extract_email(
        conversation
    )

    phone = extract_phone(
        conversation
    )

    date = extract_date(
        conversation
    )

    product_code = extract_product_code(
        conversation
    )

    product = extract_product(
        conversation
    )

    issue = detect_issue(
        conversation
    )

    evidence = extract_evidence(
        conversation
    )

    missing_information = (
        find_missing_information(
            order_id=order_id,
            product=product,
            email=email,
            phone=phone,
            issue=issue,
        )
    )

    if missing_information:
        ticket_status = "needs_information"
    else:
        ticket_status = "ready"

    return {
        "ticket_id": None,

        "created_at":
            datetime.now().isoformat(),

        "customer": {
            "name": customer_name,
            "email": email,
            "phone": phone,
        },

        "order_id": order_id,

        "product": product,

        "product_code": product_code,

        "issue": issue,

        "evidence": evidence,

        "reference_date": date,

        "conversation_summary":
            create_conversation_summary(
                conversation
            ),

        "conversation": conversation,

        "missing_information":
            missing_information,

        "status": ticket_status,
    }


# ==================================================
# Standalone Test
# ==================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("SUPPORT TICKET EXTRACTION TEST")
    print("=" * 60)

    test_cases = [

        # Test 1 - Delivery
        (
            "Delivery test",
            "My order ORD12345 has not arrived. "
            "I ordered a laptop and the expected "
            "delivery was 18/09/2026. "
            "You can contact me at "
            "test@example.com.",
        ),

        # Test 2 - Missing information
        (
            "Missing information test",
            "My order ORD56789 has not arrived.",
        ),

        # Test 3 - Damaged product
        (
            "Damaged product test",
            "My order ORD77777 is damaged. "
            "I bought a laptop and you can call "
            "me on 9876543210.",
        ),
    ]

    for test_name, test_conversation in test_cases:

        print("\n" + "-" * 60)
        print(test_name)
        print("-" * 60)

        ticket = create_support_ticket(
            test_conversation
        )

        print("\nGenerated Ticket:\n")

        for key, value in ticket.items():
            print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)