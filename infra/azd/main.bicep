// azd entry point (subscription scope): creates the resource group and deploys ../main.bicep into it.
targetScope = 'subscription'

@minLength(1)
@maxLength(32)
@description('azd environment name, e.g. "dev". Becomes the resource group `rg-stark-<environmentName>`.')
param environmentName string

@description('Azure region. Pick one that offers the models in infra/config/stark.json (default: swedencentral).')
param location string

@description('Signed-in azd user (AZURE_PRINCIPAL_ID): gets the Foundry and Log Analytics roles for the notebooks.')
param principalId string = ''

@description('Type of principalId (AZURE_PRINCIPAL_TYPE).')
param principalType string = 'User'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-stark-${environmentName}'
  location: location
  tags: {
    project: 'stark'
    'azd-env-name': environmentName
  }
}

module stark '../main.bicep' = {
  name: 'stark'
  scope: rg
  params: {
    location: location
    environment: environmentName
    principalId: principalId
    principalType: principalType
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output STARK_FOUNDRY_ACCOUNT string = stark.outputs.foundryAccountName
output STARK_FOUNDRY_PROJECT string = stark.outputs.foundryProjectName
output STARK_PROJECT_ENDPOINT string = stark.outputs.foundryProjectEndpoint
output STARK_ACCOUNT_ENDPOINT string = stark.outputs.foundryAccountEndpoint
output STARK_APPINSIGHTS string = stark.outputs.appInsightsName
output STARK_LOG_WORKSPACE_ID string = stark.outputs.logAnalyticsWorkspaceId
output STARK_CHAT_MODEL string = stark.outputs.chatModel
output STARK_JUDGE_MODEL string = stark.outputs.judgeModel
output STARK_FAST_MODEL string = stark.outputs.fastModel
output STARK_EMBEDDING_MODEL string = stark.outputs.embeddingModel
