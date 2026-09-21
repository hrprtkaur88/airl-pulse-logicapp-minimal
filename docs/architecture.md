# Simplified Architecture

This repository contains the simplified AIRL Pulse Report monthly flow. It assumes the surrounding Azure infrastructure already exists.

The scope is intentionally smaller than the full end-to-end architecture: it covers orchestration, pipeline start, report generation with Azure OpenAI, writing generated reports to Blob Storage, querying the authorization directory, sending report-ready emails, and serving the portal.

```mermaid
flowchart TB
    subgraph ORCH["Orchestration"]
        LA["Logic App<br/>Monthly Orchestration<br/>(System-assigned MSI)"]
    end

    subgraph DATAFLOW["Data Generation and Report Generation"]
        PIPE["Existing Synapse/Data Factory Pipeline<br/>Generate AIRL Workbooks"]
        FUNC["Azure Function App<br/>/api/report-generation/generate-report/{slug}<br/>(System-assigned MSI)"]
        OAI["Azure OpenAI<br/>gpt-4o"]
    end

    subgraph STORAGE["Storage"]
        DATA[("data container<br/>assessment-workbook-MMYYYY.xlsx")]
        REPORT[("report container<br/>report-file-latest.html<br/>report-file-DDMMYYYY.html<br/>status-MMYYYY.json")]
    end

    subgraph AUTH["Authorization and Directory"]
        COSMOS[("Cosmos DB<br/>reporting.users<br/>pk: /client_id")]
    end

    subgraph PORTAL["Portal"]
        WEB["ASP.NET Core Web App<br/>Entra sign-in<br/>/admin/list-users<br/>/report/latest"]
        USER["End users"]
    end

    subgraph NOTIFY["Notification"]
        EMAIL["Office 365 Outlook<br/>managed connector"]
        SUPPORT["Support email<br/>failure only"]
    end

    LA -- "1. Run pipeline via MSI" --> PIPE
    PIPE -- "2. Write workbooks" --> DATA
    LA -- "3. Generate reports per client via MSI" --> FUNC
    FUNC -- "4. Read workbook" --> DATA
    FUNC -- "5. Generate narrative" --> OAI
    FUNC -- "6. Write HTML report + status" --> REPORT
    LA -- "7. Query users via Web App MSI" --> WEB
    WEB -- "Read authorized recipients" --> COSMOS
    LA -- "8. Fan out report-ready email" --> EMAIL
    EMAIL -- "Portal link" --> USER
    USER -- "Sign in with Entra" --> WEB
    WEB -- "Lookup signed-in email" --> COSMOS
    WEB -- "Proxy authorized latest report" --> REPORT
    LA -. "On failure" .-> SUPPORT
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| Logic App | Starts the existing data pipeline, waits for completion, then calls the report Function for each configured client slug. |
| Existing pipeline | Generates one AIRL assessment workbook per client and stores it in the `data` container. |
| Azure Function | Reads each workbook, runs the copied AIRL report-generation pipeline, calls Azure OpenAI for narrative generation, renders HTML, and uploads report files. |
| Azure OpenAI | Generates the report narrative used by the AIRL report renderer. |
| Storage `data` container | Holds generated workbook input files. |
| Storage `report` container | Holds generated HTML reports and status manifests. |
| ASP.NET Core Web App | Provides the Entra-protected portal, `/admin/list-users` for Logic App fan-out, and `/report/latest` secure report proxy. |
| Cosmos DB `reporting.users` | Authorization and recipient directory keyed by client slug. |
| Office 365 connector | Sends report-ready email notifications to authorized recipients. |

## Input and output paths

The pipeline must produce:

```text
data/<client-slug>/assessment-workbook-<MMYYYY>.xlsx
```

The Function writes:

```text
report/<client-slug>/report-file-latest.html
report/<client-slug>/report-file-<DDMMYYYY>.html
report/<client-slug>/status-<MMYYYY>.json
```

## Authentication model

- Logic App calls the pipeline using Managed Identity.
- Logic App calls the report Function using Managed Identity.
- Logic App calls the web app `/admin/list-users` endpoint using Managed Identity.
- The report Function validates the Logic App caller using Entra ID token audience and allow-listed principal ID.
- The report Function uses its own Managed Identity to access Blob Storage and Azure OpenAI.
- The web app validates the Logic App caller for `/admin/*` using Entra ID token audience and allow-listed principal ID.
- End users authenticate to the portal with Entra ID.
- The portal maps signed-in user email to Cosmos DB `reporting.users` before streaming a report.

## Web app and portal paths

- `GET /admin/list-users` returns only recipient fan-out fields.
- `GET /` shows the signed-in user's portal landing page.
- `GET /report/latest` streams the signed-in user's latest client report from Blob Storage.
- `GET /Unauthorized` returns 403 when the signed-in user is not in the directory.

## Out of scope for this branch

The branch assumes Azure resource creation, private endpoint topology, Key Vault, App Insights, and Office 365 connection authorization already exist or are managed by the consuming environment.
