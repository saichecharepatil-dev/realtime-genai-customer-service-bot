from difflib import SequenceMatcher
import re


# ==================================================
# Configuration
# ==================================================

DUPLICATE_THRESHOLD = 0.75
RELATED_THRESHOLD = 0.55


# ==================================================
# Text Normalization
# ==================================================

def normalize_text(text):
    """
    Normalize text for comparison.
    """

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"[^\w\s]",
        "",
        text,
    )

    return text.strip()


# ==================================================
# Text Similarity
# ==================================================

def calculate_similarity(
    text_a,
    text_b,
):
    """
    Calculate similarity between two ticket messages.
    """

    normalized_a = normalize_text(
        text_a
    )

    normalized_b = normalize_text(
        text_b
    )

    if not normalized_a or not normalized_b:
        return 0.0

    return round(
        SequenceMatcher(
            None,
            normalized_a,
            normalized_b,
        ).ratio(),
        3,
    )


# ==================================================
# Common Ticket Information
# ==================================================

def same_value(
    value_a,
    value_b,
):
    """
    Safely compare two ticket values.
    """

    if not value_a or not value_b:
        return False

    return str(value_a).strip().lower() == str(
        value_b
    ).strip().lower()


def get_shared_identifiers(
    ticket_a,
    ticket_b,
):
    """
    Find identifiers shared by two tickets.
    """

    shared = []

    if same_value(
        ticket_a.get("order_id"),
        ticket_b.get("order_id"),
    ):
        shared.append("order_id")

    customer_a = ticket_a.get(
        "customer",
        {},
    )

    customer_b = ticket_b.get(
        "customer",
        {},
    )

    if same_value(
        customer_a.get("email"),
        customer_b.get("email"),
    ):
        shared.append("customer_email")

    if same_value(
        customer_a.get("phone"),
        customer_b.get("phone"),
    ):
        shared.append("customer_phone")

    if same_value(
        ticket_a.get("product_code"),
        ticket_b.get("product_code"),
    ):
        shared.append("product_code")

    return shared


# ==================================================
# Duplicate Detection
# ==================================================

def detect_duplicate(
    new_ticket,
    existing_tickets,
):
    """
    Determine whether a new ticket is a duplicate
    of an existing ticket.

    Strong duplicate signals:
    - Same order ID + same issue
    - Same customer contact + same issue + high similarity
    - Very high message similarity
    """

    if not existing_tickets:
        return {
            "is_duplicate": False,
            "duplicate_ticket_id": None,
            "similarity": 0.0,
            "reason": None,
        }

    new_message = new_ticket.get(
        "conversation",
        "",
    )

    new_issue = new_ticket.get(
        "issue",
        "",
    )

    for existing in existing_tickets:

        existing_message = existing.get(
            "conversation",
            "",
        )

        existing_issue = existing.get(
            "issue",
            "",
        )

        similarity = calculate_similarity(
            new_message,
            existing_message,
        )

        shared_identifiers = (
            get_shared_identifiers(
                new_ticket,
                existing,
            )
        )

        # ------------------------------------------
        # Same order + same issue
        # ------------------------------------------

        if (
            "order_id" in shared_identifiers
            and same_value(
                new_issue,
                existing_issue,
            )
        ):
            return {
                "is_duplicate": True,
                "duplicate_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Same order and same issue "
                    "detected.",
            }

        # ------------------------------------------
        # Same contact + same issue + high similarity
        # ------------------------------------------

        contact_match = (
            "customer_email"
            in shared_identifiers
            or "customer_phone"
            in shared_identifiers
        )

        if (
            contact_match
            and same_value(
                new_issue,
                existing_issue,
            )
            and similarity
            >= DUPLICATE_THRESHOLD
        ):
            return {
                "is_duplicate": True,
                "duplicate_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Same customer, same issue, "
                    "and highly similar message.",
            }

        # ------------------------------------------
        # Very high message similarity
        # ------------------------------------------

        if similarity >= 0.90:

            return {
                "is_duplicate": True,
                "duplicate_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Ticket messages are "
                    "highly similar.",
            }

    return {
        "is_duplicate": False,
        "duplicate_ticket_id": None,
        "similarity": 0.0,
        "reason": None,
    }


