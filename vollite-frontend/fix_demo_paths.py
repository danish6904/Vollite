#!/usr/bin/env python3
"""
Auto-Fix Demo Data Paths
Automatically fixes Windows file path escaping issues in demo data
"""

import re
import os
import shutil
from datetime import datetime

class DemoDataPathFixer:
    def __init__(self):
        self.app_file = "app.py"
        self.backup_file = f"app_backup_pathfix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
    def create_backup(self):
        """Create backup of current app.py"""
        if os.path.exists(self.app_file):
            shutil.copy2(self.app_file, self.backup_file)
            print(f"✅ Backup created: {self.backup_file}")
            return True
        return False
    
    def fix_all_paths(self):
        """Fix all Windows file paths in demo data"""
        print("🔧 Auto-fixing Windows file paths in demo data...")
        
        try:
            # Create backup first
            self.create_backup()
            
            # Read current app.py
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix patterns
            fixes_applied = 0
            
            # Pattern 1: Fix 'path': 'C:\...' to 'path': r'C:\...'
            pattern1 = r"(\s+)'path': 'C:([^']+)'"
            replacement1 = r"\1'path': r'C:\2'"
            new_content, count1 = re.subn(pattern1, replacement1, content)
            fixes_applied += count1
            
            # Pattern 2: Fix 'data': 'C:\...' to 'data': r'C:\...'
            pattern2 = r"(\s+)'data': 'C:([^']+)'"
            replacement2 = r"\1'data': r'C:\2'"
            new_content, count2 = re.subn(pattern2, replacement2, new_content)
            fixes_applied += count2
            
            # Pattern 3: Fix cmdline with backslashes
            pattern3 = r"(\s+)'cmdline': '([^']*\\[^']*)'"
            replacement3 = r"\1'cmdline': r'\2'"
            new_content, count3 = re.subn(pattern3, replacement3, new_content)
            fixes_applied += count3
            
            # Write fixed content
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Applied {fixes_applied} path fixes:")
            print(f"   - File paths: {count1}")
            print(f"   - Data paths: {count2}")
            print(f"   - Command lines: {count3}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing paths: {e}")
            return False
    
    def verify_fix(self):
        """Verify that the fix worked"""
        try:
            # Test syntax compilation
            import py_compile
            py_compile.compile(self.app_file, doraise=True)
            print("✅ Syntax verification passed!")
            return True
        except py_compile.PyCompileError as e:
            print(f"❌ Syntax error still exists: {e}")
            return False
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def show_examples(self):
        """Show examples of correct vs incorrect paths"""
        print("\n📋 Path Format Examples:")
        print("=" * 40)
        
        examples = [
            ("❌ WRONG", "'path': 'C:\\Windows\\System32\\ntoskrnl.exe'"),
            ("✅ CORRECT", "'path': r'C:\\Windows\\System32\\ntoskrnl.exe'"),
            ("", ""),
            ("❌ WRONG", "'data': 'C:\\Users\\Public\\file.exe'"),
            ("✅ CORRECT", "'data': r'C:\\Users\\Public\\file.exe'"),
            ("", ""),
            ("❌ WRONG", "'cmdline': 'rundll32.exe javascript:\\..\\mshtml'"),
            ("✅ CORRECT", "'cmdline': r'rundll32.exe javascript:\\..\\mshtml'"),
        ]
        
        for status, example in examples:
            if example:
                print(f"{status:<12} {example}")
            else:
                print()
    
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
    fixer = DemoDataPathFixer()
    
    print("🔧 volLite Demo Data Path Auto-Fixer")
    print("=" * 40)
    print("This tool automatically fixes Windows file path escaping issues.")
    print()
    
    print("Available options:")
    print("1. 🔧 Auto-fix all paths")
    print("2. 📋 Show correct format examples")
    print("3. 🔄 Restore from backup")
    print("4. ✅ Verify current syntax")
    print()
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == '1':
        if fixer.fix_all_paths():
            print("\n🔍 Verifying fix...")
            if fixer.verify_fix():
                print("\n🎉 All paths fixed successfully!")
                print("Your application should now run without syntax errors.")
            else:
                print("\n⚠️ Some issues may still exist. Check the output above.")
    
    elif choice == '2':
        fixer.show_examples()
    
    elif choice == '3':
        fixer.restore_backup()
    
    elif choice == '4':
        if fixer.verify_fix():
            print("✅ Current syntax is correct!")
        else:
            print("❌ Syntax errors detected. Run option 1 to fix them.")
    
    else:
        print("❌ Invalid choice. Please run the script again.")
        return
    
    print(f"\n💡 Remember: Always use raw strings (r'...') for Windows file paths!")
    print(f"   This prevents Python from interpreting backslashes as escape sequences.")

if __name__ == '__main__':
    main()
