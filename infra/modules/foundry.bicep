// Microsoft Foundry: one AIServices account (models + Foundry Tools such as Document Intelligence),
// one project (agents, datasets, evaluations) and the Application Insights connection that powers tracing.
param location string
param accountName string
param projectName string
param workspaceId string
param appInsightsName string
param tags object

@description('Each item: { name, model, version, format, sku, capacity }')
param models array

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  tags: tags
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true // Entra ID only: notebooks use DefaultAzureCredential
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: account
  name: projectName
  location: location
  identity: { type: 'SystemAssigned' }
  tags: tags
  properties: {
    displayName: 'Stark Workshop'
    description: 'Foundry from 0 to hero: tutorial project'
  }
}

// Deployments must be created one after the other on the same account.
@batchSize(1)
resource deployments 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = [for m in models: {
  parent: account
  name: m.name
  dependsOn: [project]
  sku: {
    name: m.sku
    capacity: m.capacity
  }
  properties: {
    model: {
      format: m.format
      name: m.model
      version: m.version
    }
  }
}]

resource appi 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// Connecting Application Insights to the project turns on the "Traces" and "Monitor" views in the portal.
resource appInsightsConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  parent: project
  name: 'appinsights'
  dependsOn: [deployments]
  properties: {
    category: 'AppInsights'
    target: appi.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: appi.properties.ConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appi.id
    }
  }
}

resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: account
  dependsOn: [deployments]
  properties: {
    workspaceId: workspaceId
    logs: [
      { categoryGroup: 'allLogs', enabled: true }
    ]
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}

output accountName string = account.name
output accountId string = account.id
output projectName string = project.name
output projectId string = project.id
output projectEndpoint string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
output accountEndpoint string = 'https://${account.name}.cognitiveservices.azure.com'
