const dns = require('dns');
const https = require('https');

// Función para probar DNS desde AWS
exports.testDNS = async (event) => {
  try {
    // Probar resolución DNS
    const dnsResult = await new Promise((resolve, reject) => {
      dns.lookup('api.remeocci.org', (err, address) => {
        if (err) reject(err);
        else resolve(address);
      });
    });

    // Probar conectividad HTTP
    const httpResult = await new Promise((resolve, reject) => {
      const req = https.get('https://api.remeocci.org/hello', (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve({ status: res.statusCode, data }));
      });
      req.on('error', reject);
      req.setTimeout(5000, () => reject(new Error('Timeout')));
    });

    return {
      statusCode: 200,
      body: JSON.stringify({
        dns: dnsResult,
        http: httpResult,
        message: 'Dominio accesible desde AWS'
      })
    };

  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: error.message,
        message: 'Error de conectividad'
      })
    };
  }
};