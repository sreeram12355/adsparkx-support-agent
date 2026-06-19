# SSO / SAML 2.0 Configuration

**Product:** CloudDesk (Business & Enterprise)
**Category:** Security / Administration
**Last updated:** 2026-02-05

## Overview
CloudDesk supports SP-initiated SSO via SAML 2.0 with identity providers such as Okta, Azure AD (Entra ID), Google Workspace, and OneLogin.

## Service Provider (SP) metadata
| Field | Value |
|-------|-------|
| Entity ID / Audience URI | `https://<workspace>.clouddesk.com/saml/metadata` |
| ACS (Reply) URL | `https://<workspace>.clouddesk.com/saml/acs` |
| Name ID format | `EmailAddress` |
| Binding | HTTP-POST |

## Configuration steps
1. In your IdP, create a new SAML application using the SP metadata above.
2. Map the SAML attribute `email` to the user's primary email (must match the CloudDesk email exactly).
3. (Optional) Map `firstName`, `lastName`, and `groups` for auto-provisioning.
4. Download the IdP metadata XML and upload it in CloudDesk: **Settings → Security → SSO → Upload IdP metadata**.
5. Use **Test connection** before enabling enforcement.

## Common SAML errors
### `AUTH_FAILED: assertion email mismatch`
The `email` attribute from the IdP does not match any CloudDesk member. Fix the attribute mapping or invite the user first.

### Redirect loop after IdP login
Usually a clock skew (>5 min) between IdP and SP, or an incorrect ACS URL. Verify both, and ensure the assertion is signed.

### `INVALID_SIGNATURE`
The uploaded IdP certificate is wrong or has expired. Re-download fresh IdP metadata and re-upload.

## Just-in-time (JIT) provisioning
When enabled, members who authenticate via SSO but do not yet exist are created automatically with the default role. Configure under Settings → Security → SSO → Provisioning.

## Escalation note
SAML configuration errors that persist after verifying attribute mapping, ACS URL, and certificate validity often require log inspection (the `X-Request-Id` from the failed assertion) by CloudDesk support engineering.
