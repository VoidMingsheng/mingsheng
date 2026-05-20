# Architecture

## System Intent

The platform supports HR decisions by turning messy candidate inputs into structured evidence. It should improve consistency and speed, but it must not become an autonomous hiring authority.

## Layers

Input layer:

- Resume files: PDF, DOCX, image scans through OCR.
- Interview media: audio or video.
- Job data: selected role, job description, required skills.
- Company data: departments, employee profiles, co-worker availability, onboarding scores, and personality data.

AI pipeline:

1. Resume parser extracts education, skills, experience, certifications, and projects.
2. Speech-to-text service generates transcript, timestamps, confidence, pace, and pause data.
3. Interview analyzer creates structured behavioral and communication evidence.
4. Job matcher compares resume and transcript evidence against the role.
5. Scoring engine applies the 100-point hiring rubric.
6. Co-worker matcher recommends onboarding support using department, seniority, availability, and MBTI compatibility.
7. Dashboard presents evidence, scores, gaps, and human approval actions.

## Backend Modules

- `api/routes`: REST endpoints.
- `services/resume_parser.py`: resume extraction boundary.
- `services/transcription.py`: Whisper-compatible transcription boundary.
- `services/interview_analyzer.py`: transcript semantic analysis.
- `services/job_matcher.py`: skill and experience alignment.
- `services/scoring.py`: rubric, thresholds, and recommendation logic.
- `services/coworker_matcher.py`: onboarding compatibility logic.
- `services/pipeline.py`: orchestration.

## Production Integrations

- Object storage: AWS S3 or compatible storage for resumes and interview media.
- Database: PostgreSQL managed by Prisma migrations.
- Vector store: FAISS for local MVP, Pinecone for managed production scale.
- AI: Whisper-compatible transcription and GPT reasoning model with structured output validation.
- Auth: Clerk, Auth0, or enterprise SSO.
- Observability: request logs, audit events, model outputs, and scoring versions.

## Trust Boundaries

Protected attributes must not be used in scoring. Personality data must support onboarding only. Emotion and confidence signals are soft evidence and require human interpretation.
