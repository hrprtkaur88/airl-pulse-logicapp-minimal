# Cosmos DB schema

Database: `reporting` in the customer Cosmos DB SQL account.

This document describes the two containers the web app's group-based access
model reads and writes. It's intended to be shareable with the customer as
the authoritative schema for this feature.

## Container: `group_access`

Partition key: `/group_id`

Maps an Entra ID security group to the company (client) its members are
allowed to view. One company can have several groups mapped to it (e.g. a
"Viewers" group and an "Executives" group); one user can belong to several
groups, so a single sign-in can surface several companies.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string (GUID) | yes | Document id, generated when the mapping is created. Immutable. |
| `group_id` | string (GUID) | yes | Entra security group **object ID** (not display name). This is the partition key and is immutable once created — to repoint a mapping at a different group, delete and re-add. |
| `group_name` | string | yes | Human-readable group display name, for reference in the Admin portal only. Editable. |
| `client_id` | string | yes | Slug identifying the company (matches the top-level folder name under Blob `data`/`report`, e.g. `acme-corp`). Must match an existing `clients` container document. |
| `client_name` | string | yes | Human-readable company display name shown to end users. |
| `contact_email` | string | no | Optional reference contact for the group (e.g. who requested/owns it). **Not used for anything security-relevant or for automated email delivery** — informational only. |

Example document:

```json
{
  "id": "3f9e1c2a-9b7d-4e21-9b0a-1a2b3c4d5e6f",
  "group_id": "96f3add0-92da-45c9-9800-91cbaf9e9a38",
  "group_name": "AIRL-Pulse-Viewers-AcmeCorp",
  "client_id": "acme-corp",
  "client_name": "Acme Corp",
  "contact_email": "jane.doe@acmecorp.com"
}
```

**Access computation:** on every sign-in, the web app reads the `groups`
claim from the caller's Entra ID token, queries this container for every
document whose `group_id` is in that set, and takes the distinct
`client_id`/`client_name` pairs as the caller's accessible companies. Group
membership is reflected only as of the last token issuance — a user newly
added to a group must sign out and back in before access takes effect.

## Container: `clients`

Partition key: `/client_id`

The authoritative directory of known companies, populated by the Admin
portal's "Sync from storage" action, which scans the top-level folders in
Blob `data` (the same folders Synapse's export pipeline and the monthly
report batch job read and write).

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Same value as `client_id` (used as the Cosmos item id). |
| `client_id` | string | yes | Slug matching the Blob folder name, e.g. `acme-corp`. Immutable — this is the partition key. |
| `client_name` | string | yes | Human-readable display name. Auto-suggested (de-slugified) on first discovery; admins can correct it afterward, and corrections survive repeated syncs. |
| `source` | string | yes | Always `"blob:data"` currently — provenance marker for future non-blob sources. |
| `last_synced` | string (ISO 8601) | yes | UTC timestamp of the most recent sync that touched this document. |
| `report_files` | array of string | yes | Every dated report file name for this client (`report-file-DDMMYYYY.html`), **newest first**, refreshed on every sync by scanning Blob `report`. The home page reads this array directly (a cheap Cosmos point-read) rather than listing blobs on every page view — this is why "Sync from storage" must be re-run after new monthly reports land for the report list to stay current. |

Example document:

```json
{
  "id": "acme-corp",
  "client_id": "acme-corp",
  "client_name": "Acme Corp",
  "source": "blob:data",
  "last_synced": "2026-09-25T18:04:11.0000000Z",
  "report_files": [
    "report-file-20092026.html",
    "report-file-20082026.html",
    "report-file-20072026.html"
  ]
}
```

## Legacy container: `users` (retained, no longer used)

The original one-row-per-user model (`email`, `client_id`, `client_name`,
`user_name`, pk `/client_id`) predates the group-based access model above.
It is kept in place for reference/rollback but is not read by any current
authorization logic — `CosmosUserService` in the codebase is unused
dead code, not deleted, in case of rollback need.
