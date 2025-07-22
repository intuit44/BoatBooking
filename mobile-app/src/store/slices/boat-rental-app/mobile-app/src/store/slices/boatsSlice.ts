// filepath: c:\ProyectosSimbolicos\boat-rental-app\mobile-app\src\store\slices\boatsSlice.ts
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
  listBoats,
  boatsByState // New query for fetching boats by state
} from '../../graphql/queries';

sortDirection: ModelSortDirection.DESC
// Importar tipos generados automáticamente
import * as APITypes from '../../API';

// =============================================================================
// INTERFACES Y TIPOS CORREGIDOS
// =============================================================================

// Usar los tipos generados de GraphQL para mayor compatibilidad
export type Boat = APITypes.Boat;
export type BoatType = APITypes.BoatType;
export type CreateBoatInput = APITypes.CreateBoatInput;
export type UpdateBoatInput = APITypes.UpdateBoatInput;

// Mantener interfaz personalizada para filtros de la UI
export interface BoatFilters {
  state?: string;
  type?: BoatType; // Usar tipo GraphQL
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
// ASYNC THUNKS CON TIPOS CORREGIDOS
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
        graphqlFilter.capacity = { gte: filters.capacity };
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

      return {
        boats: result.data.listBoats.items.filter((item): item is Boat => item !== null),
        nextToken: result.data.listBoats.nextToken,
        totalCount: result.data.listBoats.items.length
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

      return result.data.listBoats.items.filter((item): item is Boat => item !== null);
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

      return result.data.getBoat;
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

      return {
        boats: result.data.boatsByType.items.filter((item): item is Boat => item !== null),
        nextToken: result.data.boatsByType.nextToken
      };
    } catch (error: any) {
      console.error('Error fetching boats by type:', error);
      throw new Error(error.message || 'Failed to fetch boats by type');
    }
  }
);

/**
 * Buscar barcos por estado usando GSI
 */
export const fetchBoatsByState = createAsyncThunk(
  'boats/fetchBoatsByState',
  async (params: { state: string; limit?: number; nextToken?: string }) => {
    const { state, limit = 20, nextToken } = params;
    
    try {
      const result = await graphqlClient.graphql({
        query: boatsByState,
        variables: {
          state,
          limit,
          nextToken,
          sortDirection: ModelSortDirection.DESC
        },
      });

      return {
        boats: result.data.boatsByState.items.filter((item): item is Boat => item !== null),
        nextToken: result.data.boatsByState.nextToken
      };
    } catch (error: any) {
      console.error('Error fetching boats by state:', error);
      throw new Error(error.message || 'Failed to fetch boats by state');
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

      return result.data.createBoat;
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

      return result.data.updateBoat;
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
      state.selectedBoat = action.payload;
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
    // FETCH BOATS BY STATE
    // =============================================================================
    builder
      .addCase(fetchBoatsByState.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBoatsByState.fulfilled, (state, action) => {
        state.isLoading = false;
        state.boats = action.payload.boats;
        state.nextToken = action.payload.nextToken;
      })
      .addCase(fetchBoatsByState.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch boats by state';
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
        
        // Actualizar selectedBoat si es el mismo
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