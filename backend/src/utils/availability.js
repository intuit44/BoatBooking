const AWS = require('aws-sdk');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const BOOKINGS_TABLE = process.env.DYNAMODB_TABLE_BOOKINGS;

// Check if boat is available for given date/time range
exports.checkBoatAvailability = async (boatId, startDate, endDate, startTime, endTime) => {
  try {
    // Query all bookings for this boat
    const result = await dynamodb.query({
      TableName: BOOKINGS_TABLE,
      IndexName: 'BoatIndex',
      KeyConditionExpression: 'boatId = :boatId',
      FilterExpression: 'bookingStatus <> :cancelled',
      ExpressionAttributeValues: {
        ':boatId': boatId,
        ':cancelled': 'cancelled'
      }
    }).promise();

    const existingBookings = result.Items;

    // Convert requested time to Date objects for comparison
    const requestedStart = new Date(`${startDate}T${startTime}`);
    const requestedEnd = new Date(`${endDate}T${endTime}`);

    // Check for conflicts
    for (const booking of existingBookings) {
      const bookingStart = new Date(`${booking.startDate}T${booking.startTime}`);
      const bookingEnd = new Date(`${booking.endDate}T${booking.endTime}`);

      // Check if there's any overlap
      if (
        (requestedStart >= bookingStart && requestedStart < bookingEnd) ||
        (requestedEnd > bookingStart && requestedEnd <= bookingEnd) ||
        (requestedStart <= bookingStart && requestedEnd >= bookingEnd)
      ) {
        return false; // Conflict found
      }
    }

    return true; // No conflicts, boat is available

  } catch (error) {
    console.error('Error checking availability:', error);
    throw error;
  }
};

// Get available time slots for a boat on a specific date
exports.getAvailableTimeSlots = async (boatId, date) => {
  try {
    // Query bookings for this boat on the specific date
    const result = await dynamodb.query({
      TableName: BOOKINGS_TABLE,
      IndexName: 'BoatIndex',
      KeyConditionExpression: 'boatId = :boatId',
      FilterExpression: 'bookingStatus <> :cancelled AND (startDate = :date OR endDate = :date)',
      ExpressionAttributeValues: {
        ':boatId': boatId,
        ':cancelled': 'cancelled',
        ':date': date
      }
    }).promise();

    const bookings = result.Items;

    // Define business hours (8 AM to 8 PM)
    const businessStart = 8; // 8:00 AM
    const businessEnd = 20;  // 8:00 PM

    // Create array of all possible time slots (30-minute intervals)
    const allSlots = [];
    for (let hour = businessStart; hour < businessEnd; hour++) {
      allSlots.push(`${hour.toString().padStart(2, '0')}:00`);
      allSlots.push(`${hour.toString().padStart(2, '0')}:30`);
    }

    // Filter out booked slots
    const availableSlots = allSlots.filter(slot => {
      const slotTime = new Date(`${date}T${slot}`);
      
      return !bookings.some(booking => {
        const bookingStart = new Date(`${booking.startDate}T${booking.startTime}`);
        const bookingEnd = new Date(`${booking.endDate}T${booking.endTime}`);
        
        return slotTime >= bookingStart && slotTime < bookingEnd;
      });
    });

    return availableSlots;

  } catch (error) {
    console.error('Error getting available time slots:', error);
    throw error;
  }
};