# ==================================================
# Related Ticket Detection
# ==================================================

def detect_related_ticket(
    new_ticket,
    existing_tickets,
):
    """
    Determine whether a ticket is related to an
    existing ticket but is not necessarily a duplicate.
    """

    if not existing_tickets:
        return {
            "is_related": False,
            "related_ticket_id": None,
            "similarity": 0.0,
            "reason": None,
        }

    new_message = new_ticket.get(
        "conversation",
        "",
    )

    new_issue = new_ticket.get(
        "issue",
        "",
    )

    for existing in existing_tickets:

        existing_message = existing.get(
            "conversation",
            "",
        )

        existing_issue = existing.get(
            "issue",
            "",
        )

        similarity = calculate_similarity(
            new_message,
            existing_message,
        )

        shared_identifiers = (
            get_shared_identifiers(
                new_ticket,
                existing,
            )
        )

        # ------------------------------------------
        # Same order = related
        # ------------------------------------------

        if "order_id" in shared_identifiers:

            return {
                "is_related": True,
                "related_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Tickets reference the same "
                    "order.",
            }

        # ------------------------------------------
        # Same product + same issue
        # ------------------------------------------

        if (
            "product_code"
            in shared_identifiers
            and same_value(
                new_issue,
                existing_issue,
            )
        ):
            return {
                "is_related": True,
                "related_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Tickets reference the same "
                    "product and issue.",
            }

        # ------------------------------------------
        # Same customer + same issue
        # ------------------------------------------

        contact_match = (
            "customer_email"
            in shared_identifiers
            or "customer_phone"
            in shared_identifiers
        )

        if (
            contact_match
            and same_value(
                new_issue,
                existing_issue,
            )
        ):
            return {
                "is_related": True,
                "related_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Same customer and same "
                    "issue detected.",
            }

        # ------------------------------------------
        # Similar messages
        # ------------------------------------------

        if (
            same_value(
                new_issue,
                existing_issue,
            )
            and similarity >= RELATED_THRESHOLD
        ):
            return {
                "is_related": True,
                "related_ticket_id":
                    existing.get("ticket_id"),
                "similarity": similarity,
                "reason":
                    "Same issue with similar "
                    "ticket description.",
            }

    return {
        "is_related": False,
        "related_ticket_id": None,
        "similarity": 0.0,
        "reason": None,
    }


# ==================================================
# Ticket Relationship Analysis
# ==================================================

def analyze_ticket_relationship(
    new_ticket,
    existing_tickets,
):
    """
    Determine whether the new ticket is:
    - duplicate
    - related
    - unrelated
    """

    duplicate_result = detect_duplicate(
        new_ticket,
        existing_tickets,
    )

    if duplicate_result["is_duplicate"]:

        return {
            "relationship": "duplicate",
            "duplicate": duplicate_result,
            "related": {
                "is_related": True,
                "related_ticket_id":
                    duplicate_result[
                        "duplicate_ticket_id"
                    ],
                "similarity":
                    duplicate_result[
                        "similarity"
                    ],
                "reason":
                    "Duplicate ticket is also "
                    "related to the existing ticket.",
            },
        }

    related_result = detect_related_ticket(
        new_ticket,
        existing_tickets,
    )

    if related_result["is_related"]:

        return {
            "relationship": "related",
            "duplicate": duplicate_result,
            "related": related_result,
        }

    return {
        "relationship": "unrelated",
        "duplicate": duplicate_result,
        "related": related_result,
    }


# ==================================================
# Sensitive Data Masking
# ==================================================

