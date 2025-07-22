import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { generateClient } from 'aws-amplify/api';
import { ModelSortDirection } from '../../API';
import {
  createBoat as createBoatMutation,
  deleteBoat as deleteBoatMutation,
  updateBoat as updateBoatMutation
} from '../../graphql/mutations';
import {
  boatsByType,
  getBoat,
  listBoats
} from '../../graphql/queries';

// Importar tipos generados automáticamente
import * as APITypes from '../../API';

// =============================================================================
// INTERFACES Y TIPOS CORREGIDOS
// =============================================================================

// ✅ Crear tipo personalizado más flexible para el state
export interface BoatLocation {
  marina: string;
  state: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
}

export interface BoatState {
  id: string;
  name: string;
  type: APITypes.BoatType;
  description?: string;
  capacity: number;
  pricePerHour: number;
  pricePerDay: number;
  rating?: number;
  reviews?: number;
  images?: string[];
  amenities?: string[];
  location?: BoatLocation;
  owner?: {
    id: string;
    name: string;
    email?: string;
    phone?: string;
  };
  availability?: {
    available: boolean;
    blockedDates?: string[];
  };
  featured: boolean;
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}

// Usar el tipo personalizado para el state de Redux
export type Boat = BoatState;
export type BoatType = APITypes.BoatType;
export type CreateBoatInput = APITypes.CreateBoatInput;
export type UpdateBoatInput = APITypes.UpdateBoatInput;

// Mantener interfaz personalizada para filtros de la UI
export interface BoatFilters {
  state?: string;
  type?: BoatType;
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
  totalCount?: number;
  nextToken?: string;
}

const initialState: BoatsState = {
  boats: [],
  featuredBoats: [],
  selectedBoat: null,
  filters: {},
  isLoading: false,
  error: null,
  totalCount: 0,
  nextToken: undefined,
};

// =============================================================================
// GRAPHQL CLIENT INSTANCE
// =============================================================================

const graphqlClient = generateClient();

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * ✅ Normalizar datos de GraphQL a formato esperado por Redux
 */
function normalizeBoatData(rawBoat: any): Boat {
  return {
    id: rawBoat.id,
    name: rawBoat.name || '',
    type: rawBoat.type,
    description: rawBoat.description || undefined,
    capacity: rawBoat.capacity || 0,
    pricePerHour: rawBoat.pricePerHour || 0,
    pricePerDay: rawBoat.pricePerDay || 0,
    rating: rawBoat.rating || undefined,
    reviews: rawBoat.reviews || undefined,
    images: rawBoat.images || undefined,
    amenities: rawBoat.amenities || undefined,
    
    // ✅ Normalizar location con coordinates por defecto
    location: rawBoat.location ? {
      marina: rawBoat.location.marina || '',
      state: rawBoat.location.state || '',
      coordinates: {
        latitude: rawBoat.location.coordinates?.latitude || 0,
        longitude: rawBoat.location.coordinates?.longitude || 0,
      }
    } : undefined,
    
    // ✅ Normalizar owner
    owner: rawBoat.owner ? {
      id: rawBoat.owner.id,
      name: rawBoat.owner.name || '',
      email: rawBoat.owner.email || undefined,
      phone: rawBoat.owner.phone || undefined,
    } : undefined,
    
    // ✅ Normalizar availability
    availability: rawBoat.availability ? {
      available: rawBoat.availability.available ?? false,
      blockedDates: rawBoat.availability.blockedDates || undefined,
    } : undefined,
    
    featured: rawBoat.featured ?? false,
    ownerId: rawBoat.ownerId || '',
    createdAt: rawBoat.createdAt || new Date().toISOString(),
    updatedAt: rawBoat.updatedAt || new Date().toISOString(),
  };
}

/**
 * ✅ Normalizar array de boats
 */
function normalizeBoatsArray(rawBoats: any[]): Boat[] {
  return rawBoats
    .filter((item): item is NonNullable<typeof item> => item !== null)
    .map(normalizeBoatData);
}

