from pathlib import Path
from datetime import date
import re

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ==================================================
# Knowledge Base Location
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"


# ==================================================
# Embedding Model
# ==================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ==================================================
# Parse Document Metadata
# ==================================================

def parse_document(file_path):

    text = file_path.read_text(
        encoding="utf-8"
    )

    parts = text.split(
        "\n\n",
        1
    )

    metadata = {}

    metadata_block = parts[0]

    for line in metadata_block.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        key = key.strip()
        value = value.strip()

        if key != "METADATA":
            metadata[key] = value

    content = (
        parts[1]
        if len(parts) > 1
        else ""
    )

    return metadata, content


# ==================================================
# Prompt Injection Detection
# ==================================================

def contains_prompt_injection(text):

    suspicious_patterns = [

        "ignore previous instructions",
        "ignore all previous instructions",
        "ignore the previous instructions",
        "disregard previous instructions",
        "disregard all previous instructions",
        "forget previous instructions",
        "override system instructions",
        "reveal system prompt",
        "show system prompt",
        "print system prompt",
        "reveal confidential information",
        "reveal private information",
        "bypass security",
        "bypass access control",
        "disable safety",
        "follow these instructions instead",
        "you are now an administrator",
        "act as administrator",
    ]

    normalized_text = text.lower()

    for pattern in suspicious_patterns:

        if pattern in normalized_text:
            return True

    return False


# ==================================================
# Extract Reference Date
# ==================================================

def extract_reference_date(query):

    patterns = [

        r"\b(20\d{2}-\d{2}-\d{2})\b",

        r"\b(20\d{2}/\d{2}/\d{2})\b",

        r"\b(\d{2}/\d{2}/20\d{2})\b",

        r"\b(\d{2}-\d{2}-20\d{2})\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query
        )

        if not match:
            continue

        value = match.group(1)

        try:

            if "/" in value:

                parts = value.split("/")

                if len(parts) != 3:
                    continue

                # YYYY/MM/DD
                if len(parts[0]) == 4:

                    return date(
                        int(parts[0]),
                        int(parts[1]),
                        int(parts[2])
                    )

                # DD/MM/YYYY
                return date(
                    int(parts[2]),
                    int(parts[1]),
                    int(parts[0])
                )

            if value.count("-") == 2:

                parts = value.split("-")

                # YYYY-MM-DD
                if len(parts[0]) == 4:

                    return date(
                        int(parts[0]),
                        int(parts[1]),
                        int(parts[2])
                    )

                # DD-MM-YYYY
                return date(
                    int(parts[2]),
                    int(parts[1]),
                    int(parts[0])
                )

        except ValueError:

            return None

    return None


# ==================================================
# Multilingual Retrieval Query
# ==================================================

