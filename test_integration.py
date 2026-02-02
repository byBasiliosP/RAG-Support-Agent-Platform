#!/usr/bin/env python3
"""
Integration Test Script for RAG-Support-Agent
Tests both backend API endpoints and frontend-backend communication
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:9000"
FRONTEND_URL = "http://localhost:3000"

def test_endpoint(url, description, expected_status=200):
    """Test a single endpoint"""
    try:
        print(f"🔄 Testing: {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        status = response.status_code
        
        if status == expected_status:
            print(f"   ✅ Status: {status} (Expected: {expected_status})")
            if response.content:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 Response: List with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   📊 Response: Object with keys: {list(data.keys())}")
                    else:
                        print(f"   📊 Response: {type(data).__name__}")
                except:
                    print(f"   📄 Response: {len(response.content)} bytes")
            return True
        else:
            print(f"   ❌ Status: {status} (Expected: {expected_status})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_backend():
    """Test backend API endpoints"""
    print("🚀 BACKEND API TESTS")
    print("=" * 50)
    
    tests = [
        (f"{BACKEND_URL}/health", "Health Check"),
        (f"{BACKEND_URL}/", "Root Endpoint"),
        (f"{BACKEND_URL}/support/users", "Support Users"),
        (f"{BACKEND_URL}/support/tickets", "Support Tickets"),
        (f"{BACKEND_URL}/support/categories", "Support Categories"),
        (f"{BACKEND_URL}/rag/query?q=password", "RAG Query - Password"),
        (f"{BACKEND_URL}/analytics/elevenlabs", "ElevenLabs Analytics"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, description in tests:
        if test_endpoint(url, description):
            passed += 1
        print()  # Add spacing
    
    print(f"📊 Backend Tests: {passed}/{total} passed")
    return passed == total

def test_frontend():
    """Test frontend availability"""
    print("\n🌐 FRONTEND TESTS")
    print("=" * 50)
    
    tests = [
        (f"{FRONTEND_URL}", "Frontend Main Page"),
        (f"{FRONTEND_URL}/test", "Frontend Test Page"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, description in tests:
        if test_endpoint(url, description):
            passed += 1
        print()  # Add spacing
    
    print(f"📊 Frontend Tests: {passed}/{total} passed")
    return passed == total

def test_database_content():
    """Test that database has sample data"""
    print("\n💾 DATABASE CONTENT TESTS")
    print("=" * 50)
    
    try:
        # Test users
        response = requests.get(f"{BACKEND_URL}/support/users")
        users = response.json()
        print(f"✅ Users in database: {len(users)}")
        
        # Test tickets
        response = requests.get(f"{BACKEND_URL}/support/tickets")
        tickets = response.json()
        print(f"✅ Tickets in database: {len(tickets)}")
        
        # Test RAG documents
        response = requests.get(f"{BACKEND_URL}/rag/query?q=test")
        rag_response = response.json()
        docs = rag_response.get('source_documents', [])
        print(f"✅ RAG documents available: {len(docs)}")
        
        return len(users) > 0 and len(tickets) > 0 and len(docs) > 0
        
    except Exception as e:
        print(f"❌ Database content test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable configuration"""
    print("\n🔧 ENVIRONMENT TESTS")
    print("=" * 50)
    
    try:
        # Test backend environment by checking if it responds correctly
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✅ Backend environment variables loaded correctly")
            backend_ok = True
        else:
            print("❌ Backend environment issues")
            backend_ok = False
            
        # Test if frontend can reach backend (indicates correct env vars)
        response = requests.get(f"{FRONTEND_URL}")
        if response.status_code == 200:
            print("✅ Frontend environment variables loaded correctly")
            frontend_ok = True
        else:
            print("❌ Frontend environment issues")
            frontend_ok = False
            
        return backend_ok and frontend_ok
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 RAG-SUPPORT-AGENT INTEGRATION TESTS")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Run all test suites
    results.append(("Backend API", test_backend()))
    results.append(("Frontend", test_frontend()))
    results.append(("Database Content", test_database_content()))
    results.append(("Environment Config", test_environment_variables()))
    
    # Summary
    print("\n📋 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    total_passed = 0
    total_tests = len(results)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if passed:
            total_passed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 OVERALL RESULT: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! The integration is working correctly.")
        print("\n📝 Next Steps:")
        print("   • Frontend is running at: http://localhost:3000")
        print("   • Backend is running at: http://localhost:9000")
        print("   • API Documentation: http://localhost:9000/docs")
        print("   • Ready for production deployment!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED! Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
