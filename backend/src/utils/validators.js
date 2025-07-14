const Joi = require('joi');

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
const validateRegistration = (data) => {
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
const validateLogin = (data) => {
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

module.exports = {
  validateRegistration,
  validateLogin
};