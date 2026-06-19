# Integrations Setup

**Product:** CloudDesk
**Category:** Integrations
**Last updated:** 2026-01-30

## Available integrations
CloudDesk integrates with Slack, Microsoft Teams, Jira, GitHub, Zapier, and Salesforce. The number of active integrations depends on your plan (Starter: 3, Business+: unlimited).

## Connecting an integration
1. Go to **Settings → Integrations** and choose a provider.
2. Click **Connect** and approve the OAuth consent screen in the provider.
3. Choose which workspace/channel/project to link.
4. Configure event mapping (e.g. new CloudDesk ticket → Slack channel message).

## Slack
- `/clouddesk` slash command lets agents create and search tickets from Slack.
- Notifications can be routed per-channel by ticket priority.

## Jira
- Two-way sync: CloudDesk tickets can create linked Jira issues and mirror status changes.
- Field mapping is configured under the Jira integration settings.

## Troubleshooting
| Symptom | Resolution |
|---------|------------|
| "Connection expired" | Reauthorize: Settings → Integrations → provider → Reconnect |
| Events not syncing | Check the integration's Activity log; verify the linked channel/project still exists |
| Missing permissions | The connecting user must be an admin in both CloudDesk and the provider |

## Disconnecting
Removing an integration stops all syncing immediately but does not delete previously synced data in the external system.
