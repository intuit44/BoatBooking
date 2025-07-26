# AGENTS.md

Este archivo define las capacidades, responsabilidades y rutas de los agentes CodeGPT utilizados en el repositorio `BoatBooking`.

## 🧠 Agentes Definidos

### 1. Architect_BoatRental
* **Rol:** Arquitectura general del proyecto, análisis de flujo, estructura de carpetas y dependencias.
* **Responsabilidades:**
   * Verificar consistencia entre los módulos `mobile-app`, `admin-panel`, `backend`.
   * Gestionar configuración compartida (`package.json`, `.codegpt.yaml`, `.env.example`).
   * Validar cobertura de pruebas, CI/CD y flujos de integración Codex.
   * Revisar y aprobar cambios estructurales mayores.
   * Mantener la documentación técnica actualizada.
* **Archivos relevantes:**
   * `/mobile-app/package.json`
   * `/mobile-app/jest.config.js`
   * `/mobile-app/index.js`
   * `/amplify/`
   * `/backend/`
   * `/.github/workflows/`
   * `/README.md`
   * `/AGENTS.md`
   * `/.codegpt.yaml`
* **Palabras clave para invocación:** architecture, structure, dependencies, CI/CD, integration, documentation

### 2. Mobile_App_Agent
* **Rol:** Responsable del desarrollo de la app React Native con Expo SDK 53.
* **Responsabilidades:**
   * Navegación, pantallas, estados y test de `App.tsx`, `HomeScreen.tsx`, etc.
   * Verificación de UI, lógica de configuración (Amplify), y flujo visual.
   * Coordinación de mocks y snapshots (`__mocks__`, `__tests__`).
   * Gestión de dependencias React Native y Expo.
   * Implementación de funcionalidades de usuario final.
* **Archivos relevantes:**
   * `/mobile-app/App.tsx`
   * `/mobile-app/src/screens/home/HomeScreen.tsx`
   * `/mobile-app/__tests__/`
   * `/mobile-app/__mocks__/`
   * `/mobile-app/jest.setup.js`
   * `/mobile-app/babel.config.js`
   * `/mobile-app/metro.config.js`
* **Palabras clave para invocación:** mobile, app, React Native, Expo, screens, navigation, UI, tests

### 3. Backend_Agent
* **Rol:** Gestión de funciones Lambda, GraphQL (AppSync), y DynamoDB.
* **Responsabilidades:**
   * Verificar `schema.graphql`, resolvers y lógica en `backend/`.
   * Validar configuraciones en `amplify-config.js`, `amplify-patches.js`.
   * Sincronizar configuración Amplify con Auth, API, Storage.
   * Implementar y mantener funciones serverless.
   * Gestionar la seguridad y autenticación.
* **Archivos relevantes:**
   * `/backend/`
   * `/amplify/backend/`
   * `/amplify/backend/api/*/schema.graphql`
   * `/mobile-app/amplify-config.js`
   * `/mobile-app/aws-exports.js`
   * `/mobile-app/src/config/`
* **Palabras clave para invocación:** backend, Lambda, GraphQL, AppSync, DynamoDB, API, auth, Amplify

### 4. AdminPanel_Agent
* **Rol:** Desarrollo y mantenimiento del panel web de administración (Next.js + MUI).
* **Responsabilidades:**
   * Rutas, formularios, vistas de reservas, usuarios, embarcaciones.
   * Configuración SSR, seguridad, y rutas protegidas.
   * Integración con API GraphQL.
   * Gestión de estado y autenticación admin.
* **Archivos relevantes:**
   * `/admin-panel/pages/`
   * `/admin-panel/src/components/`
   * `/admin-panel/package.json`
   * `/admin-panel/next.config.js`
* **Palabras clave para invocación:** admin, panel, Next.js, MUI, dashboard, web

---

## 🔁 Coordinación entre Agentes

### Flujo de Comunicación
1. `Architect_BoatRental` actúa como punto de sincronización y validación.
2. Cambios estructurales deben ser aprobados por `Architect_BoatRental`.
3. Cambios en API/GraphQL requieren coordinación entre `Backend_Agent` y consumidores (`Mobile_App_Agent`, `AdminPanel_Agent`).
4. Actualizaciones de dependencias compartidas deben ser comunicadas a todos los agentes afectados.

