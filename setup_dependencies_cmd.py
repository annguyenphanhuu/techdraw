#!/usr/bin/env python3
"""
Setup script cho TechDraw pipeline sử dụng freecadcmd
Bỏ qua kiểm tra FreeCAD installation vì sử dụng freecadcmd
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Chạy command và hiển thị kết quả"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - SUCCESS")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Kiểm tra phiên bản Python"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print("✅ Python version OK")
    return True

def install_python_packages():
    """Cài đặt Python packages"""
    packages = [
        'ezdxf',
        'matplotlib', 
        'lxml'
    ]
    
    print("📦 Installing Python packages...")
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    
    return True

def check_freecadcmd():
    """Kiểm tra freecadcmd có sẵn không"""
    print("🔍 Checking freecadcmd availability...")
    
    try:
        result = subprocess.run(['freecadcmd', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ freecadcmd is available")
            if result.stdout:
                print(f"   Version info: {result.stdout.strip()}")
            return True
        else:
            print("⚠️ freecadcmd found but returned error")
            return False
    except FileNotFoundError:
        print("❌ freecadcmd not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️ freecadcmd timeout (but probably available)")
        return True
    except Exception as e:
        print(f"⚠️ Error checking freecadcmd: {e}")
        return False

def create_requirements_file():
    """Tạo requirements.txt file"""
    requirements = """# TechDraw Pipeline Dependencies (FreeCADCmd Version)
ezdxf>=1.0.0
matplotlib>=3.5.0
lxml>=4.6.0

# Note: FreeCAD is expected to be available via 'freecadcmd' command
# Install FreeCAD separately from: https://www.freecadweb.org/downloads.php
"""
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    with open(requirements_file, 'w') as f:
        f.write(requirements)
    
    print(f"📝 Created requirements.txt at: {requirements_file}")

def main():
    """Main setup function"""
    print("🚀 TechDraw Pipeline - Dependency Setup (FreeCADCmd Version)")
    print("=" * 60)
    
    # Kiểm tra Python version
    if not check_python_version():
        return 1
    
    # Tạo requirements file
    create_requirements_file()
    
    # Cài đặt Python packages
    if not install_python_packages():
        print("❌ Failed to install Python packages")
        return 1
    
    # Kiểm tra freecadcmd (không bắt buộc)
    freecadcmd_available = check_freecadcmd()
    
    if not freecadcmd_available:
        print("\n⚠️ freecadcmd not found or not working properly")
        print("\n📋 FreeCAD Installation Notes:")
        print("1. Download FreeCAD from: https://www.freecadweb.org/downloads.php")
        print("2. Install FreeCAD (recommended: version 0.20 or 0.21)")
        print("3. Make sure 'freecadcmd' is available in your system PATH")
        print("4. Test with: freecadcmd --version")
        print("\n💡 The pipeline will still attempt to run, but may fail if FreeCAD is not properly installed.")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Ensure freecadcmd is available in your PATH")
    print("2. Place your STEP files in the 'input' folder")
    print("3. Run: python run_python_cmd.py")
    print("4. Follow the interactive prompts")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
