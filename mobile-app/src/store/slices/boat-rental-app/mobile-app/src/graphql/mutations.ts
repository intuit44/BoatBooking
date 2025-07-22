// This file contains the GraphQL mutations for creating, updating, and deleting boats.

import { gql } from 'apollo-server-express';

export const createBoat = gql`
  mutation CreateBoat($input: CreateBoatInput!) {
    createBoat(input: $input) {
      id
      name
      description
      pricePerDay
      capacity
      featured
      type
      coordinates {
        latitude
        longitude
      }
    }
  }
`;

export const updateBoat = gql`
  mutation UpdateBoat($input: UpdateBoatInput!) {
    updateBoat(input: $input) {
      id
      name
      description
      pricePerDay
      capacity
      featured
      type
      coordinates {
        latitude
        longitude
      }
    }
  }
`;

export const deleteBoat = gql`
  mutation DeleteBoat($input: DeleteBoatInput!) {
    deleteBoat(input: $input) {
      id
    }
  }
`;