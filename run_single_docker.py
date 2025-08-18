#!/usr/bin/env python3
"""
Single Command Docker Wrapper for existing TechDraw Pipeline
Sử dụng Docker workflow có sẵn của bạn, chỉ tạo wrapper để chạy 1 lệnh duy nhất

Usage: python run_single_docker.py input_file.step [template.svg]
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path

def print_usage():
    """In hướng dẫn sử dụng"""
    print("🎯 Single Command TechDraw Pipeline (Docker)")
    print("=" * 45)
    print("Usage:")
    print("  python run_single_docker.py input_file.step")
    print("  python run_single_docker.py input_file.step template.svg")
    print("")
    print("Examples:")
    print("  python run_single_docker.py input/bend.step")
    print("  python run_single_docker.py input/tube.step templates/A3_Landscape_ISO5457_advanced.svg")

def find_default_template():
    """Tìm template mặc định từ thư mục templates"""
    templates_dir = Path("templates")
    if not templates_dir.exists():
        return None
    
    # Ưu tiên các template phổ biến
    preferred_templates = [
        "A3_Landscape_ISO5457_advanced.svg",
        "A4_Landscape_ISO5457_advanced.svg", 
        "A3_Landscape_TD.svg",
        "A4_Landscape_TD.svg"
    ]
    
    for template in preferred_templates:
        template_path = templates_dir / template
        if template_path.exists():
            return template
    
    # Nếu không tìm thấy, lấy template SVG đầu tiên
    svg_files = list(templates_dir.glob("*.svg"))
    if svg_files:
        return svg_files[0].name
    
    return None

def create_config_file(input_file, template_file):
    """Tạo config file tạm thời theo format của bạn"""
    config = {
        "INPUT_FILE": input_file,
        "TEMPLATE_FILE": template_file,
        "AUTO_SCALE": "true",
        "SCALE": "auto",
        "DIMENSION_OFFSET": "15.0",
        "DIMENSION_TEXT_HEIGHT": "2.5"
    }
    
    config_path = Path("config.tmp.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def check_docker():
    """Kiểm tra Docker có sẵn không"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False

def build_docker_image():
    """Build Docker image nếu cần"""
    print("🐳 Building Docker image (if needed)...")
    
    try:
        # Check if image exists
        result = subprocess.run(['docker', 'images', '-q', 'freecad-automation-v2'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("   Building new image...")
            subprocess.run(['docker', 'build', '-t', 'freecad-automation-v2', '.'], 
                         check=True, capture_output=True)
            print("   ✅ Docker image built successfully")
        else:
            print("   ✅ Docker image already exists")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to build Docker image: {e}")
        return False

def run_docker_pipeline(config_path):
    """Chạy pipeline trong Docker container sử dụng setup có sẵn của bạn"""
    print("🚀 Running pipeline in Docker...")
    
    # Setup paths (giống như trong run.sh của bạn)
    project_root = Path.cwd()
    input_dir = project_root / "input"
    template_dir = project_root / "templates"
    output_dir = project_root / "output"
    
    # Ensure directories exist
    input_dir.mkdir(exist_ok=True)
    template_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Run Docker container (giống như trong run.sh của bạn)
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{input_dir}:/app/input',
            '-v', f'{template_dir}:/app/templates', 
            '-v', f'{output_dir}:/app/output',
            '-v', f'{config_path}:/app/config.json',
            'freecad-automation-v2'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Docker pipeline completed successfully!")
        
        if result.stdout:
            print("Output:", result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Docker pipeline failed!")
        print("Error:", e.stderr)
        if e.stdout:
            print("Output:", e.stdout)
        return False

def main():
    """Main function - wrapper cho Docker pipeline có sẵn"""
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    # Parse arguments
    step_file = sys.argv[1]
    template_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Validate input file
    step_path = Path(step_file)
    if not step_path.exists():
        print(f"❌ Input file not found: {step_file}")
        return 1
    
    if not step_path.suffix.lower() == '.step':
        print(f"❌ Input file must be .step format: {step_file}")
        return 1
    
    # Find template
    if template_file:
        template_path = Path("templates") / template_file
        if not template_path.exists():
            # Try direct path
            template_path = Path(template_file)
            if not template_path.exists():
                print(f"❌ Template file not found: {template_file}")
                return 1
        template_file = template_path.name
    else:
        template_file = find_default_template()
        if not template_file:
            print("❌ No template found! Please specify template file or add templates to 'templates/' folder")
            return 1
    
    # Check Docker
    if not check_docker():
        print("❌ Docker not found! Please install Docker or use run_single_command.py instead")
        return 1
    
    # Setup paths
    input_dir = Path("input")
    output_dir = Path("output")
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Clean old outputs
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()
    
    print(f"🎯 TechDraw Pipeline (Docker - Using Your Existing Setup)")
    print(f"📥 Input: {step_path.name}")
    print(f"📄 Template: {template_file}")
    print(f"📁 Output: {output_dir}/")
    print("=" * 55)
    
    # Copy input file to input directory
    target_input = input_dir / step_path.name
    if not target_input.exists() or target_input.stat().st_mtime < step_path.stat().st_mtime:
        shutil.copy2(step_path, target_input)
        print(f"📋 Copied input to: {target_input}")
    
    # Create config file (sử dụng format config của bạn)
    config_path = create_config_file(step_path.name, template_file)
    
    try:
        # Build Docker image if needed
        if not build_docker_image():
            return 1
        
        # Run pipeline in Docker (sử dụng pipeline.py có sẵn của bạn)
        if not run_docker_pipeline(config_path):
            return 1
        
        print("\n🎉🎉🎉 SUCCESS! 🎉🎉🎉")
        print(f"📁 Check results in: {output_dir}/")
        print("📄 Generated files:")
        for file in output_dir.glob("*"):
            if file.is_file():
                print(f"   - {file.name}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup config file
        if config_path.exists():
            config_path.unlink()

if __name__ == "__main__":
    sys.exit(main())