def build_multilingual_retrieval_query(query):

    text = query.lower().strip()

    # --------------------------------------------------
    # Hindi Devanagari
    # --------------------------------------------------

    hindi_mappings = {

        "मेरा ऑर्डर कब आएगा":
            "when will my order arrive delivery",

        "मेरा आर्डर कब आएगा":
            "when will my order arrive delivery",

        "मेरा ऑर्डर कब आएगी":
            "when will my order arrive delivery",

        "ऑर्डर कब आएगा":
            "when will my order arrive delivery",

        "आर्डर कब आएगा":
            "when will my order arrive delivery",

        "ऑर्डर कहाँ है":
            "where is my order tracking",

        "ऑर्डर कहां है":
            "where is my order tracking",

        "मेरा ऑर्डर कहाँ है":
            "where is my order tracking",

        "मेरा ऑर्डर कहां है":
            "where is my order tracking",

        "पेमेंट फेल":
            "payment failed payment",

        "पेमेंट फेल हो गया":
            "payment failed payment",

        "भुगतान विफल":
            "payment failed payment",

        "पैसे वापस":
            "refund return money back",

        "मुझे रिफंड चाहिए":
            "refund return money back",

        "प्रोडक्ट वापस":
            "return product",

        "रिटर्न करना है":
            "return product",
    }

    for phrase, canonical in hindi_mappings.items():

        if phrase in text:
            return canonical


    # --------------------------------------------------
    # Marathi
    # --------------------------------------------------

    marathi_mappings = {

        "माझी ऑर्डर कधी येईल":
            "when will my order arrive delivery",

        "माझी ऑर्डर कधी येणार":
            "when will my order arrive delivery",

        "माझे ऑर्डर कुठे आहे":
            "where is my order tracking",

        "ऑर्डर कुठे आहे":
            "where is my order tracking",

        "पेमेंट फेल झाले":
            "payment failed payment",

        "पेमेंट अयशस्वी":
            "payment failed payment",

        "पैसे परत":
            "refund return money back",

        "मला रिफंड हवा":
            "refund return money back",

        "प्रोडक्ट परत":
            "return product",
    }

    for phrase, canonical in marathi_mappings.items():

        if phrase in text:
            return canonical


    # --------------------------------------------------
    # Spanish
    # --------------------------------------------------

    spanish_mappings = {

        "cuándo llegará mi pedido":
            "when will my order arrive delivery",

        "cuando llegara mi pedido":
            "when will my order arrive delivery",

        "dónde está mi pedido":
            "where is my order tracking",

        "donde esta mi pedido":
            "where is my order tracking",

        "el pago falló":
            "payment failed payment",

        "el pago fallo":
            "payment failed payment",

        "pago fallido":
            "payment failed payment",

        "quiero un reembolso":
            "refund return money back",

        "quiero devolver":
            "return product",
    }

    for phrase, canonical in spanish_mappings.items():

        if phrase in text:
            return canonical


    # --------------------------------------------------
    # Transliteration / Roman Hindi / Marathi
    # --------------------------------------------------

    transliteration_mappings = {

        "mera order kab aayega":
            "when will my order arrive delivery",

        "mera order kab ayega":
            "when will my order arrive delivery",

        "order kab aayega":
            "when will my order arrive delivery",

        "order kab ayega":
            "when will my order arrive delivery",

        "mera order kaha hai":
            "where is my order tracking",

        "mera order kahan hai":
            "where is my order tracking",

        "order kuthe aahe":
            "where is my order tracking",

        "order kuthe ahe":
            "where is my order tracking",

        "payment fail zala":
            "payment failed payment",

        "payment failed":
            "payment failed payment",

        "paise parat":
            "refund return money back",

        "mala refund hava":
            "refund return money back",

        "product parat":
            "return product",
    }

    for phrase, canonical in transliteration_mappings.items():

        if phrase in text:
            return canonical


    # --------------------------------------------------
    # Keyword-based fallback
    # --------------------------------------------------

    if any(
        word in text
        for word in [
            "ऑर्डर",
            "आर्डर",
            "डिलीवरी",
            "डिलीवर",
            "पार्सल",
            "पैकेज",
            "आएगा",
            "आएगी",
            "कब",
            "पहुंचेगा",
            "पहुंचेगी",
        ]
    ):

        return (
            "when will my order arrive delivery"
        )


    if any(
        word in text
        for word in [
            "पेमेंट",
            "भुगतान",
            "पैसा",
            "पैसे",
            "फेल",
            "असफल",
        ]
    ):

        return (
            "payment failed payment"
        )


    if any(
        word in text
        for word in [
            "रिफंड",
            "रिटर्न",
            "वापस",
            "परत",
        ]
    ):

        return (
            "refund return money back"
        )


    if any(
        word in text
        for word in [
            "ट्रैक",
            "ट्रैकिंग",
            "स्टेटस",
            "स्थिति",
        ]
    ):

        return (
            "where is my order tracking"
        )


    # --------------------------------------------------
    # English / unchanged query
    # --------------------------------------------------

    return query.strip()


# ==================================================
# Load Documents
# ==================================================

def load_documents():

    documents = []

    for file_path in KNOWLEDGE_BASE_DIR.glob(
        "*.txt"
    ):

        metadata, content = parse_document(
            file_path
        )

        # --------------------------------------------------
        # Check complete document for prompt injection
        # --------------------------------------------------

        document_is_unsafe = (
            contains_prompt_injection(
                content
            )
        )

        chunks = [
            chunk.strip()
            for chunk in content.split(
                "\n\n"
            )
            if chunk.strip()
        ]

        for chunk in chunks:

            documents.append(
                {
                    "source":
                        file_path.name,

                    "content":
                        chunk,

                    "policy_id":
                        metadata.get(
                            "policy_id",
                            file_path.stem
                        ),

                    "version":
                        metadata.get(
                            "version",
                            "1.0"
                        ),

                    "product":
                        metadata.get(
                            "product",
                            "all"
                        ),

                    "region":
                        metadata.get(
                            "region",
                            "all"
                        ),

                    "access_level":
                        metadata.get(
                            "access_level",
                            "public"
                        ),

                    "effective_date":
                        metadata.get(
                            "effective_date"
                        ),

                    "expiry_date":
                        metadata.get(
                            "expiry_date"
                        ),

                    "unsafe":
                        document_is_unsafe,
                }
            )

    return documents


