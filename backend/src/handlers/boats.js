const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');
const { validateBoat } = require('../utils/validators');
const { createResponse, createError } = require('../utils/response');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const BOATS_TABLE = process.env.DYNAMODB_TABLE_BOATS;

// Get all boats with pagination and filters
export const getBoats = async (event) => {
  try {
    const { state, type, minPrice, maxPrice, capacity, limit = 20, lastKey } = event.queryStringParameters || {};

    let params = {
      TableName: BOATS_TABLE,
      Limit: parseInt(limit)
    };

    // Add pagination
    if (lastKey) {
      params.ExclusiveStartKey = JSON.parse(decodeURIComponent(lastKey));
    }

    // If filtering by state, use GSI
    if (state) {
      params.IndexName = 'StateIndex';
      params.KeyConditionExpression = '#state = :state';
      params.ExpressionAttributeNames = { '#state': 'state' };
      params.ExpressionAttributeValues = { ':state': state };
    }

    const result = await dynamodb.scan(params).promise();
    let boats = result.Items;

    // Apply additional filters
    if (type) {
      boats = boats.filter(boat => boat.type === type);
    }
    if (minPrice) {
      boats = boats.filter(boat => boat.pricePerHour >= parseFloat(minPrice));
    }
    if (maxPrice) {
      boats = boats.filter(boat => boat.pricePerHour <= parseFloat(maxPrice));
    }
    if (capacity) {
      boats = boats.filter(boat => boat.capacity >= parseInt(capacity));
    }

    return createResponse(200, {
      boats,
      lastKey: result.LastEvaluatedKey ? encodeURIComponent(JSON.stringify(result.LastEvaluatedKey)) : null,
      count: boats.length
    });

  } catch (error) {
    console.error('Error obteniendo botes:', error);
    return createError(500, 'Error al obtener botes');
  }
};

// Get boat by ID
export const getBoatById = async (event) => {
  try {
    const { id } = event.pathParameters;

    const { Item: boat } = await dynamodb.get({
      TableName: BOATS_TABLE,
      Key: { id }
    }).promise();

    if (!boat) {
      return createError(404, 'Bote no encontrado');
    }

    return createResponse(200, boat);

  } catch (error) {
    console.error('Error obteniendo bote:', error);
    return createError(500, 'Error al obtener bote');
  }
};

// Get featured boats
export const getFeaturedBoats = async (event) => {
  try {
    const { limit = 10 } = event.queryStringParameters || {};

    const result = await dynamodb.scan({
      TableName: BOATS_TABLE,
      FilterExpression: 'featured = :featured',
      ExpressionAttributeValues: {
        ':featured': true
      },
      Limit: parseInt(limit)
    }).promise();

    return createResponse(200, result.Items);

  } catch (error) {
    console.error('Error obteniendo botes destacados:', error);
    return createError(500, 'Error al obtener botes destacados');
  }
};

// Search boats
export const searchBoats = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { 
      query, 
      state, 
      type, 
      minPrice, 
      maxPrice, 
      capacity, 
      startDate, 
      endDate,
      limit = 20 
    } = body;

    let params = {
      TableName: BOATS_TABLE,
      Limit: parseInt(limit)
    };

    // If searching by state, use GSI
    if (state) {
      params.IndexName = 'StateIndex';
      params.KeyConditionExpression = '#state = :state';
      params.ExpressionAttributeNames = { '#state': 'state' };
      params.ExpressionAttributeValues = { ':state': state };
    }

    const result = await dynamodb.scan(params).promise();
    let boats = result.Items;

    // Apply text search
    if (query) {
      const searchTerm = query.toLowerCase();
      boats = boats.filter(boat => 
        boat.name.toLowerCase().includes(searchTerm) ||
        boat.description.toLowerCase().includes(searchTerm) ||
        boat.location.marina.toLowerCase().includes(searchTerm)
      );
    }

    // Apply filters
    if (type) {
      boats = boats.filter(boat => boat.type === type);
    }
    if (minPrice) {
      boats = boats.filter(boat => boat.pricePerHour >= parseFloat(minPrice));
    }
    if (maxPrice) {
      boats = boats.filter(boat => boat.pricePerHour <= parseFloat(maxPrice));
    }
    if (capacity) {
      boats = boats.filter(boat => boat.capacity >= parseInt(capacity));
    }

    // TODO: Add availability check based on startDate and endDate
    // This would require checking against bookings table

    return createResponse(200, {
      boats,
      count: boats.length,
      query: body
    });

  } catch (error) {
    console.error('Error en búsqueda:', error);
    return createError(500, 'Error al buscar botes');
  }
};

// Create new boat (Admin/Owner only)
export const createBoat = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { user } = event.requestContext.authorizer;

    // Validate input
    const { error } = validateBoat(body);
    if (error) {
      return createError(400, error.details[0].message);
    }

    // Create boat object
    const boat = {
      id: uuidv4(),
      ...body,
      ownerId: user.id,
      featured: false,
      rating: 0,
      reviewCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save to DynamoDB
    await dynamodb.put({
      TableName: BOATS_TABLE,
      Item: boat
    }).promise();

    return createResponse(201, {
      message: 'Bote creado exitosamente',
      boat
    });

  } catch (error) {
    console.error('Error creando bote:', error);
    return createError(500, 'Error al crear bote');
  }
};

// Update boat
export const updateBoat = async (event) => {
  try {
    const { id } = event.pathParameters;
    const body = JSON.parse(event.body);
    const { user } = event.requestContext.authorizer;

    // Get existing boat
    const { Item: existingBoat } = await dynamodb.get({
      TableName: BOATS_TABLE,
      Key: { id }
    }).promise();

    if (!existingBoat) {
      return createError(404, 'Bote no encontrado');
    }

    // Check ownership (unless admin)
    if (user.role !== 'admin' && existingBoat.ownerId !== user.id) {
      return createError(403, 'No tienes permisos para editar este bote');
    }

    // Validate input
    const { error } = validateBoat(body);
    if (error) {
      return createError(400, error.details[0].message);
    }

    // Update boat
    const updatedBoat = {
      ...existingBoat,
      ...body,
      updatedAt: new Date().toISOString()
    };

    await dynamodb.put({
      TableName: BOATS_TABLE,
      Item: updatedBoat
    }).promise();

    return createResponse(200, {
      message: 'Bote actualizado exitosamente',
      boat: updatedBoat
    });

  } catch (error) {
    console.error('Error actualizando bote:', error);
    return createError(500, 'Error al actualizar bote');
  }
};

// Delete boat
export const deleteBoat = async (event) => {
  try {
    const { id } = event.pathParameters;
    const { user } = event.requestContext.authorizer;

    // Get existing boat
    const { Item: existingBoat } = await dynamodb.get({
      TableName: BOATS_TABLE,
      Key: { id }
    }).promise();

    if (!existingBoat) {
      return createError(404, 'Bote no encontrado');
    }

    // Check ownership (unless admin)
    if (user.role !== 'admin' && existingBoat.ownerId !== user.id) {
      return createError(403, 'No tienes permisos para eliminar este bote');
    }

    // Delete boat
    await dynamodb.delete({
      TableName: BOATS_TABLE,
      Key: { id }
    }).promise();

    return createResponse(200, {
      message: 'Bote eliminado exitosamente'
    });

  } catch (error) {
    console.error('Error eliminando bote:', error);
    return createError(500, 'Error al eliminar bote');
  }
};