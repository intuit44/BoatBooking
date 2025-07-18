import { NavigationProp, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { StackScreenProps } from '@react-navigation/stack';

export type RootStackParamList = {
  Home: undefined;
  BoatDetails: { boatId: string };
  Booking: { boatId: string };
  Payment: { bookingId: string };
  Profile: undefined;
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  Search: {
    search?: string;
    state?: string;
    type?: string;
    priceRange?: [number, number];
    capacity?: number;
    featured?: boolean;
  } | undefined;
};

// Navigation props
export type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Home'>;
export type HomeScreenRouteProp = RouteProp<RootStackParamList, 'Home'>;

export type BoatDetailsScreenNavigationProp = StackNavigationProp<RootStackParamList, 'BoatDetails'>;
export type BoatDetailsScreenRouteProp = RouteProp<RootStackParamList, 'BoatDetails'>;

export type SearchScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Search'>;
export type SearchScreenRouteProp = RouteProp<RootStackParamList, 'Search'>;

export type BookingScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Booking'>;
export type BookingScreenRouteProp = RouteProp<RootStackParamList, 'Booking'>;

export type PaymentScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Payment'>;
export type PaymentScreenRouteProp = RouteProp<RootStackParamList, 'Payment'>;

export type ProfileScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Profile'>;
export type ProfileScreenRouteProp = RouteProp<RootStackParamList, 'Profile'>;

// Screen Props types
export type BoatDetailsScreenProps = StackScreenProps<RootStackParamList, 'BoatDetails'>;
export type HomeScreenProps = StackScreenProps<RootStackParamList, 'Home'>;
export type SearchScreenProps = StackScreenProps<RootStackParamList, 'Search'>;
export type BookingScreenProps = StackScreenProps<RootStackParamList, 'Booking'>;
export type PaymentScreenProps = StackScreenProps<RootStackParamList, 'Payment'>;
export type ProfileScreenProps = StackScreenProps<RootStackParamList, 'Profile'>;