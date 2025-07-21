const { app } = require('@azure/functions');
const { SecretClient } = require('@azure/keyvault-secrets');
const { DefaultAzureCredential } = require('@azure/identity');
const { BlobServiceClient } = require('@azure/storage-blob');
const { TableClient } = require('@azure/data-tables');
const { Octokit } = require('@octokit/rest');


// Initialize Azure clients
const credential = new DefaultAzureCredential();
const keyVaultName = process.env.KEYVAULT_NAME;
const kvUri = keyVaultName ? `https://${keyVaultName}.vault.azure.net` : null;
const secretClient = kvUri ? new SecretClient(kvUri, credential) : null;

// Storage configuration
const storageConnectionString = process.env.AzureWebJobsStorage || 'UseDevelopmentStorage=true';
const blobServiceClient = BlobServiceClient.fromConnectionString(storageConnectionString);
const tableClient = TableClient.fromConnectionString(storageConnectionString, 'analysisresults');

// GitHub client (initialized on demand)
let octokitClient = null;

// Helper function to return JSON responses
function jsonResponse(data, status = 200) {
  return {
    status,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  };
}

// Helper function to return error responses
function errorResponse(message, status = 500) {
  return {
    status,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ error: message })
  };
}

// 1. Read TSX Source - Ya existente
app.http('readTsxSource', {
  methods: ['GET', 'POST'],
  authLevel: 'anonymous',
  handler: async (request, context) => {
    context.log(`Http readTsxSource called: "${request.url}"`);
    const name = request.query.get('name') || await request.text() || 'world';
    return { body: `Hello, ${name}!` };
  }
});

// 2. Get Secret from Key Vault
app.http('getSecretFromKeyVault', {
  methods: ['GET', 'POST'],
  authLevel: 'function',
  handler: async (request, context) => {
    context.log('Getting secret from Key Vault');

    if (!secretClient) {
      return errorResponse('Key Vault not configured. Please set KEYVAULT_NAME in environment variables.', 500);
    }

    try {
      const secretName = request.query.get('secretName') || (await request.json()).secretName;

      if (!secretName) {
        return errorResponse('Please provide a secretName parameter', 400);
      }

      const secret = await secretClient.getSecret(secretName);

      return jsonResponse({
        name: secret.name,
        value: secret.value,
        version: secret.properties.version
      });
    } catch (error) {
      context.log.error('Error getting secret:', error);
      return errorResponse(`Error getting secret: ${error.message}`);
    }
  }
});

// 3. List Repository Files
app.http('listRepoFiles', {
  methods: ['GET', 'POST'],
  authLevel: 'function',
  handler: async (request, context) => {
    context.log('Listing repository files');

    try {
      const body = request.query.get('owner') ?
        { owner: request.query.get('owner'), repo: request.query.get('repo'), path: request.query.get('path') || '' } :
        await request.json();

      const { owner, repo, path = '', githubToken } = body;

      if (!owner || !repo) {
        return errorResponse('Please provide owner and repo parameters', 400);
      }

      // Initialize Octokit with token if provided
      if (githubToken || process.env.GITHUB_TOKEN) {
        octokitClient = new Octokit({
          auth: githubToken || process.env.GITHUB_TOKEN
        });
      } else {
        octokitClient = new Octokit();
      }

      const response = await octokitClient.repos.getContent({
        owner,
        repo,
        path
      });

      // Filter for specific file types
      const allowedExtensions = ['.tsx', '.ts', '.json', '.graphql', '.js', '.jsx'];
      const files = Array.isArray(response.data) ?
        response.data.filter(item => {
          if (item.type === 'dir') return true;
          return allowedExtensions.some(ext => item.name.endsWith(ext));
        }) :
        [response.data];

      return jsonResponse({
        files: files.map(file => ({
          name: file.name,
          path: file.path,
          type: file.type,
          size: file.size,
          sha: file.sha,
          download_url: file.download_url
        }))
      });
    } catch (error) {
      context.log.error('Error listing repo files:', error);
      return errorResponse(`Error listing repository files: ${error.message}`);
    }
  }
});

