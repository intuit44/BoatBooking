// ✅ AWS Amplify v6 - Nuevos imports
import type { GraphQLResult } from '@aws-amplify/api-graphql';
import { generateClient } from 'aws-amplify/api';
import { Booking } from '../store/slices/bookingsSlice';

// ✅ Crear cliente GraphQL
const client = generateClient();

// GraphQL Queries - mantienen igual
const listBookings = /* GraphQL */ `
  query ListBookings($filter: ModelBookingFilterInput, $limit: Int, $nextToken: String) {
    listBookings(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        userId
        boatId
        startDate
        endDate
        totalHours
        totalDays
        pricePerHour
        pricePerDay
        totalAmount
        status
        paymentStatus
        paymentMethod
        paymentId
        guestCount
        specialRequests
        boat {
          id
          name
          type
          images
          location {
            marina
            state
          }
          owner {
            id
            name
            phone
          }
        }
        user {
          id
          name
          email
          phone
        }
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;

const getBooking = /* GraphQL */ `
  query GetBooking($id: ID!) {
    getBooking(id: $id) {
      id
      userId
      boatId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      paymentMethod
      paymentId
      guestCount
      specialRequests
      boat {
        id
        name
        type
        images
        location {
          marina
          state
        }
        owner {
          id
          name
          phone
        }
      }
      user {
        id
        name
        email
        phone
      }
      createdAt
      updatedAt
    }
  }
