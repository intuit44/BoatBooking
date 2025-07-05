import { API, graphqlOperation } from 'aws-amplify';

// Crear cliente GraphQL

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

  // Crear reserva temporal (válida por 30 minutos)
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

      const response: any = await API.graphql(graphqlOperation(createReservationMutation, { input }));

      return {
        success: true,
        data: response.data.createReservation,
      };
    } catch (error: any) {
      console.error('Error creating reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // Obtener reserva por ID
  static async getReservationById(reservationId: string) {
    try {
      const response: any = await API.graphql(graphqlOperation(getReservation, { id: reservationId }));

      return {
        success: true,
        data: response.data.getReservation,
      };
    } catch (error: any) {
      console.error('Error fetching reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // Obtener reservas por usuario
  static async getReservationsByUser(userId: string, status?: string) {
    try {
      const filter: any = {
        userId: { eq: userId }
      };

      if (status) {
        filter.status = { eq: status };
      }

      const response: any = await API.graphql(graphqlOperation(listReservations, { filter }));

      return {
        success: true,
        data: response.data.listReservations.items,
      };
    } catch (error: any) {
      console.error('Error fetching user reservations:', error);
      return { success: false, error: error.message };
    }
  }

  // Confirmar reserva (convertir a booking)
  static async confirmReservation(reservationId: string) {
    try {
      const response: any = await API.graphql(
        graphqlOperation(updateReservationMutation, {
          input: {
            id: reservationId,
            status: 'confirmed'
          }
        })
      );

      return {
        success: true,
        data: response.data.updateReservation,
      };
    } catch (error: any) {
      console.error('Error confirming reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // Cancelar reserva
  static async cancelReservation(reservationId: string, reason?: string) {
    try {
      const response: any = await API.graphql(
        graphqlOperation(updateReservationMutation, {
          input: {
            id: reservationId,
            status: 'cancelled',
            specialRequests: reason ? `Cancelled: ${reason}` : 'Cancelled by user'
          }
        })
      );

      return {
        success: true,
        data: response.data.updateReservation,
      };
    } catch (error: any) {
      console.error('Error cancelling reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // Extender tiempo de reserva
  static async extendReservation(reservationId: string, additionalMinutes: number = 15) {
    try {
      // Obtener reserva actual
      const reservationResult = await this.getReservationById(reservationId);
      
      if (!reservationResult.success || !reservationResult.data) {
        return { success: false, error: 'Reservation not found' };
      }

      const currentExpiry = new Date(reservationResult.data.expiresAt);
      const newExpiry = new Date(currentExpiry.getTime() + (additionalMinutes * 60 * 1000));

      const response: any = await API.graphql(
        graphqlOperation(updateReservationMutation, {
          input: {
            id: reservationId,
            expiresAt: newExpiry.toISOString()
          }
        })
      );

      return {
        success: true,
        data: response.data.updateReservation,
      };
    } catch (error: any) {
      console.error('Error extending reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // Limpiar reservas expiradas
  static async cleanupExpiredReservations() {
    try {
      const now = new Date().toISOString();
      const filter = {
        expiresAt: { lt: now },
        status: { eq: 'pending' }
      };

      const response: any = await API.graphql(graphqlOperation(listReservations, { filter }));

      const expiredReservations = response.data.listReservations.items;

      // Marcar como expiradas
      const updatePromises = expiredReservations.map((reservation: any) =>
        API.graphql(
        graphqlOperation(updateReservationMutation, {
            input: {
              id: reservation.id,
              status: 'expired'
            }
          })
      )
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

  // Eliminar reserva
  static async deleteReservation(reservationId: string) {
    try {
      const response: any = await API.graphql(
        graphqlOperation(deleteReservationMutation, { input: { id: reservationId } })
      );

      return {
        success: true,
        data: response.data.deleteReservation,
      };
    } catch (error: any) {
      console.error('Error deleting reservation:', error);
      return { success: false, error: error.message };
    }
  }

  // Verificar si una reserva está expirada
  static isReservationExpired(expiresAt: string): boolean {
    return new Date() > new Date(expiresAt);
  }

  // Obtener tiempo restante de una reserva
  static getTimeRemaining(expiresAt: string): number {
    const now = new Date().getTime();
    const expiry = new Date(expiresAt).getTime();
    return Math.max(0, expiry - now);
  }
}