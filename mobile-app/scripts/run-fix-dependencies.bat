@echo off
echo Ejecutando script para corregir dependencias incompatibles...
node "%~dp0fix-dependencies.js"
echo.
echo Si el script se ejecutó correctamente, intenta iniciar la aplicación con:
echo npx expo start
pause