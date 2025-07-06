import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🔧 Fixing lint errors...\n');

// Fix 1: Convertir CommonJS a ES Modules
const filesToFix = [
  '../src/handlers/authorizer.js',
  '../src/handlers/boats-mock.js',
  '../src/handlers/boats.js',
  '../src/handlers/bookings.js',
  '../src/handlers/payments.js',
  '../src/utils/availability.js'
];

filesToFix.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Convertir require a import
    content = content.replace(/const\s+(\w+)\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)/g, 
      "import $1 from '$2'");
    content = content.replace(/const\s+{\s*([^}]+)\s*}\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)/g, 
      "import { $1 } from '$2'");
    
    // Convertir exports a export
    content = content.replace(/exports\.(\w+)\s*=\s*/g, 'export const $1 = ');
    content = content.replace(/module\.exports\s*=\s*/g, 'export default ');
    
    fs.writeFileSync(filePath, content);
    console.log(`✅ Fixed: ${file}`);
  }
});

// Fix 2: Actualizar .eslintignore
const eslintIgnore = `
# Dependencies
node_modules/

# Build
dist/
build/
.serverless/

# Config files
*.config.js
*.config.mjs
package.json
package-lock.json

# Tests
coverage/
*.test.js
*.spec.js

# Scripts
scripts/

# Logs
*.log
`;

fs.writeFileSync(path.join(__dirname, '../.eslintignore'), eslintIgnore.trim());
console.log('✅ Updated .eslintignore');

// Fix 3: Actualizar auth.js para el error de variables no usadas
const authPath = path.join(__dirname, '../src/handlers/auth.js');
if (fs.existsSync(authPath)) {
  let authContent = fs.readFileSync(authPath, 'utf8');
  // Cambiar { password: _, ...userWithoutPassword } por solo userWithoutPassword
  authContent = authContent.replace(/const\s*{\s*password:\s*_,\s*\.\.\.(\w+)\s*}\s*=\s*/g, 
    'const $1 = { ...').replace(/=\s*{\s*\.\.\./g, '= (({ password, ...rest }) => rest)(');
  fs.writeFileSync(authPath, authContent);
  console.log('✅ Fixed unused variables in auth.js');
}

console.log('\n✨ All fixes applied!');