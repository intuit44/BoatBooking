// Tipos globales para React Native y AWS SDK

import { MaterialCommunityIcons } from '@expo/vector-icons';

declare global {
  type MaterialIconName = keyof typeof MaterialCommunityIcons.glyphMap;

  var Buffer: any;

  namespace NodeJS {
    interface Global {
      Buffer: any;
    }
  }
}

export {};