def mask_email(email):
    """
    Mask email while preserving enough information
    for an agent to recognize it.
    """

    if not email:
        return None

    email = str(email)

    if "@" not in email:
        return "[MASKED_EMAIL]"

    username, domain = email.split(
        "@",
        1,
    )

    if len(username) <= 1:
        masked_username = "*"

    elif len(username) == 2:
        masked_username = (
            username[0] + "*"
        )

    else:
        masked_username = (
            username[0]
            + "*"
            * (len(username) - 2)
            + username[-1]
        )

    return (
        masked_username
        + "@"
        + domain
    )


def mask_phone(phone):
    """
    Mask phone number except the last four digits.
    """

    if not phone:
        return None

    digits = re.sub(
        r"\D",
        "",
        str(phone),
    )

    if len(digits) <= 4:
        return "****"

    return (
        "*"
        * (len(digits) - 4)
        + digits[-4:]
    )


def mask_name(name):
    """
    Mask customer name.
    """

    if not name:
        return None

    name = str(name).strip()

    if not name:
        return None

    parts = name.split()

    masked_parts = []

    for part in parts:

        if len(part) <= 1:
            masked_parts.append("*")

        else:
            masked_parts.append(
                part[0]
                + "*"
                * (len(part) - 1)
            )

    return " ".join(
        masked_parts
    )


# ==================================================
# Masked Handoff Summary
# ==================================================

def create_masked_handoff_summary(
    ticket,
    priority_data=None,
):
    """
    Create a support-agent handoff summary
    with sensitive customer information masked.
    """

    customer = ticket.get(
        "customer",
        {},
    )

    name = mask_name(
        customer.get("name")
    )

    email = mask_email(
        customer.get("email")
    )

    phone = mask_phone(
        customer.get("phone")
    )

    order_id = ticket.get(
        "order_id"
    )

    product = ticket.get(
        "product"
    )

    product_code = ticket.get(
        "product_code"
    )

    issue = ticket.get(
        "issue"
    )

    summary = ticket.get(
        "conversation_summary"
    )

    reference_date = ticket.get(
        "reference_date"
    )

    evidence = ticket.get(
        "evidence",
        [],
    )

    missing_information = ticket.get(
        "missing_information",
        [],
    )

    priority = None
    sla_deadline = None
    assigned_agent = None

    if priority_data:

        priority = priority_data.get(
            "priority"
        )

        sla = priority_data.get(
            "sla",
            {},
        )

        sla_deadline = sla.get(
            "sla_deadline"
        )

        routing = priority_data.get(
            "routing",
            {},
        )

        assigned_agent = routing.get(
            "agent_name"
        )

    return {
        "ticket_id":
            ticket.get("ticket_id"),

        "customer": {
            "name": name,
            "email": email,
            "phone": phone,
        },

        "order_id":
            order_id,

        "product":
            product,

        "product_code":
            product_code,

        "issue":
            issue,

        "priority":
            priority,

        "sla_deadline":
            sla_deadline,

        "assigned_agent":
            assigned_agent,

        "reference_date":
            reference_date,

        "summary":
            summary,

        "evidence":
            evidence,

        "missing_information":
            missing_information,

        "status":
            ticket.get("status"),
    }


# ==================================================
# Standalone Tests
# ==================================================

def test_duplicate_same_order():

    existing_ticket = {
        "ticket_id": "TKT-001",
        "order_id": "ORD12345",
        "issue": "delivery_delay",
        "customer": {
            "email": "test@example.com",
            "phone": None,
        },
        "conversation":
            "My order ORD12345 has not arrived.",
    }

    new_ticket = {
        "ticket_id": "TKT-002",
        "order_id": "ORD12345",
        "issue": "delivery_delay",
        "customer": {
            "email": "test@example.com",
            "phone": None,
        },
        "conversation":
            "ORD12345 is still not delivered.",
    }

    result = detect_duplicate(
        new_ticket,
        [existing_ticket],
    )

    print("\n--- Test 1: Duplicate Ticket ---")
    print(result)

    assert result["is_duplicate"] is True
    assert (
        result["duplicate_ticket_id"]
        == "TKT-001"
    )

    print("PASS: Duplicate detected.")


