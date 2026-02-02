#!/bin/bash

# Test script for frontend-backend integration
echo "Testing frontend-backend integration..."

# Test 1: Backend health check
echo "1. Testing backend health..."
HEALTH=$(curl -s http://localhost:9000/)
echo "Backend response: $HEALTH"

# Test 2: Frontend accessibility
echo "2. Testing frontend accessibility..."
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/)
echo "Frontend status code: $FRONTEND"

# Test 3: Test knowledge base query
echo "3. Testing knowledge base query..."
QUERY_RESPONSE=$(curl -s "http://localhost:9000/rag/query?q=How%20do%20I%20reset%20my%20password")
echo "Query response: $QUERY_RESPONSE"

# Test 4: Get dashboard stats
echo "4. Testing dashboard stats..."
STATS=$(curl -s http://localhost:9000/support/dashboard/stats)
echo "Dashboard stats: $STATS"

# Test 5: Get ticket categories
echo "5. Testing categories..."
CATEGORIES=$(curl -s http://localhost:9000/support/categories)
echo "Categories: $CATEGORIES"

echo "Integration test complete!"
