#!/bin/bash

# Full Integration Test for Support Ticket System
echo "=== Support Ticket System Integration Test ==="
echo "Testing all endpoints and functionality..."

API_BASE="http://localhost:9000"
FRONTEND_BASE="http://localhost:3000"

echo ""
echo "1. Testing Backend Health Check..."
curl -s "$API_BASE/" | jq '.'

echo ""
echo "2. Testing Dashboard Stats..."
curl -s "$API_BASE/support/dashboard/stats" | jq '.'

echo ""
echo "3. Testing RAG Query (Password Reset)..."
curl -s "$API_BASE/rag/query?q=How%20do%20I%20reset%20my%20password%3F" | jq '.answer' | head -3

echo ""
echo "4. Testing RAG Query (Printer Issues)..."
curl -s "$API_BASE/rag/query?q=printer%20not%20working" | jq '.answer' | head -3

echo ""
echo "5. Testing RAG Query (Software Installation)..."
curl -s "$API_BASE/rag/query?q=install%20office" | jq '.answer' | head -3

echo ""
echo "6. Testing Categories Endpoint..."
curl -s "$API_BASE/support/categories" | jq '.'

echo ""
echo "7. Testing Users Endpoint..."
curl -s "$API_BASE/support/users" | jq 'length'

echo ""
echo "8. Testing Tickets Endpoint..."
curl -s "$API_BASE/support/tickets" | jq 'length'

echo ""
echo "9. Testing Frontend Accessibility..."
curl -s "$FRONTEND_BASE" | grep -q "MCIT Rapid Support" && echo "✓ Frontend accessible" || echo "✗ Frontend not accessible"

echo ""
echo "10. Creating Test Ticket..."
curl -s -X POST "$API_BASE/support/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Integration Ticket",
    "description": "This is a test ticket created by the integration test script",
    "priority": "Medium"
  }' \
  -G -d "requester_id=1" | jq '.ticket_id // "Error creating ticket"'

echo ""
echo "=== Integration Test Complete ==="
echo "Check the outputs above for any errors."
echo "Frontend should be accessible at: $FRONTEND_BASE"
echo "Backend API should be accessible at: $API_BASE"
