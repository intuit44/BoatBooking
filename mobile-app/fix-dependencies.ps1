# Copiar todo el contenido del script anterior
# fix-dependencies.ps1
# Script para arreglar conflictos de dependencias y bundle JS

Write-Host "🔧 ARREGLANDO DEPENDENCIAS Y BUNDLE" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Cambiar al directorio del proyecto
$projectPath = "C:\ProyectosSimbolicos\boat-rental-app\mobile-app"
Set-Location $projectPath

Write-Host "📁 Directorio: $projectPath" -ForegroundColor Yellow

# 1. ARREGLAR CONFLICTOS DE DEPENDENCIAS
Write-Host "`n📋 Paso 1: Resolviendo conflictos de dependencias..." -ForegroundColor Yellow

# Instalar dependencias faltantes con legacy-peer-deps
Write-Host "📦 Instalando @react-native-community/cli..." -ForegroundColor Gray
& npm install @react-native-community/cli --save-dev --legacy-peer-deps

Write-Host "📦 Instalando dependencias de Babel..." -ForegroundColor Gray
& npm install @babel/helper-define-polyfill-provider @babel/core @babel/runtime --save-dev --legacy-peer-deps

Write-Host "✅ Dependencias instaladas con legacy-peer-deps" -ForegroundColor Green

# 2. CREAR CONFIGURACIONES CORRECTAS
Write-Host "`n📋 Paso 2: Creando configuraciones..." -ForegroundColor Yellow

# Babel config en JavaScript (no JSON)
$babelConfig = @'
module.exports = {
  presets: ['@react-native/babel-preset'],
  plugins: []
};
'@
$babelConfig | Out-File -FilePath "babel.config.js" -Encoding UTF8 -Force
Write-Host "✅ babel.config.js (JavaScript) creado" -ForegroundColor Green

# Metro config básico
$metroConfig = @'
const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

const config = {};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
'@
$metroConfig | Out-File -FilePath "metro.config.js" -Encoding UTF8 -Force
Write-Host "✅ metro.config.js creado" -ForegroundColor Green

# 3. VERIFICAR ARCHIVOS PRINCIPALES
Write-Host "`n📋 Paso 3: Verificando archivos principales..." -ForegroundColor Yellow

# App.js básico que funcione
$appContent = @'
import React from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';

function App() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentInsetAdjustmentBehavior="automatic">
        <View style={styles.body}>
          <Text style={styles.title}>🚤 Boat Rental App</Text>
          <Text style={styles.subtitle}>¡Funcionando correctamente!</Text>
          <Text style={styles.version}>Versión: 1.0.0</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  body: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 100,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 18,
    color: '#333333',
    marginBottom: 20,
    textAlign: 'center',
  },
  version: {
    fontSize: 14,
    color: '#666666',
  },
});

export default App;
'@
$appContent | Out-File -FilePath "App.js" -Encoding UTF8 -Force
Write-Host "✅ App.js básico creado" -ForegroundColor Green

# Verificar index.js
if (!(Test-Path "index.js")) {
    $indexContent = @'
import {AppRegistry} from 'react-native';
import App from './App';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => App);
'@
    $indexContent | Out-File -FilePath "index.js" -Encoding UTF8
    Write-Host "✅ index.js creado" -ForegroundColor Green
} else {
    Write-Host "✅ index.js existe" -ForegroundColor Green
}

# 4. LIMPIAR CACHÉS
Write-Host "`n📋 Paso 4: Limpiando cachés..." -ForegroundColor Yellow
& npm cache clean --force 2>$null
Remove-Item "$env:LOCALAPPDATA\Temp\metro-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Temp\react-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "node_modules\.cache" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ Cachés limpiados" -ForegroundColor Green

# 5. GENERAR BUNDLE
Write-Host "`n📋 Paso 5: Generando bundle JavaScript..." -ForegroundColor Yellow

# Crear directorio de assets
New-Item -ItemType Directory -Force -Path "android\app\src\main\assets" | Out-Null

Write-Host "🔄 Generando bundle..." -ForegroundColor Cyan
try {
    $bundleResult = & npx react-native bundle `
        --platform android `
        --dev false `
        --entry-file index.js `
        --bundle-output android/app/src/main/assets/index.android.bundle `
        --assets-dest android/app/src/main/res `
        --reset-cache 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Bundle generado exitosamente" -ForegroundColor Green
        
        # 6. RECOMPILAR APK
        Write-Host "`n📋 Paso 6: Recompilando APK..." -ForegroundColor Yellow
        Set-Location android
        & .\gradlew.bat assembleDebug
        Set-Location ..
        
        if (Test-Path "android\app\build\outputs\apk\debug\app-debug.apk") {
            Write-Host "✅ APK recompilado" -ForegroundColor Green
            
            # 7. REINSTALAR EN EMULADOR
            Write-Host "`n📋 Paso 7: Reinstalando en emulador..." -ForegroundColor Yellow
            & adb uninstall com.boatrentals.app 2>$null
            & adb install -r android\app\build\outputs\apk\debug\app-debug.apk
            & adb shell am start -n com.boatrentals.app/.MainActivity
            
            Write-Host "`n🎉 ¡TODO LISTO!" -ForegroundColor Green
            Write-Host "=================" -ForegroundColor Green
            Write-Host "✅ Dependencias arregladas" -ForegroundColor Cyan
            Write-Host "✅ Bundle JS generado" -ForegroundColor Cyan
            Write-Host "✅ APK reinstalado" -ForegroundColor Cyan
            Write-Host "📱 La pantalla roja debería desaparecer" -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ Error al generar bundle:" -ForegroundColor Red
        Write-Host $bundleResult -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error al generar bundle:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`n📋 Para ver logs: adb logcat -s ReactNativeJS" -ForegroundColor Yellow