#!/usr/bin/env python3
"""
Installation script for enhanced file processing dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install new dependencies for enhanced file processing"""
    print("🔧 Installing Enhanced File Processing Dependencies")
    print("=" * 60)
    
    # New dependencies for Word and email processing
    new_dependencies = [
        "python-docx>=0.8.11",
        "python-docx2txt>=0.8",
        "email-validator>=2.0.0",
        "beautifulsoup4>=4.12.0"
    ]
    
    print("📦 Installing new dependencies:")
    for dep in new_dependencies:
        print(f"  - {dep}")
        if install_package(dep):
            print(f"    ✅ Successfully installed {dep}")
        else:
            print(f"    ❌ Failed to install {dep}")
    
    print("\n" + "=" * 60)
    print("🎉 Installation completed!")
    print("\n📋 New file types now supported:")
    print("  - .docx (Microsoft Word documents)")
    print("  - .doc (Legacy Word documents)")
    print("  - .eml (Email files)")
    print("  - .msg (Outlook message files)")
    
    print("\n🚀 You can now run the application with:")
    print("  python app.py")

if __name__ == "__main__":
    main() 