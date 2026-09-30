from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.linear_model import LogisticRegression

from .rag import (
    search_knowledge,
    extract_reference_date,
    evidence_supports_question,
    build_multilingual_retrieval_query,
)

from .multimodal import process_multimodal_file

from .ticket_workflow import create_support_ticket

from .ticket_linking import (
    analyze_ticket_relationship,
    create_masked_handoff_summary,
)

from .ticket_priority import analyze_ticket_priority

from .multilingual_context import (
    analyze_message as analyze_multilingual_message,
    check_inactivity as check_multilingual_inactivity,
    restore_session as restore_multilingual_session,
)

from .multimodal_queue import (
    submit_file_job,
    get_job_status,
    get_queue_status,
    cleanup_expired_files,
    cleanup_old_jobs,
)

from datetime import datetime, time, timedelta
from pathlib import Path
import shutil
import uuid


# ==================================================
# Create FastAPI app
# ==================================================

app = FastAPI()


# ==================================================
# Multimodal Upload Configuration
# ==================================================

UPLOAD_DIRECTORY = Path("test_files/uploads")

UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# Chat request model
# ==================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


# ==================================================
# Conversation History
# ==================================================

conversation_history = {}

MAX_HISTORY = 10


# ==================================================
# Unresolved Issue Tracking
# ==================================================

UNRESOLVED_LIMIT_MINUTES = 15

unresolved_issues = {}


# ==================================================
# Business Hours Configuration
# ==================================================

BUSINESS_START = time(9, 0)
BUSINESS_END = time(18, 0)


# ==================================================
# NLP Training Data
# ==================================================

training_data = [

    # Order tracking

    ("where is my order", "order_tracking"),
    ("track my order", "order_tracking"),
    ("where is my package", "order_tracking"),
    ("where is my parcel", "order_tracking"),
    ("order tracking", "order_tracking"),
    ("track package", "order_tracking"),
    ("my order has not arrived", "order_tracking"),

    # Payment

    ("payment failed", "payment"),
    ("payment is not working", "payment"),
    ("I have a payment problem", "payment"),
    ("my payment failed", "payment"),
    ("I was charged but order failed", "payment"),
    ("payment issue", "payment"),
    ("problem with payment", "payment"),
    ("card payment failed", "payment"),
    ("my card was declined", "payment"),

    # Return / Refund

    ("I want to return my product", "return"),
    ("I want to return my order", "return"),
    ("how can I return a product", "return"),
    ("I need a refund", "return"),
    ("how can I get a refund", "return"),
    ("refund my order", "return"),
    ("return this product", "return"),
    ("I want my money back", "return"),

    # Delivery

    ("when will my order arrive", "delivery"),
    ("when will you deliver", "delivery"),
    ("how long is delivery", "delivery"),
    ("delivery is late", "delivery"),
    ("my delivery is late", "delivery"),
    ("when can I expect delivery", "delivery"),
    ("delivery information", "delivery"),
    ("how much time for delivery", "delivery"),

    # Greeting

    ("hello", "greeting"),
    ("hi", "greeting"),
    ("hey", "greeting"),
    ("good morning", "greeting"),
    ("good afternoon", "greeting"),
    ("good evening", "greeting"),
]


# ==================================================
# Prepare NLP training data
# ==================================================

training_messages = [
    item[0]
    for item in training_data
]

training_intents = [
    item[1]
    for item in training_data
]


# ==================================================
# TF-IDF
# ==================================================

vectorizer = TfidfVectorizer()

X = vectorizer.fit_transform(
    training_messages
)


# ==================================================
# Logistic Regression
# ==================================================

model = LogisticRegression()

model.fit(
    X,
    training_intents,
)


# ==================================================
# Sentiment Detection
# ==================================================

