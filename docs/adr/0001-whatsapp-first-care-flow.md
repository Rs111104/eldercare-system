# ADR 0001: Start Care Requests In WhatsApp

## Decision

The primary request path is WhatsApp. The web app remains useful for dashboards and richer task views, but care requests must work through text and voice messages.

## Why

Families already use WhatsApp when something urgent happens. Asking them to install or learn a new app adds friction at the worst moment. Workers also benefit: they can accept, decline, mark arrival, and update availability without switching tools.

## Tradeoffs

WhatsApp requires stricter idempotency because webhooks can be delivered more than once. It also pushes us toward short, calm messages and explicit state. That is worth it because the user experience is simpler.

## Consequences

- Conversation state is stored per phone number with a 30 minute timeout.
- Duplicate webhook deliveries are acknowledged and ignored.
- Voice notes are transcribed and then handled as text.
- Every customer-facing system message has English, Tamil, and Hindi text.
