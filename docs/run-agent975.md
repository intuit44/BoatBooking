# run-agent975.mjs

This Node.js script demonstrates how to interact with the Azure AI Project agent used for BoatBooking.

## Configuration

The script reads `.codegpt/agents.context.json` to obtain the service endpoint and project name. Example content:

```json
{
  "version": "1.0.0",
  "agent": "Agent975",
  "endpoint": "https://boatRentalFoundry-dev.services.ai.azure.com",
  "project": "booking-agents"
}
```

## Environment variables

Authentication relies on the Azure SDK `DefaultAzureCredential`. Configure the following variables in your environment before running the script:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_SECRET`

These credentials must have access to the Azure AI Project specified in the context file.

## Usage

```bash
node run-agent975.mjs
```

The script retrieves the configured agent, creates a conversation thread and run, then prints the resulting messages to the console.
