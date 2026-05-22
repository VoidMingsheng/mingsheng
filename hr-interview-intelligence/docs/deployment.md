# Deployment Guide

## Local Development

1. Copy `.env.example` to `.env`.
2. Start PostgreSQL:

```bash
docker compose up db
```

3. Run Prisma migrations:

```bash
cd database
npx prisma migrate dev
```

4. Start backend:

```bash
cd backend
uvicorn app.main:app --reload
```

5. Start frontend:

```bash
cd frontend
npm run dev
```

## Docker Compose

After creating `.env`, run:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

## Production Checklist

- Use managed PostgreSQL.
- Use managed object storage with encryption.
- Store secrets in a secret manager.
- Enable TLS for all public endpoints.
- Add SSO and role-based access control.
- Restrict transcript and resume access by role.
- Add audit logs to every sensitive operation.
- Add background jobs for transcription and LLM analysis.
- Add model output validation and retry policies.
- Add monitoring, alerting, and data retention jobs.
