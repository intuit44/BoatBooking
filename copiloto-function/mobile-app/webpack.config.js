const createExpoWebpackConfigAsync = require('@expo/webpack-config');

module.exports = async function (env, argv) {
  const config = await createExpoWebpackConfigAsync(
    {
      ...env,
      babel: {
        dangerouslyAddModulePathsToTranspile: [
          'aws-amplify',
          '@aws-amplify',
        ],
      },
    },
    argv
  );

  // Resolver para aws-amplify en web
  config.resolve.alias = {
    ...config.resolve.alias,
    'aws-amplify$': 'aws-amplify/dist/esm/index.js',
  };

  // Asegurarse de que los módulos de aws-amplify sean transpilados
  config.module.rules.push({
    test: /node_modules\/(aws-amplify|@aws-amplify)/,
    use: {
      loader: 'babel-loader',
      options: {
        presets: ['@babel/preset-env', '@babel/preset-react'],
        plugins: ['@babel/plugin-transform-runtime'],
      },
    },
  });

  return config;
};