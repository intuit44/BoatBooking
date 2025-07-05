#!/usr/bin/env node

/**
 * 🔧 CORRECCIONES FINALES DE TYPESCRIPT
 * Corrige los últimos errores pendientes
 */

const fs = require('fs').promises;
const path = require('path');

const CONFIG = {
  colors: {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    green: '\x1b[32m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
  }
};

const log = {
  info: (msg) => console.log(`${CONFIG.colors.blue}ℹ${CONFIG.colors.reset}  ${msg}`),
  success: (msg) => console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${msg}`),
  fix: (msg) => console.log(`${CONFIG.colors.cyan}🔧${CONFIG.colors.reset} ${msg}`),
};

async function updateNavigationTypes() {
  const filePath = path.join('mobile-app', 'src/types/navigation.ts');
  
  const content = `import { NavigationProp, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

export type RootStackParamList = {
  Home: undefined;
  BoatDetails: { boatId: string };
  Booking: { boatId: string };
  Payment: { bookingId: string };
  Profile: undefined;
  Login: undefined;
  Register: undefined;
  Search: {
    search?: string;
    state?: string;
    type?: string;
    priceRange?: [number, number];
    capacity?: number;
    featured?: boolean;
  } | undefined;
};

// Navigation props
export type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Home'>;
export type HomeScreenRouteProp = RouteProp<RootStackParamList, 'Home'>;

export type BoatDetailsScreenNavigationProp = StackNavigationProp<RootStackParamList, 'BoatDetails'>;
export type BoatDetailsScreenRouteProp = RouteProp<RootStackParamList, 'BoatDetails'>;

export type SearchScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Search'>;
export type SearchScreenRouteProp = RouteProp<RootStackParamList, 'Search'>;

export type BookingScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Booking'>;
export type BookingScreenRouteProp = RouteProp<RootStackParamList, 'Booking'>;

export type PaymentScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Payment'>;
export type PaymentScreenRouteProp = RouteProp<RootStackParamList, 'Payment'>;

export type ProfileScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Profile'>;
export type ProfileScreenRouteProp = RouteProp<RootStackParamList, 'Profile'>;

// Screen Props types
export type BoatDetailsScreenProps = NativeStackScreenProps<RootStackParamList, 'BoatDetails'>;
export type HomeScreenProps = NativeStackScreenProps<RootStackParamList, 'Home'>;
export type SearchScreenProps = NativeStackScreenProps<RootStackParamList, 'Search'>;
export type BookingScreenProps = NativeStackScreenProps<RootStackParamList, 'Booking'>;
export type PaymentScreenProps = NativeStackScreenProps<RootStackParamList, 'Payment'>;
export type ProfileScreenProps = NativeStackScreenProps<RootStackParamList, 'Profile'>;
`;

  await fs.writeFile(filePath, content);
  log.success('navigation.ts actualizado con todos los tipos necesarios');
}

async function fixServices() {
  const services = ['bookingsService.ts', 'reservationsService.ts'];
  
  for (const service of services) {
    try {
      const filePath = path.join('mobile-app', 'src/services', service);
      let content = await fs.readFile(filePath, 'utf8');
      
      // Corregir el import de API y graphqlOperation
      if (content.includes("import { API } from 'aws-amplify';") && !content.includes('graphqlOperation')) {
        content = content.replace(
          "import { API } from 'aws-amplify';",
          "import { API, graphqlOperation } from 'aws-amplify';"
        );
        
        await fs.writeFile(filePath, content);
        log.success(`${service}: añadido graphqlOperation al import`);
      }
    } catch (error) {
      log.info(`Error procesando ${service}: ${error.message}`);
    }
  }
}

async function fixStore() {
  const storePath = path.join('mobile-app', 'src/store/store.ts');
  
  try {
    let content = await fs.readFile(storePath, 'utf8');
    
    // Añadir imports faltantes al inicio del archivo
    if (!content.includes('TypedUseSelectorHook')) {
      const importStatement = "import { TypedUseSelectorHook, useSelector } from 'react-redux';\n";
      
      // Buscar el primer import para insertar después
      const firstImportIndex = content.indexOf('import');
      if (firstImportIndex !== -1) {
        const endOfFirstImport = content.indexOf('\n', firstImportIndex);
        content = content.slice(0, endOfFirstImport + 1) + importStatement + content.slice(endOfFirstImport + 1);
      } else {
        // Si no hay imports, añadir al principio
        content = importStatement + content;
      }
      
      await fs.writeFile(storePath, content);
      log.success('store.ts: añadidos imports necesarios');
    }
  } catch (error) {
    log.info(`Error procesando store.ts: ${error.message}`);
  }
}

async function createMissingFiles() {
  // Crear SearchScreen si no existe
  const searchScreenPath = path.join('mobile-app', 'src/screens/search/SearchScreen.tsx');
  
  try {
    await fs.access(searchScreenPath);
  } catch {
    // El archivo no existe, crearlo
    const searchScreenContent = `import React from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Text, Searchbar, Chip, Card } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { SearchScreenProps } from '../../types/navigation';

export const SearchScreen: React.FC<SearchScreenProps> = ({ route }) => {
  const navigation = useNavigation();
  const params = route.params;
  
  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="Buscar embarcaciones..."
        value={params?.search || ''}
        onChangeText={() => {}}
        style={styles.searchbar}
      />
      
      <View style={styles.filters}>
        {params?.type && <Chip style={styles.chip}>Tipo: {params.type}</Chip>}
        {params?.state && <Chip style={styles.chip}>Estado: {params.state}</Chip>}
        {params?.featured && <Chip style={styles.chip}>Destacados</Chip>}
      </View>
      
      <Text style={styles.placeholder}>
        Pantalla de búsqueda en desarrollo
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  searchbar: {
    margin: 16,
  },
  filters: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
  },
  chip: {
    margin: 4,
  },
  placeholder: {
    textAlign: 'center',
    marginTop: 50,
    color: '#666',
  },
});

export default SearchScreen;
`;

    await fs.mkdir(path.dirname(searchScreenPath), { recursive: true });
    await fs.writeFile(searchScreenPath, searchScreenContent);
    log.success('SearchScreen.tsx creada');
  }
}

async function main() {
  console.log(`\n${CONFIG.colors.bright}🔧 CORRECCIONES FINALES DE TYPESCRIPT${CONFIG.colors.reset}`);
  console.log('======================================================================\n');
  
  log.info('Actualizando tipos de navegación...');
  await updateNavigationTypes();
  
  log.info('\nCorrigiendo servicios GraphQL...');
  await fixServices();
  
  log.info('\nCorrigiendo store.ts...');
  await fixStore();
  
  log.info('\nCreando archivos faltantes...');
  await createMissingFiles();
  
  console.log(`\n${CONFIG.colors.bright}✅ CORRECCIONES APLICADAS${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log('1. Añadida pantalla "Search" a los tipos de navegación');
  console.log('2. Añadido graphqlOperation a los imports de servicios');
  console.log('3. Corregido store.ts con imports necesarios');
  console.log('4. Creada SearchScreen.tsx si no existía');
  
  console.log(`\n${CONFIG.colors.cyan}🚀 SIGUIENTE PASO:${CONFIG.colors.reset}`);
  console.log('cd mobile-app');
  console.log('npx tsc --noEmit --skipLibCheck');
  console.log('\nSi no hay errores críticos:');
  console.log('npx expo start --clear');
  
  console.log('\n✨ ¡Listo para ejecutar!\n');
}

main().catch(console.error);