const fs = require('fs');
const path = require('path');

// Ruta al archivo app.json
const appJsonPath = path.join(__dirname, '..', 'app.json');

// Leer el archivo app.json
const appJson = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));

// Crear una copia de seguridad del app.json actual
const backupPath = `${appJsonPath}.backup-${Date.now()}`;
fs.copyFileSync(appJsonPath, backupPath);
console.log(`Copia de seguridad de app.json creada en: ${backupPath}`);

// Asegurarse de que la configuración de Expo sea correcta
if (appJson.expo) {
  // Verificar y actualizar la configuración de jsEngine
  if (appJson.expo.jsEngine === 'hermes') {
    console.log('La configuración de jsEngine ya está establecida en "hermes"');
  } else {
    appJson.expo.jsEngine = 'hermes';
    console.log('Configuración de jsEngine actualizada a "hermes"');
  }

  // Verificar y actualizar la configuración de plugins
  let locationPluginFound = false;
  if (Array.isArray(appJson.expo.plugins)) {
    for (const plugin of appJson.expo.plugins) {
      if (Array.isArray(plugin) && plugin[0] === 'expo-location') {
        locationPluginFound = true;
        break;
      }
    }
  } else {
    appJson.expo.plugins = [];
  }

  if (!locationPluginFound) {
    appJson.expo.plugins.push([
      'expo-location',
      {
        'locationAlwaysAndWhenInUseUsageDescription': 'Allow $(PRODUCT_NAME) to use your location.'
      }
    ]);
    console.log('Plugin de expo-location añadido');
  }

  // Guardar el app.json actualizado
  fs.writeFileSync(appJsonPath, JSON.stringify(appJson, null, 2));
  console.log('app.json actualizado correctamente');
} else {
  console.error('No se encontró la configuración de Expo en app.json');
}