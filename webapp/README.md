# Web App (ASP.NET Core, Entra-authenticated)

## What it does

1. **Entra ID sign-in** for every route (fallback authorization policy).
2. On sign-in, computes the caller's accessible companies from their Entra
   security-group membership (the `groups` claim on their ID token) against
   the `group_access` Cosmos container.
   - No accessible companies → redirect to `/Unauthorized` (HTTP 403).
   - One or more companies → the home page shows a paginated (10/page),
     newest-first list of every generated report for the selected company
     (a dropdown appears when the caller has access to more than one),
     sourced from the `clients` container's cached `report_files` array.
3. `GET /report/view?client=<clientId>&name=<reportFileName>` streams any
   single report file for a client (`GET /report/latest?client=<clientId>`
   still works unchanged, streaming only the newest report) through the Web
   App's own managed identity (never a SAS URL — storage
   `publicNetworkAccess=Disabled` makes SAS unreachable anyway). Both the
   `client` and `name` query parameters are re-validated server-side on
   every request against the caller's own accessible companies and the
   canonical `report-file-(latest|DDMMYYYY).html` file-name pattern — they
   can never be used to reach a company or blob the caller isn't already
   authorized for.
4. `/ManageAccess` — an admin portal (same app, no separate deployment) for
   managing which Entra security group maps to which company. Gated by
   membership in the Entra group configured as `Admin:AdminGroupId`. Laid
   out as three tabs:
   - **Client Directory**: the list of known companies, populated by an
     admin-triggered "Sync from storage" scan of Blob `data`'s top-level
     client folders (the real folders Synapse's export pipeline and the
     report batch job read/write) — not free-typed, so a mapping can never
     target a nonexistent or typo'd company. Auto-suggested display names
     (de-slugified from the folder name) can be corrected inline. Sync also
     refreshes every known client's `report_files` array from Blob `report`
     — re-run it after a new monthly batch to keep the home page's report
     list current.
   - **Existing Mappings**: every group→company mapping, editable in place
     (group display name, target company, and an optional reference
     contact email) and deletable.
   - **Add New Mapping**: create a mapping for a new Entra group — pick the
     group (paste its object ID + a display name for reference), a company
     from the synced directory, and an optional contact email.

## Config

All config is in `appsettings.json` (override in App Service via app settings):

- `AzureAd:*` — Entra ID app registration details. `ClientId` is set at deploy time (either via app setting or Key Vault reference). The app registration must have `groupMembershipClaims` set to `SecurityGroup` (or `All`) for the `groups` ID token claim to be emitted — see `az ad app update --id <appId> --set groupMembershipClaims=SecurityGroup`.
- `Admin:AdminGroupId` — Entra security group object ID whose members can access `/ManageAccess`.
- `Cosmos:*` — endpoint, database, `GroupAccessContainer` (`group_access`), `ClientsContainer` (`clients`), and `UsersContainer` (`users`) for the `/admin/list-users` email fan-out endpoint.
- `Storage:*` — account, `ReportContainer` (`report`), `DataContainer` (`data`, used only by the Admin portal's client-directory sync).
- `ApplicationInsights:ConnectionString` — telemetry.
- `Support:Email` — shown on the 403 page.

## Auth to Azure resources

Runs as the web app's system-assigned managed identity in production (`DefaultAzureCredential` with interactive off). Locally uses your `az login` context.

Required role assignments on the web app MSI:
- `Storage Blob Data Contributor` scoped to the storage account (covers both `report` and `data` containers).
- Cosmos data-plane built-in contributor role scoped to `reporting` (covers `group_access` and `clients` containers, which the Admin portal writes to).
- Any additional roles for App Insights (workspace-based, no additional role needed).

## Local dev

```powershell
cd webapp
dotnet restore
dotnet run
```

Open `https://localhost:5001`. Sign in with an account that is a member of at least one Entra group mapped in `group_access` (or the admin group, to reach `/ManageAccess`).

## Notes

- Entra's `groups` claim reflects membership as of the last sign-in/token refresh — a user newly added to a group must sign out and back in before it takes effect.
- `Naming.ReportLatestPath`/`ReportDatedPath` are shared with the batch job via `shared/naming.cs` (linked into the project).
- The per-email `reporting.users` container is still used by `/admin/list-users` for email fan-out; portal authorization itself uses Entra group membership plus `group_access`.
- Full Cosmos container schemas (`group_access`, `clients`): [`docs/cosmos-schema.md`](../docs/cosmos-schema.md).
- UI theme conventions (Bootstrap classes to reuse, button color rules, dependency security policy) for any future page/tab: [`../AGENTS.md`](../AGENTS.md). Read it before adding new markup or CSS to `Pages/`.
