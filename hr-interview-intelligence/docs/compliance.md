# Compliance And Ethics

## Product Boundary

The platform is a decision support system. Human HR reviewers remain accountable for hiring decisions.

## Prohibited Uses

- Automatically rejecting candidates without human review.
- Treating MBTI as a hiring determinant.
- Treating emotion detection as factual truth.
- Using protected attributes or proxies for protected attributes.
- Scoring based on race, gender, age, nationality, disability, religion, marital status, pregnancy, or other protected characteristics.

## Required Controls

- Human review before final hiring outcome.
- Explainable category-level scores and evidence.
- Rubric versioning.
- Audit logs for uploads, analyses, score changes, approvals, and overrides.
- Data retention policy and deletion workflow.
- Access controls for HR, hiring managers, admins, and auditors.
- Model evaluation for adverse impact.

## Regulatory Considerations

Singapore PDPA:

- Obtain consent for candidate data and recordings.
- State purposes clearly.
- Minimize collection and retention.
- Protect data in transit and at rest.

GDPR:

- Support data access, rectification, deletion, and portability.
- Avoid solely automated decisions with legal or similarly significant effects.
- Maintain lawful basis and data processing agreements.

EU AI Act:

- Employment AI systems are high-risk.
- Maintain risk management, logging, human oversight, accuracy, and documentation.

Employment law:

- Validate scoring criteria against job relevance.
- Keep final decisions reviewable and appealable.
