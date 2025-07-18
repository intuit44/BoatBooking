/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "../API";
type GeneratedMutation<InputType, OutputType> = string & {
  __generatedMutationInput: InputType;
  __generatedMutationOutput: OutputType;
};

export const createUser = /* GraphQL */ `mutation CreateUser(
  $input: CreateUserInput!
  $condition: ModelUserConditionInput
) {
  createUser(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.CreateUserMutationVariables,
  APITypes.CreateUserMutation
>;
export const updateUser = /* GraphQL */ `mutation UpdateUser(
  $input: UpdateUserInput!
  $condition: ModelUserConditionInput
) {
  updateUser(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdateUserMutationVariables,
  APITypes.UpdateUserMutation
>;
export const deleteUser = /* GraphQL */ `mutation DeleteUser(
  $input: DeleteUserInput!
  $condition: ModelUserConditionInput
) {
  deleteUser(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeleteUserMutationVariables,
  APITypes.DeleteUserMutation
>;
export const createBoat = /* GraphQL */ `mutation CreateBoat(
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
` as GeneratedMutation<
  APITypes.CreateBoatMutationVariables,
  APITypes.CreateBoatMutation
>;
export const updateBoat = /* GraphQL */ `mutation UpdateBoat(
  $input: UpdateBoatInput!
  $condition: ModelBoatConditionInput
) {
  updateBoat(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdateBoatMutationVariables,
  APITypes.UpdateBoatMutation
>;
export const deleteBoat = /* GraphQL */ `mutation DeleteBoat(
  $input: DeleteBoatInput!
  $condition: ModelBoatConditionInput
) {
  deleteBoat(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeleteBoatMutationVariables,
  APITypes.DeleteBoatMutation
>;
export const createBooking = /* GraphQL */ `mutation CreateBooking(
  $input: CreateBookingInput!
  $condition: ModelBookingConditionInput
) {
  createBooking(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.CreateBookingMutationVariables,
  APITypes.CreateBookingMutation
>;
export const updateBooking = /* GraphQL */ `mutation UpdateBooking(
  $input: UpdateBookingInput!
  $condition: ModelBookingConditionInput
) {
  updateBooking(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdateBookingMutationVariables,
  APITypes.UpdateBookingMutation
>;
export const deleteBooking = /* GraphQL */ `mutation DeleteBooking(
  $input: DeleteBookingInput!
  $condition: ModelBookingConditionInput
) {
  deleteBooking(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeleteBookingMutationVariables,
  APITypes.DeleteBookingMutation
>;
export const createReservation = /* GraphQL */ `mutation CreateReservation(
  $input: CreateReservationInput!
  $condition: ModelReservationConditionInput
) {
  createReservation(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.CreateReservationMutationVariables,
  APITypes.CreateReservationMutation
>;
export const updateReservation = /* GraphQL */ `mutation UpdateReservation(
  $input: UpdateReservationInput!
  $condition: ModelReservationConditionInput
) {
  updateReservation(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdateReservationMutationVariables,
  APITypes.UpdateReservationMutation
>;
export const deleteReservation = /* GraphQL */ `mutation DeleteReservation(
  $input: DeleteReservationInput!
  $condition: ModelReservationConditionInput
) {
  deleteReservation(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeleteReservationMutationVariables,
  APITypes.DeleteReservationMutation
>;
export const createPayment = /* GraphQL */ `mutation CreatePayment(
  $input: CreatePaymentInput!
  $condition: ModelPaymentConditionInput
) {
  createPayment(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.CreatePaymentMutationVariables,
  APITypes.CreatePaymentMutation
>;
export const updatePayment = /* GraphQL */ `mutation UpdatePayment(
  $input: UpdatePaymentInput!
  $condition: ModelPaymentConditionInput
) {
  updatePayment(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdatePaymentMutationVariables,
  APITypes.UpdatePaymentMutation
>;
export const deletePayment = /* GraphQL */ `mutation DeletePayment(
  $input: DeletePaymentInput!
  $condition: ModelPaymentConditionInput
) {
  deletePayment(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeletePaymentMutationVariables,
  APITypes.DeletePaymentMutation
>;
export const createReview = /* GraphQL */ `mutation CreateReview(
  $input: CreateReviewInput!
  $condition: ModelReviewConditionInput
) {
  createReview(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.CreateReviewMutationVariables,
  APITypes.CreateReviewMutation
>;
export const updateReview = /* GraphQL */ `mutation UpdateReview(
  $input: UpdateReviewInput!
  $condition: ModelReviewConditionInput
) {
  updateReview(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdateReviewMutationVariables,
  APITypes.UpdateReviewMutation
>;
export const deleteReview = /* GraphQL */ `mutation DeleteReview(
  $input: DeleteReviewInput!
  $condition: ModelReviewConditionInput
) {
  deleteReview(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeleteReviewMutationVariables,
  APITypes.DeleteReviewMutation
>;
export const createNotification = /* GraphQL */ `mutation CreateNotification(
  $input: CreateNotificationInput!
  $condition: ModelNotificationConditionInput
) {
  createNotification(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.CreateNotificationMutationVariables,
  APITypes.CreateNotificationMutation
>;
export const updateNotification = /* GraphQL */ `mutation UpdateNotification(
  $input: UpdateNotificationInput!
  $condition: ModelNotificationConditionInput
) {
  updateNotification(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.UpdateNotificationMutationVariables,
  APITypes.UpdateNotificationMutation
>;
export const deleteNotification = /* GraphQL */ `mutation DeleteNotification(
  $input: DeleteNotificationInput!
  $condition: ModelNotificationConditionInput
) {
  deleteNotification(input: $input, condition: $condition) {
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
` as GeneratedMutation<
  APITypes.DeleteNotificationMutationVariables,
  APITypes.DeleteNotificationMutation
>;
