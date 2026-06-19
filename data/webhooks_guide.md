# Webhooks Guide

**Product:** CloudDesk REST API (v2)
**Category:** Developer / API
**Last updated:** 2026-02-08

## Overview
Webhooks let CloudDesk notify your service when events occur (e.g. `ticket.created`, `ticket.updated`, `comment.added`). Configure endpoints in **Settings → Developer → Webhooks**.

## Creating a webhook
1. Provide an HTTPS endpoint URL (HTTP is not allowed).
2. Select the events to subscribe to.
3. CloudDesk generates a **signing secret** (`whsec_...`). Store it securely.

## Verifying signatures
Each delivery includes an `X-CloudDesk-Signature` header:
```
X-CloudDesk-Signature: t=<timestamp>,v1=<hmac_sha256>
```
Compute `HMAC_SHA256(secret, "<timestamp>.<raw_body>")` and compare to `v1`. Reject deliveries where the timestamp is older than 5 minutes (replay protection).

## Delivery and retries
- CloudDesk expects a `2xx` response within **10 seconds**.
- Failed deliveries are retried with exponential backoff for up to **24 hours** (max 8 attempts).
- After exhausting retries the webhook is marked **failing**; repeated failures auto-disable the endpoint and email the workspace admins.

## Debugging failed deliveries
- View recent attempts and response codes under Settings → Developer → Webhooks → **Delivery log**.
- A `410 Gone` or 3 consecutive `5xx` responses are the most common causes of auto-disable.
- Include the delivery `event_id` when contacting support so engineers can trace it.

## Common issues
| Symptom | Likely cause |
|---------|--------------|
| No deliveries received | Endpoint not publicly reachable / blocked by firewall |
| Signature verification fails | Using parsed JSON instead of the raw request body |
| Duplicate events | Your endpoint returned non-2xx, triggering a retry — make handlers idempotent |
