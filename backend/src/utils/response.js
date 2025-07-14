// Crear respuesta exitosa con CORS headers
const createResponse = (statusCode, body) => {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': process.env.CORS_ORIGIN || '*',
      'Access-Control-Allow-Credentials': true,
      'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
      'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE,PATCH'
    },
    body: JSON.stringify(body)
  };
};

// Crear respuesta de error
const createError = (statusCode, message, details = null) => {
  const errorBody = {
    error: true,
    message,
    timestamp: new Date().toISOString()
  };

  if (details) {
    errorBody.details = details;
  }

  return createResponse(statusCode, errorBody);
};

module.exports = {
  createResponse,
  createError
};