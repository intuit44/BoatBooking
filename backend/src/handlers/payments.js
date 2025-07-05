const AWS = require('aws-sdk');
const { validatePayment } = require('../utils/validators');
const { createResponse, createError } = require('../utils/response');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const BOOKINGS_TABLE = process.env.DYNAMODB_TABLE_BOOKINGS;

// Process payment
exports.processPayment = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { user } = event.requestContext.authorizer;

    // Validate input
    const { error } = validatePayment(body);
    if (error) {
      return createError(400, error.details[0].message);
    }

    // Get booking
    const { Item: booking } = await dynamodb.get({
      TableName: BOOKINGS_TABLE,
      Key: { id: body.bookingId }
    }).promise();

    if (!booking) {
      return createError(404, 'Reserva no encontrada');
    }

    // Check authorization
    if (user.role !== 'admin' && user.id !== booking.userId) {
      return createError(403, 'No tienes permisos para procesar este pago');
    }

    // Check if payment is already processed
    if (booking.paymentStatus === 'paid') {
      return createError(400, 'El pago ya ha sido procesado');
    }

    // Process payment based on method
    let paymentResult;
    switch (body.paymentMethod) {
      case 'zelle':
        paymentResult = await processZellePayment(body);
        break;
      case 'pago_movil':
        paymentResult = await processPagoMovilPayment(body);
        break;
      case 'binance':
        paymentResult = await processBinancePayment(body);
        break;
      case 'cash':
        paymentResult = await processCashPayment(body);
        break;
      default:
        return createError(400, 'Método de pago no válido');
    }

    // Update booking with payment info
    const updatedBooking = {
      ...booking,
      paymentStatus: paymentResult.status,
      paymentReference: body.referenceNumber,
      paymentData: body.paymentData,
      paymentProcessedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // If payment is successful, confirm booking
    if (paymentResult.status === 'paid') {
      updatedBooking.bookingStatus = 'confirmed';
    }

    await dynamodb.put({
      TableName: BOOKINGS_TABLE,
      Item: updatedBooking
    }).promise();

    return createResponse(200, {
      message: paymentResult.message,
      booking: updatedBooking,
      paymentStatus: paymentResult.status
    });

  } catch (error) {
    console.error('Error procesando pago:', error);
    return createError(500, 'Error al procesar pago');
  }
};

// Process Zelle payment
const processZellePayment = async (paymentData) => {
  // In a real implementation, you would integrate with Zelle API
  // For now, we'll simulate the process
  
  console.log('Processing Zelle payment:', paymentData);
  
  // Simulate payment verification
  // In reality, you'd verify the payment with Zelle
  
  return {
    status: 'paid',
    message: '¡Pago con Zelle procesado exitosamente! 💳',
    transactionId: `zelle_${Date.now()}`
  };
};

// Process Pago Móvil payment
const processPagoMovilPayment = async (paymentData) => {
  // In a real implementation, you would integrate with Venezuelan banking APIs
  // For now, we'll simulate the process
  
  console.log('Processing Pago Móvil payment:', paymentData);
  
  // Simulate payment verification
  // In reality, you'd verify with the bank
  
  return {
    status: 'paid',
    message: '¡Pago Móvil procesado exitosamente! 📱',
    transactionId: `pago_movil_${Date.now()}`
  };
};

// Process Binance payment
const processBinancePayment = async (paymentData) => {
  // In a real implementation, you would integrate with Binance Pay API
  // For now, we'll simulate the process
  
  console.log('Processing Binance payment:', paymentData);
  
  // Simulate payment verification
  // In reality, you'd verify with Binance API
  
  return {
    status: 'paid',
    message: '¡Pago con Binance procesado exitosamente! ₿',
    transactionId: `binance_${Date.now()}`
  };
};

// Process Cash payment
const processCashPayment = async (paymentData) => {
  // Cash payments are marked as pending until paid at marina
  
  console.log('Processing Cash payment:', paymentData);
  
  return {
    status: 'pending',
    message: '¡Reserva confirmada! Paga en efectivo al momento del abordaje 💵',
    transactionId: `cash_${Date.now()}`
  };
};