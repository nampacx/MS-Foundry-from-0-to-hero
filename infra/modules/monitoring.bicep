// The lab instruments: Log Analytics + Application Insights (Foundry traces land here).
param location string
param logName string
param appInsightsName string
param tags object

resource log 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logName
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: log.id
  }
}

output workspaceId string = log.id
output workspaceName string = log.name
output workspaceCustomerId string = log.properties.customerId
output appInsightsId string = appi.id
output appInsightsName string = appi.name
output appInsightsConnectionString string = appi.properties.ConnectionString
