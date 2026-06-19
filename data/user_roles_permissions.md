# User Roles & Permissions

**Product:** CloudDesk
**Category:** Administration
**Last updated:** 2026-01-25

## Built-in roles
| Role | Capabilities |
|------|--------------|
| Owner | Full control incl. billing, deletion, ownership transfer (one per workspace) |
| Admin | Manage members, settings, integrations; cannot delete workspace or change billing owner |
| Agent | Create, edit, resolve tickets; cannot change workspace settings |
| Viewer | Read-only access to tickets and reports |

## Changing a member's role
Settings → Members → ⋯ next to the member → **Change role**. Only Owners and Admins can change roles. You cannot elevate someone above your own role.

## Custom roles (Enterprise)
Enterprise plans can define custom roles with granular permissions (e.g. "Billing read-only", "Integration manager") under Settings → Members → Roles.

## Permission troubleshooting
| Symptom | Cause |
|---------|-------|
| "You don't have permission" | Your role lacks the capability; ask an Admin |
| Can't see Billing | Only Owner/Billing Admin can view billing |
| Can't change a setting | Settings require Admin or Owner |

## Group/SSO-based roles
With SSO JIT provisioning, you can map IdP groups to CloudDesk roles so role assignment is managed centrally in your identity provider. See SSO/SAML Configuration.