def detect_sentiment(message):

    text = message.lower()

    # ----------------------------------------------
    # Urgent
    # ----------------------------------------------

    urgent_words = [
        "urgent",
        "emergency",
        "immediately",
        "asap",
        "right now",
        "critical",
        "fraud",
        "scam",
        "stolen",
        "unauthorized",
        "account hacked",
        "security issue",
    ]

    if any(
        word in text
        for word in urgent_words
    ):
        return "urgent", 0.95

    # ----------------------------------------------
    # Sarcastic
    # ----------------------------------------------

    sarcastic_phrases = [
        "great job",
        "good job",
        "wonderful service",
        "excellent service",
        "thanks for nothing",
        "what a great service",
        "love waiting",
        "just perfect",
        "yeah right",
        "brilliant service",
    ]

    if any(
        phrase in text
        for phrase in sarcastic_phrases
    ):
        return "sarcastic", 0.90

    # ----------------------------------------------
    # Frustrated
    # ----------------------------------------------

    frustrated_words = [
        "again",
        "still",
        "fed up",
        "frustrated",
        "ridiculous",
        "annoying",
        "annoyed",
        "angry",
        "terrible",
        "worst",
        "useless",
        "disappointed",
        "not working",
        "why is this happening",
        "how many times",
        "already told you",
        "nothing has happened",
    ]

    if any(
        word in text
        for word in frustrated_words
    ):
        return "frustrated", 0.90

    # ----------------------------------------------
    # Negative
    # ----------------------------------------------

    negative_words = [
        "bad",
        "poor",
        "hate",
        "problem",
        "issue",
        "failed",
        "failure",
        "late",
        "wrong",
        "broken",
        "missing",
        "refund",
        "cancel",
        "cannot",
        "can't",
        "unable",
        "disappointed",
    ]

    if any(
        word in text
        for word in negative_words
    ):
        return "negative", 0.85

    # ----------------------------------------------
    # Positive
    # ----------------------------------------------

    positive_words = [
        "thank you",
        "thanks",
        "great",
        "good",
        "excellent",
        "perfect",
        "awesome",
        "happy",
        "helpful",
        "appreciate",
        "solved",
        "love",
    ]

    if any(
        word in text
        for word in positive_words
    ):
        return "positive", 0.85

    # ----------------------------------------------
    # Neutral
    # ----------------------------------------------

    return "neutral", 0.80


# ==================================================
# Store Conversation Message
# ==================================================

def store_message(
    session_id,
    message,
    sentiment,
):

    if session_id not in conversation_history:
        conversation_history[session_id] = []

    conversation_history[session_id].append(
        {
            "message": message,
            "sentiment": sentiment,
        }
    )

    conversation_history[session_id] = (
        conversation_history[session_id][-MAX_HISTORY:]
    )


# ==================================================
# Analyze Conversation History
# ==================================================

def analyze_history(session_id):

    history = conversation_history.get(
        session_id,
        [],
    )

    negative_count = sum(
        1
        for item in history
        if item["sentiment"]
        in [
            "negative",
            "frustrated",
            "sarcastic",
        ]
    )

    urgent_count = sum(
        1
        for item in history
        if item["sentiment"] == "urgent"
    )

    repeated_negative = (
        negative_count >= 2
    )

    return {
        "message_count": len(history),
        "negative_count": negative_count,
        "urgent_count": urgent_count,
        "repeated_negative": repeated_negative,
    }


# ==================================================
# Track Unresolved Negative Issue
# ==================================================

def track_unresolved_issue(
    session_id,
    sentiment,
):

    current_time = datetime.now()

    negative_sentiments = [
        "negative",
        "frustrated",
    ]

    if sentiment in negative_sentiments:

        if session_id not in unresolved_issues:
            unresolved_issues[session_id] = current_time

        start_time = unresolved_issues[
            session_id
        ]

        elapsed_seconds = (
            current_time - start_time
        ).total_seconds()

        elapsed_minutes = (
            elapsed_seconds / 60
        )

        return round(
            elapsed_minutes,
            2,
        )

    if session_id in unresolved_issues:
        del unresolved_issues[session_id]

    return 0.0


# ==================================================
# Check Business Hours
# ==================================================

def is_business_hours():

    current_time = datetime.now().time()

    return (
        BUSINESS_START
        <= current_time
        <= BUSINESS_END
    )


# ==================================================
# Tone Adjustment
# ==================================================

def adjust_tone(
    response,
    sentiment,
):

    if sentiment == "positive":
        return (
            "Thank you! I'm happy to help. "
            + response
        )

    if sentiment == "negative":
        return (
            "I understand that this situation "
            "is frustrating. "
            + response
        )

    if sentiment == "frustrated":
        return (
            "I understand your frustration, and "
            "I'm sorry you're experiencing this. "
            + response
        )

    if sentiment == "urgent":
        return (
            "I understand this is urgent. "
            + response
        )

    if sentiment == "sarcastic":
        return (
            "I understand your concern. "
            + response
        )

    return response


# ==================================================
# Escalation Detection
# ==================================================

