import AWS from 'aws-sdk';
import { v4: uuidv4  } from 'uuid';
import { validateBooking  } from '../utils/validators';
import { createResponse, createError  } from '../utils/response';
import { checkBoatAvailability  } from '../utils/availability';

const dynamodb = new AWS.DynamoDB.DocumentClient();
const BOOKINGS_TABLE = process.env.DYNAMODB_TABLE_BOOKINGS;
const BOATS_TABLE = process.env.DYNAMODB_TABLE_BOATS;

// Create new booking
export const createBooking = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { user } = event.requestContext.authorizer;

    // Validate input
    const { error } = validateBooking(body);
    if (error) {
      return createError(400, error.details[0].message);
    }

    // Get boat details
    const { Item: boat } = await dynamodb.get({
      TableName: BOATS_TABLE,
      Key: { id: body.boatId }
    }).promise();

    if (!boat) {
      return createError(404, 'Bote no encontrado');
    }

    // Check availability
    const isAvailable = await checkBoatAvailability(
      body.boatId,
      body.startDate,
      body.endDate,
      body.startTime,
      body.endTime
    );

    if (!isAvailable) {
      return createError(400, 'El bote no está disponible para las fechas/horas seleccionadas');
    }

    // Calculate total price
    const startDateTime = new Date(`${body.startDate}T${body.startTime}`);
    const endDateTime = new Date(`${body.endDate}T${body.endTime}`);
    const totalHours = Math.ceil((endDateTime - startDateTime) / (1000 * 60 * 60));
    const totalPrice = totalHours * boat.pricePerHour;

    // Create booking object
    const booking = {
      id: uuidv4(),
      userId: user.id,
      boatId: boat.id,
      boatName: boat.name,
      boatImage: boat.images[0],
      startDate: body.startDate,
      endDate: body.endDate,
      startTime: body.startTime,
      endTime: body.endTime,
      totalHours,
      pricePerHour: boat.pricePerHour,
      totalPrice,
      currency: boat.currency || 'USD',
      paymentMethod: body.paymentMethod,
      paymentStatus: 'pending',
      bookingStatus: 'pending',
      guests: body.guests,
      specialRequests: body.specialRequests,
      contactInfo: {
        name: body.contactInfo.name,
        phone: body.contactInfo.phone,
        email: body.contactInfo.email
      },
      marina: boat.location,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save to DynamoDB
    await dynamodb.put({
      TableName: BOOKINGS_TABLE,
      Item: booking
    }).promise();

    return createResponse(201, {
      message: 'Reserva creada exitosamente',
      booking
    });

  } catch (error) {
    console.error('Error creando reserva:', error);
    return createError(500, 'Error al crear reserva');
  }
};

// Get user bookings
export const getUserBookings = async (event) => {
  try {
    const { userId } = event.pathParameters;
    const { user } = event.requestContext.authorizer;

    // Check authorization
    if (user.role !== 'admin' && user.id !== userId) {
      return createError(403, 'No tienes permisos para ver estas reservas');
    }

    // Query bookings by userId
    const result = await dynamodb.query({
      TableName: BOOKINGS_TABLE,
      IndexName: 'UserIndex',
      KeyConditionExpression: 'userId = :userId',
      ExpressionAttributeValues: {
        ':userId': userId
      }
    }).promise();

    return createResponse(200, result.Items);

  } catch (error) {
    console.error('Error obteniendo reservas:', error);
    return createError(500, 'Error al obtener reservas');
  }
};

// Get booking by ID
export const getBookingById = async (event) => {
  try {
    const { id } = event.pathParameters;
    const { user } = event.requestContext.authorizer;

    // Get booking
    const { Item: booking } = await dynamodb.get({
      TableName: BOOKINGS_TABLE,
      Key: { id }
    }).promise();

    if (!booking) {
      return createError(404, 'Reserva no encontrada');
    }

    // Check authorization
    if (user.role !== 'admin' && user.id !== booking.userId) {
      return createError(403, 'No tienes permisos para ver esta reserva');
    }

    return createResponse(200, booking);

  } catch (error) {
    console.error('Error obteniendo reserva:', error);
    return createError(500, 'Error al obtener reserva');
  }
};

// Update booking status
export const updateBookingStatus = async (event) => {
  try {
    const { id } = event.pathParameters;
    const body = JSON.parse(event.body);
    const { user } = event.requestContext.authorizer;

    // Get existing booking
    const { Item: booking } = await dynamodb.get({
      TableName: BOOKINGS_TABLE,
      Key: { id }
    }).promise();

    if (!booking) {
      return createError(404, 'Reserva no encontrada');
    }

    // Check authorization
    if (user.role !== 'admin' && user.id !== booking.userId) {
      return createError(403, 'No tienes permisos para actualizar esta reserva');
    }

    // Validate status
    const validStatuses = ['pending', 'confirmed', 'active', 'completed', 'cancelled'];
    if (!validStatuses.includes(body.status)) {
      return createError(400, 'Estado de reserva inválido');
    }

    // Update booking
    const updatedBooking = {
      ...booking,
      bookingStatus: body.status,
      updatedAt: new Date().toISOString()
    };

    await dynamodb.put({
      TableName: BOOKINGS_TABLE,
      Item: updatedBooking
    }).promise();

    return createResponse(200, {
      message: 'Estado de reserva actualizado exitosamente',
      booking: updatedBooking
    });

  } catch (error) {
    console.error('Error actualizando estado de reserva:', error);
    return createError(500, 'Error al actualizar estado de reserva');
  }
};

// Cancel booking
export const cancelBooking = async (event) => {
  try {
    const { id } = event.pathParameters;
    const { user } = event.requestContext.authorizer;

    // Get existing booking
    const { Item: booking } = await dynamodb.get({
      TableName: BOOKINGS_TABLE,
      Key: { id }
    }).promise();

    if (!booking) {
      return createError(404, 'Reserva no encontrada');
    }

    // Check authorization
    if (user.role !== 'admin' && user.id !== booking.userId) {
      return createError(403, 'No tienes permisos para cancelar esta reserva');
    }

    // Check if booking can be cancelled
    if (!['pending', 'confirmed'].includes(booking.bookingStatus)) {
      return createError(400, 'No se puede cancelar una reserva en este estado');
    }

    // Update booking
    const updatedBooking = {
      ...booking,
      bookingStatus: 'cancelled',
      updatedAt: new Date().toISOString()
    };

    await dynamodb.put({
      TableName: BOOKINGS_TABLE,
      Item: updatedBooking
    }).promise();

    return createResponse(200, {
      message: 'Reserva cancelada exitosamente',
      booking: updatedBooking
    });

  } catch (error) {
    console.error('Error cancelando reserva:', error);
    return createError(500, 'Error al cancelar reserva');
  }
};