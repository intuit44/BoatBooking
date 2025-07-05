import Joi from 'joi';

// Constantes para evitar repetición y facilitar mantenimiento
const BOAT_TYPES = ['yacht', 'sailboat', 'motorboat', 'jetski', 'catamaran'];
const CURRENCIES = ['USD', 'VES', 'COP'];
const PAYMENT_METHODS = ['zelle', 'pago_movil', 'binance', 'cash', 'stripe'];
const VENEZUELAN_STATES = [
  'Amazonas', 'Anzoátegui', 'Apure', 'Aragua', 'Barinas', 'Bolívar',
  'Carabobo', 'Cojedes', 'Delta Amacuro', 'Distrito Capital', 'Falcón',
  'Guárico', 'Lara', 'Mérida', 'Miranda', 'Monagas', 'Nueva Esparta',
  'Portuguesa', 'Sucre', 'Táchira', 'Trujillo', 'Vargas', 'Yaracuy', 'Zulia'
];

// Mensajes personalizados en español
const messages = {
  'string.empty': 'Este campo no puede estar vacío',
  'any.required': 'Este campo es obligatorio',
  'string.email': 'Debe ser un email válido',
  'string.min': 'Debe tener al menos {#limit} caracteres',
  'string.max': 'No puede exceder {#limit} caracteres',
  'number.min': 'El valor mínimo es {#limit}',
  'number.max': 'El valor máximo es {#limit}',
  'number.positive': 'Debe ser un número positivo'
};

// User registration validation
export const validateRegistration = (data) => {
  const schema = Joi.object({
    name: Joi.string()
      .min(2)
      .max(100)
      .trim()
      .required()
      .messages({
        'string.min': 'El nombre debe tener al menos 2 caracteres',
        'string.max': 'El nombre no puede exceder 100 caracteres'
      }),
    email: Joi.string()
      .email()
      .lowercase()
      .trim()
      .required()
      .messages({
        'string.email': 'Por favor ingresa un email válido'
      }),
    password: Joi.string()
      .min(8)
      .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
      .required()
      .messages({
        'string.min': 'La contraseña debe tener al menos 8 caracteres',
        'string.pattern.base': 'La contraseña debe contener mayúsculas, minúsculas, números y caracteres especiales'
      }),
    phone: Joi.string()
      .pattern(/^(\+58|0)?[0-9]{10}$/)
      .required()
      .messages({
        'string.pattern.base': 'Ingresa un número de teléfono venezolano válido'
      }),
    acceptTerms: Joi.boolean()
      .valid(true)
      .required()
      .messages({
        'any.only': 'Debes aceptar los términos y condiciones'
      })
  }).messages(messages);

  return schema.validate(data, { abortEarly: false });
};

// User login validation
export const validateLogin = (data) => {
  const schema = Joi.object({
    email: Joi.string()
      .email()
      .lowercase()
      .trim()
      .required()
      .messages({
        'string.email': 'Por favor ingresa un email válido'
      }),
    password: Joi.string()
      .required()
      .messages({
        'any.required': 'La contraseña es requerida'
      })
  }).messages(messages);

  return schema.validate(data);
};

