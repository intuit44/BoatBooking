echo "?? VERIFICANDO LOGS DE LA APP..."
echo "Presiona Ctrl+C cuando termines de revisar los logs"
echo ""
adb logcat | findstr "ReactNativeJS"
