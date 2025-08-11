$key = az cognitiveservices account keys list -g boat-rental-app-group -n boatRentalFoundry-dev --query key1 -o tsv

az functionapp config appsettings set `
  --name "copiloto-semantico-func" `
  --resource-group "boat-rental-app-group" `
  --settings `
    AZURE_OPENAI_ENDPOINT="https://boatRentalFoundry-dev.openai.azure.com" `
    AZURE_OPENAI_KEY="$key" `
    WORKSPACE_NAME="boatRentalMLWorkspaceV2" `
    RESOURCE_GROUP="boat-rental-app-group" `
    APP_INSIGHTS_NAME="boatRentalInsights" `
    PROJECT_ROOT="/home/site/wwwroot" `
    MLFLOW_TRACKING_URI="azureml://eastus.api.azureml.ms/mlflow/v1.0/subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group/providers/Microsoft.MachineLearningServices/workspaces/boatRentalMLWorkspaceV2" `
    AI_AGENT_ID="Agent975" `
    AI_PROJECT_ID="booking-agents"
