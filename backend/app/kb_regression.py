from pathlib import Path


# ==================================================
# Project Paths
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"


# ==================================================
# Regression Test Cases
# ==================================================

REGRESSION_TESTS = [
    {
        "name": "Standard delivery time",
        "file": "delivery_policy.txt",
        "question": "How long does standard delivery take?",
        "expected_phrases": [
            "3 to 5 business days"
        ]
    },
    {
        "name": "Express delivery time",
        "file": "delivery_policy.txt",
        "question": "How long does express delivery take?",
        "expected_phrases": [
            "1 to 2 business days"
        ]
    },
    {
        "name": "Delivery tracking",
        "file": "delivery_policy.txt",
        "question": "How can I track my order?",
        "expected_phrases": [
            "track their order",
            "order ID"
        ]
    },
    {
        "name": "Payment failure",
        "file": "payment_policy.txt",
        "question": "What should I do if payment fails?",
        "expected_phrases": [
            "verify their payment information",
            "try the payment again"
        ]
    },
    {
        "name": "Payment security",
        "file": "payment_policy.txt",
        "question": "What payment information should I never share?",
        "expected_phrases": [
            "password",
            "PIN",
            "CVV"
        ]
    }
]


# ==================================================
# Normalize Text
# ==================================================

def normalize_text(text):
    """
    Normalize text for reliable phrase comparison.
    """

    return " ".join(
        text.lower().split()
    )


# ==================================================
# Read Knowledge File
# ==================================================

def read_knowledge_file(file_name):

    file_path = KNOWLEDGE_BASE_DIR / file_name

    if not file_path.exists():
        return None, f"Knowledge-base file does not exist: {file_name}"

    try:
        content = file_path.read_text(
            encoding="utf-8"
        )

        return content, None

    except Exception as error:

        return None, (
            f"Could not read {file_name}: {error}"
        )


# ==================================================
# Run Single Regression Test
# ==================================================

def run_regression_test(test_case):

    file_name = test_case["file"]

    content, error = read_knowledge_file(
        file_name
    )

    if error:

        return {
            "name": test_case["name"],
            "question": test_case["question"],
            "status": "FAIL",
            "reason": error,
            "missing": test_case["expected_phrases"]
        }

    normalized_content = normalize_text(
        content
    )

    missing_phrases = []

    for phrase in test_case["expected_phrases"]:

        normalized_phrase = normalize_text(
            phrase
        )

        if normalized_phrase not in normalized_content:

            missing_phrases.append(
                phrase
            )

    if missing_phrases:

        return {
            "name": test_case["name"],
            "question": test_case["question"],
            "status": "FAIL",
            "reason": "Expected factual evidence is missing.",
            "missing": missing_phrases
        }

    return {
        "name": test_case["name"],
        "question": test_case["question"],
        "status": "PASS",
        "reason": None,
        "missing": []
    }


# ==================================================
# Run All Regression Tests
# ==================================================

def run_all_regression_tests():

    results = []

    passed = 0
    failed = 0

    for test_case in REGRESSION_TESTS:

        result = run_regression_test(
            test_case
        )

        results.append(result)

        if result["status"] == "PASS":
            passed += 1
        else:
            failed += 1

    total = len(REGRESSION_TESTS)

    if total > 0:
        pass_rate = round(
            (passed / total) * 100,
            1
        )
    else:
        pass_rate = 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "results": results
    }


# ==================================================
# Print Regression Report
# ==================================================

def print_report(report):

    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE REGRESSION TEST REPORT")
    print("=" * 60)

    print(
        f"\nTotal tests: {report['total']}"
    )

    print(
        f"Passed: {report['passed']}"
    )

    print(
        f"Failed: {report['failed']}"
    )

    print(
        f"Pass rate: {report['pass_rate']}%"
    )

    print("\nTest results:")

    for result in report["results"]:

        print(
            f"\n{result['status']} - "
            f"{result['name']}"
        )

        if result["question"]:

            print(
                f"Question: "
                f"{result['question']}"
            )

        if result["reason"]:

            print(
                f"Reason: "
                f"{result['reason']}"
            )

        if result["missing"]:

            print(
                "Missing: "
                + ", ".join(
                    result["missing"]
                )
            )

    print("\n" + "=" * 60)


# ==================================================
# Main
# ==================================================

if __name__ == "__main__":

    report = run_all_regression_tests()

    print_report(
        report
    )