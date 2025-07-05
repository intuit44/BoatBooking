const AWS = require('aws-sdk');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const { validateRegistration, validateLogin } = require('../utils/validators');
const { createResponse, createError } = require('../utils/response');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const USERS_TABLE = process.env.DYNAMODB_TABLE_USERS;

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
    const { Items: existingUsers } = await dynamodb.query({
      TableName: USERS_TABLE,
      IndexName: 'EmailIndex',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': body.email
      }
    }).promise();

    if (existingUsers && existingUsers.length > 0) {
      return createError(400, 'El usuario ya existe');
    }

    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(body.password, salt);

    // Create user object
    const user = {
      id: uuidv4(),
      email: body.email,
      password: hashedPassword,
      name: body.name,
      phone: body.phone,
      role: 'user',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save user to DynamoDB
    await dynamodb.put({
      TableName: USERS_TABLE,
      Item: user
    }).promise();

    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    // Return success response
    return createResponse(201, {
      message: '¡Usuario registrado exitosamente!',
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        phone: user.phone,
        role: user.role
      }
    });

  } catch (error) {
    console.error('Error en registro:', error);
    return createError(500, 'Error al registrar usuario');
  }
};

// Login user
exports.login = async (event) => {
  try {
    const body = JSON.parse(event.body);
    
    // Validate input
    const { error } = validateLogin(body);
    if (error) {
      return createError(400, error.details[0].message);
    }

    // Find user by email
    const { Items: users } = await dynamodb.query({
      TableName: USERS_TABLE,
      IndexName: 'EmailIndex',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': body.email
      }
    }).promise();

    if (!users || users.length === 0) {
      return createError(401, 'Credenciales inválidas');
    }

    const user = users[0];

    // Verify password
    const validPassword = await bcrypt.compare(body.password, user.password);
    if (!validPassword) {
      return createError(401, 'Credenciales inválidas');
    }

    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    // Return success response
    return createResponse(200, {
      message: '¡Inicio de sesión exitoso!',
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        phone: user.phone,
        role: user.role
      }
    });

  } catch (error) {
    console.error('Error en login:', error);
    return createError(500, 'Error al iniciar sesión');
  }
};

// Refresh token
exports.refreshToken = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { token } = body;

    if (!token) {
      return createError(400, 'Token no proporcionado');
    }

    // Verify existing token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Get user from database
    const { Item: user } = await dynamodb.get({
      TableName: USERS_TABLE,
      Key: { id: decoded.id }
    }).promise();

    if (!user) {
      return createError(404, 'Usuario no encontrado');
    }

    // Generate new token
    const newToken = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    return createResponse(200, {
      message: 'Token renovado exitosamente',
      token: newToken
    });

  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      return createError(401, 'Token inválido');
    }
    if (error.name === 'TokenExpiredError') {
      return createError(401, 'Token expirado');
    }
    console.error('Error en refresh token:', error);
    return createError(500, 'Error al renovar token');
  }
};