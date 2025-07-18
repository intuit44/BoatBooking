/* eslint-disable */
// Mutations básicas para nuestra app
export const createBoat = /* GraphQL */ `
  mutation CreateBoat(
    $input: CreateBoatInput!
    $condition: ModelBoatConditionInput
  ) {
    createBoat(input: $input, condition: $condition) {
      id
      name
      type
      description
      capacity
      pricePerHour
      pricePerDay
      rating
      reviews
      images
      location {
        marina
        state
      }
      specifications {
        length
        engine
        fuel
        year
      }
      amenities
      availability {
        available
        blockedDates
      }
      featured
      ownerId
      createdAt
      updatedAt
    }
  }
`;

export const createBooking = /* GraphQL */ `
  mutation CreateBooking(
    $input: CreateBookingInput!
    $condition: ModelBookingConditionInput
  ) {
    createBooking(input: $input, condition: $condition) {
      id
      userId
      boatId
      startDate
      endDate
      totalAmount
      status
      paymentStatus
      guestCount
      createdAt
      updatedAt
    }
  }
`;

export const updateBooking = /* GraphQL */ `
  mutation UpdateBooking(
    $input: UpdateBookingInput!
    $condition: ModelBookingConditionInput
  ) {
    updateBooking(input: $input, condition: $condition) {
      id
      userId
      boatId
      startDate
      endDate
      totalAmount
      status
      paymentStatus
      guestCount
      createdAt
      updatedAt
    }
  }
`;
