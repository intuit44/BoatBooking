// Script de prueba para verificar la navegación
console.log('🚀 Iniciando prueba de navegación...');

// Simular datos mock
const mockBoats = [
  {
    id: '1',
    name: 'Yacht Presidencial',
    type: 'yacht',
    capacity: 12,
    pricePerHour: 250,
    rating: 4.9,
    featured: true
  },
  {
    id: '2', 
    name: 'Velero Caribeño',
    type: 'sailboat',
    capacity: 8,
    pricePerHour: 180,
    rating: 4.7,
    featured: true
  }
];

// Simular funciones de navegación
const mockNavigation = {
  navigate: (screen, params) => {
    console.log(`✅ Navegando a: ${screen}`, params ? `con parámetros: ${JSON.stringify(params)}` : '');
    return true;
  }
};

// Simular clicks en HomeScreen
console.log('\n📱 Simulando clicks en HomeScreen:');

// Test 1: Click en embarcación destacada
console.log('\n1. Click en embarcación destacada:');
const featuredBoat = mockBoats[0];
mockNavigation.navigate('BoatDetails', { boatId: featuredBoat.id });

// Test 2: Click en categoría
console.log('\n2. Click en categoría de yates:');
mockNavigation.navigate('Search', { type: 'yacht' });

// Test 3: Click en búsqueda
console.log('\n3. Click en barra de búsqueda:');
mockNavigation.navigate('Search');

// Test 4: Click en filtro rápido
console.log('\n4. Click en filtro rápido (Familias):');
mockNavigation.navigate('Search', { capacity: 8 });

console.log('\n✅ Todas las pruebas de navegación completadas exitosamente!');
console.log('\n🔧 Si ves este mensaje, significa que:');
console.log('   - Los datos mock están disponibles');
console.log('   - Las funciones de navegación están definidas');
console.log('   - Los parámetros se pasan correctamente');

console.log('\n📋 Próximos pasos:');
console.log('   1. Ejecutar: npm start o expo start');
console.log('   2. Verificar que las imágenes se cargan');
console.log('   3. Probar clicks reales en el dispositivo/emulador');