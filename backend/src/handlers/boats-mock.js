import { createResponse, createError  } from '../utils/response';

// Datos mock para desarrollo
const mockBoats = [
  {
    id: '1',
    name: 'Yacht Presidencial',
    type: 'yacht',
    description: 'Lujoso yacht de 45 pies perfecto para celebraciones especiales, eventos corporativos y paseos familiares. Cuenta con todas las comodidades modernas incluyendo aire acondicionado, sistema de sonido premium, cocina completa y espacios amplios para el máximo confort.',
    capacity: 12,
    pricePerHour: 250,
    pricePerDay: 1800,
    rating: 4.9,
    reviews: 47,
    images: [
      'https://picsum.photos/800/600?random=1&boat',
      'https://picsum.photos/800/600?random=2&yacht',
      'https://picsum.photos/800/600?random=3&luxury'
    ],
    location: {
      marina: 'Marina Bahía Redonda',
      state: 'Nueva Esparta',
      coordinates: {
        latitude: 11.0019,
        longitude: -63.8617
      }
    },
    specifications: {
      length: 45,
      engine: '2x Caterpillar 550HP',
      fuel: 'Diesel',
      year: 2020
    },
    amenities: [
      'Aire Acondicionado',
      'Sistema de Sonido',
      'Cocina Completa',
      'Baño Privado',
      'Nevera',
      'Equipo de Snorkel'
    ],
    owner: {
      id: 'owner1',
      name: 'Carlos Mendoza',
      phone: '+58-414-123-4567',
      rating: 4.8
    },
    availability: {
      available: true,
      blockedDates: []
    },
    featured: true,
    ownerId: 'owner1',
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z'
  },
  {
    id: '2',
    name: 'Velero Caribeño',
    type: 'sailboat',
    description: 'Hermoso velero de 38 pies ideal para navegación recreativa y deportiva. Perfecto para quienes buscan una experiencia auténtica de navegación a vela en las costas venezolanas.',
    capacity: 8,
    pricePerHour: 180,
    pricePerDay: 1200,
    rating: 4.7,
    reviews: 32,
    images: [
      'https://picsum.photos/800/600?random=5&sailboat',
      'https://picsum.photos/800/600?random=6&sailing'
    ],
    location: {
      marina: 'Puerto La Cruz Marina',
      state: 'Vargas',
      coordinates: {
        latitude: 10.4806,
        longitude: -66.9036
      }
    },
    specifications: {
      length: 38,
      engine: 'Vela + Motor auxiliar 40HP',
      fuel: 'Gasolina',
      year: 2018
    },
    amenities: [
      'Velas Profesionales',
      'Equipo de Navegación',
      'Chalecos Salvavidas',
      'Cocina Básica'
    ],
    owner: {
      id: 'owner2',
      name: 'María Rodríguez',
      phone: '+58-412-987-6543',
      rating: 4.9
    },
    availability: {
      available: true,
      blockedDates: []
    },
    featured: true,
    ownerId: 'owner2',
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z'
  },
  {
    id: '3',
    name: 'Lancha Deportiva Speed',
    type: 'motorboat',
    description: 'Emocionante lancha deportiva de alta velocidad perfecta para deportes acuáticos, esquí acuático y paseos de adrenalina.',
    capacity: 6,
    pricePerHour: 150,
    pricePerDay: 900,
    rating: 4.6,
    reviews: 28,
    images: [
      'https://picsum.photos/800/600?random=8&speedboat',
      'https://picsum.photos/800/600?random=9&motorboat'
    ],
    location: {
      marina: 'Marina Playa El Agua',
      state: 'Nueva Esparta',
      coordinates: {
        latitude: 11.0834,
        longitude: -63.7833
      }
    },
    specifications: {
      length: 28,
      engine: 'Mercury 300HP',
      fuel: 'Gasolina',
      year: 2021
    },
    amenities: [
      'Equipo de Esquí',
      'Sistema de Sonido',
      'Nevera Portátil',
      'Toldo Solar'
    ],
    owner: {
      id: 'owner3',
      name: 'José González',
      phone: '+58-416-555-0123',
      rating: 4.5
    },
    availability: {
      available: true,
      blockedDates: []
    },
    featured: false,
    ownerId: 'owner3',
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z'
  },
  {
    id: '4',
    name: 'Catamarán Tropical',
    type: 'catamaran',
    description: 'Espacioso catamarán de 42 pies con amplias zonas de descanso y estabilidad excepcional. Perfecto para familias y grupos grandes.',
    capacity: 16,
    pricePerHour: 300,
    pricePerDay: 2200,
    rating: 4.8,
    reviews: 41,
    images: [
      'https://picsum.photos/800/600?random=11&catamaran',
      'https://picsum.photos/800/600?random=12&tropical'
    ],
    location: {
      marina: 'Marina Coche',
      state: 'Nueva Esparta',
      coordinates: {
        latitude: 10.7833,
        longitude: -63.9833
      }
    },
    specifications: {
      length: 42,
      engine: '2x Yamaha 150HP',
      fuel: 'Gasolina',
      year: 2019
    },
    amenities: [
      'Doble Casco',
      'Área de Barbacoa',
      'Hamacas',
      'Bar Interior'
    ],
    owner: {
      id: 'owner4',
      name: 'Ana López',
      phone: '+58-424-111-2233',
      rating: 4.9
    },
    availability: {
      available: true,
      blockedDates: []
    },
    featured: true,
    ownerId: 'owner4',
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z'
  },
  {
    id: '5',
    name: 'Jet Ski Adventure',
    type: 'jetski',
    description: 'Moderna moto de agua de última generación para aventuras individuales o en pareja.',
    capacity: 2,
    pricePerHour: 80,
    pricePerDay: 400,
    rating: 4.4,
    reviews: 15,
    images: [
      'https://picsum.photos/800/600?random=14&jetski'
    ],
    location: {
      marina: 'Playa Caribe',
      state: 'Falcón',
      coordinates: {
        latitude: 11.7,
        longitude: -69.6
      }
    },
    specifications: {
      length: 12,
      engine: 'Yamaha 110HP',
      fuel: 'Gasolina',
      year: 2022
    },
    amenities: [
      'Chaleco Salvavidas',
      'Compartimento Estanco',
      'Sistema GPS'
    ],
    owner: {
      id: 'owner5',
      name: 'Pedro Martín',
      phone: '+58-426-789-0123',
      rating: 4.3
    },
    availability: {
      available: true,
      blockedDates: []
    },
    featured: false,
    ownerId: 'owner5',
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z'
  }
];

