// ✅ AWS Amplify v6 - Nuevos imports
import type { GraphQLResult } from '@aws-amplify/api-graphql';
import { generateClient } from 'aws-amplify/api';

// ✅ Crear cliente GraphQL
const client = generateClient();

// Interfaces para reservas temporales (antes de confirmar booking)
export interface ReservationRequest {
  boatId: string;
  userId: string;
  startDate: string;
  endDate: string;
  totalHours?: number;
  totalDays?: number;
  guestCount: number;
  specialRequests?: string;
  contactInfo: {
    name: string;
    email: string;
    phone: string;
  };
}

export interface ReservationQuote {
  boatId: string;
  startDate: string;
  endDate: string;
  totalHours: number;
  totalDays: number;
  pricePerHour: number;
  pricePerDay: number;
  subtotal: number;
  taxes: number;
  serviceFee: number;
  totalAmount: number;
  currency: string;
}

export interface Reservation {
  id: string;
  userId: string;
  boatId: string;
  startDate: string;
  endDate: string;
  totalHours: number;
  totalDays: number;
  guestCount: number;
  specialRequests?: string;
  contactInfo: {
    name: string;
    email: string;
    phone: string;
  };
  quote: {
    subtotal: number;
    taxes: number;
    serviceFee: number;
    totalAmount: number;
    currency: string;
  };
  status: string;
  expiresAt: string;
  boat?: {
    id: string;
    name: string;
    type: string;
    images: string[];
    location: {
      marina: string;
      state: string;
    };
    pricePerHour: number;
    pricePerDay: number;
    owner?: {
      id: string;
      name: string;
      phone: string;
    };
  };
  createdAt: string;
  updatedAt: string;
}

// GraphQL Queries para reservas temporales
const listReservations = /* GraphQL */ `
  query ListReservations($filter: ModelReservationFilterInput, $limit: Int, $nextToken: String) {
    listReservations(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        userId
        boatId
        startDate
        endDate
        totalHours
        totalDays
        guestCount
        specialRequests
        contactInfo {
          name
          email
          phone
        }
        quote {
          subtotal
          taxes
          serviceFee
          totalAmount
          currency
        }
        status
        expiresAt
        boat {
          id
          name
          type
          images
          location {
            marina
            state
          }
          pricePerHour
          pricePerDay
        }
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;

const getReservation = /* GraphQL */ `
  query GetReservation($id: ID!) {
    getReservation(id: $id) {
      id
      userId
      boatId
      startDate
      endDate
      totalHours
      totalDays
      guestCount
      specialRequests
      contactInfo {
        name
        email
        phone
      }
      quote {
        subtotal
        taxes
        serviceFee
        totalAmount
        currency
      }
      status
      expiresAt
      boat {
        id
        name
        type
        images
        location {
          marina
          state
        }
        pricePerHour
        pricePerDay
        owner {
          id
          name
          phone
        }
      }
      createdAt
      updatedAt
    }
  }
`;

// GraphQL Mutations
const createReservationMutation = /* GraphQL */ `
  mutation CreateReservation($input: CreateReservationInput!) {
    createReservation(input: $input) {
      id
      userId
      boatId
      startDate
      endDate
      totalHours
      totalDays
      guestCount
      specialRequests
      contactInfo {
        name
        email
        phone
      }
      quote {
        subtotal
        taxes
        serviceFee
        totalAmount
        currency
      }
      status
      expiresAt
      boat {
        id
        name
        type
        images
        location {
          marina
          state
        }
        pricePerHour
        pricePerDay
      }
      createdAt
      updatedAt
    }
  }
`;

const updateReservationMutation = /* GraphQL */ `
  mutation UpdateReservation($input: UpdateReservationInput!) {
    updateReservation(input: $input) {
      id
      userId
      boatId
      startDate
      endDate
      totalHours
      totalDays
      guestCount
      specialRequests
      contactInfo {
        name
        email
        phone
      }
      quote {
        subtotal
        taxes
        serviceFee
        totalAmount
        currency
      }
      status
      expiresAt
      createdAt
      updatedAt
    }
  }
`;

const deleteReservationMutation = /* GraphQL */ `
  mutation DeleteReservation($input: DeleteReservationInput!) {
    deleteReservation(input: $input) {
      id
    }
  }
