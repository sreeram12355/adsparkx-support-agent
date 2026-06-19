# Two-Factor Authentication (2FA)

**Product:** CloudDesk
**Category:** Security
**Last updated:** 2026-01-20

## Overview
Two-factor authentication adds a second verification step at sign-in. CloudDesk supports authenticator apps (TOTP) and, on Business/Enterprise, hardware security keys (WebAuthn/FIDO2).

## Enabling 2FA
1. Go to **Settings → Security → Two-Factor Authentication**.
2. Click **Enable** and scan the QR code with an authenticator app (Google Authenticator, Authy, 1Password).
3. Enter the 6-digit code to confirm.
4. **Save your 10 backup codes** in a secure location. Each code works once.

## Signing in with 2FA
After entering your password you will be prompted for the current 6-digit code from your authenticator app.

## Lost access to your authenticator
- Use one of your **backup codes** at the 2FA prompt.
- If you have no backup codes, an Owner or Admin can reset your 2FA from Settings → Members → ⋯ → **Reset 2FA**.
- If you are the only Owner and have lost both your device and backup codes, account recovery requires identity verification by a human support agent — this cannot be self-served for security reasons.

## Enforcing 2FA for the workspace
Owners can require all members to enable 2FA in Settings → Security → **Require 2FA**. Members without 2FA are prompted to enroll at next sign-in.
