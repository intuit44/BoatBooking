const { SESClient, SendEmailCommand } = require('@aws-sdk/client-ses');

const sesClient = new SESClient({ region: 'us-east-1' });

async function testSES() {
  try {
    const emailParams = {
      Source: 'noreply@remeocci.org',
      Destination: {
        ToAddresses: ['demo@boatrental.ve']
      },
      Message: {
        Subject: {
          Data: 'Test SES - BoatRental',
          Charset: 'UTF-8'
        },
        Body: {
          Text: {
            Data: 'Este es un email de prueba desde SES para verificar que funciona correctamente.',
            Charset: 'UTF-8'
          }
        }
      }
    };

    const result = await sesClient.send(new SendEmailCommand(emailParams));
    console.log('✅ Email enviado exitosamente:', result.MessageId);
    
  } catch (error) {
    console.error('❌ Error enviando email:', error.message);
    
    if (error.message.includes('MessageRejected')) {
      console.log('🔍 Posible causa: SES en modo sandbox - solo puede enviar a emails verificados');
    }
  }
}

testSES();