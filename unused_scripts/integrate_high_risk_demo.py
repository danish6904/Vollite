#!/usr/bin/env python3
"""
Integrate high-risk test data into the dashboard demo
This will make your dashboard show high-risk analysis results
"""

import json
import os

def update_demo_with_high_risk_data():
    """Update the demo data in app.py to use high-risk test data"""
    
    print("🔴 Integrating High-Risk Test Data into Dashboard Demo")
    print("=" * 60)
    
    # Load the high-risk test data
    test_file = "test_memory_dumps/high_risk_memory_dump.json"
    if not os.path.exists(test_file):
        print(f"❌ Test data file not found: {test_file}")
        print("Run create_high_risk_test_data.py first!")
        return
    
    with open(test_file, 'r') as f:
        high_risk_data = json.load(f)
    
    print(f"✅ Loaded high-risk test data:")
    print(f"   Processes: {len(high_risk_data['processes'])}")
    print(f"   Network connections: {len(high_risk_data['network_connections'])}")
    print(f"   Registry entries: {len(high_risk_data['system_info']['registry'])}")
    print(f"   Suspicious files: {len(high_risk_data['system_info']['files'])}")
    
    # Create the enhanced demo data structure
    enhanced_demo_data = {
        'summary': f'High-Risk Analysis: {high_risk_data["metadata"]["description"]}',
        'key_findings': [
            f'Risk Level: HIGH - Multiple threat indicators detected',
            f'Processes analyzed: {len(high_risk_data["processes"])}',
            f'Network connections: {len(high_risk_data["network_connections"])}',
            f'Registry persistence mechanisms: {len(high_risk_data["system_info"]["registry"])}',
            f'Suspicious files: {len(high_risk_data["system_info"]["files"])}'
        ],
        'risk_score': 65,  # This will be calculated by RiskAnalyzer
        'alerts': [
            {
                'type': 'critical',
                'title': 'High-Risk System Detected',
                'description': 'Multiple threat indicators found - immediate investigation required',
                'severity': 'high',
                'message': 'System shows signs of advanced persistent threat (APT) activity',
                'recommendation': 'Immediately isolate system and begin forensic investigation'
            },
            {
                'type': 'warning',
                'title': 'PowerShell with Encoded Commands',
                'description': 'Suspicious PowerShell execution detected',
                'severity': 'critical',
                'message': 'PowerShell with base64 encoded commands and hidden execution',
                'recommendation': 'Review PowerShell logs and decode suspicious commands'
            },
            {
                'type': 'warning',
                'title': 'LOLBin Abuse Detected',
                'description': 'Living-off-the-land binary abuse',
                'severity': 'high',
                'message': 'rundll32.exe used for malicious JavaScript execution',
                'recommendation': 'Audit LOLBin usage policies and implement monitoring'
            },
            {
                'type': 'warning',
                'title': 'Suspicious Network Activity',
                'description': 'Connections to suspicious ports and IPs',
                'severity': 'high',
                'message': 'Multiple connections to non-standard ports (4444, 8080, 1337)',
                'recommendation': 'Block network connections to suspicious IPs/ports'
            },
            {
                'type': 'warning',
                'title': 'Persistence Mechanisms',
                'description': 'Registry-based persistence detected',
                'severity': 'high',
                'message': 'Multiple registry autostart entries for suspicious executables',
                'recommendation': 'Remove suspicious registry entries and reset startup configs'
            }
        ],
        'process_tree': {
            'name': 'System',
            'risk': 'High',
            'children': [
                {
                    'name': 'explorer.exe',
                    'risk': 'Low',
                    'children': [
                        {
                            'name': 'powershell.exe',
                            'risk': 'Critical',
                            'children': [
                                {
                                    'name': 'rundll32.exe',
                                    'risk': 'High'
                                },
                                {
                                    'name': 'svchost.exe',
                                    'risk': 'High'
                                }
                            ]
                        },
                        {
                            'name': 'notepad.exe',
                            'risk': 'Low',
                            'children': [
                                {
                                    'name': 'cmd.exe',
                                    'risk': 'High'
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        'generated_at': high_risk_data['metadata']['timestamp'],
        'status': 'completed'
    }
    
    print(f"\n📊 Enhanced Demo Data Preview:")
    print(f"   Summary: {enhanced_demo_data['summary']}")
    print(f"   Risk Score: {enhanced_demo_data['risk_score']}")
    print(f"   Alerts: {len(enhanced_demo_data['alerts'])}")
    print(f"   Key Findings: {len(enhanced_demo_data['key_findings'])}")
    
    # Save the enhanced demo data
    demo_file = "enhanced_demo_data.json"
    with open(demo_file, 'w') as f:
        json.dump(enhanced_demo_data, f, indent=2)
    
    print(f"\n✅ Enhanced demo data saved to: {demo_file}")
    print(f"\n🎯 Your dashboard will now show:")
    print(f"   - Risk Score: 65% (High)")
    print(f"   - 5 detailed security alerts")
    print(f"   - Process tree with risk indicators")
    print(f"   - Specific threat recommendations")
    
    return enhanced_demo_data

def show_integration_steps():
    """Show how to integrate this with your dashboard"""
    
    print(f"\n🔧 INTEGRATION STEPS")
    print("=" * 25)
    
    print("""
To make your dashboard show high-risk analysis:

1. Replace the demo data in app.py:
   - Open vollite-frontend/app.py
   - Find the simulate mode section (around line 167)
   - Replace the demo_data with the enhanced_demo_data.json content

2. Or use the test data directly:
   - Upload the high_risk_memory_dump.json file
   - Your enhanced analysis will process it automatically

3. Test the dashboard:
   - Start your Flask app: python app.py
   - Go to dashboard and click "Use Demo Data"
   - You'll see high-risk analysis results

4. Expected Results:
   - Risk Score: 65% (High)
   - Multiple security alerts
   - Detailed threat indicators
   - Actionable recommendations

🎯 This will demonstrate your enhanced risk analysis system
   with realistic high-risk scenarios!
""")

if __name__ == '__main__':
    # Create enhanced demo data
    enhanced_data = update_demo_with_high_risk_data()
    
    # Show integration steps
    show_integration_steps()
    
    print(f"\n✅ High-risk demo data ready for dashboard integration!")

