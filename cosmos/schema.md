# Cosmos DB Schema

**Account** (dev): `cos-scout-pi2dl-wus3` (from `config.json`)
**Database:** `reporting`
**Container:** `users`
**Partition key:** `/client_id`
**Throughput:** serverless (billed per RU)

## `users` document shape

```jsonc
{
  "id":           "<uuid v4>",
  "client_id":    "acme-corp",           // partition key
  "client_name":  "Acme Corp",
  "user_name":    "Jane Doe",
  "user_id":      "jane.doe@acme.com",   // display / login hint
  "email":        "jane.doe@acme.com",   // lookup key (Web App + Logic App)
  "created_utc":  "2026-09-18T00:00:00Z"
}
```

## Lookups

- **Web App auth**: `SELECT * FROM c WHERE c.email = @email` (cross-partition, small container so cheap).
- **Logic App fan-out**: `SELECT c.client_id, c.client_name, c.email FROM c` (cross-partition).

## Notes

- `client_id` values MUST equal the `slugify(client_name)` used everywhere else. `cosmos/seed_users.py` enforces this.
- 2–5 users per client. Idempotent — seed script upserts by `id` and derives IDs from `email` so re-running is safe.
