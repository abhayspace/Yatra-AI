targetScope = 'resourceGroup'

param environmentName string
param location string
param tags object
param azureAiFoundryEndpoint string
param azureAiFoundryDeploymentName string
@secure()
param azureAiFoundryApiKey string
param supabaseUrl string
@secure()
param supabaseServiceRoleKey string
param backendImageName string
param frontendImageName string

var token = toLower(uniqueString(subscription().id, environmentName, location))
var placeholderImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
var backendAppName = 'ca-backend-${take(token, 8)}'
var frontendAppName = 'ca-frontend-${take(token, 8)}'

// well-known built-in role definition ids
var acrPullRole = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var keyVaultSecretsUserRole = '4633458b-17de-408a-b874-0445c86b69e6'

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${token}'
  location: location
  tags: tags
}

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${token}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'cr${token}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, acrPullRole)
  scope: registry
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRole)
  }
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${take(token, 16)}'
  location: location
  tags: tags
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

resource foundryKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'azure-ai-foundry-api-key'
  properties: { value: azureAiFoundryApiKey }
}

resource supabaseKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'supabase-service-role-key'
  properties: { value: supabaseServiceRoleKey }
}

resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, identity.id, keyVaultSecretsUserRole)
  scope: vault
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRole)
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${token}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

// Container app hostnames are <app-name>.<environment default domain>, so each app can reference the
// other's public URL without a circular dependency.
var backendUrl = 'https://${backendAppName}.${environment.properties.defaultDomain}'
var frontendUrl = 'https://${frontendAppName}.${environment.properties.defaultDomain}'

resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: backendAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  dependsOn: [acrPull, kvSecretsUser]
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true // the browser calls the API (REST + WebSocket) directly
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        { server: registry.properties.loginServer, identity: identity.id }
      ]
      secrets: [
        { name: 'foundry-api-key', keyVaultUrl: foundryKeySecret.properties.secretUri, identity: identity.id }
        { name: 'supabase-service-role-key', keyVaultUrl: supabaseKeySecret.properties.secretUri, identity: identity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: empty(backendImageName) ? placeholderImage : backendImageName
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'AZURE_AI_FOUNDRY_ENDPOINT', value: azureAiFoundryEndpoint }
            { name: 'AZURE_AI_FOUNDRY_DEPLOYMENT_NAME', value: azureAiFoundryDeploymentName }
            { name: 'AZURE_AI_FOUNDRY_API_KEY', secretRef: 'foundry-api-key' }
            { name: 'SUPABASE_URL', value: supabaseUrl }
            { name: 'SUPABASE_SERVICE_ROLE_KEY', secretRef: 'supabase-service-role-key' }
            { name: 'CORS_ORIGINS', value: frontendUrl }
            { name: 'MAX_GRAPH_STEPS', value: '30' }
          ]
          probes: [
            { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 20 }
            { type: 'Readiness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 10 }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          { name: 'http', http: { metadata: { concurrentRequests: '30' } } }
        ]
      }
    }
  }
}

resource frontend 'Microsoft.App/containerApps@2024-03-01' = {
  name: frontendAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'frontend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  dependsOn: [acrPull]
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true // the public entry point
        targetPort: 3000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        { server: registry.properties.loginServer, identity: identity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: empty(frontendImageName) ? placeholderImage : frontendImageName
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            // read by the frontend at start-up (app/api/runtime-config), not baked into the bundle
            { name: 'API_URL', value: backendUrl }
          ]
          probes: [
            { type: 'Liveness', httpGet: { path: '/api/runtime-config', port: 3000 }, periodSeconds: 20 }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          { name: 'http', http: { metadata: { concurrentRequests: '50' } } }
        ]
      }
    }
  }
}

output registryLoginServer string = registry.properties.loginServer
output keyVaultName string = vault.name
output backendUri string = backendUrl
output frontendUri string = frontendUrl
