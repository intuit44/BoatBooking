# Boat Rental App

## Overview
The Boat Rental App is a mobile application designed to facilitate the renting of boats. It allows users to browse available boats, filter them by various criteria, and manage their bookings. The application utilizes a GraphQL backend powered by AWS Amplify for data management.

## Project Structure
The project is organized into the following main directories:

- **mobile-app**: Contains the source code for the mobile application.
  - **src**: The main source directory for the application.
    - **store**: Contains Redux slices for state management.
      - **slices**: Contains the `boatsSlice.ts` file for managing boat-related state.
    - **API.ts**: Generated API interface for interacting with the GraphQL backend.
    - **graphql**: Contains GraphQL queries and mutations.
      - **queries.ts**: GraphQL queries for fetching boat data.
      - **mutations.ts**: GraphQL mutations for creating, updating, and deleting boats.
  - **amplify**: Contains the backend configuration for AWS Amplify.
    - **backend**: Backend resources for the application.
      - **api**: Contains the GraphQL API configuration.
        - **boatrentalapi**: The specific API for the boat rental service.
          - **schema.graphql**: Defines the GraphQL schema, including the `Boat` type and its indices.

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd boat-rental-app
   ```

2. **Install Dependencies**
   Navigate to the `mobile-app` directory and install the necessary dependencies:
   ```bash
   cd mobile-app
   npm install
   ```

3. **Configure AWS Amplify**
   Ensure you have the AWS Amplify CLI installed. If not, install it globally:
   ```bash
   npm install -g @aws-amplify/cli
   ```

   Configure Amplify with your AWS account:
   ```bash
   amplify configure
   ```

4. **Deploy the Backend**
   After updating the `schema.graphql` file with the necessary GSIs for the `Boat` type, run the following command to deploy the changes:
   ```bash
   amplify push
   ```

5. **Generate API Types**
   To regenerate the `API.ts` file with the new queries and types, run:
   ```bash
   amplify codegen
   ```

## Usage Guidelines
- The application allows users to filter boats by type and state using the newly defined GSIs.
- Ensure that the `Coordinates` type is fully defined in the GraphQL schema to avoid TypeScript errors.

## Contributing
Contributions to the Boat Rental App are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.