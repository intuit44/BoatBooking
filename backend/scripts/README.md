# 🛠️ Backend Scripts - Boat Rental App

Este directorio contiene scripts auxiliares para validación, generación y mantenimiento del entorno backend.

## 📜 Scripts disponibles

### `validate-env.ts`
Verifica que todas las variables requeridas estén presentes en `.env`.

### `generate-secrets.ts`
Genera claves seguras para uso en `.env`. ⚠️ No debe subirse al repo con valores reales.

### `check-schema-sync.ts`
Valida que el esquema GraphQL esté sincronizado con los tipos generados en frontends.

### `test-db-connection.ts`
Prueba la conexión real con DynamoDB, S3, u otros servicios AWS configurados.

## 🧪 Cómo ejecutar

```bash
# Ejemplo:
ts-node scripts/validate-env.ts


Asegúrate de tener `.env` correctamente cargado antes de ejecutar cualquier script.

🚫 Seguridad
------------

* **No subas `.env` reales o secrets generados.**
* Los scripts están ignorados en `.gitignore` si contienen valores sensibles.