def determine_escalation(
    sentiment,
    history_analysis,
    unresolved_minutes,
):

    if sentiment == "urgent":

        if is_business_hours():

            return {
                "escalation": True,
                "escalation_type": "immediate",
                "escalation_reason":
                    "urgent_high_risk_issue",
                "escalation_condition":
                    "Customer message contains an "
                    "urgent or high-risk condition.",
                "escalation_summary":
                    "Urgent customer issue requires "
                    "immediate human assistance.",
            }

        else:

            return {
                "escalation": True,
                "escalation_type": "on_call",
                "escalation_reason":
                    "urgent_after_hours",
                "escalation_condition":
                    "Urgent issue detected outside "
                    "business hours.",
                "escalation_summary":
                    "Urgent customer issue detected "
                    "after business hours. Route to "
                    "on-call support.",
            }

    if unresolved_minutes >= UNRESOLVED_LIMIT_MINUTES:

        if is_business_hours():

            return {
                "escalation": True,
                "escalation_type": "human_agent",
                "escalation_reason":
                    "negative_issue_unresolved_15_minutes",
                "escalation_condition":
                    "Negative or frustrated customer "
                    "issue has remained unresolved "
                    "for 15 minutes or more.",
                "escalation_summary":
                    "Customer issue has remained "
                    "unresolved for more than 15 minutes. "
                    "Escalate to a human agent.",
            }

        else:

            return {
                "escalation": True,
                "escalation_type": "next_working_day",
                "escalation_reason":
                    "negative_issue_unresolved_after_hours",
                "escalation_condition":
                    "Negative or frustrated issue has "
                    "remained unresolved for 15 minutes "
                    "outside business hours.",
                "escalation_summary":
                    "Customer issue requires human "
                    "assistance. Route to the next "
                    "working day support queue.",
            }

    if history_analysis["repeated_negative"]:

        if is_business_hours():

            return {
                "escalation": True,
                "escalation_type": "human_agent",
                "escalation_reason":
                    "repeated_negative_interaction",
                "escalation_condition":
                    "Customer has multiple negative "
                    "or frustrated messages.",
                "escalation_summary":
                    "Customer shows repeated negative "
                    "sentiment. Human agent assistance "
                    "is recommended.",
            }

        else:

            return {
                "escalation": True,
                "escalation_type": "next_working_day",
                "escalation_reason":
                    "repeated_negative_after_hours",
                "escalation_condition":
                    "Repeated negative interaction "
                    "detected outside business hours.",
                "escalation_summary":
                    "Customer issue requires human "
                    "assistance. Route to the next "
                    "working day support queue.",
            }

    return {
        "escalation": False,
        "escalation_type": None,
        "escalation_reason": None,
        "escalation_condition": None,
        "escalation_summary": None,
    }


# ==================================================
# Home route
# ==================================================

@app.get("/")
def root():

    return {
        "message":
            "Customer Service Bot API is running"
    }


# ==================================================
# Health check
# ==================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ==================================================
# Multimodal File Upload API
# ==================================================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    message: str = Form(""),
    session_id: str = Form(""),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file name provided.",
        )

    original_name = Path(
        file.filename
    ).name

    extension = Path(
        original_name
    ).suffix.lower()

    allowed_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
        ".tiff",
        ".pdf",
        ".txt",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: "
                f"{extension}"
            ),
        )

    unique_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = (
        UPLOAD_DIRECTORY
        / unique_name
    )

    try:

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        file_size_mb = (
            file_path.stat().st_size
            / (1024 * 1024)
        )

        if file_size_mb >= 5:

            job = submit_file_job(
                file_path,
                customer_message=message,
                session_id=session_id,
            )

            return {
                "status":
                    "background_processing",
                "job_id":
                    job["job_id"],
                "file_name":
                    original_name,
                "file_size_mb":
                    round(file_size_mb, 2),
                "session_id":
                    session_id or None,
                "message":
                    "The uploaded file is being "
                    "processed in the background.",
            }

        try:

            result = process_multimodal_file(
                file_path,
                customer_message=message,
            )

        except ValueError as error:

            raise HTTPException(
                status_code=400,
                detail=str(error),
            )

        except FileNotFoundError as error:

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "File processing failed: "
                    f"{type(error).__name__}"
                ),
            )

        result["session_id"] = (
            session_id or None
        )

        result["original_file_name"] = (
            original_name
        )

        result.pop(
            "text",
            None,
        )

        return result

    finally:

        file.close()

        if (
            file_path.exists()
            and file_path.stat().st_size
            < 5 * 1024 * 1024
        ):

            try:
                file_path.unlink()
            except Exception:
                pass


