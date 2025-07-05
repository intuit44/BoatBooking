import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, QueryCommand, PutCommand, GetCommand } from '@aws-sdk/lib-dynamodb';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { validateRegistration, validateLogin } from '../utils/validators.js';
import { createResponse, createError } from '../utils/response.js';

// Configurar DynamoDB
const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);

const USERS_TABLE = process.env.DYNAMODB_TABLE_USERS;
const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';

// Register new user
export const register = async (event) => {
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
    const { password: _, ...userWithoutPassword } = user;
    
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
export const login = async (event) => {
  try {
    const body = JSON.parse(event.body);
    
    // Validate input
    const { error } = validateLogin(body);
    if (error) {
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

    const { Items: users } = await dynamodb.send(queryCommand);

    if (!users || users.length === 0) {
      return createError(401, 'Credenciales inválidas');
    }

    const user = users[0];

    // Check if user is active
    if (!user.active) {
      return createError(403, 'Usuario desactivado');
    }

    // Verify password
    const validPassword = await bcrypt.compare(body.password, user.password);
    if (!validPassword) {
      return createError(401, 'Credenciales inválidas');
    }

    // Update last login
    await dynamodb.send(new PutCommand({
      TableName: USERS_TABLE,
      Item: {
        ...user,
        lastLogin: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    }));

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
    const { password: _, ...userWithoutPassword } = user;
    
    return createResponse(200, {
      message: '¡Inicio de sesión exitoso!',
      token,
      refreshToken,
      user: userWithoutPassword
    });

  } catch (error) {
    console.error('Error en login:', error);
    return createError(500, 'Error al iniciar sesión');
  }
};

// Refresh token
export const refreshToken = async (event) => {
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