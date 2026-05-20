# Production Checklist

## Security

- Enforce SSO or enterprise identity provider.
- Store JWT, database, object storage, and AI provider secrets in a secret manager.
- Encrypt resumes, transcripts, and interview media at rest.
- Use TLS for every public endpoint.
- Add malware scanning for uploaded files.

## Privacy

- Capture candidate consent for recordings and AI-assisted processing.
- Publish retention windows and deletion workflow.
- Add data export and deletion handling for GDPR-style requests.
- Limit access to sensitive candidate artifacts by role.

## AI Governance

- Version prompts, rubrics, models, and scoring logic.
- Validate LLM outputs against strict JSON schemas.
- Store evidence for every score.
- Run adverse impact reviews before production release.
- Keep human approval mandatory for final hiring outcomes.

## Operations

- Move transcription and LLM work to background jobs.
- Add queue retries and dead-letter handling.
- Monitor latency, token cost, transcription errors, and score drift.
- Back up PostgreSQL and test restore procedures.
