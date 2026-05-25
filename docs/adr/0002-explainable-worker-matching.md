# ADR 0002: Use Explainable Matching Before Optimization

## Decision

Worker matching uses a weighted score:

- distance: 35%
- rating: 30%
- availability overlap: 20%
- service experience: 15%

The engine returns the top five workers and records the score factors.

## Why

Families and operations staff need to understand why a worker was offered a task. A black-box model would be harder to debug and harder to trust. The current formula is simple enough to explain during an incident.

## Consequences

- Workers below the minimum score are not offered the job.
- Unmatched tasks are logged and surfaced to admins.
- Future model-based matching must preserve an explanation field.
