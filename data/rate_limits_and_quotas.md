# Rate Limits & Quotas

**Product:** CloudDesk REST API (v2)
**Category:** Developer / API
**Last updated:** 2026-02-08

## Rate limits by plan
| Plan | Requests / minute | Burst |
|------|-------------------|-------|
| Starter | 60 | 100 |
| Business | 600 | 900 |
| Enterprise | Custom (default 3000) | Custom |

Limits are enforced **per API key** using a token-bucket algorithm.

## Rate limit response headers
Every response includes:
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 540
X-RateLimit-Reset: 1739000000   # unix epoch when the window resets
```

## Handling 429 Too Many Requests
When you exceed the limit you receive HTTP `429` with a `Retry-After` header (seconds). Recommended client behavior:
1. Respect `Retry-After`; do not retry before it elapses.
2. Use exponential backoff with jitter for repeated 429s.
3. Cache responses and batch where possible (e.g. `GET /v2/tickets?ids=1,2,3`).

## Quotas
- Maximum request body size: **5 MB**.
- Maximum page size (`limit`): **100**.
- Webhook endpoints per workspace: 25.
- Bulk export jobs: 5 concurrent.

## Root cause guidance
Sustained 429s usually mean a polling loop with too short an interval. Prefer webhooks over polling. If your legitimate production traffic consistently exceeds your plan's limit, an Enterprise rate-limit increase must be arranged with our team — this is not self-service.
