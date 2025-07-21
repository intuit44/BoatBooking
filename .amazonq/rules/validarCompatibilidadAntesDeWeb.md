# 📋 Rule: Control de Compatibilidad Nativa y Web para Amazon Q

## 🎯 OBJETIVO
Asegurar que **la ejecución nativa esté completamente estable** (Expo en emulador) antes de realizar cualquier cambio relacionado con la compatibilidad Web (Expo Web). Toda modificación debe ser controlada, documentada y reversible.

---

## 🔍 CONDICIONES DE ACTIVACIÓN
Esta regla se aplica **cuando Amazon Q**:

- Intente modificar alguno de los siguientes archivos críticos:
  - `HomeScreen.tsx`
  - `aws-exports.js` / `aws-exports-web.js`
  - `amplify-web-config.js`
  - `webpack.config.js`
  - `tsconfig.json`

- Detecte dentro del código:
  - `Platform.OS === 'web'`
  - `typeof document !== 'undefined'`
  - Uso de `generateClient()` desde `aws-amplify/api`

---

## ✅ ACCIONES REQUERIDAS

1. **Verificación previa:**
   - Ejecutar o confirmar que `npx expo start --clear` **se ha completado exitosamente**
   - Validar que la app **renderiza correctamente en el emulador**

2. **Antes de modificar:**
   - Crear backup o sugerir commit limpio del estado actual
   - Informar al usuario qué archivo será modificado y por qué
   - Evaluar riesgo de impacto nativo

3. **Durante la modificación:**
   - Aplicar cambios **marcados con comentarios `// TEMP WEB FIX`**
   - Documentar cada cambio en `SOLUCION_TEMPORAL.md`
   - No activar lógica web en tiempo real si el entorno nativo está inestable

4. **Después de aplicar:**
   - Instruir cómo revertir los cambios temporalmente
   - Generar instrucciones claras en `README_web.md` si es parte del flujo futuro

---

## 🛑 PRECAUCIONES
- ❌ No modificar `tsconfig.json` innecesariamente (solo si TypeScript lanza errores concretos)
- ❌ No sobrescribir configuraciones compartidas sin confirmación (como `aws-exports.js`)
- ❌ No asumir que `document` o `window` existen en tiempo de compilación

---

## 🎯 RESULTADO ESPERADO

- ✅ App funciona en emulador (`Expo Go` o `Android Studio`)
- 🧪 Cambios Web son condicionales, reversibles y comentados
- 📦 Todo queda documentado en `SOLUCION_TEMPORAL.md`
- 🔁 El usuario tiene control sobre cuándo avanzar al soporte Web

