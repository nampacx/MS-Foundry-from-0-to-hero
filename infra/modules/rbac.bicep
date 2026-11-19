// The workshop operator (the signed-in azd user) gets the data-plane roles the notebooks need.
// The project's managed identity gets read access to Application Insights for trace evaluations.
param foundryAccountName string
param workspaceName string
param appInsightsName string

@description('Object id of the project managed identity (reads traces for trace evaluations).')
param projectPrincipalId string

@description('Object id of the operator; empty = no role assignments.')
param principalId string
param principalType string

// Azure AI User (Foundry projects/agents/evaluations data plane)
var azureAiUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
// Cognitive Services User (Foundry Tools: Document Intelligence, Content Understanding, Vision)
var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'
// Log Analytics Reader (KQL in the notebooks)
var logAnalyticsReaderRoleId = '73c42c96-874c-492b-b04d-ab87d138a893'
// Reader (trace evaluations: the service queries Application Insights as the project identity)
var readerRoleId = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource aiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(account.id, principalId, azureAiUserRoleId)
  scope: account
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleId)
  }
}

resource csUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(account.id, principalId, cognitiveServicesUserRoleId)
  scope: account
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
  }
}

resource logReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(workspace.id, principalId, logAnalyticsReaderRoleId)
  scope: workspace
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', logAnalyticsReaderRoleId)
  }
}

// Trace evaluations (chapter 12) run a resource-context query on Application Insights as the project identity.
resource projectTraceReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, projectPrincipalId, readerRoleId)
  scope: appInsights
  properties: {
    principalId: projectPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', readerRoleId)
  }
}
