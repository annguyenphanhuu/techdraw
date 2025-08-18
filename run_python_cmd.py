#!/usr/bin/env python3
"""
Direct Python runner for TechDraw pipeline using freecadcmd
Chạy trực tiếp bằng freecadcmd mà không cần kiểm tra FreeCAD installation
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path

# Thiết lập đường dẫn
PROJECT_ROOT = Path(__file__).parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

def check_basic_dependencies():
    """Kiểm tra các dependencies cơ bản (không bao gồm FreeCAD)"""
    print("🔍 Checking basic dependencies...")
    
    # Kiểm tra Python packages
    required_packages = ['ezdxf', 'matplotlib', 'lxml']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with:")
        for pkg in missing_packages:
            print(f"   pip install {pkg}")
        return False
    
    print("✅ All basic dependencies OK!")
    return True

def list_files(directory, extension):
    """Liệt kê files với extension cụ thể"""
    files = list(directory.glob(f"*.{extension}"))
    return [f.name for f in files]

def select_file(files, file_type):
    """Cho phép user chọn file"""
    if not files:
        print(f"❌ No {file_type} files found!")
        return None
    
    print(f"\n📁 Available {file_type} files:")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file}")
    
    while True:
        try:
            choice = input(f"Select {file_type} file (1-{len(files)}): ")
            index = int(choice) - 1
            if 0 <= index < len(files):
                return files[index]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def get_configuration():
    """Lấy cấu hình từ user"""
    print("\n⚙️ Configuration:")
    
    # Auto scale
    auto_scale_input = input("Use auto-scale? (yes/no) [Default: yes]: ").lower()
    auto_scale = auto_scale_input not in ['no', 'n']
    
    # Scale
    if auto_scale:
        scale = "auto"
    else:
        scale_input = input("Enter manual scale [1.0]: ")
        scale = scale_input if scale_input else "1.0"
    
    # Dimension settings
    dim_offset = input("Dimension line offset (mm) [15.0]: ") or "15.0"
    dim_text_height = input("Dimension text height (mm) [2.5]: ") or "2.5"
    
    return {
        "AUTO_SCALE": str(auto_scale).lower(),
        "SCALE": scale,
        "DIMENSION_OFFSET": dim_offset,
        "DIMENSION_TEXT_HEIGHT": dim_text_height
    }

def create_config_file(input_file, template_file, config):
    """Tạo file config JSON"""
    config_data = {
        "INPUT_FILE": input_file,
        "TEMPLATE_FILE": template_file,
        **config
    }
    
    config_path = PROJECT_ROOT / "config.json"
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"📝 Config saved to: {config_path}")
    return config_path

def run_step(step_name, script_path, *args):
    """Chạy một bước trong pipeline"""
    print(f"\n🚀 Running {step_name}...")
    print(f"   Script: {script_path}")
    
    cmd = [sys.executable, str(script_path)] + list(args)
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        print(f"✅ {step_name} completed successfully!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} failed!")
        print("Error:", e.stderr)
        if result.stdout:
            print("Stdout:", result.stdout)
        return False

def main():
    """Main function"""
    print("🎯 TechDraw Pipeline - FreeCADCmd Python Runner")
    print("=" * 55)
    
    # Kiểm tra basic dependencies (bỏ qua FreeCAD)
    if not check_basic_dependencies():
        return 1
    
    # Tạo output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Dọn dẹp output cũ
    print("\n🧹 Cleaning up old outputs...")
    for file in OUTPUT_DIR.glob("*"):
        if file.is_file():
            file.unlink()
    
    # Chọn file STEP
    step_files = list_files(INPUT_DIR, "step")
    input_file = select_file(step_files, "STEP")
    if not input_file:
        return 1
    
    # Chọn template SVG
    svg_files = list_files(TEMPLATES_DIR, "svg")
    template_file = select_file(svg_files, "SVG template")
    if not template_file:
        return 1
    
    # Lấy cấu hình
    config = get_configuration()
    
    # Hiển thị summary
    print("\n" + "=" * 40)
    print("📋 SUMMARY")
    print("=" * 40)
    print(f"Input file:           {input_file}")
    print(f"Template:             {template_file}")
    print(f"Auto-scale:           {config['AUTO_SCALE']}")
    print(f"Scale:                {config['SCALE']}")
    print(f"Dimension offset:     {config['DIMENSION_OFFSET']} mm")
    print(f"Dimension text height: {config['DIMENSION_TEXT_HEIGHT']} mm")
    print("=" * 40)
    
    confirm = input("Continue? (Y/n): ")
    if confirm.lower() in ['n', 'no']:
        print("Aborted.")
        return 0
    
    # Tạo config file
    config_path = create_config_file(input_file, template_file, config)
    
    try:
        # Step 1: FreeCAD TechDraw (using freecadcmd)
        if not run_step("Step 1: FreeCAD TechDraw (freecadcmd)", SCRIPTS_DIR / "freecad_techdraw_cmd.py"):
            return 1
        
        # Step 2: Add Dimensions
        if not run_step("Step 2: Add Dimensions", SCRIPTS_DIR / "dxf_add_dim_local.py"):
            return 1
        
        # Step 3: Render SVG
        template_path = TEMPLATES_DIR / template_file
        if not run_step("Step 3: Render SVG", SCRIPTS_DIR / "dxf_render_svg_local.py", str(template_path)):
            return 1
        
        print("\n🎉🎉🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉🎉🎉")
        print(f"📁 Check results in: {OUTPUT_DIR}")
        
        # Liệt kê output files
        print("\n📄 Generated files:")
        for file in OUTPUT_DIR.glob("*"):
            if file.is_file():
                print(f"   - {file.name}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup config file
        if config_path.exists():
            config_path.unlink()

if __name__ == "__main__":
    sys.exit(main())
