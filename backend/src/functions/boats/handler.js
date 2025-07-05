export const handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  return {
    statusCode: 200,
    body: JSON.stringify({
      message: 'Boat function executed successfully',
      timestamp: new Date().toISOString()
    })
  };
};