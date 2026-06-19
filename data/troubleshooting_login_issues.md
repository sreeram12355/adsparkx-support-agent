# Troubleshooting Login Issues

**Product:** CloudDesk
**Category:** Account & Access
**Last updated:** 2026-02-10

## Quick checklist
If you cannot sign in, work through these in order:
1. Confirm you are using the correct workspace URL (`https://<workspace>.clouddesk.com`).
2. Confirm Caps Lock is off and you are using the right email.
3. Try a password reset (see Password Reset Guide).
4. Clear browser cache and cookies, or try an incognito window.
5. Disable browser extensions that block scripts or cookies.
6. Try a different browser or device to rule out local issues.

## Specific symptoms
### "Invalid email or password"
The credentials don't match an active account. Reset your password. If it persists, your account may not be provisioned in this workspace — ask your Owner/Admin to confirm your membership.

### Page keeps redirecting / blank screen
Usually a stale session cookie. Clear cookies for `clouddesk.com` and retry.

### "Your account is locked"
Triggered after 10 failed attempts. Wait 30 minutes; the lock clears automatically.

### SSO loop — keeps returning to the login page
This indicates a misconfigured SSO/SAML assertion (e.g. mismatched email attribute). See the SSO/SAML Configuration guide; persistent SSO failures require an admin and may need human support.

### Works on web but not mobile app
Update the app to the latest version and confirm the device clock is set automatically (time skew breaks token validation).

## When to escalate
If a member has reset their password, cleared cache, confirmed workspace membership, and still cannot sign in, the account likely has a provisioning or lock anomaly that a human support agent must investigate.
