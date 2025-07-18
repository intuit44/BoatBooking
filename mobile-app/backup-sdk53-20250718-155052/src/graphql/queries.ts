/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "../API";
type GeneratedQuery<InputType, OutputType> = string & {
  __generatedQueryInput: InputType;
  __generatedQueryOutput: OutputType;
};

export const getUser = /* GraphQL */ `query GetUser($id: ID!) {
  getUser(id: $id) {
    id
    email
    name
    phone
    role
    verified
    rating
    profileImage
    dateOfBirth
    address
    emergencyContact {
      name
      email
      phone
      __typename
    }
    ownedBoats {
      nextToken
      __typename
    }
    bookings {
      nextToken
      __typename
    }
    reservations {
      nextToken
      __typename
    }
    reviews {
      nextToken
      __typename
    }
    payments {
      nextToken
      __typename
    }
    notifications {
      nextToken
      __typename
    }
    createdAt
    updatedAt
    __typename
  }
}
` as GeneratedQuery<APITypes.GetUserQueryVariables, APITypes.GetUserQuery>;
export const listUsers = /* GraphQL */ `query ListUsers(
  $filter: ModelUserFilterInput
  $limit: Int
  $nextToken: String
) {
  listUsers(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<APITypes.ListUsersQueryVariables, APITypes.ListUsersQuery>;
export const getBooking = /* GraphQL */ `query GetBooking($id: ID!) {
  getBooking(id: $id) {
    id
    userId
    boatId
    boatOwnerId
    startDate
    endDate
    totalHours
    totalDays
    pricePerHour
    pricePerDay
    totalAmount
    status
    paymentStatus
    guestCount
    specialRequests
    user {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    boat {
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
      __typename
    }
    payment {
      id
      userId
      bookingId
      amount
      currency
      paymentMethod
      paymentProvider
      transactionId
      status
      paidAt
      refundedAt
      createdAt
      updatedAt
      __typename
    }
    review {
      id
      userId
      boatId
      bookingId
      rating
      comment
      images
      cleanlinessRating
      communicationRating
      accuracyRating
      valueRating
      approved
      createdAt
      updatedAt
      __typename
    }
    createdAt
    updatedAt
    bookingPaymentId
    bookingReviewId
    __typename
  }
}
` as GeneratedQuery<
  APITypes.GetBookingQueryVariables,
  APITypes.GetBookingQuery
>;
export const listBookings = /* GraphQL */ `query ListBookings(
  $filter: ModelBookingFilterInput
  $limit: Int
  $nextToken: String
) {
  listBookings(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      id
      userId
      boatId
      boatOwnerId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      guestCount
      specialRequests
      createdAt
      updatedAt
      bookingPaymentId
      bookingReviewId
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListBookingsQueryVariables,
  APITypes.ListBookingsQuery
>;
export const getReservation = /* GraphQL */ `query GetReservation($id: ID!) {
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
      __typename
    }
    quote {
      subtotal
      taxes
      serviceFee
      totalAmount
      currency
      __typename
    }
    status
    expiresAt
    user {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    boat {
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
      __typename
    }
    createdAt
    updatedAt
    __typename
  }
}
` as GeneratedQuery<
  APITypes.GetReservationQueryVariables,
  APITypes.GetReservationQuery
>;
export const listReservations = /* GraphQL */ `query ListReservations(
  $filter: ModelReservationFilterInput
  $limit: Int
  $nextToken: String
) {
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
      status
      expiresAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListReservationsQueryVariables,
  APITypes.ListReservationsQuery
>;
export const getPayment = /* GraphQL */ `query GetPayment($id: ID!) {
  getPayment(id: $id) {
    id
    userId
    bookingId
    amount
    currency
    paymentMethod
    paymentProvider
    transactionId
    status
    paidAt
    refundedAt
    user {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    booking {
      id
      userId
      boatId
      boatOwnerId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      guestCount
      specialRequests
      createdAt
      updatedAt
      bookingPaymentId
      bookingReviewId
      __typename
    }
    createdAt
    updatedAt
    __typename
  }
}
` as GeneratedQuery<
  APITypes.GetPaymentQueryVariables,
  APITypes.GetPaymentQuery
>;
export const listPayments = /* GraphQL */ `query ListPayments(
  $filter: ModelPaymentFilterInput
  $limit: Int
  $nextToken: String
) {
  listPayments(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      id
      userId
      bookingId
      amount
      currency
      paymentMethod
      paymentProvider
      transactionId
      status
      paidAt
      refundedAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListPaymentsQueryVariables,
  APITypes.ListPaymentsQuery
>;
export const getNotification = /* GraphQL */ `query GetNotification($id: ID!) {
  getNotification(id: $id) {
    id
    userId
    title
    message
    type
    read
    relatedId
    actionUrl
    user {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    createdAt
    updatedAt
    __typename
  }
}
` as GeneratedQuery<
  APITypes.GetNotificationQueryVariables,
  APITypes.GetNotificationQuery
>;
export const listNotifications = /* GraphQL */ `query ListNotifications(
  $filter: ModelNotificationFilterInput
  $limit: Int
  $nextToken: String
) {
  listNotifications(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      id
      userId
      title
      message
      type
      read
      relatedId
      actionUrl
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListNotificationsQueryVariables,
  APITypes.ListNotificationsQuery
>;
export const usersByEmail = /* GraphQL */ `query UsersByEmail(
  $email: String!
  $sortDirection: ModelSortDirection
  $filter: ModelUserFilterInput
  $limit: Int
  $nextToken: String
) {
  usersByEmail(
    email: $email
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.UsersByEmailQueryVariables,
  APITypes.UsersByEmailQuery
>;
export const bookingsByUserId = /* GraphQL */ `query BookingsByUserId(
  $userId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelBookingFilterInput
  $limit: Int
  $nextToken: String
) {
  bookingsByUserId(
    userId: $userId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      boatId
      boatOwnerId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      guestCount
      specialRequests
      createdAt
      updatedAt
      bookingPaymentId
      bookingReviewId
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.BookingsByUserIdQueryVariables,
  APITypes.BookingsByUserIdQuery
>;
export const bookingsByBoatId = /* GraphQL */ `query BookingsByBoatId(
  $boatId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelBookingFilterInput
  $limit: Int
  $nextToken: String
) {
  bookingsByBoatId(
    boatId: $boatId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      boatId
      boatOwnerId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      guestCount
      specialRequests
      createdAt
      updatedAt
      bookingPaymentId
      bookingReviewId
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.BookingsByBoatIdQueryVariables,
  APITypes.BookingsByBoatIdQuery
>;
export const bookingsByStatus = /* GraphQL */ `query BookingsByStatus(
  $status: BookingStatus!
  $sortDirection: ModelSortDirection
  $filter: ModelBookingFilterInput
  $limit: Int
  $nextToken: String
) {
  bookingsByStatus(
    status: $status
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      boatId
      boatOwnerId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      guestCount
      specialRequests
      createdAt
      updatedAt
      bookingPaymentId
      bookingReviewId
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.BookingsByStatusQueryVariables,
  APITypes.BookingsByStatusQuery
>;
export const reservationsByUserId = /* GraphQL */ `query ReservationsByUserId(
  $userId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelReservationFilterInput
  $limit: Int
  $nextToken: String
) {
  reservationsByUserId(
    userId: $userId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
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
      status
      expiresAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ReservationsByUserIdQueryVariables,
  APITypes.ReservationsByUserIdQuery
>;
export const reservationsByBoatId = /* GraphQL */ `query ReservationsByBoatId(
  $boatId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelReservationFilterInput
  $limit: Int
  $nextToken: String
) {
  reservationsByBoatId(
    boatId: $boatId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
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
      status
      expiresAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ReservationsByBoatIdQueryVariables,
  APITypes.ReservationsByBoatIdQuery
>;
export const paymentsByUserId = /* GraphQL */ `query PaymentsByUserId(
  $userId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelPaymentFilterInput
  $limit: Int
  $nextToken: String
) {
  paymentsByUserId(
    userId: $userId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      bookingId
      amount
      currency
      paymentMethod
      paymentProvider
      transactionId
      status
      paidAt
      refundedAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.PaymentsByUserIdQueryVariables,
  APITypes.PaymentsByUserIdQuery
>;
export const paymentsByBookingId = /* GraphQL */ `query PaymentsByBookingId(
  $bookingId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelPaymentFilterInput
  $limit: Int
  $nextToken: String
) {
  paymentsByBookingId(
    bookingId: $bookingId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      bookingId
      amount
      currency
      paymentMethod
      paymentProvider
      transactionId
      status
      paidAt
      refundedAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.PaymentsByBookingIdQueryVariables,
  APITypes.PaymentsByBookingIdQuery
>;
export const paymentsByStatus = /* GraphQL */ `query PaymentsByStatus(
  $status: PaymentStatus!
  $sortDirection: ModelSortDirection
  $filter: ModelPaymentFilterInput
  $limit: Int
  $nextToken: String
) {
  paymentsByStatus(
    status: $status
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      bookingId
      amount
      currency
      paymentMethod
      paymentProvider
      transactionId
      status
      paidAt
      refundedAt
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.PaymentsByStatusQueryVariables,
  APITypes.PaymentsByStatusQuery
>;
export const notificationsByUserId = /* GraphQL */ `query NotificationsByUserId(
  $userId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelNotificationFilterInput
  $limit: Int
  $nextToken: String
) {
  notificationsByUserId(
    userId: $userId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      title
      message
      type
      read
      relatedId
      actionUrl
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.NotificationsByUserIdQueryVariables,
  APITypes.NotificationsByUserIdQuery
>;
export const getBoat = /* GraphQL */ `query GetBoat($id: ID!) {
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
      __typename
    }
    specifications {
      length
      engine
      fuel
      year
      __typename
    }
    amenities
    availability {
      available
      blockedDates
      __typename
    }
    featured
    ownerId
    owner {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    bookings {
      nextToken
      __typename
    }
    reservations {
      nextToken
      __typename
    }
    boatReviews {
      nextToken
      __typename
    }
    createdAt
    updatedAt
    __typename
  }
}
` as GeneratedQuery<APITypes.GetBoatQueryVariables, APITypes.GetBoatQuery>;
export const listBoats = /* GraphQL */ `query ListBoats(
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
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<APITypes.ListBoatsQueryVariables, APITypes.ListBoatsQuery>;
export const boatsByName = /* GraphQL */ `query BoatsByName(
  $name: String!
  $sortDirection: ModelSortDirection
  $filter: ModelBoatFilterInput
  $limit: Int
  $nextToken: String
) {
  boatsByName(
    name: $name
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
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
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.BoatsByNameQueryVariables,
  APITypes.BoatsByNameQuery
>;
export const boatsByType = /* GraphQL */ `query BoatsByType(
  $type: BoatType!
  $sortDirection: ModelSortDirection
  $filter: ModelBoatFilterInput
  $limit: Int
  $nextToken: String
) {
  boatsByType(
    type: $type
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
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
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.BoatsByTypeQueryVariables,
  APITypes.BoatsByTypeQuery
>;
export const boatsByOwnerId = /* GraphQL */ `query BoatsByOwnerId(
  $ownerId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelBoatFilterInput
  $limit: Int
  $nextToken: String
) {
  boatsByOwnerId(
    ownerId: $ownerId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
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
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.BoatsByOwnerIdQueryVariables,
  APITypes.BoatsByOwnerIdQuery
>;
export const getReview = /* GraphQL */ `query GetReview($id: ID!) {
  getReview(id: $id) {
    id
    userId
    boatId
    bookingId
    rating
    comment
    images
    cleanlinessRating
    communicationRating
    accuracyRating
    valueRating
    approved
    user {
      id
      email
      name
      phone
      role
      verified
      rating
      profileImage
      dateOfBirth
      address
      createdAt
      updatedAt
      __typename
    }
    boat {
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
      __typename
    }
    booking {
      id
      userId
      boatId
      boatOwnerId
      startDate
      endDate
      totalHours
      totalDays
      pricePerHour
      pricePerDay
      totalAmount
      status
      paymentStatus
      guestCount
      specialRequests
      createdAt
      updatedAt
      bookingPaymentId
      bookingReviewId
      __typename
    }
    createdAt
    updatedAt
    __typename
  }
}
` as GeneratedQuery<APITypes.GetReviewQueryVariables, APITypes.GetReviewQuery>;
export const listReviews = /* GraphQL */ `query ListReviews(
  $filter: ModelReviewFilterInput
  $limit: Int
  $nextToken: String
) {
  listReviews(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      id
      userId
      boatId
      bookingId
      rating
      comment
      images
      cleanlinessRating
      communicationRating
      accuracyRating
      valueRating
      approved
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListReviewsQueryVariables,
  APITypes.ListReviewsQuery
>;
export const reviewsByUserId = /* GraphQL */ `query ReviewsByUserId(
  $userId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelReviewFilterInput
  $limit: Int
  $nextToken: String
) {
  reviewsByUserId(
    userId: $userId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      boatId
      bookingId
      rating
      comment
      images
      cleanlinessRating
      communicationRating
      accuracyRating
      valueRating
      approved
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ReviewsByUserIdQueryVariables,
  APITypes.ReviewsByUserIdQuery
>;
export const reviewsByBoatId = /* GraphQL */ `query ReviewsByBoatId(
  $boatId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelReviewFilterInput
  $limit: Int
  $nextToken: String
) {
  reviewsByBoatId(
    boatId: $boatId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      boatId
      bookingId
      rating
      comment
      images
      cleanlinessRating
      communicationRating
      accuracyRating
      valueRating
      approved
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ReviewsByBoatIdQueryVariables,
  APITypes.ReviewsByBoatIdQuery
>;
export const reviewsByBookingId = /* GraphQL */ `query ReviewsByBookingId(
  $bookingId: ID!
  $sortDirection: ModelSortDirection
  $filter: ModelReviewFilterInput
  $limit: Int
  $nextToken: String
) {
  reviewsByBookingId(
    bookingId: $bookingId
    sortDirection: $sortDirection
    filter: $filter
    limit: $limit
    nextToken: $nextToken
  ) {
    items {
      id
      userId
      boatId
      bookingId
      rating
      comment
      images
      cleanlinessRating
      communicationRating
      accuracyRating
      valueRating
      approved
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ReviewsByBookingIdQueryVariables,
  APITypes.ReviewsByBookingIdQuery
>;
