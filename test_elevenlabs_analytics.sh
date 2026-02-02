#!/bin/bash

# Test ElevenLabs Analytics Integration
echo "Testing ElevenLabs Analytics Integration..."
echo "========================================"

BASE_URL="http://localhost:9000"

echo -e "\n1. Testing ElevenLabs Analytics Summary..."
curl -s -X GET "$BASE_URL/analytics/elevenlabs" | jq '.' || echo "Failed to get analytics summary"

echo -e "\n2. Testing ElevenLabs Conversations List..."
curl -s -X GET "$BASE_URL/analytics/elevenlabs/conversations?limit=3" | jq '.' || echo "Failed to get conversations"

echo -e "\n3. Testing ElevenLabs Specific Conversation..."
curl -s -X GET "$BASE_URL/analytics/elevenlabs/conversations/conv_001" | jq '.' || echo "Failed to get specific conversation"

echo -e "\n4. Testing ElevenLabs Conversation Messages..."
curl -s -X GET "$BASE_URL/analytics/elevenlabs/conversations/conv_001/messages" | jq '.' || echo "Failed to get conversation messages"

echo -e "\n5. Testing ElevenLabs Conversation Tracking (POST)..."
curl -s -X POST "$BASE_URL/analytics/elevenlabs/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test_conv_123",
    "agent_id": "test_agent_1",
    "user_id": "test_user_1",
    "start_time": "'$(date -u +%Y-%m-%dT%H:%M:%S)'",
    "status": "active",
    "messages_count": 0,
    "metadata": {}
  }' | jq '.' || echo "Failed to track conversation"

echo -e "\n6. Testing ElevenLabs Conversation Update (PUT)..."
curl -s -X PUT "$BASE_URL/analytics/elevenlabs/conversations/test_conv_123" \
  -H "Content-Type: application/json" \
  -d '{
    "end_time": "'$(date -u +%Y-%m-%dT%H:%M:%S)'",
    "duration_seconds": 120,
    "status": "completed",
    "messages_count": 5
  }' | jq '.' || echo "Failed to update conversation"

echo -e "\n7. Testing Updated Analytics Summary..."
curl -s -X GET "$BASE_URL/analytics/elevenlabs" | jq '.total_conversations, .conversations_by_status' || echo "Failed to get updated analytics"

echo -e "\n8. Testing Backend Health Check..."
curl -s -X GET "$BASE_URL/health" | jq '.' || echo "Failed to get health status"

echo -e "\nElevenLabs Analytics Integration Test Complete!"
echo "=============================================="
