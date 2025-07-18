import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { BoatsService } from '../../services/boatsService';

export interface Boat {
  id: string;
  name: string;
  type: 'yacht' | 'sailboat' | 'motorboat' | 'catamaran' | 'jetski';
  description: string;
  capacity: number;
  pricePerHour: number;
  pricePerDay: number;
  rating: number;
  reviews: number;
  images: string[];
  location: {
    marina: string;
    state: string;
    coordinates: {
      latitude: number;
      longitude: number;
    };
  };
  specifications: {
    length: number;
    engine: string;
    fuel: string;
    year: number;
  };
  amenities: string[];
  owner: {
    id: string;
    name: string;
    phone: string;
    rating: number;
    email: string;
    verified: boolean;
  };
  availability: {
    available: boolean;
    blockedDates: string[];
  };
  featured: boolean;
  createdAt?: string;
  updatedAt?: string;
}



export interface BoatFilters {
  state?: string;
  type?: string;
  priceRange?: [number, number];
  capacity?: number;
  search?: string;
  featured?: boolean;
}

interface BoatsState {
  boats: Boat[];
  featuredBoats: Boat[];
  selectedBoat: Boat | null;
  filters: BoatFilters;
  isLoading: boolean;
  error: string | null;
}

const initialState: BoatsState = {
  boats: [],
  featuredBoats: [],
  selectedBoat: null,
  filters: {},
  isLoading: false,
  error: null,
};

// Async Thunks para DynamoDB
export const fetchBoats = createAsyncThunk(
  'boats/fetchBoats',
  async (filters: BoatFilters = {}) => {
    const result = await BoatsService.searchBoats(filters);
    if (!result.success) {
      throw new Error('Failed to fetch boats');
    }
    return result.data as Boat[];
  }
);

export const fetchFeaturedBoats = createAsyncThunk(
  'boats/fetchFeaturedBoats',
  async () => {
    const result = await BoatsService.getFeaturedBoats();
    if (!result.success) {
      throw new Error('Failed to fetch featured boats');
    }
    return result.data as Boat[];
  }
);

export const fetchBoatById = createAsyncThunk(
  'boats/fetchBoatById',
  async (boatId: string) => {
    const result = await BoatsService.getBoatById(boatId);
    if (!result.success) {
      throw new Error('Failed to fetch boat details');
    }
    return result.data as Boat;
  }
);

export const createBoat = createAsyncThunk(
  'boats/createBoat',
  async (boatData: Omit<Boat, 'id' | 'createdAt'>) => {
    const result = await BoatsService.createBoat(boatData);
    if (!result.success) {
      throw new Error('Failed to create boat');
    }
    return result.data as Boat;
  }
);

export const updateBoat = createAsyncThunk(
  'boats/updateBoat',
  async ({ boatId, updates }: { boatId: string; updates: Partial<Boat> }) => {
    const result = await BoatsService.updateBoat(boatId, updates);
    if (!result.success) {
      throw new Error('Failed to update boat');
    }
    return result.data as Boat;
  }
);

export const deleteBoat = createAsyncThunk(
  'boats/deleteBoat',
  async (boatId: string) => {
    const result = await BoatsService.deleteBoat(boatId);
    if (!result.success) {
      throw new Error('Failed to delete boat');
    }
    return boatId;
  }
);

const boatsSlice = createSlice({
  name: 'boats',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<BoatFilters>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setSelectedBoat: (state, action: PayloadAction<Boat | null>) => {
      state.selectedBoat = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch Boats
    builder
      .addCase(fetchBoats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBoats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats = action.payload;
      })
      .addCase(fetchBoats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch boats';
      });

    // Fetch Featured Boats
    builder
      .addCase(fetchFeaturedBoats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchFeaturedBoats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.featuredBoats = action.payload;
      })
      .addCase(fetchFeaturedBoats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch featured boats';
      });

    // Fetch Boat by ID
    builder
      .addCase(fetchBoatById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBoatById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selectedBoat = action.payload;
      })
      .addCase(fetchBoatById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch boat details';
      });

    // Create Boat
    builder
      .addCase(createBoat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createBoat.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats.push(action.payload);
      })
      .addCase(createBoat.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create boat';
      });

    // Update Boat
    builder
      .addCase(updateBoat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateBoat.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.boats.findIndex(boat => boat.id === action.payload.id);
        if (index !== -1) {
          state.boats[index] = action.payload;
        }
        if (state.selectedBoat?.id === action.payload.id) {
          state.selectedBoat = action.payload;
        }
      })
      .addCase(updateBoat.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to update boat';
      });

    // Delete Boat
    builder
      .addCase(deleteBoat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteBoat.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats = state.boats.filter(boat => boat.id !== action.payload);
        if (state.selectedBoat?.id === action.payload) {
          state.selectedBoat = null;
        }
      })
      .addCase(deleteBoat.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to delete boat';
      });
  },
});

export const { setFilters, clearFilters, setSelectedBoat, clearError } = boatsSlice.actions;
export default boatsSlice.reducer;