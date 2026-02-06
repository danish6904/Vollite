#!/usr/bin/env python3
"""
Test script to demonstrate how to use the enhanced analysis API endpoints
with a running Flask server
"""

import requests
import json
import time

def test_api_endpoints():
    """Test the enhanced analysis endpoints with a running server"""
    
    base_url = "http://localhost:5000"
    
    print("🌐 Testing Enhanced Analysis API Endpoints")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ User registered successfully")
            token = response.json()['access_token']
        elif response.status_code == 409:
            print("ℹ️  User already exists, trying to login...")
            # Try to login instead
            login_data = {
                "username": "testuser",
                "password": "TestPassword123"
            }
            response = requests.post(f"{base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json()['access_token']
                print("✅ User logged in successfully")
            else:
                print(f"❌ Login failed: {response.text}")
                return
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask app is running:")
        print("   python app.py")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Check existing sessions
    print("\n2. Checking existing analysis sessions...")
    try:
        response = requests.get(f"{base_url}/api/analysis/sessions", headers=headers)
        if response.status_code == 200:
            sessions = response.json()['sessions']
            print(f"✅ Found {len(sessions)} existing sessions")
            
            if sessions:
                # Use the first session for testing
                session_id = sessions[0]['id']
                print(f"📋 Using session ID: {session_id}")
                
                # Step 3: Test detailed analysis endpoint
                print(f"\n3. Testing detailed analysis endpoint...")
                response = requests.get(f"{base_url}/api/analysis/detailed/{session_id}", headers=headers)
                
                if response.status_code == 200:
                    detailed_data = response.json()
                    print("✅ Detailed analysis endpoint works!")
                    print(f"   Risk Score: {detailed_data.get('original_risk_score', 'N/A')}")
                    print(f"   Analysis Status: {detailed_data.get('analysis_status', 'N/A')}")
                    
                    if 'detailed_analysis' in detailed_data:
                        analysis = detailed_data['detailed_analysis']
                        print(f"   Enhanced Risk Score: {analysis.get('risk_score', 'N/A')}")
                        print(f"   Risk Level: {analysis.get('risk_level', 'N/A')}")
                        print(f"   Risk Factors: {len(analysis.get('risk_factors', []))}")
                else:
                    print(f"❌ Detailed analysis failed: {response.status_code} - {response.text}")
                
                # Step 4: Test explain endpoint
                print(f"\n4. Testing explain endpoint...")
                response = requests.get(f"{base_url}/api/analysis/explain/{session_id}", headers=headers)
                
                if response.status_code == 200:
                    explain_data = response.json()
                    print("✅ Explain endpoint works!")
                    print(f"   Risk Score: {explain_data.get('risk_score', 'N/A')}")
                    print(f"   Risk Level: {explain_data.get('risk_level', 'N/A')}")
                    print(f"   Confidence: {explain_data.get('confidence', 'N/A')}%")
                    print(f"   Factor Count: {explain_data.get('factor_count', 'N/A')}")
                    
                    if 'explanation' in explain_data:
                        print(f"\n📝 Explanation Preview:")
                        explanation = explain_data['explanation']
                        # Show first 200 characters
                        preview = explanation[:200] + "..." if len(explanation) > 200 else explanation
                        print(f"   {preview}")
                    
                    if 'recommendations' in explain_data:
                        print(f"\n💡 Recommendations ({len(explain_data['recommendations'])}):")
                        for i, rec in enumerate(explain_data['recommendations'][:3], 1):
                            print(f"   {i}. {rec}")
                        if len(explain_data['recommendations']) > 3:
                            print(f"   ... and {len(explain_data['recommendations']) - 3} more")
                            
                else:
                    print(f"❌ Explain endpoint failed: {response.status_code} - {response.text}")
                
                # Step 5: Test regular results endpoint for comparison
                print(f"\n5. Testing regular results endpoint...")
                response = requests.get(f"{base_url}/api/analysis/results/{session_id}", headers=headers)
                
                if response.status_code == 200:
                    results_data = response.json()
                    print("✅ Regular results endpoint works!")
                    print(f"   Session Status: {results_data.get('session', {}).get('analysis_status', 'N/A')}")
                    print(f"   Risk Score: {results_data.get('results', {}).get('risk_score', 'N/A')}")
                    print(f"   Alerts: {len(results_data.get('alerts', []))}")
                else:
                    print(f"❌ Regular results failed: {response.status_code} - {response.text}")
                    
            else:
                print("ℹ️  No existing sessions found. You can:")
                print("   1. Upload a memory dump file first")
                print("   2. Or create a test session using the test script")
                
        else:
            print(f"❌ Failed to get sessions: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("✅ API Endpoint Testing Complete!")
    print("=" * 50)

def show_manual_testing_guide():
    """Show how to manually test the endpoints"""
    print("\n📖 Manual Testing Guide:")
    print("=" * 30)
    
    print("""
1. Start your Flask server:
   python app.py

2. Open another terminal and run:
   python test_api_endpoints.py

3. Or test manually with curl:

   # Register/Login
   curl -X POST http://localhost:5000/api/auth/register \\
        -H 'Content-Type: application/json' \\
        -d '{"username": "testuser", "email": "test@example.com", "password": "TestPassword123"}'

   # Get token from response, then:
   curl -X GET http://localhost:5000/api/analysis/sessions \\
        -H 'Authorization: Bearer YOUR_TOKEN'

   # Test enhanced endpoints (replace SESSION_ID):
   curl -X GET http://localhost:5000/api/analysis/detailed/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'

   curl -X GET http://localhost:5000/api/analysis/explain/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'

4. Or use the simple test script to see the RiskAnalyzer in action:
   python simple_test.py
""")

if __name__ == '__main__':
    test_api_endpoints()
    show_manual_testing_guide()
