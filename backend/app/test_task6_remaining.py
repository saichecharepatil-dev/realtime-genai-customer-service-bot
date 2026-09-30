from datetime import datetime, timedelta

from .multilingual_context import (
    analyze_message,
    check_inactivity,
    restore_session,
    conversation_sessions,
)


def print_result(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"      {details}")


def main():
    print("=" * 70)
    print("TASK 6 - REMAINING TESTS")
    print("=" * 70)

    # ------------------------------------------------------------
    # 1. Multiple requests
    # ------------------------------------------------------------
    result = analyze_message(
        session_id="multiple-request-test",
        message="Where is my order and I also need a refund?",
        current_time=datetime.now(),
    )

    passed = (
        result["multiple_requests"] is True
        and len(result["requests"]) >= 2
    )

    print_result(
        "Multiple request detection",
        passed,
        f"requests={result['requests']}",
    )

    # ------------------------------------------------------------
    # 2. Correction detection
    # ------------------------------------------------------------
    result = analyze_message(
        session_id="correction-test",
        message="No, I meant order ORD12345.",
        current_time=datetime.now(),
    )

    passed = result["correction"] is True

    print_result(
        "Correction detection",
        passed,
        f"correction={result['correction']}",
    )

    # ------------------------------------------------------------
    # 3. Entity preservation
    # ------------------------------------------------------------
    result = analyze_message(
        session_id="entity-full-test",
        message=(
            "My name is Rahul. My order ORD77889 "
            "for product SKUABC123 is dated 15/09/2026."
        ),
        current_time=datetime.now(),
    )

    entities = result["preserved_entities"]

    passed = (
        "ORD77889" in entities["order_ids"]
        and "15/09/2026" in entities["dates"]
        and "SKUABC123" in entities["product_codes"]
        and len(entities["names"]) > 0
    )

    print_result(
        "Name/order/date/product preservation",
        passed,
        f"entities={entities}",
    )

    # ------------------------------------------------------------
    # 4. Low language confidence
    # ------------------------------------------------------------
    result = analyze_message(
        session_id="low-language-test",
        message="xyz qwerty abc",
        current_time=datetime.now(),
    )

    passed = result["clarification_required"] is True

    print_result(
        "Low language confidence clarification",
        passed,
        f"clarification={result['clarification_required']}, "
        f"reason={result['clarification_reason']}",
    )

    # ------------------------------------------------------------
    # 5. Low intent confidence
    # ------------------------------------------------------------
    result = analyze_message(
        session_id="low-intent-test",
        message="Hello there",
        current_time=datetime.now(),
    )

    passed = (
        result["intent_confidence"] < 0.60
        and result["clarification_required"] is True
    )

    print_result(
        "Low intent confidence clarification",
        passed,
        f"intent_confidence={result['intent_confidence']}, "
        f"clarification={result['clarification_required']}",
    )

    # ------------------------------------------------------------
    # 6. 30-minute inactivity
    # ------------------------------------------------------------
    inactivity_session = "inactivity-test"

    first_time = datetime.now()

    analyze_message(
        session_id=inactivity_session,
        message="My order ORD11111 is late.",
        current_time=first_time,
    )

    check_time = first_time + timedelta(minutes=31)

    inactivity = check_inactivity(
        session_id=inactivity_session,
        current_time=check_time,
    )

    passed = (
        inactivity["inactive"] is True
        and inactivity["inactive_minutes"] >= 30
    )

    print_result(
        "30-minute inactivity detection",
        passed,
        f"inactive={inactivity['inactive']}, "
        f"minutes={inactivity['inactive_minutes']}",
    )

    # ------------------------------------------------------------
    # 7. Session restoration within 24 hours
    # ------------------------------------------------------------
    restore_session_id = "restore-12h-test"

    restore_start = datetime.now()

    analyze_message(
        session_id=restore_session_id,
        message="My order ORD22222 has not arrived.",
        current_time=restore_start,
    )

    restore_time = restore_start + timedelta(hours=12)

    restored = restore_session(
        session_id=restore_session_id,
        current_time=restore_time,
    )

    passed = (
        restored["restored"] is True
        and restored["new_session_required"] is False
        and restored["summary"] is not None
    )

    print_result(
        "Session restoration within 24 hours",
        passed,
        f"restored={restored['restored']}, "
        f"new_session_required={restored['new_session_required']}",
    )

    # ------------------------------------------------------------
    # 8. New session required after 24 hours
    # ------------------------------------------------------------
    expired_session_id = "restore-25h-test"

    expired_start = datetime.now()

    analyze_message(
        session_id=expired_session_id,
        message="I still need help with ORD33333.",
        current_time=expired_start,
    )

    expired_time = expired_start + timedelta(hours=25)

    expired = restore_session(
        session_id=expired_session_id,
        current_time=expired_time,
    )

    passed = (
        expired["restored"] is False
        and expired["new_session_required"] is True
        and expired["reason"] == "restore_window_expired"
    )

    print_result(
        "New session required after 24 hours",
        passed,
        f"restored={expired['restored']}, "
        f"new_session_required={expired['new_session_required']}, "
        f"reason={expired['reason']}",
    )

    # ------------------------------------------------------------
    # 9. Session isolation
    # ------------------------------------------------------------
    session_a = "isolated-session-a"
    session_b = "isolated-session-b"

    now = datetime.now()

    result_a = analyze_message(
        session_id=session_a,
        message="My order is ORD44444.",
        current_time=now,
    )

    result_b = analyze_message(
        session_id=session_b,
        message="My order is ORD55555.",
        current_time=now,
    )

    session_a_data = conversation_sessions.get(session_a)
    session_b_data = conversation_sessions.get(session_b)

    passed = (
        session_a_data is not None
        and session_b_data is not None
        and session_a_data["session_id"] != session_b_data["session_id"]
        and any(
            "ORD44444" in item["message"]
            for item in session_a_data["messages"]
        )
        and not any(
            "ORD55555" in item["message"]
            for item in session_a_data["messages"]
        )
        and any(
            "ORD55555" in item["message"]
            for item in session_b_data["messages"]
        )
        and not any(
            "ORD44444" in item["message"]
            for item in session_b_data["messages"]
        )
    )

    print_result(
        "Session isolation",
        passed,
        f"session_a_messages={len(session_a_data['messages']) if session_a_data else 0}, "
        f"session_b_messages={len(session_b_data['messages']) if session_b_data else 0}",
    )

    # ------------------------------------------------------------
    # 10. Spelling/transliteration variation
    # ------------------------------------------------------------
    result = analyze_message(
        session_id="spelling-test",
        message="Mera order abhi tak nahi aaya",
        current_time=datetime.now(),
    )

    passed = (
        result["language"]["language"] == "hi"
        and result["intent_confidence"] >= 0.75
        and result["clarification_required"] is False
    )

    print_result(
        "Transliteration/spelling variation",
        passed,
        f"language={result['language']['language']}, "
        f"intent_confidence={result['intent_confidence']}",
    )

    # ------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------
    print()
    print("=" * 70)
    print("TASK 6 REMAINING TESTS FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()