// Boat validation
export const validateBoat = (data) => {
  const schema = Joi.object({
    name: Joi.string()
      .min(2)
      .max(100)
      .trim()
      .required()
      .messages({
        'string.min': 'El nombre del bote debe tener al menos 2 caracteres'
      }),
    description: Joi.string()
      .min(10)
      .max(1000)
      .trim()
      .required()
      .messages({
        'string.min': 'La descripción debe tener al menos 10 caracteres',
        'string.max': 'La descripción no puede exceder 1000 caracteres'
      }),
    type: Joi.string()
      .valid(...BOAT_TYPES)
      .required()
      .messages({
        'any.only': `El tipo debe ser uno de: ${BOAT_TYPES.join(', ')}`
      }),
    capacity: Joi.number()
      .integer()
      .min(1)
      .max(50)
      .required()
      .messages({
        'number.min': 'La capacidad mínima es 1 persona',
        'number.max': 'La capacidad máxima es 50 personas'
      }),
    pricePerHour: Joi.number()
      .positive()
      .precision(2)
      .required()
      .messages({
        'number.positive': 'El precio debe ser mayor a 0'
      }),
    currency: Joi.string()
      .valid(...CURRENCIES)
      .default('USD'),
    images: Joi.array()
      .items(Joi.string().uri())
      .min(1)
      .max(10)
      .required()
      .messages({
        'array.min': 'Debes subir al menos una imagen',
        'array.max': 'Máximo 10 imágenes permitidas'
      }),
    location: Joi.object({
      state: Joi.string()
        .valid(...VENEZUELAN_STATES)
        .required()
        .messages({
          'any.only': 'Selecciona un estado válido de Venezuela'
        }),
      city: Joi.string()
        .min(2)
        .max(100)
        .required(),
      marina: Joi.string()
        .min(2)
        .max(100)
        .required(),
      address: Joi.string()
        .min(5)
        .max(200)
        .required(),
      coordinates: Joi.object({
        latitude: Joi.number()
          .min(-90)
          .max(90)
          .required(),
        longitude: Joi.number()
          .min(-180)
          .max(180)
          .required()
      }).required()
    }).required(),
    amenities: Joi.array()
      .items(Joi.string().max(50))
      .max(20)
      .default([]),
    specifications: Joi.object({
      length: Joi.number()
        .positive()
        .max(500)
        .messages({
          'number.max': 'La eslora no puede exceder 500 pies'
        }),
      engine: Joi.string()
        .max(100),
      fuel: Joi.string()
        .valid('gasolina', 'diesel', 'electrico')
        .messages({
          'any.only': 'Tipo de combustible inválido'
        }),
      year: Joi.number()
        .integer()
        .min(1950)
        .max(new Date().getFullYear() + 1)
        .messages({
          'number.min': 'El año mínimo es 1950',
          'number.max': 'El año no puede ser futuro'
        })
    }).default({}),
    rules: Joi.array()
      .items(Joi.string().max(200))
      .max(10)
      .default([]),
    cancellationPolicy: Joi.string()
      .max(500)
      .default('Cancelación gratuita hasta 24 horas antes'),
    featured: Joi.boolean()
      .default(false),
    active: Joi.boolean()
      .default(true)
  }).messages(messages);

  return schema.validate(data, { abortEarly: false });
};

// Booking validation
export const validateBooking = (data) => {
  const schema = Joi.object({
    boatId: Joi.string()
      .uuid()
      .required()
      .messages({
        'string.guid': 'ID de bote inválido'
      }),
    startDate: Joi.date()
      .iso()
      .min('now')
      .required()
      .messages({
        'date.min': 'La fecha de inicio debe ser futura'
      }),
    endDate: Joi.date()
      .iso()
      .min(Joi.ref('startDate'))
      .required()
      .messages({
        'date.min': 'La fecha de fin debe ser posterior a la de inicio'
      }),
    startTime: Joi.string()
      .pattern(/^([01]\d|2[0-3]):([0-5]\d)$/)
      .required()
      .messages({
        'string.pattern.base': 'Formato de hora inválido (HH:MM)'
      }),
    endTime: Joi.string()
      .pattern(/^([01]\d|2[0-3]):([0-5]\d)$/)
      .required()
      .messages({
        'string.pattern.base': 'Formato de hora inválido (HH:MM)'
      }),
    guests: Joi.number()
      .integer()
      .min(1)
      .required()
      .messages({
        'number.min': 'Mínimo 1 invitado'
      }),
    paymentMethod: Joi.string()
      .valid(...PAYMENT_METHODS)
      .required()
      .messages({
        'any.only': `Método de pago debe ser: ${PAYMENT_METHODS.join(', ')}`
      }),
    specialRequests: Joi.string()
      .max(500)
      .trim()
      .allow('')
      .default(''),
    contactInfo: Joi.object({
      name: Joi.string()
        .min(2)
        .max(100)
        .required(),
      phone: Joi.string()
        .pattern(/^(\+58|0)?[0-9]{10}$/)
        .required()
        .messages({
          'string.pattern.base': 'Número de teléfono inválido'
        }),
      email: Joi.string()
        .email()
        .required()
    }).required(),
    totalPrice: Joi.number()
      .positive()
      .precision(2)
      .required()
  }).messages(messages);

  return schema.validate(data, { abortEarly: false });
};

