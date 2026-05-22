# HR Interview Intelligence System

AI-powered recruitment decision support platform for interview understanding, resume and job matching, candidate scoring, and onboarding co-worker recommendations.

This repository is an MVP scaffold, not a finished hiring authority. The system is designed to assist HR teams with structured evidence and consistent rubrics while preserving human review, auditability, and compliance controls.

## Product Scope

Core workflow:

1. Ingest candidate resume, target job description, and interview transcript or audio.
2. Parse resume skills, experience, education, certifications, and projects.
3. Transcribe interview audio through a Whisper-compatible service.
4. Analyze technical competency, communication, behavior, problem solving, confidence, and culture signals.
5. Compare candidate profile against the job description.
6. Score the candidate against a 100-point rubric with critical minimums.
7. Recommend onboarding department and co-workers using MBTI only as a support signal.
8. Present results in an HR dashboard for human decision-making.

## Monorepo Layout

```text
backend/     FastAPI API, AI pipeline orchestration, scoring, matching
frontend/    Next.js + TypeScript HR dashboard prototype
database/    Prisma schema for PostgreSQL
docs/        Architecture, API, compliance, deployment, roadmap
infra/       Deployment support files
demo/        Interactive dependency-free dashboard demo
deploy/      Private server deployment files
```

## MVP Features Included

- FastAPI application with health, candidate analysis, job, and employee routes
- Modular service layer for resume parsing, transcript analysis, JD matching, scoring, and co-worker matching
- 100-point scoring rubric and recommendation thresholds
- Critical minimum checks for technical competency and communication
- MBTI co-worker matching with explicit non-discrimination guardrails
- Next.js dashboard with candidate ranking, scoring visualization, and co-worker recommendations
- Interactive static demo for stakeholder review without dependency installation
- PostgreSQL Prisma schema
- Docker Compose for local development
- API and deployment documentation

## Quick Start

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Interactive static demo:

```bash
powershell -ExecutionPolicy Bypass -File .\start-demo.ps1
```

Open `http://localhost:4173`.

Private server demo deployment:

```bash
docker compose -f deploy/private-server/docker-compose.demo.yml up -d --build
```

Open `http://YOUR_SERVER_IP:8080`.

Database:

```bash
docker compose up db
cd database
npx prisma migrate dev
```

## Environment

Copy `.env.example` to `.env` and fill in real secrets for deployed environments.

The MVP works with deterministic local scoring stubs. Production AI providers should be wired through the service classes in `backend/app/services`.

## Important Compliance Boundary

This product must remain a decision support system:

- Do not automatically reject candidates without human review.
- Do not use MBTI, emotion, age, gender, race, nationality, or other protected signals as final hiring determinants.
- Keep explainable scoring evidence and audit logs.
- Follow Singapore PDPA, GDPR, EU AI Act, and local employment requirements before production deployment.

## Development Status

Current stage: MVP scaffold.

Next engineering milestones:

1. Connect real file uploads and object storage.
2. Integrate Whisper transcription.
3. Add LLM analysis with strict JSON schemas and audit trails.
4. Add authenticated PostgreSQL persistence.
5. Add role-based access control and approval workflow.
6. Add bias monitoring and model evaluation reports.