/**
 * ✅ Verificar si un barco es válido
 */
function isValidBoat(boat: any): boat is Boat {
  return (
    boat &&
    boat.id &&
    boat.location &&
    boat.location.coordinates &&
    Array.isArray(boat.location.coordinates)
  );
}

// =============================================================================
// ASYNC THUNKS CON NORMALIZACIÓN
// =============================================================================

/**
 * Buscar barcos con filtros usando GraphQL
 */
export const fetchBoats = createAsyncThunk(
  'boats/fetchBoats',
  async (params: { filters?: BoatFilters; limit?: number; nextToken?: string } = {}) => {
    const { filters = {}, limit = 20, nextToken } = params;
    
    try {
      // Construir filtro GraphQL usando tipos correctos
      const graphqlFilter: APITypes.ModelBoatFilterInput = {};
      
      if (filters.type) {
        graphqlFilter.type = { eq: filters.type };
      }
      
      if (filters.capacity) {
        graphqlFilter.capacity = { ge: filters.capacity };
      }
      
      if (filters.priceRange) {
        graphqlFilter.pricePerDay = {
          between: filters.priceRange
        };
      }
      
      if (filters.search) {
        graphqlFilter.or = [
          { name: { contains: filters.search } },
          { description: { contains: filters.search } }
        ];
      }
      
      if (filters.featured !== undefined) {
        graphqlFilter.featured = { eq: filters.featured };
      }

      const result = await graphqlClient.graphql({
        query: listBoats,
        variables: {
          filter: Object.keys(graphqlFilter).length > 0 ? graphqlFilter : undefined,
          limit,
          nextToken
        },
      });

      // ✅ Normalizar datos antes de retornar
      const normalizedBoats = normalizeBoatsArray(result.data.listBoats.items);

      return {
        boats: normalizedBoats,
        nextToken: result.data.listBoats.nextToken || undefined,
        totalCount: normalizedBoats.length
      };
    } catch (error: any) {
      console.error('Error fetching boats:', error);
      throw new Error(error.message || 'Failed to fetch boats');
    }
  }
);

/**
 * Obtener barcos destacados - Usar filtro en lugar de GSI que no existe
 */
export const fetchFeaturedBoats = createAsyncThunk(
  'boats/fetchFeaturedBoats',
  async (limit: number = 10) => {
    try {
      const result = await graphqlClient.graphql({
        query: listBoats,
        variables: {
          filter: {
            featured: { eq: true }
          },
          limit
        },
      });

      // ✅ Normalizar datos antes de retornar
      return normalizeBoatsArray(result.data.listBoats.items);
    } catch (error: any) {
      console.error('Error fetching featured boats:', error);
      throw new Error(error.message || 'Failed to fetch featured boats');
    }
  }
);

/**
 * Obtener barco por ID
 */
export const fetchBoatById = createAsyncThunk(
  'boats/fetchBoatById',
  async (boatId: string) => {
    try {
      const result = await graphqlClient.graphql({
        query: getBoat,
        variables: {
          id: boatId
        },
      });

      if (!result.data.getBoat) {
        throw new Error('Boat not found');
      }

      // ✅ Normalizar datos antes de retornar
      return normalizeBoatData(result.data.getBoat);
    } catch (error: any) {
      console.error('Error fetching boat by ID:', error);
      throw new Error(error.message || 'Failed to fetch boat details');
    }
  }
);

/**
 * Buscar barcos por tipo usando GSI
 */
export const fetchBoatsByType = createAsyncThunk(
  'boats/fetchBoatsByType',
  async (params: { type: BoatType; limit?: number; nextToken?: string }) => {
    const { type, limit = 20, nextToken } = params;
    
    try {
      const result = await graphqlClient.graphql({
        query: boatsByType,
        variables: {
          type,
          limit,
          nextToken,
          sortDirection: ModelSortDirection.DESC
        },
      });

      // ✅ Normalizar datos antes de retornar
      const normalizedBoats = normalizeBoatsArray(result.data.boatsByType.items);

      return {
        boats: normalizedBoats,
        nextToken: result.data.boatsByType.nextToken || undefined
      };
    } catch (error: any) {
      console.error('Error fetching boats by type:', error);
      throw new Error(error.message || 'Failed to fetch boats by type');
    }
  }
);

