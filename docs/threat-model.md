# Threat Model

## Highest Risk Data

- Phone numbers
- Addresses
- Care notes
- Worker payout records
- Admin actions

## Defenses In This Repo

- JWTs expire and are signature checked.
- Admin routes require admin role.
- WhatsApp webhooks require HMAC signatures.
- Validation errors return a generic shape without schema internals.
- Logs use structured context and avoid care details.
- Payout overrides and sensitive actions append audit entries.
- High severity Bandit findings and known backend dependency vulnerabilities fail CI.

## Known Boundaries

The local in-memory store is for demo and test workflows. Production should use the SQL migrations and encrypted fields for PII. Provider credentials must stay in environment variables or a secret manager.
