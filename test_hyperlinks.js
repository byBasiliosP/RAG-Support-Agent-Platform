// Test script to verify hyperlink functionality in chat responses
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const testChatWithHyperlinks = async () => {
  console.log('\n🔗 Testing Chat Hyperlink Functionality\n');
  
  // Test messages that should contain hyperlinks
  const testMessages = [
    'What are your phone numbers and contact information?',
    'Do you have a website or email address?',
    'How can I contact support by phone?',
    'What are your office hours and contact details?'
  ];
  
  console.log('📋 Suggested test messages (copy and paste into chat):');
  testMessages.forEach((msg, idx) => {
    console.log(`${idx + 1}. "${msg}"`);
  });
  
  console.log('\n📱 Expected hyperlink patterns in responses:');
  console.log('• Phone numbers: (555) 123-4567, +1-555-123-4567, 555.123.4567');
  console.log('• Websites: https://example.com, http://support.example.com');
  console.log('• Emails: support@example.com, help@company.org');
  
  console.log('\n🎯 What to look for:');
  console.log('• Phone numbers should be clickable and open phone app');
  console.log('• Websites should be clickable and open in new tab');
  console.log('• Email addresses should be clickable and open email client');
  console.log('• Links should be blue, underlined, and have hover effects');
  
  console.log('\n🚀 Open your browser and test the chat at: http://localhost:3002/chat');
  
  rl.question('\nPress Enter when you want to test the backend API directly...', async () => {
    console.log('\n🔍 Testing backend RAG API for responses with contact info...\n');
    
    try {
      const fetch = (await import('node-fetch')).default;
      
      const response = await fetch('http://localhost:9000/api/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: 'What are your contact phone numbers and website?'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Backend Response:');
        console.log('Query:', data.query);
        console.log('Answer:', data.answer);
        console.log('\n📞 Look for phone numbers, websites, or emails in the answer above');
        
        // Simple pattern detection for verification
        const phonePattern = /(\+?1?[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})/g;
        const urlPattern = /(https?:\/\/[^\s<>"{}|\\^`[\]]+)/g;
        const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
        
        const phones = data.answer.match(phonePattern) || [];
        const urls = data.answer.match(urlPattern) || [];
        const emails = data.answer.match(emailPattern) || [];
        
        console.log('\n🔍 Detected patterns:');
        if (phones.length > 0) console.log('📞 Phone numbers:', phones);
        if (urls.length > 0) console.log('🌐 URLs:', urls);
        if (emails.length > 0) console.log('📧 Emails:', emails);
        
        if (phones.length === 0 && urls.length === 0 && emails.length === 0) {
          console.log('ℹ️  No contact patterns detected in this response');
          console.log('💡 Try asking: "What are your office hours and phone number?"');
        }
        
      } else {
        console.log('❌ Backend Error:', response.status, response.statusText);
      }
    } catch (error) {
      console.log('❌ Connection Error:', error.message);
      console.log('💡 Make sure the backend is running on http://localhost:9000');
    }
    
    rl.close();
  });
};

testChatWithHyperlinks();