`;

const listBookingsByUser = /* GraphQL */ `
  query ListBookingsByUser($userId: ID!, $sortDirection: ModelSortDirection, $filter: ModelBookingFilterInput, $limit: Int, $nextToken: String) {
    listBookingsByUser(userId: $userId, sortDirection: $sortDirection, filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        userId
        boatId
        startDate
        endDate
        totalHours
        totalDays
        pricePerHour
        pricePerDay
        totalAmount
        status
        paymentStatus
        paymentMethod
        paymentId
        guestCount
        specialRequests
        boat {
          id
          name
          type
          images
          location {
            marina
            state
          }
          owner {
            id
            name
            phone
          }
        }
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;

const listBookingsByBoat = /* GraphQL */ `
  query ListBookingsByBoat($boatId: ID!, $sortDirection: ModelSortDirection, $filter: ModelBookingFilterInput, $limit: Int, $nextToken: String) {
    listBookingsByBoat(boatId: $boatId, sortDirection: $sortDirection, filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        userId
        boatId
        startDate
        endDate
        totalHours
        totalDays
        pricePerHour
        pricePerDay
        totalAmount
        status
        paymentStatus
        paymentMethod
        paymentId
        guestCount
        specialRequests
        user {
          id
          name
          email
          phone
        }
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;

// GraphQL Mutations
const createBookingMutation = /* GraphQL */ `
  mutation CreateBooking($input: CreateBookingInput!) {
    createBooking(input: $input) {
      id
      userId
      boatId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      paymentMethod
      paymentId
      guestCount
      specialRequests
      boat {
        id
        name
        type
        images
        location {
          marina
          state
        }
        owner {
          id
          name
          phone
        }
      }
      user {
        id
        name
        email
        phone
      }
      createdAt
      updatedAt
    }
  }
`;

const updateBookingMutation = /* GraphQL */ `
  mutation UpdateBooking($input: UpdateBookingInput!) {
    updateBooking(input: $input) {
      id
      userId
      boatId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      paymentMethod
      paymentId
      guestCount
      specialRequests
      boat {
        id
        name
        type
        images
        location {
          marina
          state
        }
        owner {
          id
          name
          phone
        }
      }
      user {
        id
        name
        email
        phone
      }
      createdAt
      updatedAt
    }
  }
`;

const deleteBookingMutation = /* GraphQL */ `
  mutation DeleteBooking($input: DeleteBookingInput!) {
    deleteBooking(input: $input) {
      id
    }
  }
`;

export class BookingsService {
  static confirmBooking(bookingId: string) {
    throw new Error('Method not implemented.');
  }
  
  static getUserBookingHistory(userId: string) {
    throw new Error('Method not implemented.');
  }

  // ✅ Crear nueva reserva - Nueva sintaxis v6
  static async createBooking(bookingData: Omit<Booking, 'id' | 'createdAt' | 'updatedAt'>) {
    try {
      const response = await client.graphql({
        query: createBookingMutation,
        variables: { input: bookingData }
      }) as GraphQLResult<{ createBooking: Booking }>;
      
      return {
        success: true,
        data: response.data?.createBooking as Booking,
      };
    } catch (error: any) {
      console.error('Error creating booking:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Obtener reserva por ID - Nueva sintaxis v6
  static async getBookingById(bookingId: string) {
    try {
      const response = await client.graphql({
        query: getBooking,
        variables: { id: bookingId }
      }) as GraphQLResult<{ getBooking: Booking }>;
      
      return {
        success: true,
        data: response.data?.getBooking as Booking,
      };
    } catch (error: any) {
      console.error('Error fetching booking by ID:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Obtener reservas por usuario - Nueva sintaxis v6
  static async getBookingsByUser(userId: string, filters?: {
    status?: string;
    limit?: number;
    nextToken?: string;
  }) {
    try {
      const filter: any = {};
      
      if (filters?.status) {
        filter.status = { eq: filters.status };
      }

      const response = await client.graphql({
        query: listBookingsByUser,
        variables: {
          userId,
          sortDirection: 'DESC',
          filter: Object.keys(filter).length > 0 ? filter : undefined,
          limit: filters?.limit || 20,
          nextToken: filters?.nextToken
        }
      }) as GraphQLResult<{ listBookingsByUser: { items: Booking[], nextToken?: string } }>;
      
      return {
        success: true,
        data: response.data?.listBookingsByUser.items as Booking[],
        nextToken: response.data?.listBookingsByUser.nextToken,
      };
    } catch (error: any) {
      console.error('Error fetching user bookings:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Obtener reservas por bote - Nueva sintaxis v6
  static async getBookingsByBoat(boatId: string, filters?: {
    status?: string;
    limit?: number;
    nextToken?: string;
  }) {
    try {
      const filter: any = {};
      
      if (filters?.status) {
        filter.status = { eq: filters.status };
      }

      const response = await client.graphql({
        query: listBookingsByBoat,
        variables: {
          boatId,
          sortDirection: 'DESC',
          filter: Object.keys(filter).length > 0 ? filter : undefined,
          limit: filters?.limit || 20,
          nextToken: filters?.nextToken
        }
      }) as GraphQLResult<{ listBookingsByBoat: { items: Booking[], nextToken?: string } }>;
      
      return {
        success: true,
        data: response.data?.listBookingsByBoat.items as Booking[],
        nextToken: response.data?.listBookingsByBoat.nextToken,
      };
    } catch (error: any) {
      console.error('Error fetching boat bookings:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Obtener todas las reservas - Nueva sintaxis v6
  static async getAllBookings(filters?: {
    status?: string;
    userId?: string;
    boatId?: string;
    limit?: number;
    nextToken?: string;
  }) {
    try {
      const filter: any = {};
      
      if (filters?.status) {
        filter.status = { eq: filters.status };
      }
      
      if (filters?.userId) {
        filter.userId = { eq: filters.userId };
      }
      
      if (filters?.boatId) {
        filter.boatId = { eq: filters.boatId };
      }

      const response = await client.graphql({
        query: listBookings,
        variables: {
          filter: Object.keys(filter).length > 0 ? filter : undefined,
          limit: filters?.limit || 20,
          nextToken: filters?.nextToken
        }
      }) as GraphQLResult<{ listBookings: { items: Booking[], nextToken?: string } }>;
      
      return {
        success: true,
        data: response.data?.listBookings.items as Booking[],
        nextToken: response.data?.listBookings.nextToken,
      };
    } catch (error: any) {
      console.error('Error fetching all bookings:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Actualizar estado de reserva - Nueva sintaxis v6
  static async updateBookingStatus(bookingId: string, status: string, paymentStatus?: string) {
    try {
      const updates: any = { status };
      
      if (paymentStatus) {
        updates.paymentStatus = paymentStatus;
      }

      const response = await client.graphql({
        query: updateBookingMutation,
        variables: {
          input: {
            id: bookingId,
            ...updates,
          }
        }
      }) as GraphQLResult<{ updateBooking: Booking }>;
      
      return {
        success: true,
        data: response.data?.updateBooking as Booking,
      };
    } catch (error: any) {
      console.error('Error updating booking status:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Actualizar información de pago - Nueva sintaxis v6
  static async updateBookingPayment(bookingId: string, paymentData: {
    paymentStatus: string;
    paymentMethod?: string;
    paymentId?: string;
  }) {
    try {
      const response = await client.graphql({
        query: updateBookingMutation,
        variables: {
          input: {
            id: bookingId,
            ...paymentData,
          }
        }
      }) as GraphQLResult<{ updateBooking: Booking }>;
      
      return {
        success: true,
        data: response.data?.updateBooking as Booking,
      };
    } catch (error: any) {
      console.error('Error updating booking payment:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Cancelar reserva - Nueva sintaxis v6
  static async cancelBooking(bookingId: string, reason?: string) {
    try {
      const response = await client.graphql({
        query: updateBookingMutation,
        variables: {
          input: {
            id: bookingId,
            status: 'cancelled',
            specialRequests: reason ? `Cancelled: ${reason}` : 'Cancelled by user',
          }
        }
       }) as GraphQLResult<{ updateBooking: Booking }>;
      
      return {
        success: true,
        data: response.data?.updateBooking as Booking,
      };
    } catch (error: any) {
      console.error('Error cancelling booking:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Eliminar reserva - Nueva sintaxis v6
  static async deleteBooking(bookingId: string) {
    try {
      const response = await client.graphql({
        query: deleteBookingMutation,
        variables: { input: { id: bookingId } }
      }) as GraphQLResult<{ deleteBooking: { id: string } }>;
      
      return {
        success: true,
        data: response.data?.deleteBooking,
      };
    } catch (error: any) {
      console.error('Error deleting booking:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Verificar disponibilidad - Nueva sintaxis v6
  static async checkAvailability(boatId: string, startDate: string, endDate: string) {
    try {
      const filter = {
        boatId: { eq: boatId },
        and: [
          {
            or: [
              {
                and: [
                  { startDate: { le: startDate } },
                  { endDate: { gt: startDate } }
                ]
              },
              {
                and: [
                  { startDate: { lt: endDate } },
                  { endDate: { ge: endDate } }
                ]
              },
              {
                and: [
                  { startDate: { ge: startDate } },
                  { endDate: { le: endDate } }
                ]
              }
            ]
          },
          {
            status: { ne: 'cancelled' }
          }
        ]
      };

      const response = await client.graphql({
        query: listBookings,
        variables: { filter }
      }) as GraphQLResult<{ listBookings: { items: Booking[] } }>;
      
      const conflictingBookings = response.data?.listBookings.items || [];
      
      return {
        success: true,
        available: conflictingBookings.length === 0,
        conflictingBookings,
      };
    } catch (error: any) {
      console.error('Error checking availability:', error);
      return { success: false, error: error.message };
    }
  }
}