import json
import urllib.request
import urllib.error
import uuid


BASE_URL = "http://127.0.0.1:8000"
CHAT_URL = f"{BASE_URL}/chat"


def chat(message, session_id=None):
    if session_id is None:
        session_id = f"task6-test-{uuid.uuid4().hex[:8]}"

    payload = {
        "session_id": session_id,
        "message": message,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        CHAT_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, {
            "error": body,
        }

    except Exception as error:
        return 0, {
            "error": str(error),
        }


def check(condition, title, details=""):
    if condition:
        print(f"PASS: {title}")
        if details:
            print(details)
    else:
        print(f"FAIL: {title}")
        if details:
            print(details)

    return condition


def print_result(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    print("=" * 70)
    print("TASK 6 - /chat API INTEGRATION TESTS")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Hindi / transliteration
    # --------------------------------------------------

    session_id = f"task6-hindi-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "Mera order ORD12345 abhi tak nahi aaya",
        session_id,
    )

    print("\n[TEST 1] Hindi / transliteration")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        check(
            result.get("language") == "hi",
            "Hindi language detection",
            f"language={result.get('language')}",
        )

        check(
            result.get("preserved_entities", {}).get("order_ids")
            == ["ORD12345"],
            "Order ID preservation",
            f"entities={result.get('preserved_entities')}",
        )

        check(
            result.get("clarification_required") is False,
            "No unnecessary clarification",
            f"clarification={result.get('clarification_required')}",
        )

    # --------------------------------------------------
    # 2. Marathi
    # --------------------------------------------------

    session_id = f"task6-marathi-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "Maza order ORD54321 ajun aala nahi",
        session_id,
    )

    print("\n[TEST 2] Marathi")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        check(
            result.get("language") == "mr",
            "Marathi language detection",
            f"language={result.get('language')}",
        )

        check(
            "ORD54321"
            in result.get("preserved_entities", {}).get("order_ids", []),
            "Marathi order ID preservation",
            f"entities={result.get('preserved_entities')}",
        )

    # --------------------------------------------------
    # 3. Spanish
    # --------------------------------------------------

    session_id = f"task6-spanish-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "¿Dónde está mi pedido ORD67890?",
        session_id,
    )

    print("\n[TEST 3] Spanish")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        check(
            result.get("language") == "es",
            "Spanish language detection",
            f"language={result.get('language')}",
        )

        check(
            "ORD67890"
            in result.get("preserved_entities", {}).get("order_ids", []),
            "Spanish order ID preservation",
            f"entities={result.get('preserved_entities')}",
        )

    # --------------------------------------------------
    # 4. Mixed language
    # --------------------------------------------------

    session_id = f"task6-mixed-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "Mera order ORD99887 is late",
        session_id,
    )

    print("\n[TEST 4] Mixed Hindi + English")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        check(
            result.get("language") == "hi",
            "Primary language is Hindi",
            f"language={result.get('language')}",
        )

        check(
            result.get("mixed_language") is True,
            "Mixed-language detection",
            f"mixed_language={result.get('mixed_language')}",
        )

        check(
            "en" in result.get("detected_languages", []),
            "English detected in mixed message",
            f"detected_languages={result.get('detected_languages')}",
        )

    # --------------------------------------------------
    # 5. Multiple requests
    # --------------------------------------------------

    session_id = f"task6-multiple-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "Where is my order and I also need a refund?",
        session_id,
    )

    print("\n[TEST 5] Multiple requests")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        requests = result.get("requests", [])

        check(
            result.get("multiple_requests") is True,
            "Multiple request detection",
            f"multiple_requests={result.get('multiple_requests')}",
        )

        check(
            len(requests) >= 2,
            "At least two requests detected",
            f"requests={requests}",
        )

    # --------------------------------------------------
    # 6. Low language confidence
    # --------------------------------------------------

    session_id = f"task6-low-language-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "xyz qwerty abc",
        session_id,
    )

    print("\n[TEST 6] Low language confidence")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        check(
            result.get("clarification_required") is True,
            "Clarification requested for low confidence",
            f"clarification={result.get('clarification_required')}",
        )

        print(
            f"reason={result.get('clarification_reason')}"
        )

    # --------------------------------------------------
    # 7. Low intent confidence
    # --------------------------------------------------

    session_id = f"task6-low-intent-{uuid.uuid4().hex[:8]}"

    status, result = chat(
        "Hello there",
        session_id,
    )

    print("\n[TEST 7] Low intent confidence")
    print(f"HTTP status: {status}")

    if status != 200:
        print_result(result)
    else:
        check(
            result.get("clarification_required") is True,
            "Clarification requested for low intent confidence",
            f"clarification={result.get('clarification_required')}",
        )

        check(
            result.get("multilingual_intent_confidence", 1.0) < 0.60,
            "Low multilingual intent confidence",
            f"intent_confidence={result.get('multilingual_intent_confidence')}",
        )

    # --------------------------------------------------
    # 8. Context persistence
    # --------------------------------------------------

    session_id = f"task6-context-{uuid.uuid4().hex[:8]}"

    status1, result1 = chat(
        "My order is ORD11111",
        session_id,
    )

    status2, result2 = chat(
        "Where is it?",
        session_id,
    )

    print("\n[TEST 8] Context persistence")
    print(f"First HTTP status: {status1}")
    print(f"Second HTTP status: {status2}")

    if status1 == 200 and status2 == 200:
        check(
            result2.get("context_message_count", 0) >= 2,
            "Conversation context retained",
            f"context_message_count={result2.get('context_message_count')}",
        )
    else:
        print_result(result1)
        print_result(result2)

    # --------------------------------------------------
    # 9. Session isolation
    # --------------------------------------------------

    session_a = f"task6-isolation-a-{uuid.uuid4().hex[:8]}"
    session_b = f"task6-isolation-b-{uuid.uuid4().hex[:8]}"

    status_a, result_a = chat(
        "My order is ORDAAAA1",
        session_a,
    )

    status_b, result_b = chat(
        "My order is ORDBBBB2",
        session_b,
    )

    print("\n[TEST 9] Session isolation")
    print(f"Session A HTTP status: {status_a}")
    print(f"Session B HTTP status: {status_b}")

    if status_a == 200 and status_b == 200:
        entities_a = result_a.get("preserved_entities", {})
        entities_b = result_b.get("preserved_entities", {})

        orders_a = entities_a.get("order_ids", [])
        orders_b = entities_b.get("order_ids", [])

        check(
            "ORDAAAA1" in orders_a
            and "ORDBBBB2" not in orders_a,
            "Session A isolation",
            f"session_a_orders={orders_a}",
        )

        check(
            "ORDBBBB2" in orders_b
            and "ORDAAAA1" not in orders_b,
            "Session B isolation",
            f"session_b_orders={orders_b}",
        )
    else:
        print_result(result_a)
        print_result(result_b)

    # --------------------------------------------------
    # Final
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("TASK 6 - /chat API INTEGRATION TESTS FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()