# Mobile App FAQ

**Product:** CloudDesk for iOS & Android
**Category:** Mobile
**Last updated:** 2026-02-01

**Which devices are supported?** iOS 16+ and Android 11+. Older versions may work but are unsupported.

**How do I enable push notifications?** Allow notifications at first launch, or go to device Settings → CloudDesk → Notifications. In-app, configure types under Profile → Notifications.

**Why am I not receiving push notifications?**
- Confirm notifications are allowed at the OS level.
- Confirm Do Not Disturb / Focus mode is off.
- Background App Refresh must be enabled (iOS).
- Force-quit and reopen the app to refresh the push token.

**Can I use the app offline?** You can read recently synced tickets offline. Creating or editing requires a connection; changes queue and sync when you reconnect.

**Why does the app sign me out?** Sessions expire after 30 days, or sooner if your admin enforces a shorter session policy. SSO users follow the IdP session lifetime.

**The app is slow or crashing.** Update to the latest version, restart the device, and ensure at least 500 MB free storage. If crashes persist, send a diagnostic report from Profile → Help → Send Diagnostics, which includes a log ID for support.
