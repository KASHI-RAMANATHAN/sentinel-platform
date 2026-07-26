# Behavioral Anomaly Detection Platform — Backend

AI-powered behavioral anomaly detection backend for a cybersecurity hackathon.
Built with **FastAPI**, **Firebase Firestore**, and the **Firebase Admin SDK**.

> **Status:** Scaffolding only. Business logic, Firestore queries, and the ML
> pipeline are intentionally left as placeholders — see [Roadmap](#roadmap).

## Tech Stack

- Python 3.11+
- FastAPI (REST API)
- Pydantic v2 (request/response validation, settings)
- Firebase Admin SDK (Firestore + Authentication)
- Uvicorn (ASGI server)

## Project Structure

```
backend/
├── app/
│   ├── api/            # API routers only (thin — no business logic)
│   │   ├── deps.py          # Shared dependency providers (services, DB client)
│   │   ├── routes.py        # Aggregates all routers into one api_router
│   │   ├── health.py        # GET /health
│   │   ├── logs.py          # POST /logs
│   │   ├── alerts.py        # GET /alerts
│   │   ├── predict.py       # POST /predict
│   │   └── dashboard.py     # GET /dashboard/stats
│   │
│   ├── core/            # Configuration & environment loading
│   │   ├── config.py        # Settings (env vars), get_settings()
│   │   └── logging_config.py
│   │
│   ├── firebase/         # Firebase initialization & clients
│   │   ├── firebase.py      # Admin SDK bootstrap
│   │   ├── firestore_client.py  # Firestore client accessor (DI-friendly)
│   │   └── auth.py          # Auth helper (PLACEHOLDER — not enforced yet)
│   │
│   ├── models/           # Internal Python/domain models (not API schemas)
│   │   ├── log_model.py
│   │   └── alert_model.py
│   │
│   ├── schemas/           # Pydantic request/response schemas
│   │   ├── common.py
│   │   ├── log_schema.py
│   │   ├── alert_schema.py
│   │   ├── prediction_schema.py
│   │   └── dashboard_schema.py
│   │
│   ├── services/          # Business logic + Firestore CRUD (placeholders)
│   │   ├── log_service.py
│   │   ├── alert_service.py
│   │   ├── prediction_service.py
│   │   └── dashboard_service.py
│   │
│   ├── ml/                # ML pipeline — PLACEHOLDER ONLY, not implemented
│   │   ├── dataset_generation.py
│   │   ├── feature_engineering.py
│   │   ├── anomaly_detection.py
│   │   ├── attack_classification.py
│   │   ├── explainability.py
│   │   └── risk_scoring.py
│   │
│   ├── utils/              # Shared helpers
│   │   ├── response_helpers.py
│   │   └── time_utils.py
│   │
│   └── main.py             # FastAPI app entrypoint
│
├── requirements.txt
├── .env.example
└── README.md
```

## Getting Started

### 1. Create a virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set:
- `FIREBASE_SERVICE_ACCOUNT_PATH` — path to your Firebase service account JSON
- `FIREBASE_PROJECT_ID` — your Firebase project ID

Place your downloaded service account key at the path referenced above
(e.g. `./secrets/firebase-service-account.json`). **Never commit this file.**

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

## API Endpoints (Placeholder)

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| GET    | `/api/v1/health`        | Health check                         |
| POST   | `/api/v1/logs`          | Upload behavioral logs               |
| GET    | `/api/v1/alerts`        | Get anomaly alerts                   |
| POST   | `/api/v1/predict`       | Predict anomaly risk for a user      |
| GET    | `/api/v1/dashboard/stats` | Get dashboard summary statistics   |

All endpoints are currently backed by stubbed service methods — no real
Firestore queries or ML inference are performed yet.

## Architecture Notes

- **Dependency Injection:** Routers never instantiate services or Firestore
  clients directly. `app/api/deps.py` provides them via FastAPI's `Depends`,
  making it straightforward to override with mocks in tests.
- **Separation of concerns:** `schemas/` (API contracts) is kept separate
  from `models/` (internal representations), so the public API can evolve
  independently of storage details.
- **No business logic in routers:** Every router method delegates
  immediately to a service method.

## Roadmap

- [ ] Implement Firestore CRUD in `services/`
- [ ] Enforce Firebase Authentication (`firebase/auth.py`)
- [ ] Build the ML pipeline in `app/ml/` (dataset generation → feature
      engineering → anomaly detection → attack classification →
      explainability → risk scoring)
- [ ] Wire `prediction_service.py` to the completed ML pipeline
- [ ] Add automated tests (pytest + httpx)
- [ ] Add rate limiting / request validation hardening for production
