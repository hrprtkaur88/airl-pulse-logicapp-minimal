targetScope = 'subscription'

@description('Azure region for the Logic App resource group and workflow.')
param location string = 'westus3'

@description('Existing or new resource group where the Logic App is deployed.')
param resourceGroupName string

@description('Logic App Consumption workflow name.')
param logicAppName string = 'logic-airl-minimal'

@description('Existing storage account used by the pipeline and batch process.')
param storageAccountName string

@description('Blob container where the pipeline writes generated data.')
param dataContainerName string = 'data'

@description('Blob container where the batch process writes generated reports.')
param reportContainerName string = 'report'

@description('Pipeline API base endpoint without a trailing slash. Synapse example: https://<workspace>.dev.azuresynapse.net')
param pipelineEndpoint string

@description('Pipeline name to run.')
param pipelineName string

@description('Managed Identity token audience for the pipeline API.')
param pipelineAudience string = 'https://dev.azuresynapse.net/'

@description('Batch/report-generation API base endpoint without a trailing slash.')
param batchEndpoint string

@description('Batch route or operation name appended to batchEndpoint.')
param batchName string

@description('Managed Identity token audience for the batch API.')
param batchAudience string

resource rg 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: resourceGroupName
  location: location
}

module logicapp 'logicapp.bicep' = {
  scope: rg
  name: 'logicapp-${logicAppName}'
  params: {
    location: location
    logicAppName: logicAppName
    storageAccountName: storageAccountName
    dataContainerName: dataContainerName
    reportContainerName: reportContainerName
    pipelineEndpoint: pipelineEndpoint
    pipelineName: pipelineName
    pipelineAudience: pipelineAudience
    batchEndpoint: batchEndpoint
    batchName: batchName
    batchAudience: batchAudience
  }
}

output logicAppName string = logicapp.outputs.logicAppName
output logicAppPrincipalId string = logicapp.outputs.logicAppPrincipalId

