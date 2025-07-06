exports.handler = async (event) => {
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify({
      message: "Welcome to Boat Rental API!",
      version: "1.0.0",
      stage: process.env.STAGE || "dev",
      timestamp: new Date().toISOString(),
      path: event.path,
      method: event.httpMethod
    })
  };
};
