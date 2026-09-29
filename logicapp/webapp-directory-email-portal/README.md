# Web App Directory, Email Fan-Out, and Portal

This package contains the Logic App portion for querying report recipients from the web app and sending report-ready emails. The portal and directory endpoint code lives in the existing `webapp/` project.

## Relevant source files

| Area | Files |
|---|---|
| Portal shell and pages | `webapp/Pages/Index.cshtml`, `webapp/Pages/Index.cshtml.cs`, `webapp/Pages/Shared/_Layout.cshtml` |
| Unauthorized user handling | `webapp/Pages/Unauthorized.cshtml`, `webapp/Pages/Unauthorized.cshtml.cs` |
| Entra sign-in, admin JWT gate, security headers, `/report/latest`, `/admin/list-users` | `webapp/Program.cs` |
| Authorization & Directory lookup | `webapp/Services/CosmosUserService.cs`, `cosmos/schema.md` |
| Secure report proxy from Blob Storage | `webapp/Services/BlobReportService.cs` |
| Shared client slug/blob-path rules | `shared/naming.cs` |
| Email fan-out workflow | `logicapp/webapp-directory-email-portal/workflow.json` |

## Runtime behavior

1. A prior report-generation step writes client reports to the Storage `report` container.
2. This workflow calls the web app endpoint:

   ```http
   GET /admin/list-users
   ```

   using Logic App Managed Identity authentication.
3. The web app validates the bearer token audience and allow-listed caller object ID in `webapp/Program.cs`.
4. The web app queries Cosmos DB `reporting.users` and returns only:

   ```json
   {
     "email": "user@example.com",
     "client_id": "acme-corp",
     "client_name": "Acme Corp",
     "user_name": "Jane Doe"
   }
   ```

5. The Logic App fans out one email per returned user using the Office 365 connector.
6. The email links to the portal URL.
7. The user signs in with Entra ID.
8. The portal looks up the signed-in email in Cosmos and streams only that user's client report from:

   ```text
   report/<client-slug>/report-file-latest.html
   ```

   through `GET /report/latest`.

Direct Blob URLs and SAS URLs are not exposed to end users.

## Required app settings

Configure the web app with existing infrastructure values:

| Setting | Purpose |
|---|---|
| `AzureAd__TenantId` | Entra tenant for portal sign-in and admin token validation. |
| `AzureAd__ClientId` | App registration client ID. Also accepted as `api://<client-id>` audience for admin calls. |
| `AzureAd__ClientSecret` | Required by the interactive web app sign-in flow if not using another supported auth mechanism. Store only in app settings or Key Vault references. |
| `Admin__AllowedPrincipalIds` | Comma-separated object IDs allowed to call `/admin/*`, usually the Logic App system-assigned MSI object ID. |
| `Cosmos__Endpoint` | Cosmos DB SQL endpoint. |
| `Cosmos__Database` | Usually `reporting`. |
| `Cosmos__UsersContainer` | Usually `users`. |
| `Storage__Account` | Existing Storage Account containing reports. |
| `Storage__ReportContainer` | Usually `report`. |
| `ApplicationInsights__ConnectionString` | Optional telemetry. |
| `Support__Email` | Address shown on the Unauthorized page. |

## Required managed identity permissions

Grant the web app system-assigned managed identity:

- Cosmos DB built-in data contributor or equivalent data-plane role on `reporting.users`.
- Storage Blob Data Reader or Contributor on the Storage Account/report container.

Grant the Logic App system-assigned managed identity:

- Permission to request a token for the web app audience.
- Inclusion in `Admin__AllowedPrincipalIds` so `/admin/list-users` authorizes it.

Configure the Office 365 API connection used by the Logic App for email sending.

## Workflow parameters

| Parameter | Description |
|---|---|
| `webAppBaseUrl` | Base URL of the web app, without trailing slash. |
| `portalUrl` | URL inserted into user emails. Usually the same as `webAppBaseUrl`. |
| `adminAudience` | MSI token audience for `/admin/list-users`, e.g. `api://<client-id>`. |
| `supportEmail` | Support recipient for workflow failure notifications. |
| `$connections.office365` | Office 365 Logic App API connection. |

## Validation

From the repository root:

```powershell
dotnet build .\webapp\AirlPulseReport.Web.csproj -c Release --no-restore
dotnet test .\tests\webapp.unit\AirlPulseReport.Web.Tests.csproj -c Release --no-restore
Get-Content .\logicapp\webapp-directory-email-portal\workflow.json -Raw | ConvertFrom-Json | Out-Null
```

