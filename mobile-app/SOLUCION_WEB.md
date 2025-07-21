# Solución para AWS Amplify en Web

## Problema
El error `Unable to resolve "aws-amplify" from "src\screens\home\HomeScreen.tsx"` ocurre porque AWS Amplify tiene problemas de compatibilidad con la plataforma web en Expo.

## Solución implementada

### 1. Configuración específica para web
- Creado `aws-exports-web.js` con URLs de redirección adecuadas para web
- Creado módulo `amplify-web-config.js` para manejar la configuración específica de web

### 2. Detección de plataforma
- Modificado `HomeScreen.tsx` para detectar si estamos en web o nativo
- Aplicada configuración específica según la plataforma

### 3. Configuración de Webpack
- Creado `webpack.config.js` para transpilación correcta de AWS Amplify
- Agregados alias para resolver correctamente los módulos de AWS Amplify
- Configurado babel-loader para procesar los módulos de AWS Amplify

## Cómo usar

Para iniciar la aplicación web:
```bash
npx expo start --web --clear
```

## Notas adicionales
- La configuración web usa URLs de redirección específicas para localhost
- Si despliegas la aplicación, deberás actualizar estas URLs en `aws-exports-web.js`
- Esta solución mantiene la compatibilidad con la versión nativa de la aplicación