/**
 * Crear nuevo barco
 */
export const createBoat = createAsyncThunk(
  'boats/createBoat',
  async (boatData: Omit<CreateBoatInput, 'id'> & { ownerId: string }) => {
    try {
      const input: CreateBoatInput = {
        ...boatData,
        // Asegurar que los campos requeridos estén presentes
        rating: boatData.rating || 0,
        reviews: boatData.reviews || 0,
        featured: boatData.featured || false,
      };

      const result = await graphqlClient.graphql({
        query: createBoatMutation,
        variables: {
          input
        },
      });

      if (!result.data.createBoat) {
        throw new Error('Failed to create boat');
      }

      // ✅ Normalizar datos antes de retornar
      return normalizeBoatData(result.data.createBoat);
    } catch (error: any) {
      console.error('Error creating boat:', error);
      throw new Error(error.message || 'Failed to create boat');
    }
  }
);

/**
 * Actualizar barco existente
 */
export const updateBoat = createAsyncThunk(
  'boats/updateBoat',
  async (params: { boatId: string; updates: Partial<UpdateBoatInput> }) => {
    const { boatId, updates } = params;
    
    try {
      const input: UpdateBoatInput = {
        id: boatId,
        ...updates
      };

      const result = await graphqlClient.graphql({
        query: updateBoatMutation,
        variables: {
          input
        },
      });

      if (!result.data.updateBoat) {
        throw new Error('Failed to update boat');
      }

      // ✅ Normalizar datos antes de retornar
      return normalizeBoatData(result.data.updateBoat);
    } catch (error: any) {
      console.error('Error updating boat:', error);
      throw new Error(error.message || 'Failed to update boat');
    }
  }
);

/**
 * Eliminar barco
 */
export const deleteBoat = createAsyncThunk(
  'boats/deleteBoat',
  async (boatId: string) => {
    try {
      const result = await graphqlClient.graphql({
        query: deleteBoatMutation,
        variables: {
          input: {
            id: boatId
          }
        },
      });

      return boatId;
    } catch (error: any) {
      console.error('Error deleting boat:', error);
      throw new Error(error.message || 'Failed to delete boat');
    }
  }
);

