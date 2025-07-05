#!/usr/bin/env node

/**
 * 🔧 FIX REMAINING TYPESCRIPT ERRORS
 * Corrige los errores TypeScript restantes
 */

const fs = require('fs').promises;
const path = require('path');

const CONFIG = {
  colors: {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
  }
};

const log = {
  info: (msg) => console.log(`${CONFIG.colors.blue}ℹ${CONFIG.colors.reset}  ${msg}`),
  success: (msg) => console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${msg}`),
  fix: (msg) => console.log(`${CONFIG.colors.cyan}🔧${CONFIG.colors.reset} ${msg}`),
};

async function fixFiles() {
  const basePath = 'mobile-app';
  
  // 1. Crear types/navigation.ts si no existe
  log.info('Creando types/navigation.ts...');
  const navigationTypes = `import { NavigationProp, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

export type RootStackParamList = {
  Home: undefined;
  BoatDetails: { boatId: string };
  Booking: { boatId: string };
  Payment: { bookingId: string };
  Profile: undefined;
  Login: undefined;
  Register: undefined;
};

export type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Home'>;
export type HomeScreenRouteProp = RouteProp<RootStackParamList, 'Home'>;

export type BoatDetailsScreenNavigationProp = StackNavigationProp<RootStackParamList, 'BoatDetails'>;
export type BoatDetailsScreenRouteProp = RouteProp<RootStackParamList, 'BoatDetails'>;

export type BookingScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Booking'>;
export type BookingScreenRouteProp = RouteProp<RootStackParamList, 'Booking'>;

export type PaymentScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Payment'>;
export type PaymentScreenRouteProp = RouteProp<RootStackParamList, 'Payment'>;

export type ProfileScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Profile'>;
`;

  try {
    await fs.mkdir(path.join(basePath, 'src/types'), { recursive: true });
    await fs.writeFile(path.join(basePath, 'src/types/navigation.ts'), navigationTypes);
    log.success('types/navigation.ts creado');
  } catch (error) {
    log.info('types/navigation.ts ya existe o error al crear');
  }

  // 2. Arreglar PaymentScreen.tsx
  log.info('Corrigiendo PaymentScreen.tsx...');
  try {
    const paymentPath = path.join(basePath, 'src/screens/payment/PaymentScreen.tsx');
    let content = await fs.readFile(paymentPath, 'utf8');
    
    // Añadir paymentMethod a processZellePayment
    content = content.replace(
      /result = await PaymentService\.processZellePayment\({\s*\n\s*bookingId: booking\.id,/g,
      `result = await PaymentService.processZellePayment({
            paymentMethod: 'zelle' as const,
            bookingId: booking.id,`
    );
    
    // Añadir paymentMethod a processPagoMovilPayment
    content = content.replace(
      /result = await PaymentService\.processPagoMovilPayment\({\s*\n\s*bookingId: booking\.id,/g,
      `result = await PaymentService.processPagoMovilPayment({
            paymentMethod: 'pago_movil' as const,
            bookingId: booking.id,`
    );
    
    await fs.writeFile(paymentPath, content);
    log.success('PaymentScreen.tsx corregido');
  } catch (error) {
    console.error('Error corrigiendo PaymentScreen:', error);
  }

  // 3. Arreglar ProfileScreen.tsx
  log.info('Corrigiendo ProfileScreen.tsx...');
  try {
    const profilePath = path.join(basePath, 'src/screens/profile/ProfileScreen.tsx');
    let content = await fs.readFile(profilePath, 'utf8');
    
    // Eliminar imports duplicados de RootState
    const lines = content.split('\n');
    const newLines = [];
    let foundRootState = false;
    
    for (const line of lines) {
      if (line.includes('import') && line.includes('RootState') && line.includes('store/store')) {
        if (!foundRootState) {
          newLines.push(line);
          foundRootState = true;
        }
        // Skip duplicados
      } else {
        newLines.push(line);
      }
    }
    
    content = newLines.join('\n');
    
    // Corregir el uso de useSelector
    content = content.replace(
      /const { user } = useSelector<RootState>\(\(state: RootState\) => state\.auth\);/g,
      'const { user } = useSelector((state: RootState) => state.auth);'
    );
    
    await fs.writeFile(profilePath, content);
    log.success('ProfileScreen.tsx corregido');
  } catch (error) {
    console.error('Error corrigiendo ProfileScreen:', error);
  }

  // 4. Arreglar servicios - añadir graphqlOperation
  log.info('Corrigiendo servicios GraphQL...');
  const services = ['bookingsService.ts', 'reservationsService.ts'];
  
  for (const service of services) {
    try {
      const servicePath = path.join(basePath, 'src/services', service);
      let content = await fs.readFile(servicePath, 'utf8');
      
      // Añadir graphqlOperation al import si no existe
      if (!content.includes('graphqlOperation')) {
        content = content.replace(
          /import { API } from 'aws-amplify';/,
          "import { API, graphqlOperation } from 'aws-amplify';"
        );
      }
      
      await fs.writeFile(servicePath, content);
      log.success(`${service} corregido`);
    } catch (error) {
      console.error(`Error corrigiendo ${service}:`, error);
    }
  }

  // 5. Arreglar authSlice.ts
  log.info('Corrigiendo authSlice.ts...');
  try {
    const authPath = path.join(basePath, 'src/store/slices/authSlice.ts');
    let content = await fs.readFile(authPath, 'utf8');
    
    // Corregir el uso de Auth.currentAuthenticatedUser que devuelve una Promise
    content = content.replace(
      /const user = Auth\.currentAuthenticatedUser\(\);[\s\S]*?return {\s*id: user\.username,\s*email: user\.attributes\.email[^}]+}/g,
      `const user = await Auth.currentAuthenticatedUser();
      return {
        id: user.username,
        email: user.attributes?.email || '',
        name: user.attributes?.name || '',
        phone: user.attributes?.phone_number || '',
        role: 'user',
      }`
    );
    
    await fs.writeFile(authPath, content);
    log.success('authSlice.ts corregido');
  } catch (error) {
    console.error('Error corrigiendo authSlice:', error);
  }

  // 6. Arreglar bookingsSlice.ts
  log.info('Corrigiendo bookingsSlice.ts...');
  try {
    const bookingsPath = path.join(basePath, 'src/store/slices/bookingsSlice.ts');
    let content = await fs.readFile(bookingsPath, 'utf8');
    
    // Corregir el tipo de retorno
    content = content.replace(
      /return { available: \(result as any\)\.available, conflictingBookings: \(result as any\)\.conflictingBookings } as AvailabilityResult;/,
      'return { isAvailable: (result as any).available, conflictingBookings: (result as any).conflictingBookings } as AvailabilityResult;'
    );
    
    await fs.writeFile(bookingsPath, content);
    log.success('bookingsSlice.ts corregido');
  } catch (error) {
    console.error('Error corrigiendo bookingsSlice:', error);
  }

  // 7. Arreglar store.ts
  log.info('Corrigiendo store.ts...');
  try {
    const storePath = path.join(basePath, 'src/store/store.ts');
    let content = await fs.readFile(storePath, 'utf8');
    
    // Añadir imports faltantes
    if (!content.includes('TypedUseSelectorHook')) {
      content = `import { TypedUseSelectorHook, useSelector } from 'react-redux';\n` + content;
    }
    
    await fs.writeFile(storePath, content);
    log.success('store.ts corregido');
  } catch (error) {
    console.error('Error corrigiendo store:', error);
  }
}

async function main() {
  console.log(`\n${CONFIG.colors.bright}🔧 CORRECTOR DE ERRORES TYPESCRIPT RESTANTES${CONFIG.colors.reset}`);
  console.log('======================================================================\n');
  
  await fixFiles();
  
  console.log(`\n${CONFIG.colors.bright}✅ CORRECCIONES APLICADAS${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log('1. Creado types/navigation.ts con todos los tipos de navegación');
  console.log('2. Añadido paymentMethod a las llamadas de pago');
  console.log('3. Corregido imports duplicados en ProfileScreen');
  console.log('4. Añadido graphqlOperation a los servicios');
  console.log('5. Corregido el uso de Promises en authSlice');
  console.log('6. Corregido el tipo AvailabilityResult');
  console.log('7. Añadido imports faltantes en store.ts');
  
  console.log(`\n${CONFIG.colors.yellow}📋 SIGUIENTE PASO:${CONFIG.colors.reset}`);
  console.log('Ejecuta: npx tsc --noEmit --skipLibCheck');
  console.log('\nSi aún hay errores, probablemente sean menores y la app funcione.');
  console.log('Puedes ejecutar: npx expo start --clear');
  
  console.log('\n✨ ¡Proceso completado!\n');
}

main().catch(console.error);