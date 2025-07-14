@echo off
echo ===================================================
echo Herramienta de corrección para BoatRental App
echo ===================================================
echo.
echo Este script realizará las siguientes acciones:
echo 1. Actualizar dependencias incompatibles
echo 2. Verificar y corregir la configuración de la app
echo 3. Limpiar la caché de Expo
echo.
echo Presiona cualquier tecla para continuar o Ctrl+C para cancelar...
pause > nul

echo.
echo [1/3] Actualizando dependencias incompatibles...
node "%~dp0fix-dependencies.js"

echo.
echo [2/3] Verificando y corrigiendo la configuración de la app...
node "%~dp0fix-app-config.js"

echo.
echo [3/3] Limpiando la caché de Expo...
cd ..
call npx expo start --clear --no-dev --minify

echo.
echo ===================================================
echo Proceso completado
echo ===================================================
echo.
echo Si todo se ejecutó correctamente, intenta iniciar la aplicación con:
echo npx expo start
echo.
pause