// 4. Read File from Storage
app.http('readFileFromStorage', {
  methods: ['GET', 'POST'],
  authLevel: 'function',
  handler: async (request, context) => {
    context.log('Reading file from storage');

    try {
      const filePath = request.query.get('filePath') || (await request.json()).filePath;

      if (!filePath) {
        return errorResponse('Please provide a filePath parameter', 400);
      }

      // Parse container and blob name from path
      const pathParts = filePath.split('/').filter(p => p);
      const containerName = pathParts[0] || 'tsx-files';
      const blobName = pathParts.slice(1).join('/');

      const containerClient = blobServiceClient.getContainerClient(containerName);
      const blobClient = containerClient.getBlobClient(blobName);

      const exists = await blobClient.exists();
      if (!exists) {
        return errorResponse(`File not found: ${filePath}`, 404);
      }

      const downloadResponse = await blobClient.download();
      const content = await streamToBuffer(downloadResponse.readableStreamBody);

      return jsonResponse({
        path: filePath,
        content: content.toString('utf-8'),
        properties: downloadResponse.properties
      });
    } catch (error) {
      context.log.error('Error reading file:', error);
      return errorResponse(`Error reading file: ${error.message}`);
    }
  }
});

// 5. Save Analysis Result
app.http('saveAnalysisResult', {
  methods: ['POST'],
  authLevel: 'function',
  handler: async (request, context) => {
    context.log('Saving analysis result');

    try {
      const body = await request.json();
      const {
        analysisType,
        targetFile,
        result,
        suggestions,
        metadata
      } = body;

      if (!analysisType || !result) {
        return errorResponse('Please provide analysisType and result', 400);
      }

      // Create table if it doesn't exist
      await tableClient.createTable();

      // Create entity
      const entity = {
        partitionKey: analysisType,
        rowKey: `${Date.now()}_${Math.random().toString(36).substring(7)}`,
        timestamp: new Date().toISOString(),
        targetFile: targetFile || '',
        result: JSON.stringify(result),
        suggestions: JSON.stringify(suggestions || []),
        metadata: JSON.stringify(metadata || {}),
        status: 'completed'
      };

      await tableClient.createEntity(entity);

      // Also save to blob storage for larger content
      if (result.length > 32000) { // Table storage has limits
        const containerClient = blobServiceClient.getContainerClient('analysis-results');
        await containerClient.createIfNotExists();

        const blobName = `${analysisType}/${entity.rowKey}.json`;
        const blockBlobClient = containerClient.getBlockBlobClient(blobName);

        await blockBlobClient.upload(
          JSON.stringify(body),
          Buffer.byteLength(JSON.stringify(body))
        );

        entity.blobPath = blobName;
        await tableClient.updateEntity(entity, 'Merge');
      }

      return jsonResponse({
        message: 'Analysis result saved successfully',
        id: entity.rowKey,
        partitionKey: entity.partitionKey
      });
    } catch (error) {
      context.log.error('Error saving analysis:', error);
      return errorResponse(`Error saving analysis result: ${error.message}`);
    }
  }
});

