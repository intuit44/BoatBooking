import crypto from 'crypto';

const secrets = {
  JWT_SECRET: crypto.randomBytes(64).toString('hex'),
  REFRESH_TOKEN_SECRET: crypto.randomBytes(64).toString('hex'),
  ENCRYPTION_KEY: crypto.randomBytes(32).toString('hex'),
  API_KEY: crypto.randomUUID()
};

console.log('\n🔐 Secrets generados:\n');
Object.entries(secrets).forEach(([key, value]) => {
  console.log(`${key}=${value}`);
});
console.log('\n⚠️  IMPORTANTE: Guarda estos valores de forma segura!');