### Protocolos de Colaboración
* **Para cambios en API:** Backend_Agent → notifica → Mobile_App_Agent + AdminPanel_Agent
* **Para cambios en autenticación:** Backend_Agent → coordina con → todos los agentes
* **Para cambios en CI/CD:** Architect_BoatRental → actualiza → todos los agentes
* **Para nuevas features:** Architect_BoatRental → asigna → agente(s) específico(s)

---

## 📁 Estructura del Proyecto

```
BoatBooking/
├── mobile-app/                    # [Mobile_App_Agent]
│   ├── App.tsx
│   ├── index.js
│   ├── amplify-config.js
│   ├── aws-exports.js
│   ├── src/
│   │   └── screens/
│   ├── __tests__/
│   └── __mocks__/
├── backend/                       # [Backend_Agent]
│   ├── functions/
│   └── api/
├── amplify/                       # [Backend_Agent + Architect_BoatRental]
│   └── backend/
├── admin-panel/                   # [AdminPanel_Agent]
│   ├── pages/
│   ├── src/
│   └── package.json
├── .github/workflows/             # [Architect_BoatRental]
├── .codegpt.yaml                 # [Architect_BoatRental]
├── AGENTS.md                     # [Architect_BoatRental]
└── README.md                     # [Architect_BoatRental]
```

---

## 🧩 Uso por Codex

### Cómo asignar tareas:
1. **Identifica el módulo afectado** según la estructura de carpetas.
2. **Usa palabras clave** para invocar al agente correcto.
3. **Para tareas cross-module**, involucra primero a `Architect_BoatRental`.

### Ejemplos de asignación:
- "Fix jest tests in mobile app" → `Mobile_App_Agent`
- "Update GraphQL schema" → `Backend_Agent` + notificar a `Mobile_App_Agent` y `AdminPanel_Agent`
- "Add new CI/CD pipeline" → `Architect_BoatRental`
- "Implement booking feature" → `Architect_BoatRental` → distribuye a agentes relevantes

### Prioridades:
1. **Alta:** Errores en producción, fallos de CI/CD, problemas de seguridad
2. **Media:** Nuevas features, optimizaciones, refactoring
3. **Baja:** Documentación, mejoras estéticas, warnings no críticos

---

## 📋 Estado Actual del Proyecto

### Mobile App
- **Framework:** React Native 0.79.5 + Expo SDK 53
- **Estado:** Tests corrigiendo, HomeScreen funcional
- **Próximos pasos:** Completar cobertura de tests, implementar navegación completa

### Backend
- **Stack:** AWS Amplify v6, GraphQL, Lambda
- **Estado:** Configuración base establecida
- **Próximos pasos:** Implementar resolvers, autenticación

### Admin Panel
- **Framework:** Next.js + Material-UI
- **Estado:** En desarrollo inicial
- **Próximos pasos:** Estructura base, autenticación admin

---

## 🔄 Actualización de este archivo

Si agregas o modificas un módulo:
1. Actualiza la sección correspondiente del agente
2. Modifica la estructura de carpetas si es necesario
3. Notifica a `Architect_BoatRental` para validación
4. Commitea los cambios con mensaje descriptivo: `docs: update AGENTS.md with [cambio]`
# Agents overview for BoatBooking

This repository uses Codex agents to coordinate development across modules.

## Active agents

- **Architect_BoatRental** - handles overall architecture and repository standards.
- **Mobile_App_Agent** - manages all code under `mobile-app/` using React Native and Expo.
- **Backend_Agent** - responsible for serverless backend inside `backend/` and Amplify resources.
- **AdminPanel_Agent** - oversees the Next.js admin panel inside `admin-panel/`.

These roles are defined in `.codegpt/agents.yaml`. The main module configuration in `.codegpt.yaml` references this file via `agents_file` so Codex can automatically assign tasks based on the changed paths.

## Testing policy

- Do **not** remove or modify existing tests in `__tests__`, `__mocks__`, or `__snapshots__`.
- Always run `npm run test` and `npm run test:coverage` before pushing changes.
- Maintain coverage above 80%.

