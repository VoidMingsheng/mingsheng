# HR Interview Intelligence System

AI-powered recruitment decision support platform for interview understanding, resume and job matching, candidate scoring, and onboarding mentor recommendations.

This repository is an MVP scaffold, not a finished hiring authority. The system is designed to assist HR teams with structured evidence and consistent rubrics while preserving human review, auditability, and compliance controls.

## Product Scope

Core workflow:

1. Ingest candidate resume, target job description, and interview transcript or audio.
2. Parse resume skills, experience, education, certifications, and projects.
3. Transcribe interview audio through a Whisper-compatible service.
4. Analyze technical competency, communication, behavior, problem solving, confidence, and culture signals.
5. Compare candidate profile against the job description.
6. Score the candidate against a 100-point rubric with critical minimums.
7. Recommend onboarding department and mentor using MBTI only as a support signal.
8. Present results in an HR dashboard for human decision-making.

## Monorepo Layout

```text
backend/     FastAPI API, AI pipeline orchestration, scoring, matching
frontend/    Next.js + TypeScript HR dashboard prototype
database/    Prisma schema for PostgreSQL
docs/        Architecture, API, compliance, deployment, roadmap
infra/       Deployment support files
demo/        Dependency-free dashboard preview
```

## MVP Features Included

- FastAPI application with health, candidate analysis, job, and employee routes
- Modular service layer for resume parsing, transcript analysis, JD matching, scoring, and mentor matching
- 100-point scoring rubric and recommendation thresholds
- Critical minimum checks for technical competency and communication
- MBTI mentor matching with explicit non-discrimination guardrails
- Next.js dashboard with candidate ranking, scoring visualization, and mentor recommendations
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

Static demo:

```bash
cd demo
python -m http.server 4173
```

Open `http://localhost:4173`.

## Important Compliance Boundary

This product must remain a decision support system:

- Do not automatically reject candidates without human review.
- Do not use MBTI, emotion, age, gender, race, nationality, or other protected signals as final hiring determinants.
- Keep explainable scoring evidence and audit logs.
- Follow Singapore PDPA, GDPR, EU AI Act, and local employment requirements before production deployment.
