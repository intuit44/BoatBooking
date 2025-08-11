const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand } = require('@aws-sdk/lib-dynamodb');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');

const client = new DynamoDBClient({ region: 'us-east-1' });
const dynamodb = DynamoDBDocumentClient.from(client);

async function createDemoUser() {
  try {
    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash('demo123456', salt);

    // Create demo user
    const demoUser = {
      id: uuidv4(),
      email: 'demo@boatrental.ve',
      password: hashedPassword,
      name: 'Usuario Demo',
      phone: '+584141234567',
      role: 'user',
      avatar: null,
      emailVerified: true,
      active: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const putCommand = new PutCommand({
      TableName: 'boat-rental-backend-prod-users',
      Item: demoUser
    });

    await dynamodb.send(putCommand);
    
    console.log('✅ Usuario demo creado exitosamente:');
    console.log('Email: demo@boatrental.ve');
    console.log('Password: demo123456');
    console.log('ID:', demoUser.id);

  } catch (error) {
    console.error('❌ Error creando usuario demo:', error);
  }
}

createDemoUser();