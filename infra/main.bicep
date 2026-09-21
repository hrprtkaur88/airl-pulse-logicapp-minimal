targetScope = 'subscription'

@description('Azure region for the Logic App resource group and workflow.')
param location string = 'westus3'

@description('Existing or new resource group where the Logic App is deployed.')
param resourceGroupName string

@description('Logic App Consumption workflow name.')
param logicAppName string = 'logic-airl-minimal'

@description('Azure Function App name that hosts function/function_app.py. The Function App infrastructure is assumed to exist.')
param reportFunctionAppName string

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

@description('Base URL of the report-generation Function App, including /api when using the default Azure Functions route prefix.')
param reportFunctionBaseUrl string

@description('Managed Identity token audience for the report-generation Function App.')
param reportFunctionAudience string

@description('Client slugs to generate reports for after the pipeline succeeds.')
param clientSlugs array = [
  'acme-corp'
  'globex-labs'
  'initech-systems'
  'umbrella-health'
  'stark-industries'
  'wayne-enterprises'
  'soylent-foods'
  'tyrell-robotics'
  'cyberdyne-io'
  'pied-piper'
]

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
    reportFunctionBaseUrl: reportFunctionBaseUrl
    reportFunctionAudience: reportFunctionAudience
    clientSlugs: clientSlugs
  }
}

output logicAppName string = logicapp.outputs.logicAppName
output logicAppPrincipalId string = logicapp.outputs.logicAppPrincipalId
output reportFunctionAppName string = reportFunctionAppName
