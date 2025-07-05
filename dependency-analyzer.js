#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colores para la consola
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Compatibilidad conocida
const COMPATIBILITY_MATRIX = {
  expo: {
    '53.0.0': {
      react: '19.0.0',
      'react-native': '0.79.5',
      'react-dom': '19.0.0',
      '@types/react': '~19.0.10',
      typescript: '~5.8.3'
    },
    '52.0.0': {
      react: '18.3.1',
      'react-native': '0.76.5',
      'react-dom': '18.3.1',
      '@types/react': '~18.3.12',
      typescript: '~5.7.2'
    },
    '51.0.0': {
      react: '18.2.0',
      'react-native': '0.74.5',
      'react-dom': '18.2.0',
      '@types/react': '~18.2.45',
      typescript: '~5.3.3'
    }
  },
  amplify: {
    v6: {
      'aws-amplify': '^6.0.0',
      '@aws-amplify/ui-react-native': '^2.2.0',
      react: '^19.0.0'
    },
    v5: {
      'aws-amplify': '^5.3.0',
      '@aws-amplify/react-native': '^1.1.4',
      '@aws-amplify/ui-react-native': null, // No compatible
      react: '18.2.0'
    }
  },
  mui: {
    v5: {
      '@mui/material': '^5.0.0',
      react: '^17.0.0 || ^18.0.0',
      'react-dom': '^17.0.0 || ^18.0.0'
    },
    v4: {
      '@material-ui/core': '^4.0.0',
      react: '^16.8.0 || ^17.0.0',
      'react-dom': '^16.8.0 || ^17.0.0'
    }
  }
};

