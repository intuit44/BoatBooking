const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, QueryCommand, PutCommand, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { SESClient, SendEmailCommand } = require('@aws-sdk/client-ses');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const { validateRegistration, validateLogin } = require('../utils/validators');
const { createResponse, createError } = require('../utils/response');

// Configurar DynamoDB y SES
const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);
const sesClient = new SESClient({ region: process.env.AWS_REGION || 'us-east-1' });

const USERS_TABLE = process.env.DYNAMODB_TABLE_USERS;
const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';
const FROM_EMAIL = process.env.FROM_EMAIL;

// Validar FROM_EMAIL al iniciar
if (!FROM_EMAIL) {
  console.error('ERROR: FROM_EMAIL no está configurado');
}

// Register new user
exports.register = async (event) => {
  try {
    const body = JSON.parse(event.body);
    
    // Validate input
    const { error } = validateRegistration(body);
    if (error) {
      return createError(400, error.details[0].message);
    }

    // Check if user exists
    const existingUsersCommand = new QueryCommand({
      TableName: USERS_TABLE,
      IndexName: 'EmailIndex',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': body.email
      }
    });

    const { Items: existingUsers } = await dynamodb.send(existingUsersCommand);

    if (existingUsers && existingUsers.length > 0) {
      return createError(400, 'El usuario ya existe');
    }

    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(body.password, salt);

    // Create user object
    const user = {
      id: uuidv4(),
      email: body.email.toLowerCase(), // Normalizar email
      password: hashedPassword,
      name: body.name,
      phone: body.phone,
      role: body.role || 'user',
      avatar: null,
      emailVerified: false,
      active: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save user to DynamoDB
    const putCommand = new PutCommand({
      TableName: USERS_TABLE,
      Item: user,
      ConditionExpression: 'attribute_not_exists(id)' // Evitar sobrescribir
    });

    await dynamodb.send(putCommand);

    // Generate JWT token
    const token = jwt.sign(
      { 
        id: user.id, 
        email: user.email, 
        role: user.role 
      },
      JWT_SECRET,
      { 
        expiresIn: JWT_EXPIRES_IN,
        issuer: 'boat-rental-api'
      }
    );

    // Generate refresh token (opcional)
    const refreshToken = jwt.sign(
      { 
        id: user.id,
        type: 'refresh'
      },
      JWT_SECRET,
      { 
        expiresIn: '30d'
      }
    );

    // Return success response (sin incluir password)
    const { password, ...userWithoutPassword } = user;
    delete userWithoutPassword.password;

    
    return createResponse(201, {
      message: '¡Usuario registrado exitosamente!',
      token,
      refreshToken,
      user: userWithoutPassword
    });

  } catch (error) {
    console.error('Error en registro:', error);
    
    if (error.name === 'ConditionalCheckFailedException') {
      return createError(409, 'El usuario ya existe');
    }
    
    return createError(500, 'Error al registrar usuario');
  }
};

// Login user
exports.login = async (event) => {
  try {
    console.log('🔍 LOGIN REQUEST:', {
      headers: event.headers,
      body: event.body,
      table: USERS_TABLE
    });

    const body = JSON.parse(event.body);
    console.log('📧 Email recibido:', body.email);
    console.log('🔑 Password recibido:', body.password ? '[PRESENTE]' : '[AUSENTE]');

    // Validate input
    const { error } = validateLogin(body);
    if (error) {
      console.log('❌ Error de validación:', error.details[0].message);
      return createError(400, error.details[0].message);
    }

    // Find user by email
    const queryCommand = new QueryCommand({
      TableName: USERS_TABLE,
      IndexName: 'EmailIndex',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': body.email.toLowerCase()
      }
    });

    console.log('🔍 Buscando usuario con email:', body.email.toLowerCase());
    const { Items: users } = await dynamodb.send(queryCommand);
    console.log('👥 Usuarios encontrados:', users ? users.length : 0);

    if (!users || users.length === 0) {
      console.log('❌ Usuario no encontrado en DB');
      return createError(401, 'Credenciales inválidas');
    }

    const user = users[0];
    console.log('👤 Usuario encontrado:', {
      id: user.id,
      email: user.email,
      active: user.active,
      hasPassword: !!user.password
    });

    // Check if user is active
    if (!user.active) {
      console.log('❌ Usuario desactivado');
      return createError(403, 'Usuario desactivado');
    }

    // Verify password
    console.log('🔐 Verificando contraseña...');
    const validPassword = await bcrypt.compare(body.password, user.password);
    console.log('🔐 Contraseña válida:', validPassword);
    
    if (!validPassword) {
      console.log('❌ Contraseña incorrecta');
      return createError(401, 'Credenciales inválidas');
    }

    // Generate JWT tokens
    const token = jwt.sign(
      { 
        id: user.id, 
        email: user.email, 
        role: user.role 
      },
      JWT_SECRET,
      { 
        expiresIn: JWT_EXPIRES_IN,
        issuer: 'boat-rental-api'
      }
    );

    const refreshToken = jwt.sign(
      { 
        id: user.id,
        type: 'refresh'
      },
      JWT_SECRET,
      { 
        expiresIn: '30d'
      }
    );

    // Return success response
    const { password, ...userWithoutPassword } = user;

    return createResponse(200, {
      message: '¡Inicio de sesión exitoso!',
      token,
      refreshToken,
      user: userWithoutPassword
    });

    console.log('✅ Login exitoso para:', user.email);

  } catch (error) {
    console.error('❌ Error crítico en login:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    }); 
    return createError(500, 'Error al iniciar sesión');
  }
};