# ==================================================
# Load Knowledge Base
# ==================================================

documents = load_documents()

print(
    f"Loaded {len(documents)} knowledge chunks"
)


# ==================================================
# Create Embeddings
# ==================================================

document_texts = [
    document["content"]
    for document in documents
]


if document_texts:

    embeddings = embedding_model.encode(
        document_texts
    )

    embeddings = np.array(
        embeddings
    ).astype("float32")

else:

    embeddings = np.empty(
        (0, 384),
        dtype="float32"
    )


# ==================================================
# Create FAISS Index
# ==================================================

if len(embeddings) > 0:

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

else:

    index = None
# ==================================================
# Evidence Support Check
# ==================================================

def evidence_supports_question(question, evidence, threshold=0.35):
    """
    Check whether the retrieved evidence semantically supports
    the user's question.

    For multilingual questions, the question is first converted
    into a retrieval-friendly query so Hindi, Marathi, Spanish,
    and transliterated questions can match English KB content.
    """

    if not question or not evidence:
        return False

    retrieval_query = build_multilingual_retrieval_query(question)

    question_embedding = embedding_model.encode(
        [retrieval_query],
        normalize_embeddings=True,
    )

    evidence_embedding = embedding_model.encode(
        [evidence],
        normalize_embeddings=True,
    )

    similarity = float(
        np.dot(
            question_embedding[0],
            evidence_embedding[0],
        )
    )

    return similarity >= threshold


# ==================================================
# Knowledge Base Search
# ==================================================

def search_knowledge(
    query,
    top_k=2,
    max_distance=0.8,
    user_access_level="customer",
    reference_date=None,
):
    """
    Search the knowledge base while applying:

    - multilingual retrieval
    - prompt-injection protection
    - access control
    - effective/expiry dates
    - policy version handling
    - FAISS similarity filtering
    """

    if not query or not query.strip():
        return []

    if index is None or not documents:
        return []

    # --------------------------------------------------
    # Convert multilingual user input into a retrieval
    # query that can match the English knowledge base.
    # --------------------------------------------------

    retrieval_query = build_multilingual_retrieval_query(query)

    query_embedding = embedding_model.encode(
        [retrieval_query],
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32,
    )

    # --------------------------------------------------
    # Search FAISS
    # --------------------------------------------------

    search_k = min(
        max(top_k * 10, 20),
        len(documents),
    )

    distances, indices = index.search(
        query_embedding,
        search_k,
    )

    # --------------------------------------------------
    # Reference date
    # --------------------------------------------------

    if reference_date is None:
        reference_date = extract_reference_date(query)

    if reference_date is None:
        reference_date = date.today()

    # --------------------------------------------------
    # Access-level hierarchy
    # --------------------------------------------------

    access_levels = {
        "customer": 0,
        "agent": 1,
        "admin": 2,
    }

    requested_access = access_levels.get(
        user_access_level,
        0,
    )

    candidates = []

    # --------------------------------------------------
    # Process search results
    # --------------------------------------------------

    for distance, idx in zip(
        distances[0],
        indices[0],
    ):

        if idx < 0 or idx >= len(documents):
            continue

        document = documents[idx]

        # ----------------------------------------------
        # FAISS distance filter
        # ----------------------------------------------

        if float(distance) > max_distance:
            continue

        # ----------------------------------------------
        # Prompt-injection protection
        # ----------------------------------------------

        content = document.get("content", "")

        if contains_prompt_injection(content):
            continue

        # ----------------------------------------------
        # Access control
        # ----------------------------------------------

        document_access = document.get(
            "access_level",
            "customer",
        )

        document_access_value = access_levels.get(
            document_access,
            0,
        )

        if document_access_value > requested_access:
            continue

        # ----------------------------------------------
        # Effective date
        # ----------------------------------------------

        effective_date = document.get(
            "effective_date"
        )

        if effective_date:
            try:
                effective = date.fromisoformat(
                    str(effective_date)
                )

                if effective > reference_date:
                    continue

            except ValueError:
                pass

        # ----------------------------------------------
        # Expiry date
        # ----------------------------------------------

        expiry_date = document.get(
            "expiry_date"
        )

        if expiry_date:
            try:
                expiry = date.fromisoformat(
                    str(expiry_date)
                )

                if expiry < reference_date:
                    continue

            except ValueError:
                pass

        # ----------------------------------------------
        # Store valid candidate
        # ----------------------------------------------

        candidates.append(
            {
                "source": document.get(
                    "source",
                    "unknown",
                ),
                "content": content,
                "distance": float(distance),
                "version": document.get(
                    "version",
                    "unknown",
                ),
                "effective_date": document.get(
                    "effective_date"
                ),
                "expiry_date": document.get(
                    "expiry_date"
                ),
                "product": document.get(
                    "product"
                ),
                "region": document.get(
                    "region"
                ),
                "access_level": document_access,
            }
        )

    return candidates
