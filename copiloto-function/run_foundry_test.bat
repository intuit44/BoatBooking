@echo off
echo ========================================
echo TEST: Captura de entrada desde Foundry
echo ========================================
echo.
echo Asegurate de que func start este corriendo en otra terminal
echo.
pause

cd /d "%~dp0"
python test_foundry_input_capture.py

echo.
echo ========================================
echo Test completado
echo ========================================
pause
