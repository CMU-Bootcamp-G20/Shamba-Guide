Here is a concise, executive-quality `README.md` tailored specifically for your backend repository submission to the TA.

```markdown
# ShambaGuide API (Backend)

An offline-first, traceable agricultural advisory REST API built with FastAPI, SQLite, and deterministic safety validation.

---

## Architecture Overview

```text
User Query (Kinyarwanda / English)
       │
       ▼
[ POST /api/v1/advice ]
       │
       ├──► 1. Retrieval Engine (C4IR-RW/kiny-colbert-free) ──► Extract Evidence
       ├──► 2. Micro-Climate Context (SQLite)               ──► Fetch Weather
       ├──► 3. Local SLM Planner (Phi-3)                   ──► Generate Draft Plan
       └──► 4. Deterministic Safety Engine                 ──► Enforce Rules
                                                                │
                                                [ APPROVED / REPAIRED / BLOCKED / ABSTAINED ]
                                                                │
                                                      Persist Decision Receipt

```

---

## Core Features

* **Traceable Advisory Pipeline:** Generates structured advice or safely abstains when evidence is insufficient.
* **Deterministic Safety Engine:** Evaluates draft plans against micro-climate constraints (e.g., blocking spray actions during high rain probability) and regulatory policies.
* **Audit & Decision Receipts:** Persists immutable `AdviceRequest` and `AdviceResponse` pairs in SQLite for auditability.
* **Kinyarwanda RAG Integration:** Designed for late-interaction ColBERT retrieval (`C4IR-RW/kiny-colbert-free`).

---

## Getting Started

### Prerequisites

* Python **3.11+** or **3.12**
* PowerShell (Windows) or Terminal (Linux/macOS)

### Installation

1. **Create and activate a virtual environment:**
```powershell
py -3.12 -m venv svenv
.\svenv\Scripts\Activate.ps1

```


2. **Install dependencies in editable mode:**
```powershell
pip install -e ".[rag,dev]"

```


3. **Start the FastAPI server:**
```powershell
uvicorn shambaguide.api:app --reload --port 8000

```



---

## API Documentation & Interactive Testing

Once the server is running, access the interactive OpenAPI documentation:

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

---

## Endpoint Summary

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health/live` | Basic Liveness check |
| `GET` | `/health/ready` | Component readiness (Database, Retriever, Planner status) |
| `POST` | `/api/v1/advice` | Main advisory endpoint |
| `GET` | `/api/v1/receipts/{receipt_id}` | Retrieve decision audit receipt |

---

## Quick Endpoint Test (PowerShell)

Execute a sample advisory query against the live server:

```powershell
$body = @{
    session_id = "demo-session-001"
    question   = "Amababi y urutoki rwanjye yabaye umuhondo, nakora iki?"
    crop       = "banana"
    district   = "Bugesera"
    sector     = "Nyamata"
    language   = "rw"
    channel    = "web"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/advice -Method Post -ContentType "application/json" -Body $body

```

---

## Running Automated Tests

To run the complete test suite:

```powershell
pytest

```

```

```