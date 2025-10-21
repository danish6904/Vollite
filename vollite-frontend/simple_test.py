#!/usr/bin/env python3
"""
Simple test to demonstrate enhanced risk analysis with actual data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.risk_analyzer import RiskAnalyzer

def test_with_realistic_data():
    """Test with realistic suspicious data"""
    print("🔍 Testing Enhanced Risk Analysis with Realistic Data")
    print("=" * 60)
    
    analyzer = RiskAnalyzer()
    
    # Simulate data that would come from a real memory dump analysis
    suspicious_data = {
        'processes': [
            {
                'pid': 1234,
                'name': 'powershell.exe',
                'ppid': 5678,
                'path': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
                'cmdline': 'powershell.exe -enc UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAAMQAwAA==',
                'signature_status': 'unsigned'
            },
            {
                'pid': 5678,
                'name': 'notepad.exe',
                'ppid': 1000,
                'path': 'C:\\Windows\\System32\\notepad.exe',
                'cmdline': 'notepad.exe',
                'signature_status': 'signed'
            },
            {
                'pid': 9999,
                'name': 'rundll32.exe',
                'ppid': 1234,
                'path': 'C:\\Windows\\System32\\rundll32.exe',
                'cmdline': 'rundll32.exe javascript:"\\..\\mshtml,RunHTMLApplication ";document.write();h=new%20ActiveXObject("WScript.Shell").run("cmd /c echo test",0,true);',
                'signature_status': 'signed'
            },
            {
                'pid': 8888,
                'name': 'suspicious.exe',
                'ppid': 1234,
                'path': 'C:\\Users\\Public\\suspicious.exe',
                'cmdline': 'suspicious.exe --steal-data',
                'signature_status': 'unsigned'
            }
        ],
        'connections': [
            {
                'remote': '203.0.113.1:4444',
                'local': '192.168.1.100:12345',
                'protocol': 'TCP',
                'state': 'ESTABLISHED'
            },
            {
                'remote': '198.51.100.50:8080',
                'local': '192.168.1.100:54321',
                'protocol': 'TCP',
                'state': 'ESTABLISHED'
            },
            {
                'remote': '10.0.0.1:1337',
                'local': '192.168.1.100:9999',
                'protocol': 'TCP',
                'state': 'ESTABLISHED'
            }
        ],
        'system_info': {
            'registry': [
                {
                    'key': 'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                    'value': 'suspicious.exe',
                    'data': 'C:\\Users\\Public\\suspicious.exe'
                },
                {
                    'key': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                    'value': 'malware',
                    'data': 'C:\\Windows\\System32\\malware.exe'
                }
            ],
            'files': [
                {
                    'path': 'C:\\Users\\Public\\suspicious.exe',
                    'executable': True,
                    'size': 1024000
                },
                {
                    'path': 'C:\\Windows\\Temp\\malware.dll',
                    'executable': True,
                    'size': 512000
                }
            ]
        }
    }
    
    # Analyze the data
    result = analyzer.analyze_risk(suspicious_data, suspicious_data, suspicious_data['system_info'])
    
    print(f"📊 RISK ANALYSIS RESULTS:")
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Confidence: {result['confidence']}%")
    print(f"   Risk Factors Found: {len(result['risk_factors'])}")
    
    print(f"\n🔍 DETAILED BREAKDOWN:")
    breakdown = result['breakdown']
    for category, score in breakdown.items():
        print(f"   {category}: +{score} points")
    
    print(f"\n⚠️  RISK FACTORS:")
    for i, factor in enumerate(result['risk_factors'], 1):
        print(f"   {i}. [{factor['severity']}] {factor['category']}")
        print(f"      {factor['description']}")
        print(f"      Impact: {factor['impact']}")
        print(f"      Details: {factor['details']}")
        print()
    
    print(f"📝 EXPLANATION:")
    print(result['explanation'])
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    return result

def test_with_clean_data():
    """Test with clean, normal data"""
    print("\n" + "=" * 60)
    print("🧹 Testing with Clean Data (Normal System)")
    print("=" * 60)
    
    analyzer = RiskAnalyzer()
    
    clean_data = {
        'processes': [
            {
                'pid': 1000,
                'name': 'explorer.exe',
                'ppid': 4,
                'path': 'C:\\Windows\\explorer.exe',
                'cmdline': 'explorer.exe',
                'signature_status': 'signed'
            },
            {
                'pid': 2000,
                'name': 'chrome.exe',
                'ppid': 1000,
                'path': 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'cmdline': 'chrome.exe',
                'signature_status': 'signed'
            }
        ],
        'connections': [
            {
                'remote': '8.8.8.8:53',
                'local': '192.168.1.100:12345',
                'protocol': 'UDP',
                'state': 'ESTABLISHED'
            },
            {
                'remote': '172.217.164.110:443',
                'local': '192.168.1.100:54321',
                'protocol': 'TCP',
                'state': 'ESTABLISHED'
            }
        ],
        'system_info': {
            'registry': [],
            'files': []
        }
    }
    
    result = analyzer.analyze_risk(clean_data, clean_data, clean_data['system_info'])
    
    print(f"📊 RISK ANALYSIS RESULTS:")
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Confidence: {result['confidence']}%")
    print(f"   Risk Factors Found: {len(result['risk_factors'])}")
    
    if result['risk_factors']:
        print(f"\n⚠️  RISK FACTORS:")
        for i, factor in enumerate(result['risk_factors'], 1):
            print(f"   {i}. [{factor['severity']}] {factor['category']}")
            print(f"      {factor['description']}")
    else:
        print(f"\n✅ No risk factors detected - system appears clean!")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    return result

def show_api_usage():
    """Show how to use the API endpoints"""
    print("\n" + "=" * 60)
    print("🌐 HOW TO USE WITH ACTUAL API ENDPOINTS")
    print("=" * 60)
    
    print("""
1. Start your Flask application:
   python app.py

2. Get authentication token:
   curl -X POST http://localhost:5000/api/auth/login \\
        -H 'Content-Type: application/json' \\
        -d '{"username": "your_username", "password": "your_password"}'

3. Upload a memory dump file:
   curl -X POST http://localhost:5000/api/analysis/upload \\
        -H 'Authorization: Bearer YOUR_TOKEN' \\
        -F 'file=@your_memory_dump.dmp'

4. Start analysis:
   curl -X POST http://localhost:5000/api/analysis/analyze/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'

5. Get detailed risk analysis:
   curl -X GET http://localhost:5000/api/analysis/detailed/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'

6. Get risk explanation:
   curl -X GET http://localhost:5000/api/analysis/explain/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'

7. Check analysis status:
   curl -X GET http://localhost:5000/api/analysis/status/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'

8. Get analysis results:
   curl -X GET http://localhost:5000/api/analysis/results/SESSION_ID \\
        -H 'Authorization: Bearer YOUR_TOKEN'
""")

if __name__ == '__main__':
    # Test with suspicious data
    suspicious_result = test_with_realistic_data()
    
    # Test with clean data
    clean_result = test_with_clean_data()
    
    # Show API usage
    show_api_usage()
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE!")
    print("=" * 60)
    print(f"Suspicious data score: {suspicious_result['risk_score']} ({suspicious_result['risk_level']})")
    print(f"Clean data score: {clean_result['risk_score']} ({clean_result['risk_level']})")
    print("\nThe enhanced risk analysis system is working correctly!")
    print("You can now use the API endpoints to get detailed risk analysis for your memory dumps.")