def test_related_same_order_different_issue():

    existing_ticket = {
        "ticket_id": "TKT-003",
        "order_id": "ORD55555",
        "issue": "delivery_delay",
        "customer": {
            "email": "customer@example.com",
            "phone": None,
        },
        "conversation":
            "My order ORD55555 has not arrived.",
    }

    new_ticket = {
        "ticket_id": "TKT-004",
        "order_id": "ORD55555",
        "issue": "payment_issue",
        "customer": {
            "email": "customer@example.com",
            "phone": None,
        },
        "conversation":
            "I have a payment problem with ORD55555.",
    }

    result = analyze_ticket_relationship(
        new_ticket,
        [existing_ticket],
    )

    print(
        "\n--- Test 2: Related Ticket ---"
    )
    print(result)

    assert result["relationship"] == "related"
    assert (
        result["related"][
            "related_ticket_id"
        ]
        == "TKT-003"
    )

    print("PASS: Related ticket detected.")


def test_unrelated_ticket():

    existing_ticket = {
        "ticket_id": "TKT-005",
        "order_id": "ORD11111",
        "issue": "delivery_delay",
        "customer": {
            "email": "one@example.com",
            "phone": None,
        },
        "conversation":
            "My laptop delivery is delayed.",
    }

    new_ticket = {
        "ticket_id": "TKT-006",
        "order_id": "ORD99999",
        "issue": "payment_issue",
        "customer": {
            "email": "two@example.com",
            "phone": None,
        },
        "conversation":
            "I have a payment problem with my order.",
    }

    result = analyze_ticket_relationship(
        new_ticket,
        [existing_ticket],
    )

    print(
        "\n--- Test 3: Unrelated Ticket ---"
    )
    print(result)

    assert result["relationship"] == "unrelated"

    print("PASS: Unrelated ticket separated.")


def test_masked_handoff():

    ticket = {
        "ticket_id": "TKT-007",
        "customer": {
            "name": "Rahul Patil",
            "email": "rahulpatil@example.com",
            "phone": "9876543210",
        },
        "order_id": "ORD77777",
        "product": "laptop",
        "product_code": "LAP-001",
        "issue": "delivery_delay",
        "reference_date":
            "18/09/2026",
        "conversation_summary":
            "Customer reports delayed delivery.",
        "evidence": [
            "Expected delivery was 18/09/2026."
        ],
        "missing_information": [],
        "status": "ready",
    }

    priority_data = {
        "priority": "high",
        "sla": {
            "sla_deadline":
                "2026-09-23T14:00:00"
        },
        "routing": {
            "agent_name":
                "Support Agent 1"
        },
    }

    result = create_masked_handoff_summary(
        ticket,
        priority_data,
    )

    print(
        "\n--- Test 4: Masked Handoff ---"
    )
    print(result)

    assert (
        result["customer"]["email"]
        != "rahulpatil@example.com"
    )

    assert (
        result["customer"]["phone"]
        != "9876543210"
    )

    assert (
        result["customer"]["phone"]
        == "******3210"
    )

    assert (
        result["customer"]["email"]
        == "r********l@example.com"
    )   

    assert (
        result["order_id"]
        == "ORD77777"
    )

    print(
        "PASS: Sensitive customer data masked."
    )


# ==================================================
# Run Tests
# ==================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("TASK 3 - DAY 3 TICKET LINKING TESTS")
    print("=" * 60)

    test_duplicate_same_order()

    test_related_same_order_different_issue()

    test_unrelated_ticket()

    test_masked_handoff()

    print("\n" + "=" * 60)
    print("ALL DAY 3 BASIC TESTS COMPLETED")
    print("=" * 60)