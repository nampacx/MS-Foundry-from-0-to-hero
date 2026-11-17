// Optional Azure AI Search for chapter 11 (RAG): one search service, Entra ID only, connected to the Foundry project.
// Not run on a live subscription yet: check the deployment with `azd provision --preview` first.
param location string
param searchName string
param foundryAccountName string
param projectName string
param tags object

@description('basic is the smallest tier with a managed identity and an SLA. It is billed by the hour while it exists.')
param sku string = 'basic'

@description('Object id of the operator; empty = no role assignments for the operator.')
param principalId string
param principalType string

// Search Index Data Contributor (read and write documents) and Search Service Contributor (create and delete indexes)
var searchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var searchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
var searchRoleIds = [searchIndexDataContributorRoleId, searchServiceContributorRoleId]

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: account
  name: projectName
}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchName
  location: location
  tags: tags
  sku: { name: sku }
  identity: { type: 'SystemAssigned' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    disableLocalAuth: true // Entra ID only, like the Foundry account: no admin or query keys
  }
}

// The agent tool reaches the index through this connection, with the Foundry identity instead of a key.
resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  parent: project
  name: 'stark-search'
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${search.name}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: search.id
      location: location
    }
  }
}

// The operator creates the index and uploads documents from the notebook.
resource operatorRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for roleId in searchRoleIds: if (!empty(principalId)) {
  name: guid(search.id, principalId, roleId)
  scope: search
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
  }
}]

// Microsoft Learn names the Foundry account identity in the prerequisites and the project identity in the
// troubleshooting table of the Azure AI Search tool, so both get the two roles.
resource accountRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for roleId in searchRoleIds: {
  name: guid(search.id, account.id, roleId)
  scope: search
  properties: {
    principalId: account.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
  }
}]

resource projectRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for roleId in searchRoleIds: {
  name: guid(search.id, project.id, roleId)
  scope: search
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
  }
}]

output name string = search.name
output endpoint string = 'https://${search.name}.search.windows.net'
output connectionName string = searchConnection.name
