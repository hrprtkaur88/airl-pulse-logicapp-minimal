# Web App (ASP.NET Core, Entra-authenticated)

## What it does

1. **Entra ID sign-in** for every route (fallback authorization policy).
2. On sign-in, looks up the caller's email in Cosmos `reporting.users`.
    - Not found → redirect to `/Unauthorized` (HTTP 403).
    - Found → shows a single **View Latest Report** button.
3. The button links to a **short-lived user-delegation SAS URL** for `report/<client-slug>/report-file-latest.html` (default 15 min TTL). Never exposes the storage account key.

## Config

All config is in `appsettings.json` (override in App Service via app settings):

- `AzureAd:*` — Entra ID app registration details. `ClientId` is set at deploy time (either via app setting or Key Vault reference).
- `Cosmos:*` — endpoint, database, users container.
- `Storage:*` — account, report container, SAS TTL.
- `ApplicationInsights:ConnectionString` — telemetry.
- `Support:Email` — shown on the 403 page.

## Auth to Azure resources

Runs as the web app's system-assigned managed identity in production (`DefaultAzureCredential` with interactive off). Locally uses your `az login` context.

Required role assignments on the web app MSI:
- `Storage Blob Data Reader` scoped to the `report` container.
- Cosmos data-plane built-in reader role scoped to `reporting`.
- Any additional roles for App Insights (workspace-based, no additional role needed).

## Local dev

```powershell
cd webapp
dotnet restore
dotnet run
```

Open `https://localhost:5001`. Sign in with an account whose email is seeded in Cosmos.

## Notes

- The `SasTtlMinutes` default (15) balances shareability vs. leakage. Reduce for tighter security posture.
- `Naming.ReportLatestPath` is shared with the batch job via `shared/naming.cs` (linked into the project).