class DependencyAnalyzer {
  constructor() {
    this.results = {
      'mobile-app': { issues: [], suggestions: [] },
      'backend': { issues: [], suggestions: [] },
      'admin-panel': { issues: [], suggestions: [] }
    };
    this.rootPath = process.cwd();
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  fileExists(filePath) {
    try {
      return fs.existsSync(filePath);
    } catch {
      return false;
    }
  }

  readJSON(filePath) {
    try {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (error) {
      this.log(`Error reading ${filePath}: ${error.message}`, 'red');
      return null;
    }
  }

  getInstalledVersion(packageName, projectPath) {
    try {
      const result = execSync(`npm list ${packageName} --json`, {
        cwd: projectPath,
        encoding: 'utf8',
        stdio: 'pipe'
      });
      const data = JSON.parse(result);
      return data.dependencies?.[packageName]?.version;
    } catch {
      return null;
    }
  }

  analyzeMobileApp() {
    this.log('\n📱 Analyzing mobile-app...', 'cyan');
    const projectPath = path.join(this.rootPath, 'mobile-app');
    
    if (!this.fileExists(projectPath)) {
      this.log('mobile-app directory not found', 'yellow');
      return;
    }

    const packageJsonPath = path.join(projectPath, 'package.json');
    const packageJson = this.readJSON(packageJsonPath);
    
    if (!packageJson) return;

    const appJsonPath = path.join(projectPath, 'app.json');
    const appJson = this.readJSON(appJsonPath);

    // Detectar Expo SDK
    const expoVersion = packageJson.dependencies?.expo?.replace(/[~^]/, '');
    if (expoVersion) {
      const majorVersion = expoVersion.split('.')[0] + '.0.0';
      const expectedVersions = COMPATIBILITY_MATRIX.expo[majorVersion];
      
      if (expectedVersions) {
        this.log(`Expo SDK ${expoVersion} detected`, 'green');
        
        // Verificar React Native
        const rnVersion = packageJson.dependencies['react-native'];
        if (rnVersion && !rnVersion.includes(expectedVersions['react-native'])) {
          this.results['mobile-app'].issues.push({
            severity: 'error',
            message: `react-native@${rnVersion} incompatible with Expo SDK ${expoVersion}`,
            suggestion: `Update to react-native@${expectedVersions['react-native']}`
          });
        }

        // Verificar React
        const reactVersion = packageJson.dependencies.react;
        if (reactVersion && !reactVersion.includes(expectedVersions.react)) {
          this.results['mobile-app'].issues.push({
            severity: 'error',
            message: `react@${reactVersion} incompatible with Expo SDK ${expoVersion}`,
            suggestion: `Update to react@${expectedVersions.react}`
          });
        }
      }
    }

    // Analizar AWS Amplify
    const amplifyVersion = packageJson.dependencies?.['aws-amplify'];
    if (amplifyVersion) {
      const majorVersion = amplifyVersion.match(/\d+/)?.[0];
      const amplifyUI = packageJson.dependencies?.['@aws-amplify/ui-react-native'];
      
      if (majorVersion === '5' && amplifyUI) {
        this.results['mobile-app'].issues.push({
          severity: 'error',
          message: '@aws-amplify/ui-react-native is not compatible with aws-amplify v5',
          suggestion: 'Remove @aws-amplify/ui-react-native or upgrade to aws-amplify v6'
        });
      }

      if (majorVersion === '6') {
        const reactNativeAmplify = packageJson.dependencies?.['@aws-amplify/react-native'];
        if (reactNativeAmplify) {
          this.results['mobile-app'].issues.push({
            severity: 'warning',
            message: '@aws-amplify/react-native may not be fully compatible with aws-amplify v6',
            suggestion: 'Consider using aws-amplify v5.3.27 for React Native projects'
          });
        }
      }
    }

    // Verificar babel plugins
    const babelConfigPath = path.join(projectPath, 'babel.config.js');
    if (this.fileExists(babelConfigPath)) {
      const devDeps = packageJson.devDependencies || {};
      const babelContent = fs.readFileSync(babelConfigPath, 'utf8');
      
      // Buscar plugins mencionados en babel.config.js
      const pluginRegex = /@babel\/plugin-[a-zA-Z-]+/g;
      const usedPlugins = babelContent.match(pluginRegex) || [];
      
      usedPlugins.forEach(plugin => {
        if (!devDeps[plugin] && !packageJson.dependencies?.[plugin]) {
          this.results['mobile-app'].issues.push({
            severity: 'error',
            message: `Babel plugin ${plugin} used but not installed`,
            suggestion: `npm install --save-dev ${plugin}`
          });
        }
      });
    }

    // Verificar TypeScript
    if (packageJson.devDependencies?.typescript) {
      const tsConfigPath = path.join(projectPath, 'tsconfig.json');
      if (!this.fileExists(tsConfigPath)) {
        this.results['mobile-app'].issues.push({
          severity: 'warning',
          message: 'TypeScript installed but tsconfig.json not found',
          suggestion: 'Create tsconfig.json or remove TypeScript'
        });
      }
    }
  }

  analyzeBackend() {
    this.log('\n🚀 Analyzing backend...', 'cyan');
    const projectPath = path.join(this.rootPath, 'backend');
    
    if (!this.fileExists(projectPath)) {
      this.log('backend directory not found', 'yellow');
      return;
    }

    // Verificar serverless.yml
    const serverlessPath = path.join(projectPath, 'serverless.yml');
    if (this.fileExists(serverlessPath)) {
      const serverlessContent = fs.readFileSync(serverlessPath, 'utf8');
      
      // Verificar runtime
      const runtimeMatch = serverlessContent.match(/runtime:\s*nodejs(\d+\.x)/);
      if (runtimeMatch) {
        const nodeVersion = parseInt(runtimeMatch[1]);
        if (nodeVersion < 18) {
          this.results.backend.issues.push({
            severity: 'warning',
            message: `Node.js ${runtimeMatch[1]} is outdated for Lambda`,
            suggestion: 'Update to nodejs18.x or nodejs20.x'
          });
        }
      }

      // Verificar Python runtime si existe
      const pythonMatch = serverlessContent.match(/runtime:\s*python(\d+\.\d+)/);
      if (pythonMatch) {
        const pythonVersion = parseFloat(pythonMatch[1]);
        if (pythonVersion < 3.9) {
          this.results.backend.issues.push({
            severity: 'error',
            message: `Python ${pythonMatch[1]} is deprecated in Lambda`,
            suggestion: 'Update to python3.11 or python3.12'
          });
        }
      }
    }

    // Verificar Amplify backend
    const amplifyPath = path.join(projectPath, 'amplify');
    if (this.fileExists(amplifyPath)) {
      const backendConfigPath = path.join(amplifyPath, 'backend', 'backend-config.json');
      if (this.fileExists(backendConfigPath)) {
        this.log('Amplify backend detected', 'green');
        
        // Verificar CLI version
        try {
          const cliVersion = execSync('amplify --version', { encoding: 'utf8' }).trim();
          this.log(`Amplify CLI: ${cliVersion}`, 'green');
        } catch {
          this.results.backend.issues.push({
            severity: 'warning',
            message: 'Amplify CLI not found or not accessible',
            suggestion: 'npm install -g @aws-amplify/cli'
          });
        }
      }
    }

    // Verificar package.json si existe
    const packageJsonPath = path.join(projectPath, 'package.json');
    if (this.fileExists(packageJsonPath)) {
      const packageJson = this.readJSON(packageJsonPath);
      
      // Verificar AWS SDK
      if (packageJson?.dependencies?.['aws-sdk']) {
        this.results.backend.issues.push({
          severity: 'warning',
          message: 'Using aws-sdk v2 (legacy)',
          suggestion: 'Consider migrating to @aws-sdk/* v3 modules'
        });
      }
    }
  }

  analyzeAdminPanel() {
    this.log('\n🖥️  Analyzing admin-panel...', 'cyan');
    const projectPath = path.join(this.rootPath, 'admin-panel');
    
    if (!this.fileExists(projectPath)) {
      this.log('admin-panel directory not found', 'yellow');
      return;
    }

    const packageJsonPath = path.join(projectPath, 'package.json');
    const packageJson = this.readJSON(packageJsonPath);
    
    if (!packageJson) return;

    // Verificar Next.js
    const nextVersion = packageJson.dependencies?.next;
    if (nextVersion) {
      this.log(`Next.js ${nextVersion} detected`, 'green');
      
      // Verificar React version compatibility
      const reactVersion = packageJson.dependencies?.react;
      const nextMajor = parseInt(nextVersion.match(/\d+/)?.[0] || '0');
      
      if (nextMajor >= 13 && reactVersion && !reactVersion.includes('18')) {
        this.results['admin-panel'].issues.push({
          severity: 'error',
          message: `Next.js ${nextVersion} requires React 18`,
          suggestion: 'Update to react@^18.0.0 and react-dom@^18.0.0'
        });
      }
    }

    // Verificar Material UI
    const muiCore = packageJson.dependencies?.['@material-ui/core'];
    const muiMaterial = packageJson.dependencies?.['@mui/material'];
    
    if (muiCore) {
      this.results['admin-panel'].issues.push({
        severity: 'warning',
        message: '@material-ui/core (v4) is legacy',
        suggestion: 'Migrate to @mui/material (v5)'
      });
      
      const reactVersion = packageJson.dependencies?.react;
      if (reactVersion && reactVersion.includes('18')) {
        this.results['admin-panel'].issues.push({
          severity: 'error',
          message: '@material-ui/core v4 not compatible with React 18',
          suggestion: 'Upgrade to @mui/material v5'
        });
      }
    }

    // Verificar configuración de TypeScript
    const tsConfigPath = path.join(projectPath, 'tsconfig.json');
    if (this.fileExists(tsConfigPath)) {
      const tsConfig = this.readJSON(tsConfigPath);
      
      if (tsConfig?.compilerOptions?.jsx !== 'preserve' && nextVersion) {
        this.results['admin-panel'].issues.push({
          severity: 'warning',
          message: 'tsconfig.json jsx should be "preserve" for Next.js',
          suggestion: 'Set "jsx": "preserve" in tsconfig.json'
        });
      }
    }
  }

  generateReport() {
    this.log('\n📊 DEPENDENCY ANALYSIS REPORT', 'bright');
    this.log('=' .repeat(50), 'bright');

    Object.entries(this.results).forEach(([project, data]) => {
      if (data.issues.length === 0) {
        this.log(`\n✅ ${project}: All dependencies look good!`, 'green');
      } else {
        this.log(`\n❌ ${project}: Found ${data.issues.length} issue(s)`, 'red');
        
        data.issues.forEach((issue, index) => {
          const icon = issue.severity === 'error' ? '🚨' : '⚠️';
          this.log(`\n  ${icon} Issue ${index + 1}:`, issue.severity === 'error' ? 'red' : 'yellow');
          this.log(`     ${issue.message}`);
          this.log(`     💡 ${issue.suggestion}`, 'cyan');
        });
      }
    });

    this.generateFixScript();
  }

  generateFixScript() {
    this.log('\n\n🔧 SUGGESTED FIX COMMANDS', 'bright');
    this.log('=' .repeat(50), 'bright');

    // Mobile app fixes
    const mobileIssues = this.results['mobile-app'].issues;
    if (mobileIssues.length > 0) {
      this.log('\n📱 Mobile App Fixes:', 'cyan');
      this.log('cd mobile-app');
      
      const packagesToInstall = [];
      const packagesToUpdate = [];
      
      mobileIssues.forEach(issue => {
        if (issue.suggestion.includes('npm install')) {
          const match = issue.suggestion.match(/npm install.*?([@\w\/-]+)/);
          if (match) packagesToInstall.push(match[1]);
        }
        if (issue.suggestion.includes('Update to')) {
          const match = issue.suggestion.match(/Update to ([@\w\/-]+@[\d.~^]+)/);
          if (match) packagesToUpdate.push(match[1]);
        }
      });

      if (packagesToInstall.length > 0) {
        this.log(`npm install --save-dev ${packagesToInstall.join(' ')}`);
      }
      
      if (packagesToUpdate.length > 0) {
        this.log(`npm install ${packagesToUpdate.join(' ')} --legacy-peer-deps`);
      }
      
      this.log('cd ..');
    }

    // Backend fixes
    const backendIssues = this.results.backend.issues;
    if (backendIssues.length > 0) {
      this.log('\n🚀 Backend Fixes:', 'cyan');
      backendIssues.forEach(issue => {
        if (issue.suggestion.includes('Update to')) {
          this.log(`# ${issue.suggestion}`);
        }
      });
    }

    // Admin panel fixes
    const adminIssues = this.results['admin-panel'].issues;
    if (adminIssues.length > 0) {
      this.log('\n🖥️  Admin Panel Fixes:', 'cyan');
      this.log('cd admin-panel');
      
      const muiMigration = adminIssues.find(i => i.suggestion.includes('@mui/material'));
      if (muiMigration) {
        this.log('npm uninstall @material-ui/core @material-ui/icons');
        this.log('npm install @mui/material @emotion/react @emotion/styled');
      }
      
      this.log('cd ..');
    }

    this.log('\n\n💡 Run these commands one by one and test after each change!', 'yellow');
  }

  async run() {
    this.log('🔍 Starting Boat Rental App Dependency Analysis...', 'bright');
    this.log('=' .repeat(50), 'bright');

    this.analyzeMobileApp();
    this.analyzeBackend();
    this.analyzeAdminPanel();
    this.generateReport();

    this.log('\n\n✨ Analysis complete!', 'green');
  }
}

// Ejecutar el analizador
const analyzer = new DependencyAnalyzer();
analyzer.run();