// Get all boats with filters
export const getBoats = async (event) => {
  try {
    const { state, type, minPrice, maxPrice, capacity, limit = 20 } = event.queryStringParameters || {};
    
    let boats = [...mockBoats];

    // Apply filters
    if (state) {
      boats = boats.filter(boat => boat.location.state === state);
    }
    if (type) {
      boats = boats.filter(boat => boat.type === type);
    }
    if (minPrice) {
      boats = boats.filter(boat => boat.pricePerHour >= parseFloat(minPrice));
    }
    if (maxPrice) {
      boats = boats.filter(boat => boat.pricePerHour <= parseFloat(maxPrice));
    }
    if (capacity) {
      boats = boats.filter(boat => boat.capacity >= parseInt(capacity));
    }

    // Apply limit
    boats = boats.slice(0, parseInt(limit));

    return createResponse(200, {
      boats,
      count: boats.length
    });

  } catch (error) {
    console.error('Error obteniendo botes:', error);
    return createError(500, 'Error al obtener botes');
  }
};

// Get boat by ID
export const getBoatById = async (event) => {
  try {
    const { id } = event.pathParameters;

    const boat = mockBoats.find(b => b.id === id);

    if (!boat) {
      return createError(404, 'Bote no encontrado');
    }

    return createResponse(200, boat);

  } catch (error) {
    console.error('Error obteniendo bote:', error);
    return createError(500, 'Error al obtener bote');
  }
};

// Get featured boats
export const getFeaturedBoats = async (event) => {
  try {
    const { limit = 10 } = event.queryStringParameters || {};

    const featuredBoats = mockBoats
      .filter(boat => boat.featured === true)
      .slice(0, parseInt(limit));

    return createResponse(200, featuredBoats);

  } catch (error) {
    console.error('Error obteniendo botes destacados:', error);
    return createError(500, 'Error al obtener botes destacados');
  }
};

// Search boats
export const searchBoats = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { 
      query, 
      state, 
      type, 
      minPrice, 
      maxPrice, 
      capacity,
      limit = 20 
    } = body;

    let boats = [...mockBoats];

    // Apply text search
    if (query) {
      const searchTerm = query.toLowerCase();
      boats = boats.filter(boat => 
        boat.name.toLowerCase().includes(searchTerm) ||
        boat.description.toLowerCase().includes(searchTerm) ||
        boat.location.marina.toLowerCase().includes(searchTerm)
      );
    }

    // Apply filters
    if (state) {
      boats = boats.filter(boat => boat.location.state === state);
    }
    if (type) {
      boats = boats.filter(boat => boat.type === type);
    }
    if (minPrice) {
      boats = boats.filter(boat => boat.pricePerHour >= parseFloat(minPrice));
    }
    if (maxPrice) {
      boats = boats.filter(boat => boat.pricePerHour <= parseFloat(maxPrice));
    }
    if (capacity) {
      boats = boats.filter(boat => boat.capacity >= parseInt(capacity));
    }

    // Apply limit
    boats = boats.slice(0, parseInt(limit));

    return createResponse(200, {
      boats,
      count: boats.length,
      query: body
    });

  } catch (error) {
    console.error('Error en búsqueda:', error);
    return createError(500, 'Error al buscar botes');
  }
};