// src/graphql/customQueries.ts
// Queries personalizadas que no están en el archivo generado

import * as APITypes from "../API";

type GeneratedQuery<InputType, OutputType> = string & {
  __generatedQueryInput: InputType;
  __generatedQueryOutput: OutputType;
};

// Query para barcos destacados (si no existe un GSI específico)
export const boatsByFeatured = /* GraphQL */ `query BoatsByFeatured(
  $featured: Boolean!
  $sortDirection: ModelSortDirection
  $filter: ModelBoatFilterInput
  $limit: Int
  $nextToken: String
) {
  listBoats(
    filter: { 
      featured: { eq: $featured }
      and: [$filter]
    }
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
        verified
        rating
        __typename
      }
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  {
    featured: boolean;
    sortDirection?: APITypes.ModelSortDirection;
    filter?: APITypes.ModelBoatFilterInput;
    limit?: number;
    nextToken?: string;
  },
  {
    listBoats: {
      items: APITypes.Boat[];
      nextToken?: string;
    };
  }
>;

// Query mejorada para búsqueda avanzada
export const searchBoats = /* GraphQL */ `query SearchBoats(
  $filter: ModelBoatFilterInput
  $limit: Int
  $nextToken: String
  $sortDirection: ModelSortDirection
) {
  listBoats(
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
        name
        verified
        rating
        __typename
      }
      createdAt
      updatedAt
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  {
    filter?: APITypes.ModelBoatFilterInput;
    limit?: number;
    nextToken?: string;
    sortDirection?: APITypes.ModelSortDirection;
  },
  {
    listBoats: {
      items: APITypes.Boat[];
      nextToken?: string;
    };
  }
>;