// =============================================================================
// SLICE DEFINITION
// =============================================================================

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
      // ✅ Ahora funciona correctamente porque los datos están normalizados
      if (isValidBoat(action.payload)) {
        state.selectedBoat = action.payload;
      } else {
        // Maneja el error o asigna un valor por defecto
      }
    },
    clearError: (state) => {
      state.error = null;
    },
    clearBoats: (state) => {
      state.boats = [];
      state.nextToken = undefined;
    },
    appendBoats: (state, action: PayloadAction<Boat[]>) => {
      // Para paginación - agregar más barcos sin reemplazar
      state.boats = [...state.boats, ...action.payload];
    },
    resetState: (state) => {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    // =============================================================================
    // FETCH BOATS
    // =============================================================================
    builder
      .addCase(fetchBoats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBoats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats = action.payload.boats;
        state.nextToken = action.payload.nextToken;
        state.totalCount = action.payload.totalCount;
      })
      .addCase(fetchBoats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch boats';
      });

    // =============================================================================
    // FETCH FEATURED BOATS
    // =============================================================================
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

    // =============================================================================
    // FETCH BOAT BY ID
    // =============================================================================
    builder
      .addCase(fetchBoatById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBoatById.fulfilled, (state, action) => {
        state.isLoading = false;
        // ✅ Ahora funciona porque action.payload está normalizado
        state.selectedBoat = action.payload;
        
        // También actualizar en la lista si existe
        const index = state.boats.findIndex(boat => boat.id === action.payload.id);
        if (index !== -1) {
          state.boats[index] = action.payload;
        }
      })
      .addCase(fetchBoatById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch boat details';
      });

    // =============================================================================
    // FETCH BOATS BY TYPE
    // =============================================================================
    builder
      .addCase(fetchBoatsByType.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBoatsByType.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats = action.payload.boats;
        state.nextToken = action.payload.nextToken;
      })
      .addCase(fetchBoatsByType.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch boats by type';
      });

    // =============================================================================
    // CREATE BOAT
    // =============================================================================
    builder
      .addCase(createBoat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createBoat.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats.unshift(action.payload); // Agregar al inicio
        
        // Si es destacado, también agregarlo a featuredBoats
        if (action.payload.featured) {
          state.featuredBoats.unshift(action.payload);
        }
      })
      .addCase(createBoat.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create boat';
      });

    // =============================================================================
    // UPDATE BOAT
    // =============================================================================
    builder
      .addCase(updateBoat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateBoat.fulfilled, (state, action) => {
        state.isLoading = false;
        
        // Actualizar en boats
        const index = state.boats.findIndex(boat => boat.id === action.payload.id);
        if (index !== -1) {
          state.boats[index] = action.payload;
        }
        
        // Actualizar en featuredBoats si aplica
        const featuredIndex = state.featuredBoats.findIndex(boat => boat.id === action.payload.id);
        if (action.payload.featured && featuredIndex === -1) {
          // Agregar a featured si ahora es destacado
          state.featuredBoats.push(action.payload);
        } else if (!action.payload.featured && featuredIndex !== -1) {
          // Remover de featured si ya no es destacado
          state.featuredBoats.splice(featuredIndex, 1);
        } else if (featuredIndex !== -1) {
          // Actualizar en featured
          state.featuredBoats[featuredIndex] = action.payload;
        }
        
        // ✅ Actualizar selectedBoat si es el mismo - ahora funciona
        if (state.selectedBoat?.id === action.payload.id) {
          state.selectedBoat = action.payload;
        }
      })
      .addCase(updateBoat.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to update boat';
      });

    // =============================================================================
    // DELETE BOAT
    // =============================================================================
    builder
      .addCase(deleteBoat.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteBoat.fulfilled, (state, action) => {
        state.isLoading = false;
        
        // Remover de boats
        state.boats = state.boats.filter(boat => boat.id !== action.payload);
        
        // Remover de featuredBoats
        state.featuredBoats = state.featuredBoats.filter(boat => boat.id !== action.payload);
        
        // Limpiar selectedBoat si es el mismo
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

// =============================================================================
// EXPORTS
// =============================================================================

export const { 
  setFilters, 
  clearFilters, 
  setSelectedBoat, 
  clearError,
  clearBoats,
  appendBoats,
  resetState
} = boatsSlice.actions;

export default boatsSlice.reducer;

// =============================================================================
// SELECTORS CON TIPOS CORREGIDOS
// =============================================================================

export const selectAllBoats = (state: { boats: BoatsState }) => state.boats.boats;
export const selectFeaturedBoats = (state: { boats: BoatsState }) => state.boats.featuredBoats;
export const selectSelectedBoat = (state: { boats: BoatsState }) => state.boats.selectedBoat;
export const selectBoatsLoading = (state: { boats: BoatsState }) => state.boats.isLoading;
export const selectBoatsError = (state: { boats: BoatsState }) => state.boats.error;
export const selectBoatsFilters = (state: { boats: BoatsState }) => state.boats.filters;
export const selectHasMoreBoats = (state: { boats: BoatsState }) => !!state.boats.nextToken;

// =============================================================================
// HELPER TYPES PARA USO EN COMPONENTES
// =============================================================================

export type BoatTypeOptions = BoatType;

// Enum values para usar en componentes
export const BoatTypeEnum = APITypes.BoatType;

// Helper para convertir string a BoatType
export const stringToBoatType = (type: string): BoatType => {
  const upperType = type.toUpperCase() as keyof typeof BoatTypeEnum;
  return BoatTypeEnum[upperType] || BoatTypeEnum.YACHT;
};