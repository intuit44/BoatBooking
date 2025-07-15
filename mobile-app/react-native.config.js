module.exports = {
  dependencies: {
    // Excluir completamente @aws-amplify/react-native del autolinking
    '@aws-amplify/react-native': {
      platforms: {
        android: null,
        ios: null,
      },
    },
  },
};