// Payment validation
export const validatePayment = (data) => {
  const schema = Joi.object({
    bookingId: Joi.string()
      .uuid()
      .required(),
    paymentMethod: Joi.string()
      .valid(...PAYMENT_METHODS)
      .required(),
    amount: Joi.number()
      .positive()
      .precision(2)
      .required(),
    currency: Joi.string()
      .valid(...CURRENCIES)
      .required(),
    referenceNumber: Joi.string()
      .allow('')
      .default(''),
    paymentData: Joi.when('paymentMethod', [
      {
        is: 'zelle',
        then: Joi.object({
          email: Joi.string()
            .email()
            .required()
            .messages({
              'string.email': 'Email de Zelle inválido'
            }),
          holderName: Joi.string()
            .min(2)
            .max(100)
        }).required()
      },
      {
        is: 'pago_movil',
        then: Joi.object({
          phone: Joi.string()
            .pattern(/^(0412|0414|0416|0424|0426)[0-9]{7}$/)
            .required()
            .messages({
              'string.pattern.base': 'Número de pago móvil inválido'
            }),
          bank: Joi.string()
            .valid('Banco de Venezuela', 'Banesco', 'Mercantil', 'Provincial', 'BOD', 'Bicentenario')
            .required(),
          cedula: Joi.string()
            .pattern(/^[VE]-?\d{6,8}$/)
            .required()
        }).required()
      },
      {
        is: 'binance',
        then: Joi.object({
          binanceId: Joi.string()
            .min(5)
            .max(50)
            .required(),
          transactionId: Joi.string()
            .required()
        }).required()
      },
      {
        is: 'stripe',
        then: Joi.object({
          paymentIntentId: Joi.string()
            .required(),
          paymentMethodId: Joi.string()
            .required()
        }).required()
      }
    ]),
    notes: Joi.string()
      .max(500)
      .allow('')
  }).messages(messages);

  return schema.validate(data, { abortEarly: false });
};

// Search validation
export const validateSearch = (data) => {
  const schema = Joi.object({
    location: Joi.object({
      state: Joi.string()
        .valid(...VENEZUELAN_STATES),
      city: Joi.string()
        .min(2)
        .max(100)
    }),
    dates: Joi.object({
      start: Joi.date()
        .iso()
        .min('now'),
      end: Joi.date()
        .iso()
        .min(Joi.ref('start'))
    }),
    guests: Joi.number()
      .integer()
      .min(1)
      .max(50),
    type: Joi.string()
      .valid(...BOAT_TYPES),
    priceRange: Joi.object({
      min: Joi.number()
        .positive()
        .default(0),
      max: Joi.number()
        .positive()
        .min(Joi.ref('min'))
    }),
    amenities: Joi.array()
      .items(Joi.string()),
    sortBy: Joi.string()
      .valid('price_asc', 'price_desc', 'rating', 'newest')
      .default('rating'),
    page: Joi.number()
      .integer()
      .min(1)
      .default(1),
    limit: Joi.number()
      .integer()
      .min(1)
      .max(50)
      .default(20)
  }).messages(messages);

  return schema.validate(data);
};

// Update boat status validation
export const validateBoatStatus = (data) => {
  const schema = Joi.object({
    active: Joi.boolean()
      .required(),
    reason: Joi.when('active', {
      is: false,
      then: Joi.string()
        .min(10)
        .max(200)
        .required()
        .messages({
          'string.min': 'La razón debe tener al menos 10 caracteres'
        }),
      otherwise: Joi.forbidden()
    })
  }).messages(messages);

  return schema.validate(data);
};

// Rating validation
export const validateRating = (data) => {
  const schema = Joi.object({
    bookingId: Joi.string()
      .uuid()
      .required(),
    rating: Joi.number()
      .integer()
      .min(1)
      .max(5)
      .required()
      .messages({
        'number.min': 'La calificación mínima es 1',
        'number.max': 'La calificación máxima es 5'
      }),
    comment: Joi.string()
      .min(10)
      .max(500)
      .trim()
      .required()
      .messages({
        'string.min': 'El comentario debe tener al menos 10 caracteres'
      }),
    aspects: Joi.object({
      cleanliness: Joi.number().integer().min(1).max(5),
      communication: Joi.number().integer().min(1).max(5),
      accuracy: Joi.number().integer().min(1).max(5),
      value: Joi.number().integer().min(1).max(5)
    })
  }).messages(messages);

  return schema.validate(data, { abortEarly: false });
};