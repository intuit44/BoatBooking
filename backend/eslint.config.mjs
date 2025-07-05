import js from '@eslint/js';
import json from '@eslint/json';

export default [
  js.configs.recommended,
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        console: 'readonly',
        process: 'readonly',
        Buffer: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly'
      }
    }
  },
  {
    files: ['**/*.json'],
    ...json.configs.recommended,
    rules: {
      ...json.configs.recommended.rules
    }
  },
  {
    // IGNORAR ARCHIVOS GENERADOS
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      'coverage/**',
      '.serverless/**',
      'package-lock.json',  // ← IMPORTANTE
      '*.log'
    ]
  }
];