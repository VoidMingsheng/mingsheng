# HR Interview Intelligence Runbook

This runbook is the fastest path from project scaffold to a working local review.

## 1. Preview The UI Without Installing Dependencies

The branch includes a static dashboard preview.

From the `hr-interview-intelligence` folder:

```bash
cd demo
python -m http.server 4173
```

Open:

```text
http://localhost:4173
```

This preview mirrors the dashboard layout and lets stakeholders review the product direction immediately.

## 2. Run The Backend API

From `hr-interview-intelligence/backend`:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open API docs:

```text
http://localhost:8000/docs
```

Useful endpoint:

```text
POST /api/v1/candidates/analyze
```

## 3. Run Backend Checks

```bash
cd backend
pytest
```

The included tests cover scoring thresholds and mentor matching priority.

## 4. Run The Next.js Frontend

From `hr-interview-intelligence/frontend`:

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## 5. Start PostgreSQL For Persistence Work

From `hr-interview-intelligence`:

```bash
docker compose up db
```

Then generate or migrate Prisma from `hr-interview-intelligence/database`:

```bash
npm install
npx prisma generate
npx prisma migrate dev
```

## 6. Next Implementation Priorities

1. Add real resume and interview audio upload endpoints.
2. Persist candidates, jobs, interviews, scorecards, and audit events in PostgreSQL.
3. Connect Whisper-compatible transcription behind `WhisperTranscriptionService`.
4. Replace deterministic MVP analysis with structured LLM output validation.
5. Add authentication, role-based access control, and audit logging.
6. Add adverse-impact monitoring before production use.

## Compliance Reminder

This must remain a decision support system. Human review is required before any hiring decision, and MBTI/personality data must support onboarding only, not rejection.