// 6. Run Refactor Task
app.http('runRefactorTask', {
  methods: ['POST'],
  authLevel: 'function',
  handler: async (request, context) => {
    context.log('Running refactor task');

    try {
      const body = await request.json();
      const {
        taskType,
        targetFile,
        instructions,
        parameters,
        outputPath
      } = body;

      if (!taskType || !instructions) {
        return errorResponse('Please provide taskType and instructions', 400);
      }

      // This is a placeholder for actual refactoring logic
      // In a real implementation, this would:
      // 1. Read the target file
      // 2. Apply the refactoring based on instructions
      // 3. Save the result
      // 4. Return the status

      const taskId = `task_${Date.now()}_${Math.random().toString(36).substring(7)}`;

      // Save task to table storage
      await tableClient.createTable();

      const taskEntity = {
        partitionKey: 'refactorTasks',
        rowKey: taskId,
        timestamp: new Date().toISOString(),
        taskType,
        targetFile: targetFile || '',
        instructions: JSON.stringify(instructions),
        parameters: JSON.stringify(parameters || {}),
        outputPath: outputPath || '',
        status: 'pending'
      };

      await tableClient.createEntity(taskEntity);

      // In a real implementation, you would queue this task
      // For now, we'll just return the task ID

      return jsonResponse({
        message: 'Refactor task created successfully',
        taskId,
        status: 'pending',
        estimatedCompletionTime: new Date(Date.now() + 5 * 60 * 1000).toISOString()
      });
    } catch (error) {
      context.log.error('Error creating refactor task:', error);
      return errorResponse(`Error creating refactor task: ${error.message}`);
    }
  }
});

// 7. Get Task Status
app.http('getTaskStatus', {
  methods: ['GET'],
  authLevel: 'function',
  handler: async (request, context) => {
    const taskId = request.query.get('taskId');

    if (!taskId) {
      return {
        status: 400,
        body: 'Please provide a taskId parameter'
      };
    }

    try {
      const entity = await tableClient.getEntity('refactorTasks', taskId);

      return {
        status: 200,
        jsonBody: {
          taskId: entity.rowKey,
          status: entity.status,
          taskType: entity.taskType,
          targetFile: entity.targetFile,
          timestamp: entity.timestamp,
          result: entity.result ? JSON.parse(entity.result) : null
        }
      };
    } catch (error) {
      if (error.statusCode === 404) {
        return {
          status: 404,
          body: 'Task not found'
        };
      }

      return {
        status: 500,
        body: `Error getting task status: ${error.message}`
      };
    }
  }
});

// 8. Read File from GitHub
// 8. Read File from GitHub
app.http('readFileFromGit', {
  methods: ['GET', 'POST'],
  authLevel: 'function',
  handler: async (request, context) => {
    context.log('Reading file from GitHub');

    try {
      // Support both GET and POST
      const owner = request.query.get('owner');
      const repo = request.query.get('repo');
      const path = request.query.get('path');
      const branch = request.query.get('branch');

      let params = { owner, repo, path, branch };

      // If not in query params, try body
      if (!owner || !repo || !path) {
        const body = await request.json().catch(() => ({}));
        params = { ...params, ...body };
      }

      if (!params.owner || !params.repo || !params.path) {
        return errorResponse('Missing owner, repo or path parameters', 400);
      }

      // Default to main branch if not specified
      const targetBranch = params.branch || 'main';

      // Try main first, then master if it fails
      let url = `https://raw.githubusercontent.com/${params.owner}/${params.repo}/${targetBranch}/${params.path}`;
      let response;

      try {
        response = await fetch(url);
        if (!response.ok && targetBranch === 'main') {
          // Try master branch
          url = `https://raw.githubusercontent.com/${params.owner}/${params.repo}/master/${params.path}`;
          response = await fetch(url);
        }
      } catch (fetchError) {
        throw new Error(`Network error: ${fetchError.message}`);
      }

      if (!response.ok) {
        return errorResponse(`File not found: ${response.status} ${response.statusText}`, 404);
      }

      const content = await response.text();

      return jsonResponse({
        filename: params.path.split('/').pop(),
        path: params.path,
        owner: params.owner,
        repo: params.repo,
        branch: targetBranch,
        content: content,
        url: url
      });

    } catch (error) {
      context.log.error('Error fetching file from GitHub:', error);
      return errorResponse(`Failed to fetch file: ${error.message}`);
    }
  }
});

// Helper function to convert stream to buffer
async function streamToBuffer(readableStream) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    readableStream.on('data', (data) => {
      chunks.push(data instanceof Buffer ? data : Buffer.from(data));
    });
    readableStream.on('end', () => {
      resolve(Buffer.concat(chunks));
    });
    readableStream.on('error', reject);
  });
}