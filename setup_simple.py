#!/usr/bin/env python3
"""
Simple setup script for TechDraw Generator
"""

import subprocess
import sys

def install_packages():
    """Cài đặt các Python packages cần thiết"""
    packages = ['ezdxf', 'matplotlib', 'lxml']
    
    print("📦 Installing required packages...")
    for package in packages:
        print(f"   Installing {package}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")
            return False
    
    return True

def main():
    print("🚀 TechDraw Generator - Simple Setup")
    print("=" * 40)
    
    if install_packages():
        print("\n✅ Setup completed!")
        print("\n📋 Usage:")
        print("  python techdraw_simple.py input_file.step")
        print("  python techdraw_simple.py input_file.step template.svg")
        print("\n💡 Make sure FreeCAD is installed and 'freecadcmd' is in your PATH")
    else:
        print("\n❌ Setup failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
