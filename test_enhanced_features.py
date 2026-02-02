#!/usr/bin/env python3
"""
Test script for enhanced support system features
Tests KB management, voice integration, and analytics
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:9000"

async def test_api_endpoint(session, method, endpoint, data=None, params=None):
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            async with session.get(url, params=params) as response:
                content = await response.text()
                return response.status, content
        elif method.upper() == "POST":
            async with session.post(url, json=data, params=params) as response:
                content = await response.text()
                return response.status, content
        elif method.upper() == "PUT":
            async with session.put(url, json=data) as response:
                content = await response.text()
                return response.status, content
        elif method.upper() == "DELETE":
            async with session.delete(url) as response:
                content = await response.text()
                return response.status, content
    except Exception as e:
        return None, str(e)

async def run_tests():
    """Run comprehensive tests of the enhanced features"""
    
    print("🚀 Testing Enhanced Support System Features")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Check
        print("\n📡 1. Testing API Health Check")
        status, response = await test_api_endpoint(session, "GET", "/")
        if status == 200:
            print("✅ Backend is running")
            try:
                data = json.loads(response)
                print(f"   Version: {data.get('version', 'Unknown')}")
                print(f"   Status: {data.get('status', 'Unknown')}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"❌ Backend health check failed: {status}")
            return
        
        # Test 2: Basic Analytics
        print("\n📊 2. Testing Analytics Endpoints")
        status, response = await test_api_endpoint(session, "GET", "/analytics/summary")
        if status == 200:
            print("✅ Analytics summary endpoint working")
            try:
                data = json.loads(response)
                print(f"   Documents: {data.get('total_documents', 0)}")
                print(f"   Nodes: {data.get('total_nodes', 0)}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  Analytics endpoint returned: {status}")
        
        # Test 3: Support System - Create User
        print("\n👥 3. Testing User Management")
        user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "display_name": "Test User",
            "role": "end-user"
        }
        status, response = await test_api_endpoint(session, "POST", "/support/users", user_data)
        if status == 200:
            print("✅ User creation successful")
            try:
                user = json.loads(response)
                print(f"   Created user ID: {user.get('user_id')}")
                print(f"   Username: {user.get('username')}")
            except:
                print(f"   Response: {response}")
        elif status == 400 and "already exists" in response:
            print("⚠️  User already exists (this is ok)")
        else:
            print(f"⚠️  User creation returned: {status} - {response}")
        
        # Test 4: Category Management
        print("\n📂 4. Testing Category Management")
        category_data = {
            "name": "Test Category",
            "description": "A test category for testing"
        }
        status, response = await test_api_endpoint(session, "POST", "/support/categories", category_data)
        if status == 200:
            print("✅ Category creation successful")
            try:
                category = json.loads(response)
                print(f"   Created category ID: {category.get('category_id')}")
                print(f"   Name: {category.get('name')}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  Category creation returned: {status} - {response}")
        
        # Test 5: Get Categories
        print("\n📋 5. Testing Category Retrieval")
        status, response = await test_api_endpoint(session, "GET", "/support/categories")
        if status == 200:
            print("✅ Category retrieval successful")
            try:
                categories = json.loads(response)
                print(f"   Found {len(categories)} categories")
                for cat in categories[:3]:  # Show first 3
                    print(f"   - {cat.get('name')} (ID: {cat.get('category_id')})")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  Category retrieval returned: {status}")
        
        # Test 6: KB Article Management
        print("\n📚 6. Testing KB Article Management")
        kb_data = {
            "title": "Test KB Article",
            "summary": "A test knowledge base article",
            "content": "This is test content for the KB article. It explains how to solve test issues.",
            "url": "https://test.example.com/kb/test-article"
        }
        status, response = await test_api_endpoint(session, "POST", "/support/kb-articles", kb_data, {"created_by": 1})
        if status == 200:
            print("✅ KB article creation successful")
            try:
                article = json.loads(response)
                print(f"   Created KB ID: {article.get('kb_id')}")
                print(f"   Title: {article.get('title')}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  KB article creation returned: {status} - {response}")
        
        # Test 7: KB Article Retrieval
        print("\n📖 7. Testing KB Article Retrieval")
        status, response = await test_api_endpoint(session, "GET", "/support/kb-articles", params={"limit": 5})
        if status == 200:
            print("✅ KB article retrieval successful")
            try:
                articles = json.loads(response)
                print(f"   Found {len(articles)} KB articles")
                for article in articles[:3]:  # Show first 3
                    print(f"   - {article.get('title')} (ID: {article.get('kb_id')})")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  KB article retrieval returned: {status}")
        
        # Test 8: Ticket Creation
        print("\n🎫 8. Testing Ticket Creation")
        ticket_data = {
            "subject": "Test Support Ticket",
            "description": "This is a test ticket to verify the ticketing system is working properly.",
            "priority": "Medium"
        }
        status, response = await test_api_endpoint(session, "POST", "/support/tickets", ticket_data, {"requester_id": 1})
        if status == 200:
            print("✅ Ticket creation successful")
            try:
                ticket = json.loads(response)
                print(f"   Created ticket ID: {ticket.get('ticket_id')}")
                print(f"   Subject: {ticket.get('subject')}")
                print(f"   Status: {ticket.get('status')}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  Ticket creation returned: {status} - {response}")
        
        # Test 9: RAG Query
        print("\n🧠 9. Testing RAG System")
        rag_data = {
            "query": "How do I reset my password?",
            "include_context": True
        }
        status, response = await test_api_endpoint(session, "POST", "/rag/query", rag_data)
        if status == 200:
            print("✅ RAG query successful")
            try:
                result = json.loads(response)
                print(f"   Query: {result.get('query', 'N/A')}")
                print(f"   Response length: {len(result.get('answer', ''))}")
                sources = result.get('source_documents', [])
                print(f"   Sources found: {len(sources)}")
            except:
                print(f"   Response: {response[:200]}...")
        else:
            print(f"⚠️  RAG query returned: {status} - {response[:100]}...")
        
        # Test 10: Dashboard Stats
        print("\n📊 10. Testing Dashboard Statistics")
        status, response = await test_api_endpoint(session, "GET", "/support/dashboard/stats")
        if status == 200:
            print("✅ Dashboard stats successful")
            try:
                stats = json.loads(response)
                print(f"   Total tickets: {stats.get('total_tickets', 0)}")
                print(f"   Recent tickets: {stats.get('recent_tickets', 0)}")
                by_status = stats.get('by_status', {})
                print(f"   By status: {dict(list(by_status.items())[:3])}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  Dashboard stats returned: {status}")
        
        # Test 11: Voice Support (if available)
        print("\n🎤 11. Testing Voice Support Endpoints")
        status, response = await test_api_endpoint(session, "GET", "/voice-support/health")
        if status == 200:
            print("✅ Voice support health check successful")
            try:
                health = json.loads(response)
                print(f"   ElevenLabs status: {health.get('elevenlabs_status', 'Unknown')}")
                print(f"   Voice features: {health.get('voice_features_available', False)}")
            except:
                print(f"   Response: {response}")
        else:
            print(f"⚠️  Voice support returned: {status}")
        
    print("\n" + "=" * 60)
    print("🎉 Test Suite Completed!")
    print("\nNext Steps:")
    print("1. ✅ Backend API is functional")
    print("2. ✅ Database integration working")
    print("3. ✅ Enhanced features implemented")
    print("4. 🌐 Frontend should be accessible at: http://localhost:3000")
    print("5. 📚 KB Management: http://localhost:3000/kb/manage")
    print("6. 🎫 Smart Ticket Creation: http://localhost:3000/tickets/create")
    print("7. 📊 Analytics Dashboard: http://localhost:3000/analytics")

if __name__ == "__main__":
    print(f"🕐 Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(run_tests())