# ==================================================
# Background Upload Status
# ==================================================

@app.get("/upload/status/{job_id}")
async def upload_status(
    job_id: str,
):

    return get_job_status(
        job_id
    )


# ==================================================
# Background Queue Status
# ==================================================

@app.get("/upload/queue-status")
async def upload_queue_status():

    return get_queue_status()


# ==================================================
# Upload Cleanup
# ==================================================

@app.delete("/upload/cleanup")
async def upload_cleanup():

    deleted_files = (
        cleanup_expired_files()
    )

    removed_jobs = (
        cleanup_old_jobs()
    )

    return {
        "deleted_files":
            deleted_files,
        "removed_jobs":
            removed_jobs,
        "deleted_file_count":
            len(deleted_files),
        "removed_job_count":
            len(removed_jobs),
    }
# ==================================================
# Support Ticket Creation API
# ==================================================

support_ticket_store = []


@app.post("/ticket/create")
def create_ticket(
    request: ChatRequest,
):

    """Create, prioritize, link, route, and prepare a masked support ticket."""

    ticket = create_support_ticket(
        conversation=request.message,
    )

    ticket["ticket_id"] = (
        f"TKT-{uuid.uuid4().hex[:8].upper()}"
    )

    ticket["session_id"] = request.session_id

    relationship = analyze_ticket_relationship(
        new_ticket=ticket,
        existing_tickets=support_ticket_store,
    )

    sentiment, _ = detect_sentiment(
        request.message
    )

    if sentiment == "urgent":
        severity = "critical"

    elif sentiment == "frustrated":
        severity = "high"

    elif sentiment == "negative":
        severity = "medium"

    else:
        severity = "low"

    priority_data = analyze_ticket_priority(
        ticket=ticket,
        sentiment=sentiment,
        severity=severity,
        waiting_minutes=0,
        business_impact="normal",
    )

    handoff = create_masked_handoff_summary(
        ticket=ticket,
        priority_data=priority_data,
    )

    if relationship["relationship"] != "duplicate":
        support_ticket_store.append(ticket)

    return {
        "ticket": ticket,
        "relationship": relationship,
        "priority": priority_data,
        "handoff": handoff,
    }


