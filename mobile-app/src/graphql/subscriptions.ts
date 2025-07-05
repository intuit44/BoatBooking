/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "../API";
type GeneratedSubscription<InputType, OutputType> = string & {
  __generatedSubscriptionInput: InputType;
  __generatedSubscriptionOutput: OutputType;
};

export const onCreateUser = /* GraphQL */ `subscription OnCreateUser(
  $filter: ModelSubscriptionUserFilterInput
  $id: String
) {
  onCreateUser(filter: $filter, id: $id) {
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
` as GeneratedSubscription<
  APITypes.OnCreateUserSubscriptionVariables,
  APITypes.OnCreateUserSubscription
>;
export const onUpdateUser = /* GraphQL */ `subscription OnUpdateUser(
  $filter: ModelSubscriptionUserFilterInput
  $id: String
) {
  onUpdateUser(filter: $filter, id: $id) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateUserSubscriptionVariables,
  APITypes.OnUpdateUserSubscription
>;
export const onDeleteUser = /* GraphQL */ `subscription OnDeleteUser(
  $filter: ModelSubscriptionUserFilterInput
  $id: String
) {
  onDeleteUser(filter: $filter, id: $id) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteUserSubscriptionVariables,
  APITypes.OnDeleteUserSubscription
>;
export const onCreateBooking = /* GraphQL */ `subscription OnCreateBooking(
  $filter: ModelSubscriptionBookingFilterInput
  $userId: String
  $boatOwnerId: String
) {
  onCreateBooking(filter: $filter, userId: $userId, boatOwnerId: $boatOwnerId) {
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
` as GeneratedSubscription<
  APITypes.OnCreateBookingSubscriptionVariables,
  APITypes.OnCreateBookingSubscription
>;
export const onUpdateBooking = /* GraphQL */ `subscription OnUpdateBooking(
  $filter: ModelSubscriptionBookingFilterInput
  $userId: String
  $boatOwnerId: String
) {
  onUpdateBooking(filter: $filter, userId: $userId, boatOwnerId: $boatOwnerId) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateBookingSubscriptionVariables,
  APITypes.OnUpdateBookingSubscription
>;
export const onDeleteBooking = /* GraphQL */ `subscription OnDeleteBooking(
  $filter: ModelSubscriptionBookingFilterInput
  $userId: String
  $boatOwnerId: String
) {
  onDeleteBooking(filter: $filter, userId: $userId, boatOwnerId: $boatOwnerId) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteBookingSubscriptionVariables,
  APITypes.OnDeleteBookingSubscription
>;
export const onCreateReservation = /* GraphQL */ `subscription OnCreateReservation(
  $filter: ModelSubscriptionReservationFilterInput
  $userId: String
) {
  onCreateReservation(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnCreateReservationSubscriptionVariables,
  APITypes.OnCreateReservationSubscription
>;
export const onUpdateReservation = /* GraphQL */ `subscription OnUpdateReservation(
  $filter: ModelSubscriptionReservationFilterInput
  $userId: String
) {
  onUpdateReservation(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateReservationSubscriptionVariables,
  APITypes.OnUpdateReservationSubscription
>;
export const onDeleteReservation = /* GraphQL */ `subscription OnDeleteReservation(
  $filter: ModelSubscriptionReservationFilterInput
  $userId: String
) {
  onDeleteReservation(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteReservationSubscriptionVariables,
  APITypes.OnDeleteReservationSubscription
>;
export const onCreatePayment = /* GraphQL */ `subscription OnCreatePayment(
  $filter: ModelSubscriptionPaymentFilterInput
  $userId: String
) {
  onCreatePayment(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnCreatePaymentSubscriptionVariables,
  APITypes.OnCreatePaymentSubscription
>;
export const onUpdatePayment = /* GraphQL */ `subscription OnUpdatePayment(
  $filter: ModelSubscriptionPaymentFilterInput
  $userId: String
) {
  onUpdatePayment(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnUpdatePaymentSubscriptionVariables,
  APITypes.OnUpdatePaymentSubscription
>;
export const onDeletePayment = /* GraphQL */ `subscription OnDeletePayment(
  $filter: ModelSubscriptionPaymentFilterInput
  $userId: String
) {
  onDeletePayment(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnDeletePaymentSubscriptionVariables,
  APITypes.OnDeletePaymentSubscription
>;
export const onCreateNotification = /* GraphQL */ `subscription OnCreateNotification(
  $filter: ModelSubscriptionNotificationFilterInput
  $userId: String
) {
  onCreateNotification(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnCreateNotificationSubscriptionVariables,
  APITypes.OnCreateNotificationSubscription
>;
export const onUpdateNotification = /* GraphQL */ `subscription OnUpdateNotification(
  $filter: ModelSubscriptionNotificationFilterInput
  $userId: String
) {
  onUpdateNotification(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateNotificationSubscriptionVariables,
  APITypes.OnUpdateNotificationSubscription
>;
export const onDeleteNotification = /* GraphQL */ `subscription OnDeleteNotification(
  $filter: ModelSubscriptionNotificationFilterInput
  $userId: String
) {
  onDeleteNotification(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteNotificationSubscriptionVariables,
  APITypes.OnDeleteNotificationSubscription
>;
export const onCreateBoat = /* GraphQL */ `subscription OnCreateBoat($filter: ModelSubscriptionBoatFilterInput) {
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
` as GeneratedSubscription<
  APITypes.OnCreateBoatSubscriptionVariables,
  APITypes.OnCreateBoatSubscription
>;
export const onUpdateBoat = /* GraphQL */ `subscription OnUpdateBoat($filter: ModelSubscriptionBoatFilterInput) {
  onUpdateBoat(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateBoatSubscriptionVariables,
  APITypes.OnUpdateBoatSubscription
>;
export const onDeleteBoat = /* GraphQL */ `subscription OnDeleteBoat($filter: ModelSubscriptionBoatFilterInput) {
  onDeleteBoat(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteBoatSubscriptionVariables,
  APITypes.OnDeleteBoatSubscription
>;
export const onCreateReview = /* GraphQL */ `subscription OnCreateReview(
  $filter: ModelSubscriptionReviewFilterInput
  $userId: String
) {
  onCreateReview(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnCreateReviewSubscriptionVariables,
  APITypes.OnCreateReviewSubscription
>;
export const onUpdateReview = /* GraphQL */ `subscription OnUpdateReview(
  $filter: ModelSubscriptionReviewFilterInput
  $userId: String
) {
  onUpdateReview(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateReviewSubscriptionVariables,
  APITypes.OnUpdateReviewSubscription
>;
export const onDeleteReview = /* GraphQL */ `subscription OnDeleteReview(
  $filter: ModelSubscriptionReviewFilterInput
  $userId: String
) {
  onDeleteReview(filter: $filter, userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteReviewSubscriptionVariables,
  APITypes.OnDeleteReviewSubscription
>;
