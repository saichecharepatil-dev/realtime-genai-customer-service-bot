# Real-Time GenAI Customer Service Bot

A customer service chatbot built with FastAPI, React,
Retrieval-Augmented Generation (RAG), multilingual processing, sentiment
analysis, multimodal document/image processing, and automated
support-ticket workflows.

This project extends the original training project with the assigned
internship tasks on the same customer-service chatbot.

## Features

### Task 1 --- Production Knowledge Base Pipeline

-   New and modified document processing
-   Duplicate detection
-   Invalid-file quarantine
-   Knowledge-base versioning and rollback
-   Quality and regression checks
-   Retry and scheduling support
-   Maintenance-window handling
-   Health monitoring
-   Access control
-   Prompt-injection protection
-   Sensitive-data masking

Main modules: - `backend/app/kb_access_control.py` -
`backend/app/kb_monitoring.py` - `backend/app/kb_pipeline.py` -
`backend/app/kb_regression.py` - `backend/app/kb_retry.py` -
`backend/app/kb_schedule.py` - `backend/app/kb_security.py`

### Task 2 --- Multimodal Customer Service

Supports customer images and documents with OCR and extraction.

Supported formats: - Images: PNG, JPG, JPEG, WEBP, BMP, TIFF -
Documents: PDF, TXT

Features: - Image OCR - PDF extraction and scanned-PDF OCR - File
validation and corrupt-file detection - Order ID, date, amount,
product-code and error-code extraction - Message/document comparison -
Conflict detection - Sensitive-information masking - Unsafe-instruction
detection - Safe logging - Background processing queue

Main modules: - `backend/app/multimodal.py` -
`backend/app/multimodal_queue.py`

### Task 3 --- Support Ticket Workflow

-   Customer/order/product/issue/evidence/contact extraction
-   Missing-information detection
-   Priority classification
-   SLA calculation, warning and breach detection
-   Agent routing
-   Business-hours and weekend/holiday handling
-   Duplicate and related-ticket linking
-   Masked handoff summaries

Main modules: - `backend/app/ticket_workflow.py` -
`backend/app/ticket_priority.py` - `backend/app/ticket_linking.py`

### Task 4 --- RAG Knowledge Assistant

Uses Sentence Transformers and FAISS for local knowledge retrieval.

Features: - Product, FAQ, delivery, payment and return/refund
retrieval - Metadata filtering - Version handling - Access control -
Effective/expiry-date handling - Historical policy retrieval - Latest
applicable policy selection - Evidence validation - Unsupported-claim
protection - Prompt-injection protection - Clarification when reliable
evidence is unavailable

Main module: - `backend/app/rag.py`

### Task 5 --- Sentiment and Escalation

Sentiment categories include positive, neutral, negative, frustrated,
urgent and sarcastic.

Features: - Sentiment confidence - Urgency detection -
Conversation-history consideration - Repeated-negative detection -
High-risk escalation - After-hours urgent escalation -
Unresolved-negative escalation - Escalation reason, condition and
summary - Tone adjustment without changing policy information

### Task 6 --- Multilingual Context and Sessions

Supported languages: - English - Hindi - Marathi - Spanish

Features: - Language and confidence detection - Mixed-language and
transliteration handling - Hindi Devanagari handling - Entity
preservation - Multiple-request detection - Corrections and spelling
variations - Last 10 messages of context - Session isolation - 30-minute
inactivity detection - Session restoration within 24 hours -
Clarification for low language/intent confidence

Main module: - `backend/app/multilingual_context.py`

## Technology Stack

### Backend

-   Python
-   FastAPI
-   Uvicorn
-   Scikit-learn
-   Sentence Transformers
-   FAISS
-   Pillow
-   PyMuPDF
-   Tesseract OCR
-   Python Multipart

### Frontend

-   React
-   Vite
-   JavaScript
-   HTML
-   CSS

## Architecture

``` text
React + Vite Frontend
        |
        | HTTP
        v
FastAPI Backend
        |
        +-------------------+
        |                   |
        v                   v
 Multilingual          Sentiment /
 Context               Escalation
        |
        v
      RAG Layer
 Sentence Transformers
        +
      FAISS
        |
        v
 Knowledge Base

Multimodal path:
Customer File -> Validation/Safety -> OCR/PDF Extraction
-> Information Extraction -> Message Comparison -> Support Response
```

## Project Structure

``` text
realtime-genai-customer-service-bot/
├── backend/
│   └── app/
│       ├── main.py
│       ├── rag.py
│       ├── multilingual_context.py
│       ├── multimodal.py
│       ├── multimodal_queue.py
│       ├── kb_access_control.py
│       ├── kb_monitoring.py
│       ├── kb_pipeline.py
│       ├── kb_regression.py
│       ├── kb_retry.py
│       ├── kb_schedule.py
│       ├── kb_security.py
│       ├── ticket_workflow.py
│       ├── ticket_priority.py
│       ├── ticket_linking.py
│       └── __init__.py
```text
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── assets/
│   │       └── hero.png
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── index.html
├── knowledge_base/
├── test_files/
│   ├── corrupted.pdf
│   ├── test_invoice.pdf
│   ├── test_invoice.png
│   └── unsafe_test.png
├── .gitignore
└── README.md
```

## Setup

Create and activate a virtual environment on Windows:

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the required backend packages:

pip install -r backend/requirements.txt

Tesseract OCR is required for image OCR. Install Tesseract OCR separately and make sure the executable is available at:

C:\Program Files\Tesseract-OCR\tesseract.exe

## Run Backend

From the project root:

``` powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Local API: `http://127.0.0.1:8000`

Swagger: `http://127.0.0.1:8000/docs`

Health check: `http://127.0.0.1:8000/health`

## Run Frontend

``` powershell
cd frontend
npm install
npm run dev
```

Local frontend: `http://localhost:5173`

## Testing

The project was tested at module, API and frontend levels.

Knowledge-base regression: - Total tests: 5 - Passed: 5 - Failed: 0 -
Pass rate: 100%

Multimodal testing covered: - Invoice OCR - PDF extraction -
Unsafe-image detection - Corrupt PDF handling - Unsupported-file
handling - Date conflict detection - Sensitive-information masking -
Background queue processing

Ticket testing covered: - Ticket extraction - Missing information -
Priority classification - SLA calculation/warning/breach - Agent
routing - Duplicate/related/unrelated ticket detection - Masked handoff
summaries

Multilingual testing covered: - English - Hindi - Hindi Devanagari -
Marathi - Spanish - Mixed language - Transliteration - Multiple
requests - Corrections - Entity preservation - Context persistence -
Session isolation - Inactivity and restoration

Final live smoke tests covered English delivery, Hindi delivery, payment
failure, urgent payment escalation, and the React frontend connection to
the FastAPI backend.

## Security and Safety

The project includes: - Prompt-injection detection - Unsafe-document
filtering - Access-control checks - Effective/expiry-date checks -
Evidence validation - File-type and file-size validation - Corrupt-file
detection - Sensitive-information masking - Safe logging - Protection
against unsupported or fabricated responses

## Current Limitation

The project does not connect to a live order-management database.
Therefore, it does not claim a real-time order status when that
information is unavailable. This prevents unsupported or fabricated
order-status responses.

## Internship Project

This project extends the original training project with: 1. Production
knowledge-base management 2. Multimodal customer support 3. Automated
support-ticket workflows 4. RAG knowledge assistance 5. Sentiment and
escalation 6. Multilingual conversation and session management

All six assigned internship task areas were implemented and tested on
the same customer-service chatbot project.
