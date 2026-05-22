# HR Interview Intelligence Runbook

This runbook is the fastest path from project scaffold to a working local or private-server review.

## 1. Preview The UI Without Installing Dependencies

From this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-demo.ps1
```

Open:

```text
http://localhost:4173
```

The demo is interactive. You can add a candidate, import resume/transcript files, track interview recordings, paste resume and transcript text, generate a deterministic score, select candidates, view multiple co-worker matches for hire recommendations, reset demo data, and export the selected candidate as JSON.

## 2. Private Server Demo Deployment

The static demo can run on a private server with Docker:

```bash
docker compose -f deploy/private-server/docker-compose.demo.yml up -d --build
```

Open:

```text
http://YOUR_SERVER_IP:8080
```

See `deploy/private-server/README.md` for firewall, domain, HTTPS, update, and stop instructions.

## 3. Run The Backend API

From `backend`:

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

## 4. Run Backend Checks

```bash
cd backend
pytest
```

## 5. Run The Next.js Frontend

From `frontend`:

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
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
