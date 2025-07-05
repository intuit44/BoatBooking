const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env') });

const OpenAI = require('openai');

const archivo = process.argv[2];
if (!archivo) {
  console.error('❌ Debes pasar el archivo a corregir. Ej: node corregir_archivo.js ../mobile-app/src/screens/HomeScreen.tsx');
  process.exit(1);
}

const promptBase = fs.readFileSync(path.join(__dirname, '../prompt.md'), 'utf8');
const erroresEjemplo = require('../samples/errores-resueltos.json');
const inputCode = fs.readFileSync(archivo, 'utf8');

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  console.error('❌ Falta la variable OPENAI_API_KEY en el entorno.');
  process.exit(1);
}

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

(async () => {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4-1106-preview", // puedes cambiar a "gpt-4-1106-preview" si no tienes acceso
      messages: [
        { role: "system", content: promptBase },
        {
          role: "user",
          content: `Corrige el siguiente archivo TypeScript:\n\n${inputCode}\n\nErrores similares:\n${JSON.stringify(erroresEjemplo, null, 2)}`
        }
      ],
      temperature: 0.2
    });

    const result = response.choices[0].message.content;
    const outputPath = path.resolve(path.dirname(archivo), path.basename(archivo).replace('.tsx', '.corregido.tsx'));

    fs.writeFileSync(outputPath, result);
    console.log(`✅ Archivo corregido generado: ${outputPath}`);
  } catch (error) {
    if (
      error?.error?.message?.includes("does not exist") ||
      error?.error?.code === "model_not_found"
    ) {
      console.error("❌ No tienes acceso al modelo gpt-4-32k. Prueba con 'gpt-4' o 'gpt-4-1106-preview'");
    } else if (
      error?.error?.message?.includes("context length") ||
      error?.error?.code === "context_length_exceeded"
    ) {
      console.error("⚠️ El archivo es demasiado grande para este modelo. Usa gpt-4-32k o fragmenta el archivo.");
    } else {
      console.error("❌ Error general:", error.message || error);
    }
  }
})();

