module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      [
        'babel-preset-expo',
        {
          jsxRuntime: 'automatic',
        },
      ],
    ],
    plugins: [
      [
        '@babel/plugin-transform-runtime',
        {
          regenerator: false,
          useESModules: false,
        },
      ],
      [
        'module-resolver',
        {
          alias: {
            crypto: 'crypto-browserify',
            stream: 'stream-browserify',
            buffer: 'buffer',
          },
        },
      ],
      [
        '@babel/plugin-proposal-class-properties',
        {
          loose: true,
        },
      ],
      // Removido @babel/plugin-transform-operators (no existe)
      // Solo plugins que existen realmente
    ],
  };
};
