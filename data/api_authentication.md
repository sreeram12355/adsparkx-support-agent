# API Authentication Guide

**Product:** CloudDesk REST API (v2)
**Category:** Developer / API
**Last updated:** 2026-02-03

## Authentication model
CloudDesk uses **Bearer token authentication** with API keys scoped to a workspace. Every request to `https://api.clouddesk.com/v2/` must include an `Authorization` header:

```
Authorization: Bearer cd_live_<your_api_key>
```

API keys are created in **Settings → Developer → API Keys**. Keys come in two types:
- `cd_test_*` — sandbox keys, no rate cost, isolated test data.
- `cd_live_*` — production keys.

## Common authentication errors
### 401 Unauthorized — `invalid_api_key`
- The key is malformed, revoked, or belongs to a different workspace.
- Verify there is no leading/trailing whitespace and the full prefix (`cd_live_`) is present.

### 401 Unauthorized — `expired_token`
- OAuth access tokens expire after **3600 seconds**. Use the refresh token at `POST /v2/oauth/token` with `grant_type=refresh_token` to obtain a new access token.

### 403 Forbidden — `insufficient_scope`
- The key does not have the required scope. Scopes are assigned at creation time and cannot be widened later; create a new key with the needed scopes (e.g. `tickets:write`, `users:read`).

### 429 Too Many Requests
- You exceeded the rate limit. See the Rate Limits & Quotas guide. Inspect the `Retry-After` response header and back off accordingly.

## Root cause checklist for failed authentication
1. Confirm the `Authorization` header is present and correctly formatted.
2. Confirm the key is active (Settings → Developer → API Keys shows status `Active`).
3. Confirm the key's workspace matches the resource you are requesting.
4. Confirm system clock skew is under 5 minutes (affects OAuth signature validation).
5. Inspect the `X-Request-Id` header in the response and include it when contacting support — it lets engineers trace the exact request in server logs.

## Example request
```bash
curl -H "Authorization: Bearer cd_live_xxx" \
     -H "Content-Type: application/json" \
     https://api.clouddesk.com/v2/tickets?limit=10
```
