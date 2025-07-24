module.exports = function (api) {
  api.cache(true);

  return {
    presets: ['babel-preset-expo'],
    plugins: [
      // Remover todos los plugins problemáticos por ahora
    ]
  };
};