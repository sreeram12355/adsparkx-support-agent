# Data Export & Import

**Product:** CloudDesk
**Category:** Data Management
**Last updated:** 2026-01-22

## Exporting data
- Go to **Settings → Data → Export**.
- Choose a scope (tickets, contacts, knowledge base) and format (CSV or JSON).
- Exports run as a background job; you receive an email with a secure download link when ready.
- Download links expire after 72 hours.
- Large exports (>100k records) are split into multiple files.

## Importing data
- Settings → Data → Import. Supported: CSV with a header row matching our template.
- Download the import template first to ensure correct column names.
- Imports are validated before commit; rows with errors are reported and skipped.
- Maximum import file size is 50 MB; split larger files.

## API-based export
Programmatic export is available via `POST /v2/exports`. Poll `GET /v2/exports/{id}` until `status = completed`, then download from the returned URL. See Rate Limits & Quotas for concurrency limits (5 concurrent jobs).

## Common issues
| Symptom | Cause / fix |
|---------|-------------|
| Import rows skipped | Column headers don't match the template, or required fields are empty |
| Export email not received | Check spam; ensure your email is verified |
| Download link expired | Re-run the export; links last 72 hours |

## Data retention note
Deleted data enters a 30-day soft-delete window before permanent purge. Recovery of purged data is not possible via self-service and requires escalation.
