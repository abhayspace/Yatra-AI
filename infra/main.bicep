// Yatra AI on Azure Container Apps.
// Two container apps (FastAPI backend, Next.js frontend) behind public ingress, images in Azure Container
// Registry, and the two secrets (Azure AI Foundry API key, Supabase service role key) held in Key Vault and
// injected as Container Apps secrets that reference Key Vault. No secret value appears in this file.
targetScope = 'subscription'

@minLength(1)
@maxLength(32)
@description('Name of the azd environment; used to derive resource names.')
param environmentName string

@description('Azure region for all resources.')
param location string

@description('Azure AI Foundry endpoint (project or resource URL). Not a secret.')
param azureAiFoundryEndpoint string

@description('Name of the Claude Sonnet deployment in the Foundry project.')
param azureAiFoundryDeploymentName string

@secure()
@description('Azure AI Foundry API key. Stored in Key Vault.')
param azureAiFoundryApiKey string

@description('Supabase project URL. Not a secret.')
param supabaseUrl string

@secure()
@description('Supabase service role key. Stored in Key Vault; only the backend ever receives it.')
param supabaseServiceRoleKey string

@description('Backend image, set by azd after it builds and pushes. Empty on the first provision.')
param backendImageName string = ''

@description('Frontend image, set by azd after it builds and pushes. Empty on the first provision.')
param frontendImageName string = ''

var tags = { 'azd-env-name': environmentName, app: 'yatra-ai' }

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    environmentName: environmentName
    location: location
    tags: tags
    azureAiFoundryEndpoint: azureAiFoundryEndpoint
    azureAiFoundryDeploymentName: azureAiFoundryDeploymentName
    azureAiFoundryApiKey: azureAiFoundryApiKey
    supabaseUrl: supabaseUrl
    supabaseServiceRoleKey: supabaseServiceRoleKey
    backendImageName: backendImageName
    frontendImageName: frontendImageName
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.registryLoginServer
output AZURE_KEY_VAULT_NAME string = resources.outputs.keyVaultName
output BACKEND_URI string = resources.outputs.backendUri
output FRONTEND_URI string = resources.outputs.frontendUri
