# Cloudinary Support Request — Usage API Permission Issue

## Summary

The `/usage` Admin API endpoint returns 403 for all API keys on our account. We need the `cld::role::prodenv::billing` role assigned to our API key.

---

## Account Details

| Field | Value |
|-------|-------|
| Cloud name | `dnkcbkdgk` |
| Product Environment ID | `2607aa1695167a96b92a8f2a2e0f00` |
| Affected API key | `***REMOVED***` |
| SDK version | cloudinary-python 1.44.1 |

---

## What Works

- `GET /v1_1/dnkcbkdgk/ping` → ✅ 200 OK
- `GET /v1_1/dnkcbkdgk/resources/image` → ✅ 200 OK (returns real assets)

## What Fails

- `GET /v1_1/dnkcbkdgk/usage` → ❌ 403 Forbidden

**Error response:**
```json
{
  "error": {
    "message": "[prodenv:2607aa1695167a96b92a8f2a2e0f00] Request forbidden due to missing permissions (actions=[\"read\"])"
  }
}
```

**Request ID:** `6b52d6ad6ca3c998bc414122707d24cd`

---

## What We Already Tried

1. Created a new API key (`***REMOVED***`) with Master Admin role → same 403
2. Tested all available API keys on the account → all return the same 403 on `/usage`
3. Confirmed it is NOT an IP allowlist issue (ping and resources work from the same IP `5.66.29.213`)
4. Confirmed it is NOT an SDK issue (raw HTTP request also returns 403)
5. Attempted to assign the billing role via the Permissions API — our account does not have access to Account Management / Provisioning credentials

---

## Root Cause (confirmed by Cloudinary support bot)

> *"Older API keys were automatically given Master Admin during the permissions migration, which is why some integrations previously worked without explicit role assignment. New keys start with no permissions and access must be explicitly granted."*

The `cld::role::prodenv::billing` role (which includes `cld::policy::global::reports::usage::view`) does not appear in the Console's "Assign Roles" UI for product environment API keys, and cannot be assigned via the Provisioning API without account-level management credentials.

---

## What We Need

Please assign the following role to our API key:

```
Role ID:    cld::role::prodenv::billing
Principal:  apiKey / ***REMOVED***
Scope:      prodenv / 2607aa1695167a96b92a8f2a2e0f00  (cloud: dnkcbkdgk)
```

Equivalent Permissions API call (if you can run it on your end):
```
POST /v1_1/provisioning/accounts/{account_id}/permissions/roles/assign
{
  "principal_type": "apiKey",
  "principal_id": "***REMOVED***",
  "roles": [
    {
      "id": "cld::role::prodenv::billing",
      "scope_id": "2607aa1695167a96b92a8f2a2e0f00"
    }
  ]
}
```

Alternatively, please advise how a free-tier account can assign this role without access to provisioning credentials.
