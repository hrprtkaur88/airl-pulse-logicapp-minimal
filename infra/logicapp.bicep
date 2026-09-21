param location string
param logicAppName string
param storageAccountName string
param dataContainerName string
param reportContainerName string
param pipelineEndpoint string
param pipelineName string
param pipelineAudience string
param batchEndpoint string
param batchName string
param batchAudience string

resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: logicAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    state: 'Enabled'
    definition: loadJsonContent('workflow.json')
    parameters: {
      storageAccountName: {
        value: storageAccountName
      }
      dataContainerName: {
        value: dataContainerName
      }
      reportContainerName: {
        value: reportContainerName
      }
      pipelineEndpoint: {
        value: pipelineEndpoint
      }
      pipelineName: {
        value: pipelineName
      }
      pipelineAudience: {
        value: pipelineAudience
      }
      batchEndpoint: {
        value: batchEndpoint
      }
      batchName: {
        value: batchName
      }
      batchAudience: {
        value: batchAudience
      }
    }
  }
}

output logicAppName string = logicApp.name
output logicAppPrincipalId string = logicApp.identity.principalId

