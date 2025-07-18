/* eslint-disable */
// Queries básicas para nuestra app
export const listBoats = /* GraphQL */ `
  query ListBoats(
    $filter: ModelBoatFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listBoats(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
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
        amenities
        featured
        ownerId
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;

export const getBoat = /* GraphQL */ `
  query GetBoat($id: ID!) {
    getBoat(id: $id) {
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

export const listBookings = /* GraphQL */ `
  query ListBookings(
    $filter: ModelBookingFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listBookings(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
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
      nextToken
    }
  }
`;