# ==================================================
# Chat API
# ==================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):

    message = request.message.strip()

    # ==================================================
    # Empty message
    # ==================================================

    if not message:

        return {
            "response":
                "Please enter a message.",

            "intent":
                "empty",

            "confidence":
                1.0,

            "sentiment":
                "neutral",

            "sentiment_confidence":
                1.0,

            "session_id":
                request.session_id,

            "message_count":
                0,

            "negative_count":
                0,

            "urgent_count":
                0,

            "repeated_negative":
                False,

            "unresolved_minutes":
                0.0,

            "escalation":
                False,

            "escalation_type":
                None,

            "escalation_reason":
                None,

            "escalation_condition":
                None,

            "escalation_summary":
                None,

            "source":
                None,

            "version":
                None,

            "effective_date":
                None,
        }

    # ==================================================
    # Task 6 - Multilingual and Session Context
    # ==================================================

    multilingual_inactivity = (
        check_multilingual_inactivity(
            request.session_id,
            datetime.now(),
        )
    )

    multilingual_restore = None

    if multilingual_inactivity.get("inactive"):

        multilingual_restore = (
            restore_multilingual_session(
                request.session_id,
                datetime.now(),
            )
        )

    multilingual_analysis = (
        analyze_multilingual_message(
            session_id=request.session_id,
            message=message,
            current_time=datetime.now(),
        )
    )

    new_session_required = bool(
        multilingual_restore
        and multilingual_restore.get(
            "new_session_required"
        )
    )

    # ==================================================
    # Intent Detection
    # ==================================================

    message_vector = vectorizer.transform(
        [message]
    )

    intent = model.predict(
        message_vector
    )[0]

    probabilities = model.predict_proba(
        message_vector
    )

    confidence = max(
        probabilities[0]
    )

    # ==================================================
    # Task 6 - Multilingual Intent Override
    # ==================================================

    multilingual_confidence = (
        multilingual_analysis[
            "intent_confidence"
        ]
    )

    language_code = (
        multilingual_analysis[
            "language"
        ]["language"]
    )

    if (
        language_code in {"hi", "mr", "es"}
        and multilingual_confidence >= 0.75
    ):

        multilingual_text = " ".join(
            multilingual_analysis.get(
                "requests",
                []
            )
        ).lower()

        # ----------------------------------------------
        # Delivery
        # ----------------------------------------------

        if any(
            term in multilingual_text
            for term in [

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

                "पहुंचेगा",
                "पहुंचेगी",

                "कब",
                "कहाँ",
                "कहां",

                "order",
                "delivery",
                "arrive",

                "aaya",
                "aayi",
                "aale",
                "aala",
                "kuthe",
                "kahan",

                "pedido",
                "entrega",
                "llegar",
                "dónde",
                "donde",
            ]
        ):

            intent = "delivery"

            confidence = (
                multilingual_confidence
            )

        # ----------------------------------------------
        # Payment
        # ----------------------------------------------

        elif any(
            term in multilingual_text
            for term in [

                "भुगतान",
                "पेमेंट",
                "पैसा",
                "पैसे",
                "फेल",
                "असफल",

                "payment",
                "paid",
                "pay",
                "paisa",
                "paise",
                "failed",

                "pago",
                "pagado",
            ]
        ):

            intent = "payment"

            confidence = (
                multilingual_confidence
            )

        # ----------------------------------------------
        # Return / Refund
        # ----------------------------------------------

        elif any(
            term in multilingual_text
            for term in [

                "रिफंड",
                "रिटर्न",
                "पैसे वापस",
                "वापस",
                "परत",

                "refund",
                "return",
                "wapas",
                "parat",

                "reembolso",
                "devolver",
            ]
        ):

            intent = "return"

            confidence = (
                multilingual_confidence
            )

        # ----------------------------------------------
        # Order Tracking
        # ----------------------------------------------

        elif any(
            term in multilingual_text
            for term in [

                "ट्रैक",
                "ट्रैकिंग",
                "स्टेटस",
                "स्थिति",

                "कहाँ है",
                "कहां है",
                "कहाँ गया",
                "कहां गया",

                "tracking",
                "track",
                "status",

                "where is my order",

                "kaha",
                "kuthe",

                "dónde está",
                "donde esta",
            ]
        ):

            intent = "order_tracking"

            confidence = (
                multilingual_confidence
            )

    # ==================================================
    # Unknown Intent
    # ==================================================

    if confidence < 0.35:
        intent = "unknown"

    # ==================================================
    # Sentiment Detection
    # ==================================================

    sentiment, sentiment_confidence = (
        detect_sentiment(message)
    )

    # ==================================================
    # Store Message
    # ==================================================

    store_message(
        request.session_id,
        message,
        sentiment,
    )

    # ==================================================
    # Analyze History
    # ==================================================

    history_analysis = analyze_history(
        request.session_id
    )

    # ==================================================
    # Track Unresolved Issue
    # ==================================================

    unresolved_minutes = (
        track_unresolved_issue(
            request.session_id,
            sentiment,
        )
    )

    # ==================================================
    # Escalation
    # ==================================================

    escalation = determine_escalation(
        sentiment,
        history_analysis,
        unresolved_minutes,
    )

    # ==================================================
    # Historical Date Detection
    # ==================================================

    reference_date = extract_reference_date(
        message
    )

    # ==================================================
    # RAG Search
    # ==================================================
