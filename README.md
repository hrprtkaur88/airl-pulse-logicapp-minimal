# AIRL Pulse Report Generation Minimal

Minimal implementation for the AIRL monthly flow through report generation. This repository assumes the broader platform infrastructure already exists and includes code for:

1. Starting the data export pipeline with Managed Identity.
2. Calling the report-generation Azure Function with Managed Identity.
3. Reading generated workbooks from Blob Storage.
4. Running the AIRL report-generation pipeline.
5. Writing generated HTML reports and status manifests to Blob Storage.

The pipeline is expected to write source artifacts to the configured `data` blob container. The Function reads those workbooks, runs the copied `ai-foundry/jobs/run_batch.py` pipeline and `ai-foundry/skill` scripts, then writes reports to the configured `report` blob container.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the simplified architecture diagram and component readout.

## Repository layout

```text
docs/
  architecture.md  # simplified architecture diagram and readout
infra/
  main.bicep       # subscription-scope deployment entry point
  logicapp.bicep   # Logic App Consumption workflow resource
  workflow.json    # Logic App workflow definition
function/
  function_app.py   # Azure Function HTTP endpoint for report generation
  host.json
  requirements.txt
ai-foundry/
  jobs/             # report-generation orchestrator copied from source repo
  skill/            # AIRL skill scripts/references/assets needed to render HTML
shared/
  naming.py         # shared blob path rules
README.md
.gitignore
```

## Existing Azure resources

This repo does not create the storage account, blob containers, Synapse/Data Factory pipeline, Azure OpenAI account, or Function App host. Provide those as parameters/app settings:

- Existing storage account name.
- Existing blob containers, usually `data` and `report`.
- Pipeline endpoint and pipeline name.
- Pipeline Managed Identity audience.
- Existing Azure Function App where `function/` is deployed.
- Report Function Managed Identity audience.
- Azure OpenAI endpoint and deployment settings on the Function App.

## Managed Identity permissions

The deployed Logic App uses a system-assigned managed identity. Grant that principal the minimum permissions required by your existing services:

- Pipeline service: permission to create and read pipeline runs.
  - Synapse example: role assignment that allows pipeline execution on the Synapse workspace.
  - Data Factory example: role assignment that allows creating pipeline runs on the Data Factory.
- Report Function: allow the Logic App principal ID in `ADMIN_ALLOWED_PRINCIPAL_IDS`.
- Function App managed identity:
  - Storage Blob Data Contributor on the storage account so it can read `data` and write `report`.
  - Cognitive Services OpenAI User on the Azure OpenAI account.
- Storage access for the pipeline identity so it can write workbooks into `data`.

## Function App settings

Configure these settings on the existing Function App:

| Setting | Description |
|---|---|
| `TENANT_ID` | Entra tenant ID used to validate Logic App MSI tokens. |
| `ADMIN_CLIENT_ID` | App registration client ID used as the Function audience. |
| `ADMIN_ALLOWED_PRINCIPAL_IDS` | Comma-separated object IDs allowed to call report generation, usually the Logic App MSI principal ID. |
| `STORAGE_ACCOUNT_NAME` | Existing storage account. Request body can override this. |
| `DATA_CONTAINER_NAME` | Data container, usually `data`. |
| `REPORT_CONTAINER_NAME` | Report container, usually `report`. |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint, for example `https://<account>.openai.azure.com/`. |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat deployment name, usually `gpt-4o`. |
| `AZURE_OPENAI_API_VERSION` | API version, default `2024-10-21`. |
| `REPORT_GENERATION_RETRIES` | Per-client retry count, default `2`. |

## Parameters

| Parameter | Description |
|---|---|
| `resourceGroupName` | Resource group where the Logic App is deployed. |
| `location` | Azure region. |
| `logicAppName` | Logic App workflow name. |
| `storageAccountName` | Existing storage account used by pipeline and batch. |
| `dataContainerName` | Blob container for pipeline output. |
| `reportContainerName` | Blob container for generated reports. |
| `pipelineEndpoint` | Base endpoint for pipeline API, without trailing slash. |
| `pipelineName` | Pipeline name to start. |
| `pipelineAudience` | Managed Identity token audience for the pipeline API. |
| `reportFunctionAppName` | Existing Function App name that hosts `function/`. |
| `reportFunctionBaseUrl` | Base URL of the Function App, including `/api`. |
| `reportFunctionAudience` | Managed Identity token audience for the Function App. |
| `clientSlugs` | Client slugs to process after the pipeline succeeds. |

## Deploy

```powershell
az deployment sub create `
  --location westus3 `
  --template-file .\infra\main.bicep `
  --parameters `
    resourceGroupName='rg-scout-lean-wus3' `
    logicAppName='logic-airl-minimal' `
    storageAccountName='<existing-storage-account>' `
    dataContainerName='data' `
    reportContainerName='report' `
    pipelineEndpoint='https://<workspace>.dev.azuresynapse.net' `
    pipelineName='pl-export-clients' `
    pipelineAudience='https://dev.azuresynapse.net/' `
    reportFunctionAppName='<existing-function-app-name>' `
    reportFunctionBaseUrl='https://<function-app>.azurewebsites.net/api' `
    reportFunctionAudience='api://<app-registration-client-id>'
```

After deployment, assign permissions to the output `logicAppPrincipalId`.

## Deploy Function code

From the repository root, deploy the `function/` folder to an existing Python Azure Function App. The Function package depends on sibling folders in this repo, so stage them next to `function_app.py` before publishing or use your existing CI packaging process.

```powershell
Copy-Item .\ai-foundry .\function\ai-foundry -Recurse -Force
Copy-Item .\shared .\function\shared -Recurse -Force
Set-Location .\function
func azure functionapp publish <existing-function-app-name> --python --build remote
```

The HTTP endpoint is:

```text
POST /api/report-generation/generate-report/{slug}?runMonth=MMYYYY
```

It reads:

```text
data/<slug>/assessment-workbook-<MMYYYY>.xlsx
```

It writes:

```text
report/<slug>/report-file-latest.html
report/<slug>/report-file-<DDMMYYYY>.html
report/<slug>/status-<MMYYYY>.json
```

## Notes

- No secrets, storage keys, SAS tokens, client secrets, or connection strings are used.
- The workflow uses `ManagedServiceIdentity` authentication for both Step 1 and Step 2.
- The workflow passes storage account/container names to the Function so report generation reads from `data` and writes to `report`.
