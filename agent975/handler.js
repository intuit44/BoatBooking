module.exports = async function (context) {
  const code = context.request.body?.input?.code;

  if (!code) {
    return {
      statusCode: 400,
      body: {
        error: "Missing input.code field in request body"
      }
    };
  }

  const lines = code.split('\n').length;
  const size = code.length;

  return {
    analysis: {
      lines,
      size,
      feedback: [
        "✅ Código recibido correctamente.",
        "📏 Líneas de código: " + lines,
        "📦 Tamaño (caracteres): " + size
      ]
    }
  };
};
