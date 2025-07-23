module.exports = function (api) {
  api.cache(true);

  return {
    presets: [
      [
        'babel-preset-expo',
        {
          jsxRuntime: 'automatic',
          web: { unstable_transformProfile: 'hermes-stable' }
        }
      ]
    ],
    plugins: [],
    // ✅ CONFIGURACIÓN CLAVE: Ignorar .babelrc de node_modules
    babelrc: false,        // No buscar .babelrc
    configFile: false,     // No buscar babel.config.js adicionales
    only: [                // Solo procesar archivos del proyecto
      './src/**/*',
      './App.js',
      './App.tsx',
      './index.js'
    ],
    ignore: [              // Ignorar node_modules explícitamente
      'node_modules/**',
      '**/node_modules/**'
    ]
  };
};
