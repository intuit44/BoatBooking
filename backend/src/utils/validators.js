const Joi = require('joi');

// User registration validation
exports.validateRegistration = (data) => {
  const schema = Joi.object({
    name: Joi.string().min(2).max(100).required(),
    email: Joi.string().email().required(),
    password: Joi.string().min(6).required(),
    phone: Joi.string().pattern(/^[0-9+\-\s()]+$/).required(),
    acceptTerms: Joi.boolean().valid(true).required()
  });

  return schema.validate(data);
};

// User login validation
exports.validateLogin = (data) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required()
  });

  return schema.validate(data);
};

// Boat validation
exports.validateBoat = (data) => {
  const schema = Joi.object({
    name: Joi.string().min(2).max(100).required(),
    description: Joi.string().min(10).max(1000).required(),
    type: Joi.string().valid('yacht', 'sailboat', 'motorboat', 'jetski', 'catamaran').required(),
    capacity: Joi.number().integer().min(1).max(50).required(),
    pricePerHour: Joi.number().positive().required(),
    currency: Joi.string().valid('USD', 'VES', 'COP').default('USD'),
    images: Joi.array().items(Joi.string().uri()).min(1).required(),
    location: Joi.object({
      state: Joi.string().required(),
      city: Joi.string().required(),
      marina: Joi.string().required(),
      address: Joi.string().required(),
      coordinates: Joi.object({
        latitude: Joi.number().required(),
        longitude: Joi.number().required()
      }).required()
    }).required(),
    amenities: Joi.array().items(Joi.string()),
    specifications: Joi.object({
      length: Joi.number().positive(),
      engine: Joi.string(),
      fuel: Joi.string(),
      year: Joi.number().integer().min(1950).max(new Date().getFullYear() + 1)
    }),
    rules: Joi.array().items(Joi.string()),
    cancellationPolicy: Joi.string()
  });

  return schema.validate(data);
};

// Booking validation
exports.validateBooking = (data) => {
  const schema = Joi.object({
    boatId: Joi.string().required(),
    startDate: Joi.string().pattern(/^\d{4}-\d{2}-\d{2}$/).required(),
    endDate: Joi.string().pattern(/^\d{4}-\d{2}-\d{2}$/).required(),
    startTime: Joi.string().pattern(/^\d{2}:\d{2}$/).required(),
    endTime: Joi.string().pattern(/^\d{2}:\d{2}$/).required(),
    guests: Joi.number().integer().min(1).required(),
    paymentMethod: Joi.string().valid('zelle', 'pago_movil', 'binance', 'cash').required(),
    specialRequests: Joi.string().max(500).allow(''),
    contactInfo: Joi.object({
      name: Joi.string().min(2).max(100).required(),
      phone: Joi.string().pattern(/^[0-9+\-\s()]+$/).required(),
      email: Joi.string().email().required()
    }).required()
  });

  return schema.validate(data);
};

// Payment validation
exports.validatePayment = (data) => {
  const schema = Joi.object({
    bookingId: Joi.string().required(),
    paymentMethod: Joi.string().valid('zelle', 'pago_movil', 'binance', 'cash').required(),
    amount: Joi.number().positive().required(),
    currency: Joi.string().valid('USD', 'VES', 'COP').required(),
    referenceNumber: Joi.string().allow(''),
    paymentData: Joi.object().when('paymentMethod', {
      is: 'zelle',
      then: Joi.object({
        email: Joi.string().email().required()
      }),
      otherwise: Joi.when('paymentMethod', {
        is: 'pago_movil',
        then: Joi.object({
          phone: Joi.string().required(),
          bank: Joi.string().required()
        }),
        otherwise: Joi.when('paymentMethod', {
          is: 'binance',
          then: Joi.object({
            binanceId: Joi.string().required()
          }),
          otherwise: Joi.object()
        })
      })
    })
  });

  return schema.validate(data);
};