`;

export class ReservationsService {
  // Calcular cotización de reserva
  static calculateQuote(
    startDate: string,
    endDate: string,
    pricePerHour: number,
    pricePerDay: number
  ): ReservationQuote {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const totalHours = Math.ceil(diffTime / (1000 * 60 * 60));
    const totalDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    // Determinar si es mejor precio por hora o por día
    const hourlyTotal = totalHours * pricePerHour;
    const dailyTotal = totalDays * pricePerDay;
    const subtotal = Math.min(hourlyTotal, dailyTotal);

    // Calcular impuestos y tarifas de servicio
    const taxes = subtotal * 0.16; // 16% IVA Venezuela
    const serviceFee = subtotal * 0.05; // 5% tarifa de servicio
    const totalAmount = subtotal + taxes + serviceFee;

    return {
      boatId: '',
      startDate,
      endDate,
      totalHours,
      totalDays,
      pricePerHour,
      pricePerDay,
      subtotal,
      taxes,
      serviceFee,
      totalAmount,
      currency: 'USD'
    };
  }

  // ✅ Crear reserva temporal (válida por 30 minutos) - Nueva sintaxis v6
  static async createReservation(reservationData: ReservationRequest) {
    try {
      // Calcular fecha de expiración (30 minutos)
      const expiresAt = new Date();
      expiresAt.setMinutes(expiresAt.getMinutes() + 30);

      const input = {
        ...reservationData,
        status: 'pending',
        expiresAt: expiresAt.toISOString(),
      };

      const response = await client.graphql({
        query: createReservationMutation,
        variables: { input }
      }) as GraphQLResult<{ createReservation: Reservation }>;

      return {
        success: true,
        data: response.data?.createReservation,
      };
    } catch (error: any) {
      console.error('Error creating reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Obtener reserva por ID - Nueva sintaxis v6
  static async getReservationById(reservationId: string) {
    try {
      const response = await client.graphql({
        query: getReservation,
        variables: { id: reservationId }
      }) as GraphQLResult<{ getReservation: Reservation }>;

      return {
        success: true,
        data: response.data?.getReservation,
      };
    } catch (error: any) {
      console.error('Error fetching reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Obtener reservas por usuario - Nueva sintaxis v6
  static async getReservationsByUser(userId: string, status?: string) {
    try {
      const filter: any = {
        userId: { eq: userId }
      };

      if (status) {
        filter.status = { eq: status };
      }

      const response = await client.graphql({
        query: listReservations,
        variables: { filter }
      }) as GraphQLResult<{ listReservations: { items: Reservation[] } }>;

      return {
        success: true,
        data: response.data?.listReservations.items || [],
      };
    } catch (error: any) {
      console.error('Error fetching user reservations:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Confirmar reserva (convertir a booking) - Nueva sintaxis v6
  static async confirmReservation(reservationId: string) {
    try {
      const response = await client.graphql({
        query: updateReservationMutation,
        variables: {
          input: {
            id: reservationId,
            status: 'confirmed'
          }
        }
      }) as GraphQLResult<{ updateReservation: Reservation }>;

      return {
        success: true,
        data: response.data?.updateReservation,
      };
    } catch (error: any) {
      console.error('Error confirming reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Cancelar reserva - Nueva sintaxis v6
  static async cancelReservation(reservationId: string, reason?: string) {
    try {
      const response = await client.graphql({
        query: updateReservationMutation,
        variables: {
          input: {
            id: reservationId,
            status: 'cancelled',
            specialRequests: reason ? `Cancelled: ${reason}` : 'Cancelled by user'
          }
        }
      }) as GraphQLResult<{ updateReservation: Reservation }>;

      return {
        success: true,
        data: response.data?.updateReservation,
      };
    } catch (error: any) {
      console.error('Error cancelling reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Extender tiempo de reserva - Nueva sintaxis v6
  static async extendReservation(reservationId: string, additionalMinutes: number = 15) {
    try {
      // Obtener reserva actual
      const reservationResult = await this.getReservationById(reservationId);
      
      if (!reservationResult.success || !reservationResult.data) {
        return { success: false, error: 'Reservation not found' };
      }

      const currentExpiry = new Date(reservationResult.data.expiresAt);
      const newExpiry = new Date(currentExpiry.getTime() + (additionalMinutes * 60 * 1000));

      const response = await client.graphql({
        query: updateReservationMutation,
        variables: {
          input: {
            id: reservationId,
            expiresAt: newExpiry.toISOString()
          }
        }
      }) as GraphQLResult<{ updateReservation: Reservation }>;

      return {
        success: true,
        data: response.data?.updateReservation,
      };
    } catch (error: any) {
      console.error('Error extending reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Limpiar reservas expiradas - Nueva sintaxis v6
  static async cleanupExpiredReservations() {
    try {
      const now = new Date().toISOString();
      const filter = {
        expiresAt: { lt: now },
        status: { eq: 'pending' }
      };

      const response = await client.graphql({
        query: listReservations,
        variables: { filter }
      }) as GraphQLResult<{ listReservations: { items: Reservation[] } }>;

      const expiredReservations = response.data?.listReservations.items || [];

      // Marcar como expiradas
      const updatePromises = expiredReservations.map((reservation: Reservation) =>
        client.graphql({
          query: updateReservationMutation,
          variables: {
            input: {
              id: reservation.id,
              status: 'expired'
            }
          }
        })
      );

      await Promise.all(updatePromises);

      return {
        success: true,
        data: { cleaned: expiredReservations.length },
      };
    } catch (error: any) {
      console.error('Error cleaning expired reservations:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Eliminar reserva - Nueva sintaxis v6
  static async deleteReservation(reservationId: string) {
    try {
      const response = await client.graphql({
        query: deleteReservationMutation,
        variables: { input: { id: reservationId } }
      }) as GraphQLResult<{ deleteReservation: { id: string } }>;

      return {
        success: true,
        data: response.data?.deleteReservation,
      };
    } catch (error: any) {
      console.error('Error deleting reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Verificar si una reserva está expirada
  static isReservationExpired(expiresAt: string): boolean {
    return new Date() > new Date(expiresAt);
  }

  // ✅ Obtener tiempo restante de una reserva
  static getTimeRemaining(expiresAt: string): number {
    const now = new Date().getTime();
    const expiry = new Date(expiresAt).getTime();
    return Math.max(0, expiry - now);
  }

  // ✅ Obtener reservas activas por usuario
  static async getActiveReservationsByUser(userId: string) {
    try {
      const now = new Date().toISOString();
      const filter = {
        userId: { eq: userId },
        and: [
          { expiresAt: { gt: now } },
          { status: { eq: 'pending' } }
        ]
      };

      const response = await client.graphql({
        query: listReservations,
        variables: { filter }
      }) as GraphQLResult<{ listReservations: { items: Reservation[] } }>;

      return {
        success: true,
        data: response.data?.listReservations.items || [],
      };
    } catch (error: any) {
      console.error('Error fetching active reservations:', error);
      return { success: false, error: error.message };
    }
  }

  // ✅ Convertir reserva a booking
  static async convertReservationToBooking(reservationId: string) {
    try {
      // Primero obtener la reserva
      const reservationResult = await this.getReservationById(reservationId);
      
      if (!reservationResult.success || !reservationResult.data) {
        return { success: false, error: 'Reservation not found' };
      }

      const reservation = reservationResult.data;

      // Verificar que no esté expirada
      if (this.isReservationExpired(reservation.expiresAt)) {
        return { success: false, error: 'Reservation has expired' };
      }

      // TODO: Aquí llamarías al BookingsService para crear el booking real
      // const bookingData = {
      //   userId: reservation.userId,
      //   boatId: reservation.boatId,
      //   startDate: reservation.startDate,
      //   endDate: reservation.endDate,
      //   totalHours: reservation.totalHours,
      //   totalDays: reservation.totalDays,
      //   guestCount: reservation.guestCount,
      //   specialRequests: reservation.specialRequests,
      //   contactInfo: reservation.contactInfo,
      //   totalAmount: reservation.quote.totalAmount,
      //   currency: reservation.quote.currency
      // };

      // const bookingResult = await BookingsService.createBooking(bookingData);

      // Por ahora solo marcamos como confirmada
      const confirmedReservation = await this.confirmReservation(reservationId);

      return {
        success: true,
        data: {
          reservation: confirmedReservation.data,
          // booking: bookingResult.data // Cuando implementes BookingsService
        }
      };

    } catch (error: any) {
      console.error('Error converting reservation to booking:', error);
      return { success: false, error: error.message };
    }
  }
}