# ==================================================
# Select Latest Applicable Policy Version
# ==================================================

def select_latest_versions(results):
    """
    When multiple versions of the same source are retrieved,
    keep the latest applicable version.
    """

    grouped = {}

    for result in results:
        source = result.get("source", "unknown")

        if source not in grouped:
            grouped[source] = []

        grouped[source].append(result)

    selected = []

    for source, items in grouped.items():

        def version_key(item):
            version = str(
                item.get("version", "0")
            )

            numbers = re.findall(
                r"\d+",
                version,
            )

            if not numbers:
                return (0,)

            return tuple(
                int(number)
                for number in numbers
            )

        items.sort(
            key=version_key,
            reverse=True,
        )

        selected.append(items[0])

    return selected


# ==================================================
# Final Knowledge Search
# ==================================================

def retrieve_knowledge(
    query,
    top_k=2,
    max_distance=0.8,
    user_access_level="customer",
    reference_date=None,
):
    """
    Complete retrieval pipeline.

    Steps:
    1. Search FAISS
    2. Apply security/date/access filters
    3. Select latest applicable versions
    4. Sort by relevance
    5. Return top results
    """

    results = search_knowledge(
        query=query,
        top_k=top_k,
        max_distance=max_distance,
        user_access_level=user_access_level,
        reference_date=reference_date,
    )

    if not results:
        return []

    # --------------------------------------------------
    # Keep only the latest applicable policy version
    # --------------------------------------------------

    results = select_latest_versions(results)

    # --------------------------------------------------
    # Sort by semantic distance
    # Lower distance = closer match
    # --------------------------------------------------

    results.sort(
        key=lambda item: item.get(
            "distance",
            float("inf"),
        )
    )

    return results[:top_k]


# ==================================================
# Public Search Alias
# ==================================================

def get_relevant_documents(
    query,
    top_k=2,
    max_distance=0.8,
    user_access_level="customer",
    reference_date=None,
):
    """
    Public helper used by the chatbot.
    """

    return retrieve_knowledge(
        query=query,
        top_k=top_k,
        max_distance=max_distance,
        user_access_level=user_access_level,
        reference_date=reference_date,
    )


# ==================================================
# Simple Terminal Test
# ==================================================

if __name__ == "__main__":

    print("=" * 60)
    print("RAG KNOWLEDGE BASE TEST")
    print("=" * 60)

    print()
    print("Documents loaded:", len(documents))
    print("Index available:", index is not None)

    test_queries = [
        "How long does standard delivery take?",
        "मेरा ऑर्डर कब आएगा?",
        "My payment failed.",
        "I want to return the product.",
    ]

    for query in test_queries:

        print()
        print("-" * 60)
        print("QUERY:", query)

        results = retrieve_knowledge(
            query=query,
            top_k=2,
            max_distance=1.05,
            user_access_level="customer",
        )

        if not results:
            print("RESULT: No relevant knowledge found.")
            continue

        for result in results:

            print()
            print("SOURCE:", result.get("source"))
            print("VERSION:", result.get("version"))
            print(
                "EFFECTIVE:",
                result.get("effective_date"),
            )
            print(
                "DISTANCE:",
                result.get("distance"),
            )
            print("CONTENT:")
            print(result.get("content"))