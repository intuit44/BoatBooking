module.exports = async function (context) {
  console.log('Input:', JSON.stringify(context.request.body, null, 2));
  return {
    statusCode: 200,
    body: {
      message: 'Boat function executed successfully',
      timestamp: new Date().toISOString()
    }
  };
};
