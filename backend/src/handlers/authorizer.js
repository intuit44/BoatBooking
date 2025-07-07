const jwt = require('jsonwebtoken');
const AWS = require('aws-sdk');
const { generatePolicy } = require('./policy.js');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const USERS_TABLE = process.env.DYNAMODB_TABLE_USERS;

// Generate IAM policy
const generatePolicy = (principalId, effect, resource, user) => {
  const authResponse = {
    principalId
  };

  if (effect && resource) {
    const policyDocument = {
      Version: '2012-10-17',
      Statement: [{
        Action: 'execute-api:Invoke',
        Effect: effect,
        Resource: resource
      }]
    };
    authResponse.policyDocument = policyDocument;
  }

  // Include user info in context
  if (user) {
    authResponse.context = {
      user: JSON.stringify(user)
    };
  }

  return authResponse;
};

// Authorizer handler
export const handler = async (event) => {
  try {
    // Get token from Authorization header
    const token = event.authorizationToken;
    if (!token) {
      throw new Error('No token provided');
    }

    // Verify JWT token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Get user from database
    const { Item: user } = await dynamodb.get({
      TableName: USERS_TABLE,
      Key: { id: decoded.id }
    }).promise();

    if (!user) {
      throw new Error('User not found');
    }

    // Generate policy
    return generatePolicy(
      decoded.id, 
      'Allow', 
      event.methodArn, 
      {
        id: user.id,
        email: user.email,
        role: user.role,
        name: user.name
      }
    );

  } catch (error) {
    console.error('Authorization error:', error);

    if (error.name === 'JsonWebTokenError') {
      return generatePolicy('user', 'Deny', event.methodArn);
    }

    if (error.name === 'TokenExpiredError') {
      return generatePolicy('user', 'Deny', event.methodArn);
    }

    throw error;
  }
};