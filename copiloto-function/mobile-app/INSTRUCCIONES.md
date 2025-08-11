# Instrucciones para Solucionar Problemas de Dependencias

Se han detectado incompatibilidades entre las versiones de algunas dependencias y la versión instalada de Expo. Sigue estos pasos para solucionarlas:

## Opción 1: Actualizar Dependencias con PowerShell

1. Abre PowerShell en la carpeta del proyecto mobile-app
2. Ejecuta el script de actualización de dependencias:
   ```
   .\update-dependencies.ps1
   ```
3. Una vez completado, inicia la aplicación:
   ```
   npx expo start
   ```

## Opción 2: Limpiar Caché y Reiniciar

Si sigues teniendo problemas después de actualizar las dependencias:

1. Ejecuta el script para limpiar la caché y reiniciar:
   ```
   .\clear-and-start.ps1
   ```

## Opción 3: Actualización Manual

Si los scripts no funcionan, puedes actualizar manualmente las dependencias:

1. Edita el archivo `package.json` y actualiza estas versiones:
   ```json
   "@expo/metro-runtime": "~4.0.1",
   "@react-native-async-storage/async-storage": "1.23.1",
   "@react-native-community/datetimepicker": "8.2.0",
   "@react-native-community/slider": "4.5.5",
   "react-native": "0.76.9",
   "react-native-maps": "1.18.0",
   "react-native-safe-area-context": "4.12.0"
   ```

2. Ejecuta `npm install` para aplicar los cambios

3. Limpia la caché de Expo:
   ```
   npx expo start --clear
   ```

## Solución de Problemas Adicionales

Si sigues experimentando problemas:

1. Elimina la carpeta `node_modules` y el archivo `package-lock.json`
2. Ejecuta `npm install` para reinstalar todas las dependencias
3. Limpia la caché de Expo con `npx expo start --clear`

Nota: Se crean copias de seguridad automáticas de los archivos modificados por los scripts.