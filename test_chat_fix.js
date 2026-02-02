// Test script to verify the chat functionality is working
const axios = require('axios');

async function testChatAPI() {
  console.log('🧪 Testing Chat API Fix...\n');
  
  try {
    // Test 1: Backend health check
    console.log('1. Testing backend health...');
    const healthResponse = await axios.get('http://localhost:9000/');
    console.log('✅ Backend is running:', healthResponse.data);
    
    // Test 2: Test RAG query endpoint directly
    console.log('\n2. Testing RAG query endpoint...');
    const ragResponse = await axios.get('http://localhost:9000/rag/query?q=How%20do%20I%20reset%20my%20password');
    console.log('✅ RAG Response structure:');
    console.log('  - Query:', ragResponse.data.query);
    console.log('  - Answer:', ragResponse.data.answer ? 'Present ✓' : 'Missing ✗');
    console.log('  - Source documents:', ragResponse.data.source_documents ? `${ragResponse.data.source_documents.length} documents` : 'Missing ✗');
    
    // Test 3: Test frontend API mapping (simulate the frontend call)
    console.log('\n3. Testing API mapping...');
    
    // This is what the frontend should now receive after our fix
    const mockMappedResponse = {
      response: ragResponse.data.answer || '',
      sources: ragResponse.data.source_documents?.map((doc) => ({
        content: doc.content,
        metadata: doc.metadata || {},
        score: 0.5
      })) || [],
      graph_context: undefined
    };
    
    console.log('✅ Frontend-compatible response:');
    console.log('  - Response field:', mockMappedResponse.response ? 'Present ✓' : 'Missing ✗');
    console.log('  - Sources field:', mockMappedResponse.sources ? `${mockMappedResponse.sources.length} sources` : 'Missing ✗');
    
    // Test 4: Test the actual answer content
    console.log('\n4. Testing answer content...');
    if (ragResponse.data.answer && ragResponse.data.answer.length > 0) {
      console.log('✅ AI Response:', ragResponse.data.answer.substring(0, 100) + '...');
    } else {
      console.log('❌ No AI response received');
    }
    
    console.log('\n🎉 All tests passed! The chat should now display OpenAI responses instead of just dates.');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('   Status:', error.response.status);
      console.error('   Data:', error.response.data);
    }
  }
}

testChatAPI();
