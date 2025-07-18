// src/config/payment.config.ts
/**
 * Configuración de pagos para la aplicación
 * Este archivo centraliza todas las configuraciones relacionadas con pagos
 */

export const PaymentConfig = {
  // API Gateway endpoint para procesamiento de pagos
  API_ENDPOINT: process.env.EXPO_PUBLIC_API_ENDPOINT || 'https://your-api-gateway-url.amazonaws.com/dev',
  
  // Configuración de Zelle
  ZELLE: {
    recipientEmail: 'payments@boatrentals.ve',
    recipientName: 'Boat Rentals VE',
    maxAmount: 10000,
    minAmount: 10
  },
  
  // Configuración de Pago Móvil
  PAGO_MOVIL: {
    bankName: 'Banco de Venezuela',
    bankCode: '0102',
    phoneNumber: '0414-1234567',
    cedula: 'V-12345678',
    accountHolder: 'Boat Rentals C.A.'
  },
  
  // Configuración de Binance Pay
  BINANCE: {
    merchantId: process.env.EXPO_PUBLIC_BINANCE_MERCHANT_ID || '',
    apiKey: process.env.EXPO_PUBLIC_BINANCE_API_KEY || '',
    walletAddress: '0x1234567890abcdef...',
    supportedCryptos: ['USDT', 'BTC', 'ETH']
  },
  
  // Configuración de Stripe (para futuro uso)
  STRIPE: {
    publishableKey: process.env.EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY || '',
    merchantId: process.env.EXPO_PUBLIC_STRIPE_MERCHANT_ID || '',
    androidPayMode: 'test', // 'test' o 'production'
    merchantName: 'Boat Rentals'
  },
  
  // Configuración de PayPal (para futuro uso)
  PAYPAL: {
    clientId: process.env.EXPO_PUBLIC_PAYPAL_CLIENT_ID || '',
    environment: 'sandbox', // 'sandbox' o 'production'
    merchantName: 'Boat Rentals'
  },
  
  // Configuración de Apple Pay (para futuro uso)
  APPLE_PAY: {
    merchantId: process.env.EXPO_PUBLIC_APPLE_PAY_MERCHANT_ID || '',
    countryCode: 'US',
    currencyCode: 'USD',
    merchantName: 'Boat Rentals',
    supportedNetworks: ['visa', 'mastercard', 'amex']
  },
  
  // Configuración de Google Pay (para futuro uso)
  GOOGLE_PAY: {
    merchantId: process.env.EXPO_PUBLIC_GOOGLE_PAY_MERCHANT_ID || '',
    merchantName: 'Boat Rentals',
    environment: 'TEST', // 'TEST' o 'PRODUCTION'
    allowedCardNetworks: ['AMEX', 'DISCOVER', 'JCB', 'MASTERCARD', 'VISA'],
    allowedCardAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS']
  },
  
  // Timeouts y reintentos
  REQUEST_TIMEOUT: 30000, // 30 segundos
  MAX_RETRIES: 3,
  
  // Mensajes de error personalizados
  ERROR_MESSAGES: {
    NETWORK_ERROR: 'Error de conexión. Por favor verifica tu internet.',
    TIMEOUT: 'La operación tardó demasiado. Por favor intenta nuevamente.',
    INVALID_PAYMENT: 'Los datos del pago son inválidos.',
    PAYMENT_EXISTS: 'Este pago ya fue procesado.',
    INSUFFICIENT_FUNDS: 'Fondos insuficientes para completar la transacción.',
    GENERIC: 'Ocurrió un error al procesar el pago. Por favor intenta más tarde.'
  },
  
  // Mensajes de éxito
  SUCCESS_MESSAGES: {
    PAYMENT_COMPLETED: '¡Pago completado exitosamente!',
    PAYMENT_PENDING: 'Tu pago está siendo procesado. Te notificaremos cuando esté confirmado.',
    RECEIPT_SENT: 'El recibo ha sido enviado a tu correo electrónico.'
  }
};

// Validador de configuración
export function validatePaymentConfig(): boolean {
  const requiredEnvVars = [
    'EXPO_PUBLIC_API_ENDPOINT'
  ];
  
  const missingVars = requiredEnvVars.filter(
    varName => !process.env[varName]
  );
  
  if (missingVars.length > 0) {
    console.warn(`Missing environment variables: ${missingVars.join(', ')}`);
    return false;
  }
  
  return true;
}

// Helper para obtener la configuración de un método de pago específico
export function getPaymentMethodConfig(method: string): any {
  const configs: Record<string, any> = {
    zelle: PaymentConfig.ZELLE,
    pago_movil: PaymentConfig.PAGO_MOVIL,
    binance: PaymentConfig.BINANCE,
    stripe: PaymentConfig.STRIPE,
    paypal: PaymentConfig.PAYPAL,
    apple_pay: PaymentConfig.APPLE_PAY,
    google_pay: PaymentConfig.GOOGLE_PAY
  };
  
  return configs[method] || null;
}

// Ejemplo de archivo .env necesario:
/*
# .env.local o .env

# API Configuration
EXPO_PUBLIC_API_ENDPOINT=https://api.boatrentals.ve/v1

# Payment Providers
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51...
EXPO_PUBLIC_STRIPE_MERCHANT_ID=merchant.com.boatrentals

EXPO_PUBLIC_PAYPAL_CLIENT_ID=AZD...
EXPO_PUBLIC_PAYPAL_SECRET=EH5...

EXPO_PUBLIC_BINANCE_MERCHANT_ID=123456
EXPO_PUBLIC_BINANCE_API_KEY=abc...

EXPO_PUBLIC_APPLE_PAY_MERCHANT_ID=merchant.com.boatrentals.apple
EXPO_PUBLIC_GOOGLE_PAY_MERCHANT_ID=BCR2DN6T...
*/