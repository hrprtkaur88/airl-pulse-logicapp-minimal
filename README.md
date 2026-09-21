# AIRL Pulse Logic App Minimal

Minimal Azure Logic App implementation for the AIRL monthly flow. This repository assumes the broader platform already exists and only deploys the Logic App orchestration for:

1. Starting the data export pipeline with Managed Identity.
2. Starting the batch/report-generation process with Managed Identity.

The pipeline is expected to write source artifacts to the configured `data` blob container. The batch endpoint is expected to read from `data` and write generated reports to the configured `report` blob container.

## Repository layout

```text
infra/
  main.bicep       # subscription-scope deployment entry point
  logicapp.bicep   # Logic App Consumption workflow resource
  workflow.json    # Logic App workflow definition
README.md
.gitignore
```

## Existing Azure resources

This repo does not create the storage account, blob containers, Synapse/Data Factory pipeline, or batch/report-generation host. Provide those as parameters:

- Existing storage account name.
- Existing blob containers, usually `data` and `report`.
- Pipeline endpoint and pipeline name.
- Pipeline Managed Identity audience.
- Batch endpoint and batch route/name.
- Batch Managed Identity audience.

## Managed Identity permissions

The deployed Logic App uses a system-assigned managed identity. Grant that principal the minimum permissions required by your existing services:

- Pipeline service: permission to create and read pipeline runs.
  - Synapse example: role assignment that allows pipeline execution on the Synapse workspace.
  - Data Factory example: role assignment that allows creating pipeline runs on the Data Factory.
- Batch/report-generation service: allow the Logic App principal ID in the batch service's JWT or IAM allow-list.
- Storage access is normally required by the pipeline and batch service identities, not by this Logic App, unless those services require the Logic App to access blobs directly.

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
| `batchEndpoint` | Base endpoint for the batch/report-generation API, without trailing slash. |
| `batchName` | Batch route or operation name appended to `batchEndpoint`. |
| `batchAudience` | Managed Identity token audience for the batch API. |

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
    batchEndpoint='https://<batch-host>.azurewebsites.net/api' `
    batchName='report-generation/start-batch' `
    batchAudience='api://<app-registration-client-id>'
```

After deployment, assign permissions to the output `logicAppPrincipalId`.

## Notes

- No secrets, storage keys, SAS tokens, client secrets, or connection strings are used.
- The workflow uses `ManagedServiceIdentity` authentication for both Step 1 and Step 2.
- The workflow passes storage account/container names to both services so the external pipeline and batch code can use the same `data` and `report` locations.