// Refresh token
exports.refreshToken = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { refreshToken } = body;

    if (!refreshToken) {
      return createError(400, 'Refresh token no proporcionado');
    }

    // Verify refresh token
    let decoded;
    try {
      decoded = jwt.verify(refreshToken, JWT_SECRET);
      
      if (decoded.type !== 'refresh') {
        return createError(401, 'Token inválido');
      }
    } catch (error) {
      if (error.name === 'TokenExpiredError') {
        return createError(401, 'Refresh token expirado');
      }
      return createError(401, 'Token inválido');
    }

    // Get user from database
    const getCommand = new GetCommand({
      TableName: USERS_TABLE,
      Key: { id: decoded.id }
    });

    const { Item: user } = await dynamodb.send(getCommand);

    if (!user) {
      return createError(404, 'Usuario no encontrado');
    }

    if (!user.active) {
      return createError(403, 'Usuario desactivado');
    }

    // Generate new tokens
    const newToken = jwt.sign(
      { 
        id: user.id, 
        email: user.email, 
        role: user.role 
      },
      JWT_SECRET,
      { 
        expiresIn: JWT_EXPIRES_IN,
        issuer: 'boat-rental-api'
      }
    );

    const newRefreshToken = jwt.sign(
      { 
        id: user.id,
        type: 'refresh'
      },
      JWT_SECRET,
      { 
        expiresIn: '30d'
      }
    );

    return createResponse(200, {
      message: 'Token renovado exitosamente',
      token: newToken,
      refreshToken: newRefreshToken
    });

  } catch (error) {
    console.error('Error en refresh token:', error);
    return createError(500, 'Error al renovar token');
  }
};

// Send verification code
exports.sendVerificationCode = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { email } = body;

    if (!email) {
      return createError(400, 'Email es requerido');
    }

    if (!FROM_EMAIL) {
      return createError(500, 'Configuración de email no disponible');
    }

    // Verificar si el usuario existe
    const queryCommand = new QueryCommand({
      TableName: USERS_TABLE,
      IndexName: 'EmailIndex',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': email.toLowerCase()
      }
    });

    const { Items: users } = await dynamodb.send(queryCommand);
    if (!users || users.length === 0) {
      return createError(404, 'Usuario no encontrado');
    }

    const user = users[0];
    
    // Generar código de 6 dígitos
    const verificationCode = Math.floor(100000 + Math.random() * 900000).toString();
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000).toISOString(); // 15 minutos

    // Guardar código en DynamoDB
    const updateCommand = new UpdateCommand({
      TableName: USERS_TABLE,
      Key: { id: user.id },
      UpdateExpression: 'SET verificationCode = :code, codeExpiresAt = :expires',
      ExpressionAttributeValues: {
        ':code': verificationCode,
        ':expires': expiresAt
      }
    });

    await dynamodb.send(updateCommand);

    // Enviar email con SES
    const emailParams = {
      Source: FROM_EMAIL,
      Destination: {
        ToAddresses: [email]
      },
      Message: {
        Subject: {
          Data: 'Código de Verificación - BoatRental Venezuela',
          Charset: 'UTF-8'
        },
        Body: {
          Text: {
            Data: `Tu código de verificación es: ${verificationCode}\n\nEste código expira en 15 minutos.`,
            Charset: 'UTF-8'
          },
          Html: {
            Data: `
              <h2>Código de Verificación</h2>
              <p>Tu código de verificación es:</p>
              <h1 style="color: #007bff; font-size: 32px;">${verificationCode}</h1>
              <p>Este código expira en 15 minutos.</p>
              <p>Si no solicitaste este código, ignora este email.</p>
            `,
            Charset: 'UTF-8'
          }
        }
      }
    };

    await sesClient.send(new SendEmailCommand(emailParams));

    return createResponse(200, {
      message: 'Código de verificación enviado exitosamente'
    });

  } catch (error) {
    console.error('Error enviando código:', error);
    return createError(500, 'Error al enviar código de verificación');
  }
};

// Reset password with verification code
exports.resetPassword = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { email, verificationCode, newPassword } = body;

    if (!email || !verificationCode || !newPassword) {
      return createError(400, 'Email, código y nueva contraseña son requeridos');
    }

    // Buscar usuario
    const queryCommand = new QueryCommand({
      TableName: USERS_TABLE,
      IndexName: 'EmailIndex',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': email.toLowerCase()
      }
    });

    const { Items: users } = await dynamodb.send(queryCommand);
    if (!users || users.length === 0) {
      return createError(404, 'Usuario no encontrado');
    }

    const user = users[0];

    // Verificar código
    if (!user.verificationCode || user.verificationCode !== verificationCode) {
      return createError(400, 'Código de verificación inválido');
    }

    // Verificar expiración
    if (!user.codeExpiresAt || new Date() > new Date(user.codeExpiresAt)) {
      return createError(400, 'Código de verificación expirado');
    }

    // Hash nueva contraseña
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(newPassword, salt);

    // Actualizar contraseña y limpiar código
    const updateCommand = new UpdateCommand({
      TableName: USERS_TABLE,
      Key: { id: user.id },
      UpdateExpression: 'SET password = :password REMOVE verificationCode, codeExpiresAt',
      ExpressionAttributeValues: {
        ':password': hashedPassword
      }
    });

    await dynamodb.send(updateCommand);

    return createResponse(200, {
      message: 'Contraseña actualizada exitosamente'
    });

  } catch (error) {
    console.error('Error reseteando contraseña:', error);
    return createError(500, 'Error al resetear contraseña');
  }
};