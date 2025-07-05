// Create success response
exports.createResponse = (statusCode, body) => {
  return {
    statusCode,
    headers: {
      'Access-Control-Allow-Origin': process.env.CORS_ORIGIN || '*',
      'Access-Control-Allow-Credentials': true,
    },
    body: JSON.stringify(body)
  };
};

// Create error response
exports.createError = (statusCode, message) => {
  return {
    statusCode,
    headers: {
      'Access-Control-Allow-Origin': process.env.CORS_ORIGIN || '*',
      'Access-Control-Allow-Credentials': true,
    },
    body: JSON.stringify({
      error: message
    })
  };
};