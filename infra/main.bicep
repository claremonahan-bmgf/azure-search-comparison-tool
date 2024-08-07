targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param appServicePlanName string = 'search-comparison-tool'
param backendServiceName string = ''

param searchServiceEndpoint string // Set in main.parameters.json
param resourceGroupName string // Set in main.parameters.json
param searchInvestmentIndexPrevName string // Set in main.parameters.json
param searchInvestmentIndexCurrName string // Set in main.parameters.json

@description('Location for the OpenAI resource group')
@allowed(['canadaeast', 'eastus', 'francecentral', 'japaneast', 'northcentralus', 'southcentralus', 'westeurope'])
@metadata({
  azd: {
    type: 'location'
  }
})
param openAiResourceGroupLocation string

param embeddingDeploymentName string = 'embedding'

var abbrs = loadJsonContent('./abbreviations.json')

// tags that should be applied to all resources. CLM
var tags = { 'azd-env-name': environmentName,'application': 'search-discovery','cost-center': '10692-enterprise-data-solutions','environment': 'development','owner': 'knowledge-management' }

// Generate a unique token to be used in naming resources.
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      capacity: 1
    }
    kind: 'linux'
  }
}

// The application backend
module backend 'core/host/appservice.bicep' = {
  name: 'web'
  scope: resourceGroup
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.10'
    appCommandLine: 'python3 -m gunicorn main:app'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
  }
}



output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name

output AZURE_OPENAI_DEPLOYMENT_NAME string = embeddingDeploymentName

output AZURE_SEARCH_SERVICE_ENDPOINT string = searchServiceEndpoint
output AZURE_SEARCH_INVESTMENT_INDEX_NAME_PREV string = searchInvestmentIndexPrevName
output AZURE_SEARCH_INVESTMENT_INDEX_NAME_CURR string = searchInvestmentIndexCurrName
