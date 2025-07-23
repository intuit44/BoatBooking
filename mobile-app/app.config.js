import 'dotenv/config';

export default {
  expo: {
    name: "Boat Rental App",
    slug: "boat-rental-app",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    splash: {
      image: "./assets/splash.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff"
    },
    assetBundlePatterns: [
      "**/*"
    ],
    ios: {
      supportsTablet: true
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#FFFFFF"
      }
    },
    web: {
      favicon: "./assets/favicon.png"
    },
    // ✅ CONFIGURACIÓN CLAVE: Variables de entorno expuestas
    extra: {
      apiEndpoint: process.env.EXPO_PUBLIC_API_ENDPOINT,
      env: process.env.EXPO_PUBLIC_ENV || 'development',
      stripePublishableKey: process.env.EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY,
      mapboxToken: process.env.EXPO_PUBLIC_MAPBOX_TOKEN,
      userPoolId: process.env.EXPO_PUBLIC_USER_POOL_ID,
      userPoolClientId: process.env.EXPO_PUBLIC_USER_POOL_CLIENT_ID,
      identityPoolId: process.env.EXPO_PUBLIC_IDENTITY_POOL_ID,
      awsRegion: process.env.EXPO_PUBLIC_AWS_REGION,
      graphqlEndpoint: process.env.EXPO_PUBLIC_GRAPHQL_ENDPOINT,
      apiKey: process.env.EXPO_PUBLIC_API_KEY,
      s3Bucket: process.env.EXPO_PUBLIC_S3_BUCKET,
      oauthDomain: process.env.EXPO_PUBLIC_OAUTH_DOMAIN,
    },
    scheme: "boat-rental-app",
    // ✅ PLUGINS ACTUALIZADOS: Agregar expo-font
    plugins: [
      "expo-router",
      "expo-font"
    ]
  }
};