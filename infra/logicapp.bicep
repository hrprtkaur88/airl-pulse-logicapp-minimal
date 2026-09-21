param location string
param logicAppName string
param storageAccountName string
param dataContainerName string
param reportContainerName string
param pipelineEndpoint string
param pipelineName string
param pipelineAudience string
param reportFunctionBaseUrl string
param reportFunctionAudience string
param clientSlugs array

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
      reportFunctionBaseUrl: {
        value: reportFunctionBaseUrl
      }
      reportFunctionAudience: {
        value: reportFunctionAudience
      }
      clientSlugs: {
        value: clientSlugs
      }
    }
  }
}

output logicAppName string = logicApp.name
output logicAppPrincipalId string = logicApp.identity.principalId
