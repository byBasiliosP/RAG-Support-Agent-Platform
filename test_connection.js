// Test script to verify frontend-backend connection
const axios = require('axios');

const testConnection = async () => {
  console.log('Testing frontend-backend connection...\n');
  
  // Test 1: Backend health check
  try {
    console.log('1. Testing backend health check...');
    const response = await axios.get('http://localhost:9000/');
    console.log('✅ Backend health check successful:');
    console.log('   Status:', response.status);
    console.log('   Data:', response.data);
    console.log('   CORS headers present:', !!response.headers['access-control-allow-origin']);
  } catch (error) {
    console.log('❌ Backend health check failed:', error.message);
    return;
  }
  
  // Test 2: RAG endpoint
  try {
    console.log('\n2. Testing RAG endpoint...');
    const ragResponse = await axios.post('http://localhost:9000/rag/query', {
      query: 'How do I reset my password?'
    });
    console.log('✅ RAG endpoint successful:');
    console.log('   Status:', ragResponse.status);
    console.log('   Response length:', ragResponse.data.response?.length || 0, 'characters');
    console.log('   Sources found:', ragResponse.data.sources?.length || 0);
  } catch (error) {
    console.log('❌ RAG endpoint failed:', error.message);
  }
  
  // Test 3: Frontend accessibility
  try {
    console.log('\n3. Testing frontend accessibility...');
    const frontendResponse = await axios.get('http://localhost:3000');
    console.log('✅ Frontend accessible:');
    console.log('   Status:', frontendResponse.status);
    console.log('   Contains React app:', frontendResponse.data.includes('__next'));
  } catch (error) {
    console.log('❌ Frontend not accessible:', error.message);
  }
  
  console.log('\n✨ Connection test completed!');
};

testConnection();