# ==================================================
# RAG Search
# ==================================================

    retrieval_query = build_multilingual_retrieval_query(
        message
    )

    is_multilingual_retrieval = (
        retrieval_query.strip().lower()
        != message.strip().lower()
    )

    rag_max_distance = (
        1.05
        if is_multilingual_retrieval
        else 0.9
    )

    rag_results = search_knowledge(
        query=message,
        reference_date=reference_date,
        max_distance=rag_max_distance,
    )

    # ==================================================
    # Default Metadata
    # ==================================================

    source = None

    version = None

    effective_date = None

    # ==================================================
    # Generate Grounded Response
    # ==================================================

    if intent == "unknown":

        response = (
            "I could not find reliable information "
            "in the knowledge base to answer that question."
        )

    elif not rag_results:

        response = (
            "I could not find reliable information "
            "in the knowledge base to answer that question."
        )

    else:

        best_result = rag_results[0]
        
        
        # ==================================================
        # Multilingual RAG Relevance Check
        # ==================================================

        

        

        # English retrieval keeps original threshold.
        #
        # Multilingual retrieval gets a slightly higher
        # distance threshold because the query is first
        # normalized into English for semantic retrieval.

        relevance_threshold = (
            1.05
            if is_multilingual_retrieval
            else 0.9
        )

        if (
            best_result["distance"]
            > relevance_threshold
        ):

            response = (
                "I could not find reliable information "
                "in the knowledge base to answer that question."
            )

        # ==================================================
        # Evidence Check
        # ==================================================

        elif not evidence_supports_question(
            retrieval_query,
            best_result["content"],
            threshold=0.20,
        ):

            response = (
                "I could not find enough reliable "
                "evidence in the knowledge base "
                "to answer that question."
            )

        else:

            response = (
                best_result["content"]
            )

            source = (
                best_result["source"]
            )

            version = (
                best_result["version"]
            )

            effective_date = (
                best_result["effective_date"]
            )

            # ==================================================
            # Tone Adjustment
            # ==================================================

            response = adjust_tone(
                response,
                sentiment,
            )
    # ==================================================
    # Task 6 - Clarification Handling
    # ==================================================

    if multilingual_analysis["clarification_required"]:

        if multilingual_analysis[
            "language"
        ]["needs_clarification"]:

            response = (
                "I want to make sure I understood your language "
                "and request correctly. Please rephrase your "
                "message or provide a little more detail."
            )

        else:

            response = (
                "I want to make sure I understood your request "
                "correctly. Could you please rephrase it or "
                "provide a little more detail?"
            )

    # ==================================================
    # Session Restoration Handling
    # ==================================================

    if new_session_required:

        response = (
            "This conversation session has exceeded the 24-hour "
            "restoration window. Please start a new session so "
            "I can assist you with fresh context."
        )

    # ==================================================
    # Final API Response
    # ==================================================

    return {

        "response":
            response,

        "intent":
            intent,

        "confidence":
            round(
                float(confidence),
                2,
            ),

        "sentiment":
            sentiment,

        "sentiment_confidence":
            round(
                float(sentiment_confidence),
                2,
            ),

        "session_id":
            request.session_id,

        "message_count":
            history_analysis[
                "message_count"
            ],

        "negative_count":
            history_analysis[
                "negative_count"
            ],

        "urgent_count":
            history_analysis[
                "urgent_count"
            ],

        "repeated_negative":
            history_analysis[
                "repeated_negative"
            ],

        "unresolved_minutes":
            unresolved_minutes,

        "escalation":
            escalation[
                "escalation"
            ],

        "escalation_type":
            escalation[
                "escalation_type"
            ],

        "escalation_reason":
            escalation[
                "escalation_reason"
            ],

        "escalation_condition":
            escalation[
                "escalation_condition"
            ],

        "escalation_summary":
            escalation[
                "escalation_summary"
            ],

        "source":
            source,

        "version":
            version,

        "effective_date":
            effective_date,

        # ==================================================
        # Task 6 - Multilingual Response Fields
        # ==================================================

        "language":
            multilingual_analysis[
                "language"
            ]["language"],

        "language_name":
            multilingual_analysis[
                "language"
            ]["language_name"],

        "language_confidence":
            multilingual_analysis[
                "language"
            ]["confidence"],

        "detected_languages":
            multilingual_analysis[
                "language"
            ]["detected_languages"],

        "mixed_language":
            multilingual_analysis[
                "language"
            ]["mixed_language"],

        "preserved_entities":
            multilingual_analysis[
                "preserved_entities"
            ],

        "multiple_requests":
            multilingual_analysis[
                "multiple_requests"
            ],

        "requests":
            multilingual_analysis[
                "requests"
            ],

        "correction":
            multilingual_analysis[
                "correction"
            ],

        "multilingual_intent_confidence":
            multilingual_analysis[
                "intent_confidence"
            ],

        "clarification_required":
            multilingual_analysis[
                "clarification_required"
            ],

        "clarification_reason":
            multilingual_analysis[
                "clarification_reason"
            ],

        "context_message_count":
            multilingual_analysis[
                "context_message_count"
            ],

        "session_status":
            multilingual_analysis[
                "session_status"
            ],

        "session_inactivity":
            multilingual_analysis[
                "inactivity"
            ],

        "session_restored":
            bool(
                multilingual_restore
                and multilingual_restore.get(
                    "restored"
                )
            ),

        "new_session_required":
            new_session_required,

        "session_restore_summary":
            (
                multilingual_restore.get(
                    "summary"
                )
                if multilingual_restore
                else None
            ),
    }