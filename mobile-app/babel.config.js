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
          root: ['./src'],
          alias: {
            '@': './src',
            '@/components': './src/components',
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
    ],
  };
};
