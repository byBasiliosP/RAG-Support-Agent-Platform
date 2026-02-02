// Test script to verify environment variables are properly loaded
const axios = require('axios');

async function testFrontendEnvVars() {
  try {
    console.log('Testing frontend environment variables...');
    
    // Test if frontend is responding
    const response = await axios.get('http://localhost:3000', {
      timeout: 5000
    });
    
    console.log('✅ Frontend is accessible');
    console.log('Status:', response.status);
    
    // Check if the HTML contains any environment variable references
    const htmlContent = response.data;
    if (htmlContent.includes('NEXT_PUBLIC_AGENT_ID')) {
      console.log('✅ NEXT_PUBLIC_AGENT_ID is referenced in the frontend');
    } else {
      console.log('❌ NEXT_PUBLIC_AGENT_ID not found in frontend HTML');
    }
    
  } catch (error) {
    console.error('❌ Error testing frontend:', error.message);
  }
}

// Run the test
testFrontendEnvVars();
