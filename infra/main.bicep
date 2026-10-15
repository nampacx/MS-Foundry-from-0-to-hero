// STARK workshop: Foundry + monitoring, deployed into an existing resource group (see infra/azd/main.bicep).
targetScope = 'resourceGroup'

param location string = resourceGroup().location
@description('Short environment name, used in resource names.')
param environment string
param principalId string = ''
param principalType string = 'User'
@description('Deploy the stark-mcp Function (chapter 06).')
param enableMcp bool = true
@description('Also deploy the models Content Understanding needs (chapter 13). Off by default: they need extra quota.')
param enableContentUnderstanding bool = false

var cfg = loadJsonContent('config/stark.json')
var deployedModels = enableContentUnderstanding ? concat(cfg.models, cfg.contentUnderstandingModels) : cfg.models
var suffix = toLower(uniqueString(subscription().id, resourceGroup().id))
var tags = { project: 'stark', 'azd-env-name': environment }

var accountName = 'stark-${take(suffix, 8)}'
var projectName = 'stark-workshop'

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    logName: 'log-stark-${environment}'
    appInsightsName: 'appi-stark-${environment}'
    tags: tags
  }
}

module foundry 'modules/foundry.bicep' = {
  name: 'foundry'
  params: {
    location: location
    accountName: accountName
    projectName: projectName
    workspaceId: monitoring.outputs.workspaceId
    appInsightsName: monitoring.outputs.appInsightsName
    models: deployedModels
    tags: tags
  }
}

module mcp 'modules/mcp-function.bicep' = if (enableMcp) {
  name: 'mcp'
  params: {
    location: location
    functionAppName: 'func-stark-mcp-${take(suffix, 8)}'
    planName: 'plan-stark-mcp-${environment}'
    storageName: 'ststark${take(suffix, 10)}'
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    tags: tags
  }
}

module rbac 'modules/rbac.bicep' = {
  name: 'rbac'
  params: {
    foundryAccountName: foundry.outputs.accountName
    workspaceName: monitoring.outputs.workspaceName
    principalId: principalId
    principalType: principalType
  }
}

output foundryAccountName string = foundry.outputs.accountName
output foundryProjectName string = foundry.outputs.projectName
output foundryProjectEndpoint string = foundry.outputs.projectEndpoint
output foundryAccountEndpoint string = foundry.outputs.accountEndpoint
output appInsightsName string = monitoring.outputs.appInsightsName
output logAnalyticsWorkspaceId string = monitoring.outputs.workspaceCustomerId
output chatModel string = cfg.chatModel
output judgeModel string = cfg.judgeModel
output fastModel string = cfg.fastModel
output embeddingModel string = cfg.embeddingModel
output mcpFunctionName string = enableMcp ? mcp!.outputs.name : ''
output mcpUrl string = enableMcp ? 'https://${mcp!.outputs.defaultHostName}/runtime/webhooks/mcp' : ''
output contentUnderstandingEnabled bool = enableContentUnderstanding
