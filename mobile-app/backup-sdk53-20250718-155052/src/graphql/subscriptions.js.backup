/* eslint-disable */
// Subscriptions para actualizaciones en tiempo real
export const onCreateBoat = /* GraphQL */ `
  subscription OnCreateBoat($filter: ModelSubscriptionBoatFilterInput) {
    onCreateBoat(filter: $filter) {
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
      featured
      ownerId
      createdAt
      updatedAt
    }
  }
`;

export const onCreateBooking = /* GraphQL */ `
  subscription OnCreateBooking(
    $filter: ModelSubscriptionBookingFilterInput
    $userId: String
    $boatOwnerId: String
  ) {
    onCreateBooking(filter: $filter, userId: $userId, boatOwnerId: $boatOwnerId) {
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
