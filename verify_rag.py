
import sys
import os
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"

def verify_rag_integration():
    print("🤖 Verifying RAG AI Integration...")
    print("-" * 50)

    # 1. Trigger Simulation Analysis
    print("\n1. Triggering Simulation Mode...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"simulate": True},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Analysis failed: {response.text}")
            return
            
        data = response.json()
        print("✅ Simulation successful")
        
        # 2. Check for AI Insights in Response
        print("\n2. Checking Response for AI Insights...")
        if 'ai_insights' in data:
            print("✅ 'ai_insights' field present in response")
            insights = data['ai_insights']
            print(f"   Threat Assessment: {insights.get('threat_assessment', 'N/A')[:50]}...")
            print(f"   Similar Cases: {len(insights.get('similar_cases', []))}")
            
            # Check for error (fallback mode)
            if 'error' in insights:
                print(f"⚠️  Note: RAG service returned error (expected if dependencies missing): {insights['error']}")
            else:
                print("🎉 SIMULATION: Real AI insights returned!")
        else:
            print("❌ 'ai_insights' MISING from response")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is Flask running?")
        return

    print("-" * 50)
    print("Verification Complete")

if __name__ == "__main__":
    verify_rag_integration()
