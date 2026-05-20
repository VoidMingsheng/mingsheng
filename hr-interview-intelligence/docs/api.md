# API Documentation

Base URL: `http://localhost:8000`

## Health

`GET /api/v1/health`

Returns service status and API version.

## Analyze Candidate

`POST /api/v1/candidates/analyze`

Request:

```json
{
  "candidate": {
    "name": "Aisha Tan",
    "email": "aisha@example.com",
    "resume_text": "Python backend engineer with 5 years...",
    "mbti": "INTJ"
  },
  "job": {
    "id": "software-engineer",
    "title": "Software Engineer",
    "department": "Software Engineering",
    "description": "Build APIs and AI workflow services.",
    "required_skills": ["python", "fastapi", "postgresql", "system design"]
  },
  "interview": {
    "transcript": "I designed a FastAPI service..."
  }
}
```

Response:

```json
{
  "candidate_name": "Aisha Tan",
  "job_title": "Software Engineer",
  "total_score": 82,
  "recommendation": "Hire",
  "critical_minimums_passed": true,
  "category_scores": [],
  "strengths": [],
  "weaknesses": [],
  "skill_match_percent": 75,
  "mentor_recommendations": []
}
```

## Jobs

`GET /api/v1/jobs`

Returns seed job descriptions for the MVP dashboard.

## Employees

`GET /api/v1/employees/mentors`

Returns seed mentor records with department, MBTI, availability, and mentoring scores.

## Notes

File upload endpoints should be added before production storage integration:

- `POST /api/v1/candidates/{id}/resume`
- `POST /api/v1/candidates/{id}/interview-audio`

All production write actions should emit `AuditEvent` records.
