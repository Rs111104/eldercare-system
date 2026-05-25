# Data Model Notes

This repo has SQL migrations under `database/migrations` and a local store under `backend/app/store.py`. The local store mirrors the entities needed for tests and Docker demos.

## Core Entities

- Customer: phone, name, address, trusted contacts.
- Worker: phone, service type, verification status, location, rating, completed task count.
- Task: customer, optional worker, service type, price, lifecycle state, transition history.
- Review: task, customer, worker, rating, dispute flag.
- Payout: worker, task, gross amount, platform fee, net amount, split status.
- WhatsApp message: direction, phone, message type, content, processing status.
- Audit entry: actor, action, target, before/after, reason, timestamp.

## Task States

`REQUESTED -> MATCHED -> CONFIRMED -> IN_PROGRESS -> COMPLETED -> RATED -> PAID`

Disputes move a completed or rated task to `DISPUTED`; payout stays held until admin review.
