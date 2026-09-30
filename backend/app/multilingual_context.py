"""
Task 6 - Multilingual and Conversation Context

Supported languages:
- English
- Hindi
- Marathi
- Spanish

Features:
- Language detection
- Hindi/Marathi transliteration support
- Mixed-language detection
- Entity preservation
- Multiple-request detection
- Correction detection
- Intent-confidence estimation
- Maximum 10-message context
- 30-minute inactivity detection
- 24-hour session restoration window
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
}


MAX_CONTEXT_MESSAGES = 10
INACTIVITY_MINUTES = 30
RESTORE_WINDOW_HOURS = 24

conversation_sessions = {}


# Words that are commonly used across support conversations
# and should not by themselves indicate a language.
SHARED_WORDS = {
    "order",
    "orders",
    "payment",
    "refund",
    "delivery",
    "product",
    "return",
    "returns",
    "amount",
    "invoice",
    "date",
    "email",
    "phone",
    "code",
    "support",
    "issue",
    "problem",
    "status",
    "tracking",
    "track",
    "online",
    "app",
    "customer",
}


ENGLISH_WORDS = {
    "the",
    "is",
    "are",
    "was",
    "were",
    "my",
    "your",
    "our",
    "this",
    "that",
    "what",
    "when",
    "where",
    "why",
    "how",
    "can",
    "could",
    "please",
    "want",
    "need",
    "has",
    "have",
    "not",
    "arrived",
    "come",
    "received",
    "today",
    "tomorrow",
    "yesterday",
    "help",
    "tell",
    "give",
    "show",
    "refund",
    "payment",
    "delivery",
    "late",
    "yet",
    "also",
    "and",
    "i",
}


# English words that are especially useful for identifying
# English content inside a mixed-language message.
MIXED_ENGLISH_WORDS = {
    "is",
    "are",
    "was",
    "were",
    "my",
    "your",
    "our",
    "this",
    "that",
    "what",
    "when",
    "where",
    "why",
    "how",
    "can",
    "could",
    "please",
    "want",
    "need",
    "has",
    "have",
    "not",
    "arrived",
    "come",
    "received",
    "today",
    "tomorrow",
    "yesterday",
    "help",
    "tell",
    "give",
    "show",
    "late",
    "yet",
    "also",
    "and",
    "i",
}


HINDI_WORDS = {
    "mera",
    "meri",
    "mere",
    "mujhe",
    "mujhko",
    "aap",
    "apka",
    "aapki",
    "hamara",
    "hamari",
    "hai",
    "hain",
    "tha",
    "thi",
    "the",
    "ho",
    "hoga",
    "hogi",
    "kab",
    "kaha",
    "kahan",
    "kyun",
    "kyon",
    "kaise",
    "kaisa",
    "kaisi",
    "kya",
    "nahi",
    "nahin",
    "abhi",
    "tak",
    "aa",
    "aaya",
    "aayi",
    "aaye",
    "mila",
    "mili",
    "milega",
    "chahiye",
    "chahie",
    "karna",
    "karni",
    "karo",
    "batao",
    "bataiye",
    "order",
}


MARATHI_WORDS = {
    "majha",
    "majhi",
    "majhe",
    "mala",
    "tumcha",
    "tumchi",
    "tumche",
    "aamcha",
    "aamchi",
    "aahe",
    "ahet",
    "hota",
    "hoti",
    "hote",
    "kadhi",
    "kuthe",
    "ka",
    "kaay",
    "kay",
    "kasa",
    "kashi",
    "kase",
    "nahi",
    "ajun",
    "paryant",
    "aala",
    "aali",
    "aale",
    "milala",
    "milali",
    "milt",
    "havay",
    "hava",
    "havi",
    "sanga",
    "sangaa",
    "karaycha",
    "karaychi",
    "karayche",
    "order",
}


SPANISH_WORDS = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "mi",
    "mis",
    "tu",
    "su",
    "que",
    "es",
    "son",
    "está",
    "esta",
    "están",
    "estan",
    "donde",
    "dónde",
    "cuando",
    "cuándo",
    "como",
    "cómo",
    "por",
    "para",
    "con",
    "sin",
    "quiero",
    "necesito",
    "puede",
    "puedes",
    "ayuda",
    "pedido",
    "entrega",
    "pago",
    "reembolso",
    "devolución",
    "devolucion",
}


DEVANAGARI_PATTERN = re.compile(
    r"[\u0900-\u097F]+"
)


HINDI_DEVANAGARI_WORDS = {
    "मेरा",
    "मेरी",
    "मेरे",
    "मुझे",
    "आपका",
    "आपकी",
    "आपके",
    "हमारा",
    "हमारी",
    "है",
    "हैं",
    "था",
    "थी",
    "थे",
    "कब",
    "कहाँ",
    "कहा",
    "क्यों",
    "कैसे",
    "क्या",
    "नहीं",
    "अभी",
    "तक",
    "आया",
    "आई",
    "आए",
    "मिला",
    "मिली",
    "चाहिए",
    "करना",
    "करो",
    "बताओ",
}


MARATHI_DEVANAGARI_WORDS = {
    "माझा",
    "माझी",
    "माझे",
    "मला",
    "तुमचा",
    "तुमची",
    "तुमचे",
    "आमचा",
    "आमची",
    "आहे",
    "आहेत",
    "होता",
    "होती",
    "होते",
    "कधी",
    "कुठे",
    "का",
    "काय",
    "कसा",
    "कशी",
    "कसे",
    "नाही",
    "अजून",
    "पर्यंत",
    "आला",
    "आली",
    "आले",
    "मिळाला",
    "मिळाली",
    "हवा",
    "हवी",
    "सांगा",
}


def _tokenize(text: str):
    return re.findall(
        r"[A-Za-zÀ-ÿ\u0900-\u097F]+",
        text.lower(),
    )


def _latin_tokens(text: str):
    return re.findall(
        r"[a-zà-ÿ]+",
        text.lower(),
    )


def _count_matches(tokens, vocabulary):
    return sum(
        1
        for token in tokens
        if token in vocabulary
    )


def _has_devanagari(text: str):
    return bool(
        DEVANAGARI_PATTERN.search(text)
    )


def _normalize_transliteration(text: str):
    replacements = {
        "nahin": "nahi",
        "nahii": "nahi",
        "nhi": "nahi",
        "kaha": "kahan",
        "kahaan": "kahan",
        "kaise": "kaise",
        "kaisa": "kaisa",
        "kaisi": "kaisi",
        "mujko": "mujhe",
        "mujhko": "mujhe",
        "chahiye": "chahiye",
        "chahie": "chahiye",
        "krna": "karna",
        "krni": "karni",
        "krdo": "kardo",
        "btao": "batao",
        "btaiye": "bataiye",
        "majha": "majha",
        "mazha": "majha",
        "majhi": "majhi",
        "maza": "majha",
        "ajun": "ajun",
        "ahe": "aahe",
        "aahe": "aahe",
    }

    words = text.split()
    normalized = []

    for word in words:
        clean = re.sub(
            r"[^A-Za-zÀ-ÿ]",
            "",
            word.lower(),
        )

        if clean in replacements:
            normalized.append(
                word.replace(
                    clean,
                    replacements[clean],
                )
            )
        else:
            normalized.append(word)

    return " ".join(normalized)


def extract_preserved_entities(text: str):
    order_ids = re.findall(
        r"\b(?:ORD|ORDER)[-\_]?[A-Z0-9]{4,}\b",
        text.upper(),
    )

    dates = re.findall(
        r"\b(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|"
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"
        r")\b",
        text,
    )

    product_codes = re.findall(
        r"\b(?:SKU|PROD|PRODUCT)[-\_]?[A-Z0-9]{3,}\b",
        text.upper(),
    )

    names = []

    name_matches = re.findall(
        r"\b(?:my name is|i am|i'm)\s+"
        r"([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,2})",
        text,
        flags=re.IGNORECASE,
    )

    for name in name_matches:
        names.append(name.strip())

    return {
        "order_ids": list(
            dict.fromkeys(order_ids)
        ),
        "dates": list(
            dict.fromkeys(dates)
        ),
        "product_codes": list(
            dict.fromkeys(product_codes)
        ),
        "names": list(
            dict.fromkeys(names)
        ),
    }


def detect_language(text: str):
    normalized = _normalize_transliteration(
        text
    )

    latin_tokens = _latin_tokens(
        normalized
    )

    all_tokens = _tokenize(
        normalized
    )

    scores = {
        "en": 0.0,
        "hi": 0.0,
        "mr": 0.0,
        "es": 0.0,
    }

    scores["en"] += (
        _count_matches(
            latin_tokens,
            ENGLISH_WORDS,
        )
        * 1.0
    )

    scores["hi"] += (
        _count_matches(
            latin_tokens,
            HINDI_WORDS,
        )
        * 1.5
    )

    scores["mr"] += (
        _count_matches(
            latin_tokens,
            MARATHI_WORDS,
        )
        * 1.5
    )

    scores["es"] += (
        _count_matches(
            latin_tokens,
            SPANISH_WORDS,
        )
        * 1.5
    )

    devanagari_tokens = (
        DEVANAGARI_PATTERN.findall(
            normalized.lower()
        )
    )

    devanagari_words = []

    for group in devanagari_tokens:
        devanagari_words.extend(
            group.split()
        )

    hindi_deva_score = _count_matches(
        devanagari_words,
        HINDI_DEVANAGARI_WORDS,
    )

    marathi_deva_score = _count_matches(
        devanagari_words,
        MARATHI_DEVANAGARI_WORDS,
    )

    scores["hi"] += (
        hindi_deva_score * 2.5
    )

    scores["mr"] += (
        marathi_deva_score * 2.5
    )

    meaningful_tokens = [
        token
        for token in latin_tokens
        if token not in SHARED_WORDS
    ]

    language_hits = {
        "en": _count_matches(
            meaningful_tokens,
            ENGLISH_WORDS,
        ),
        "hi": _count_matches(
            meaningful_tokens,
            HINDI_WORDS,
        ),
        "mr": _count_matches(
            meaningful_tokens,
            MARATHI_WORDS,
        ),
        "es": _count_matches(
            meaningful_tokens,
            SPANISH_WORDS,
        ),
    }

    # Separate English-content detection for mixed-language
    # messages. Common support words are allowed here because
    # they can still be useful evidence of English in a
    # Hindi/English or Marathi/English message.
    mixed_english_hits = _count_matches(
        latin_tokens,
        MIXED_ENGLISH_WORDS,
    )

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    top_language, top_score = ranked[0]

    second_language, second_score = ranked[1]

    total_score = sum(
        scores.values()
    )

    if _has_devanagari(normalized):
        if (
            hindi_deva_score
            > marathi_deva_score
        ):
            top_language = "hi"
            top_score = scores["hi"]

        elif (
            marathi_deva_score
            > hindi_deva_score
        ):
            top_language = "mr"
            top_score = scores["mr"]

    if total_score <= 0:
        return {
            "language": "en",
            "language_name": "English",
            "confidence": 0.25,
            "detected_languages": ["en"],
            "mixed_language": False,
            "needs_clarification": True,
        }

    confidence = (
        top_score / total_score
    )

    if (
        top_language in {"hi", "mr"}
        and top_score >= 2
    ):
        confidence = max(
            confidence,
            0.75,
        )

    if (
        top_language == "es"
        and top_score >= 2
    ):
        confidence = max(
            confidence,
            0.80,
        )

    if (
        top_language == "en"
        and top_score >= 2
    ):
        confidence = max(
            confidence,
            0.80,
        )

    confidence = min(
        confidence,
        1.0,
    )

    detected_languages = []

    for language, hits in language_hits.items():
        if hits > 0:
            detected_languages.append(
                language
            )

    if (
        top_language
        not in detected_languages
    ):
        detected_languages.insert(
            0,
            top_language,
        )

    mixed_language = False

    # Explicit mixed-language handling.
    #
    # Example:
    # "Mera order ORD12345 is late."
    #
    # Hindi should remain the primary language,
    # while English should also be detected.
    if top_language in {"hi", "mr"}:
        if mixed_english_hits >= 2:
            mixed_language = True

            if "en" not in detected_languages:
                detected_languages.append(
                    "en"
                )

        elif (
            mixed_english_hits == 1
            and language_hits["en"] >= 1
        ):
            mixed_language = True

            if "en" not in detected_languages:
                detected_languages.append(
                    "en"
                )

    elif top_language == "en":
        secondary_languages = [
            language
            for language in (
                "hi",
                "mr",
                "es",
            )
            if language_hits.get(
                language,
                0,
            ) >= 1
        ]

        if secondary_languages:
            mixed_language = True

            for language in secondary_languages:
                if (
                    language
                    not in detected_languages
                ):
                    detected_languages.append(
                        language
                    )

    else:
        secondary_languages = [
            language
            for language in (
                "en",
                "hi",
                "mr",
            )
            if language_hits.get(
                language,
                0,
            ) >= 1
        ]

        if secondary_languages:
            mixed_language = True

            for language in secondary_languages:
                if (
                    language
                    not in detected_languages
                ):
                    detected_languages.append(
                        language
                    )

    # Remove duplicates while preserving order.
    detected_languages = list(
        dict.fromkeys(
            detected_languages
        )
    )

    needs_clarification = (
        confidence < 0.60
    )

    if (
        top_language in {"hi", "mr"}
        and top_score >= 3
    ):
        needs_clarification = False

    if (
        top_language == "es"
        and top_score >= 2
    ):
        needs_clarification = False

    return {
        "language": top_language,
        "language_name": SUPPORTED_LANGUAGES[
            top_language
        ],
        "confidence": round(
            confidence,
            2,
        ),
        "detected_languages": detected_languages,
        "mixed_language": mixed_language,
        "needs_clarification": needs_clarification,
    }


def detect_multiple_requests(text: str):
    """
    Detect multiple customer requests.

    The function avoids splitting phrases such as:

        "I also need a refund?"

    into:

        "I"
        "need a refund?"

    Example:

        "Where is my order and I also need a refund?"

    becomes:

        [
            "Where is my order",
            "I also need a refund?"
        ]

    A message containing separate questions is also supported:

        "Where is my order? I need a refund?"

    becomes:

        [
            "Where is my order?",
            "I need a refund?"
        ]
    """

    text = text.strip()

    if not text:
        return {
            "multiple_requests": False,
            "requests": [],
        }

    # IMPORTANT:
    # "also" is NOT treated as an independent separator.
    #
    # We primarily split on conjunctions that join
    # two separate requests.
    connector_pattern = (
        r"\s+(?:"
        r"and"
        r"|plus"
        r"|aur"
        r"|ani"
        r"|y"
        r"|también"
        r"|tambien"
        r")\s+"
    )

    parts = re.split(
        connector_pattern,
        text,
        flags=re.IGNORECASE,
    )

    requests = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    # If no connector was found, support multiple
    # independently written questions.
    if len(requests) == 1:
        sentence_parts = re.split(
            r"\?\s+(?=[A-Za-zÀ-ÿ])"
            r"|;\s+",
            text,
        )

        sentence_parts = [
            part.strip()
            for part in sentence_parts
            if part.strip()
        ]

        if len(sentence_parts) > 1:
            requests = sentence_parts

    requests = [
        request.strip()
        for request in requests
        if request.strip()
    ]

    return {
        "multiple_requests": len(
            requests
        ) > 1,
        "requests": requests,
    }


def detect_correction(text: str):
    correction_patterns = [
        r"\bno\b.*\bnot\b",
        r"\bi meant\b",
        r"\bi mean\b",
        r"\bactually\b",
        r"\bcorrection\b",
        r"\bnot that\b",
        r"\bgalat\b",
        r"\bnahi\b.*\bmera\b",
        r"\bchuk\b",
        r"\bmaza matlab\b",
        r"\bnahi\s+majha\b",
    ]

    for pattern in correction_patterns:
        if re.search(
            pattern,
            text.lower(),
        ):
            return True

    return None


def calculate_intent_confidence(
    text: str,
    language_data,
):
    text_lower = text.lower()

    intent_patterns = {
        "delivery": [
            # English
            "order",
            "delivery",
            "arrived",
            "come",

            # Hindi transliteration
            "aaya",
            "aayi",
            "aale",
            "aala",
            "kahan",
            "late",
            "tak",
            "paryant",

            # Marathi transliteration
            "kuthe",

            # Hindi Devanagari
            "ऑर्डर",
            "आर्डर",
            "डिलीवरी",
            "डिलीवर",
            "पार्सल",
            "पैकेज",
            "आएगा",
            "आएगी",
            "आएंगे",
            "आया",
            "आई",
            "आए",
            "कब",
            "कहाँ",
            "कहां",
            "अभी",
            "तक",
            "पहुंचेगा",
            "पहुंचेगी",
            "पहुंचे",
            "नहीं आया",
            "नहीं आई",
            "नहीं मिला",
            "नहीं मिली",
        ],

        "payment": [
            # English
            "payment",
            "paid",
            "pay",
            "paisa",
            "paise",
            "payment fail",
            "failed",

            # Hindi Devanagari
            "भुगतान",
            "पेमेंट",
            "पैसा",
            "पैसे",
            "भुगतान विफल",
            "पेमेंट फेल",
            "फेल",
            "असफल",
            "कार्ड",
        ],

        "return": [
            # English
            "return",
            "refund",
            "money back",

            # Hindi / Marathi transliteration
            "wapas",
            "parat",

            # Devanagari
            "वापस",
            "परत",
            "रिफंड",
            "रिटर्न",
            "पैसे वापस",
        ],

        "tracking": [
            # English
            "track",
            "tracking",
            "status",
            "where is my order",

            # Hindi / Marathi transliteration
            "kaha",
            "kuthe",

            # Hindi Devanagari
            "कहाँ है",
            "कहां है",
            "कहाँ गया",
            "कहां गया",
            "स्थिति",
            "स्टेटस",
            "ट्रैक",
            "ट्रैकिंग",
            "मेरा ऑर्डर कहाँ",
            "मेरा ऑर्डर कहां",
        ],
    }

    scores = {}

    for intent, patterns in (
        intent_patterns.items()
    ):
        scores[intent] = sum(
            1
            for pattern in patterns
            if pattern in text_lower
        )

    best_score = max(
        scores.values(),
        default=0,
    )

    if best_score == 0:
        confidence = 0.35

    elif best_score == 1:
        confidence = 0.65

    elif best_score == 2:
        confidence = 0.85

    else:
        confidence = 0.95

    if (
        language_data["language"]
        in {"hi", "mr", "es"}
    ):
        if best_score >= 1:
            confidence = max(
                confidence,
                0.75,
            )

    return round(
        confidence,
        2,
    )


def _get_session(session_id: str):
    return conversation_sessions.get(
        session_id
    )


def _create_session(
    session_id: str,
    current_time: datetime,
):
    session = {
        "session_id": session_id,
        "created_at": current_time,
        "last_activity": current_time,
        "messages": [],
        "summary": None,
    }

    conversation_sessions[
        session_id
    ] = session

    return session


def _build_summary(session):
    messages = session.get(
        "messages",
        [],
    )

    if not messages:
        return None

    recent_messages = messages[
        -MAX_CONTEXT_MESSAGES:
    ]

    return {
        "session_id": session[
            "session_id"
        ],
        "message_count": len(
            messages
        ),
        "recent_messages": [
            {
                "message": item[
                    "message"
                ],
                "language": item[
                    "language"
                ],
            }
            for item in recent_messages
        ],
        "languages": list(
            dict.fromkeys(
                item["language"]
                for item in recent_messages
            )
        ),
    }


def check_inactivity(
    session_id: str,
    current_time: datetime,
):
    session = _get_session(
        session_id
    )

    if session is None:
        return {
            "session_id": session_id,
            "inactive": False,
            "inactive_minutes": 0,
            "status": "not_found",
            "summary": None,
        }

    elapsed = (
        current_time
        - session["last_activity"]
    ).total_seconds() / 60

    inactive = (
        elapsed
        >= INACTIVITY_MINUTES
    )

    status = (
        "inactive"
        if inactive
        else "active"
    )

    summary = (
        _build_summary(session)
        if inactive
        else None
    )

    return {
        "session_id": session_id,
        "inactive": inactive,
        "inactive_minutes": round(
            elapsed,
            2,
        ),
        "status": status,
        "summary": summary,
    }


def restore_session(
    session_id: str,
    current_time: datetime,
):
    session = _get_session(
        session_id
    )

    if session is None:
        return {
            "restored": False,
            "new_session_required": True,
            "summary": None,
            "reason": "session_not_found",
        }

    elapsed = (
        current_time
        - session["last_activity"]
    ).total_seconds()

    if (
        elapsed
        > RESTORE_WINDOW_HOURS * 3600
    ):
        return {
            "restored": False,
            "new_session_required": True,
            "summary": _build_summary(
                session
            ),
            "reason": "restore_window_expired",
        }

    summary = _build_summary(
        session
    )

    session[
        "last_activity"
    ] = current_time

    return {
        "restored": True,
        "new_session_required": False,
        "summary": summary,
        "reason": "session_restored",
    }


def analyze_message(
    session_id: str,
    message: str,
    current_time: datetime | None = None,
):
    if current_time is None:
        current_time = datetime.now()

    message = message.strip()

    language_data = detect_language(
        message
    )

    entities = (
        extract_preserved_entities(
            message
        )
    )

    request_data = (
        detect_multiple_requests(
            message
        )
    )

    correction = detect_correction(
        message
    )

    intent_confidence = (
        calculate_intent_confidence(
            message,
            language_data,
        )
    )

    session = _get_session(
        session_id
    )

    if session is None:
        session = _create_session(
            session_id,
            current_time,
        )

    session["messages"].append(
        {
            "message": message,
            "language": language_data[
                "language"
            ],
            "language_name": language_data[
                "language_name"
            ],
            "entities": entities,
            "timestamp": current_time,
        }
    )

    session["messages"] = (
        session["messages"][
            -MAX_CONTEXT_MESSAGES:
        ]
    )

    session[
        "last_activity"
    ] = current_time

    clarification_reasons = []

    if language_data[
        "needs_clarification"
    ]:
        clarification_reasons.append(
            "language_confidence_low"
        )

    if intent_confidence < 0.60:
        clarification_reasons.append(
            "intent_confidence_low"
        )

    if not message:
        clarification_reasons.append(
            "empty_message"
        )

    clarification_required = bool(
        clarification_reasons
    )

    return {
        "language": language_data,
        "preserved_entities": entities,
        "multiple_requests": request_data[
            "multiple_requests"
        ],
        "requests": request_data[
            "requests"
        ],
        "correction": correction,
        "intent_confidence": intent_confidence,
        "clarification_required": (
            clarification_required
        ),
        "clarification_reason": (
            clarification_reasons
        ),
        "context_message_count": len(
            session["messages"]
        ),
        "session_status": "active",
        "inactivity": check_inactivity(
            session_id,
            current_time,
        ),
    }


if __name__ == "__main__":

    tests = [
        (
            "Hindi transliteration",
            "Mera order ORD12345 abhi tak nahi aaya.",
            "hi",
        ),
        (
            "Hindi Devanagari",
            "मेरा ऑर्डर कब आएगा?",
            "hi",
        ),
        (
            "Marathi transliteration",
            "Majha order ORD12345 ajun aala nahi.",
            "mr",
        ),
        (
            "English",
            "My order ORD12345 has not arrived yet.",
            "en",
        ),
        (
            "Spanish",
            "Quiero saber dónde está mi pedido.",
            "es",
        ),
        (
            "Mixed",
            "Mera order ORD12345 is late.",
            "hi",
        ),
    ]

    print("=" * 60)
    print(
        "TASK 6 MULTILINGUAL TESTS"
    )
    print("=" * 60)

    for name, text, expected in tests:

        result = analyze_message(
            session_id=f"test-{expected}-{name}",
            message=text,
            current_time=datetime.now(),
        )

        print()
        print(name)
        print(
            "Message:",
            text,
        )
        print(
            "Detected:",
            result["language"][
                "language"
            ],
        )
        print(
            "Confidence:",
            result["language"][
                "confidence"
            ],
        )
        print(
            "Detected languages:",
            result["language"][
                "detected_languages"
            ],
        )
        print(
            "Mixed:",
            result["language"][
                "mixed_language"
            ],
        )
        print(
            "Entities:",
            result[
                "preserved_entities"
            ],
        )
        print(
            "Intent confidence:",
            result[
                "intent_confidence"
            ],
        )
        print(
            "Clarification:",
            result[
                "clarification_required"
            ],
        )

        if (
            result["language"][
                "language"
            ]
            == expected
        ):
            print("PASS")
        else:
            print(
                "FAIL - expected:",
                expected,
            )

    print()
    print("=" * 60)
    print(
        "TESTING MULTIPLE REQUESTS"
    )
    print("=" * 60)

    multiple_request_test = (
        "Where is my order and I also need a refund?"
    )

    multiple_result = (
        detect_multiple_requests(
            multiple_request_test
        )
    )

    print(
        "Message:",
        multiple_request_test,
    )

    print(
        "Multiple requests:",
        multiple_result[
            "multiple_requests"
        ],
    )

    print(
        "Requests:",
        multiple_result[
            "requests"
        ],
    )

    expected_requests = [
        "Where is my order",
        "I also need a refund?",
    ]

    if (
        multiple_result[
            "multiple_requests"
        ]
        and multiple_result[
            "requests"
        ]
        == expected_requests
    ):
        print("PASS")
    else:
        print(
            "FAIL - expected:",
            expected_requests,
        )

    print()
    print("=" * 60)
    print(
        "TESTING MIXED LANGUAGE"
    )
    print("=" * 60)

    mixed_test = (
        "Mera order ORD12345 is late."
    )

    mixed_result = detect_language(
        mixed_test
    )

    print(
        "Message:",
        mixed_test,
    )

    print(
        "Primary language:",
        mixed_result["language"],
    )

    print(
        "Detected languages:",
        mixed_result[
            "detected_languages"
        ],
    )

    print(
        "Mixed language:",
        mixed_result[
            "mixed_language"
        ],
    )

    if (
        mixed_result["language"]
        == "hi"
        and mixed_result[
            "mixed_language"
        ]
        is True
        and "en"
        in mixed_result[
            "detected_languages"
        ]
    ):
        print("PASS")
    else:
        print(
            "FAIL - expected Hindi + English mixed language"
        )

    print()
    print("=" * 60)
    print(
        "TESTING ENTITY PRESERVATION"
    )
    print("=" * 60)

    entity_test = analyze_message(
        session_id="entity-test",
        message=(
            "Mera order ORD99887 "
            "15/09/2026 ko nahi aaya."
        ),
    )

    print(
        entity_test[
            "preserved_entities"
        ]
    )

    print()
    print("=" * 60)
    print(
        "TESTING CONTEXT LIMIT"
    )
    print("=" * 60)

    context_session = (
        "context-test"
    )

    for i in range(12):

        result = analyze_message(
            session_id=context_session,
            message=f"Message {i + 1}",
        )

    print(
        "Context count:",
        result[
            "context_message_count"
        ],
    )

    if (
        result[
            "context_message_count"
        ]
        == 10
    ):
        print("PASS")
    else:
        print("FAIL")

    print()
    print("=" * 60)
    print(
        "ALL TESTS FINISHED"
    )
    print("=" * 60)