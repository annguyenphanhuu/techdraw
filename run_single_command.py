#!/usr/bin/env python3
"""
Single Command Wrapper for existing TechDraw Pipeline
Sử dụng toàn bộ code có sẵn của bạn, chỉ tạo wrapper để chạy 1 lệnh duy nhất

Usage: python run_single_command.py input_file.step [template.svg]
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

def print_usage():
    """In hướng dẫn sử dụng"""
    print("🎯 Single Command TechDraw Pipeline")
    print("=" * 40)
    print("Usage:")
    print("  python run_single_command.py input_file.step")
    print("  python run_single_command.py input_file.step template.svg")
    print("")
    print("Examples:")
    print("  python run_single_command.py input/bend.step")
    print("  python run_single_command.py input/tube.step templates/A3_Landscape_ISO5457_advanced.svg")

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
    """Tạo config file tạm thời sử dụng cấu trúc config của bạn"""
    config = {
        "INPUT_FILE": input_file,
        "TEMPLATE_FILE": template_file,
        "AUTO_SCALE": "true",
        "SCALE": "auto",
        "DIMENSION_OFFSET": "15.0",
        "DIMENSION_TEXT_HEIGHT": "2.5"
    }
    
    config_path = Path("config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def run_pipeline_step(step_name, script_path, *args):
    """Chạy một bước trong pipeline sử dụng scripts có sẵn của bạn"""
    print(f"🚀 {step_name}...")
    
    cmd = [sys.executable, str(script_path)] + list(args)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {step_name} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} failed!")
        print("Error:", e.stderr)
        if e.stdout:
            print("Output:", e.stdout)
        return False

def main():
    """Main function - wrapper cho pipeline có sẵn"""
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
    
    # Setup paths
    scripts_dir = Path("scripts")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Clean old outputs
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()
    
    print(f"🎯 TechDraw Pipeline (Using Your Existing Code)")
    print(f"📥 Input: {step_path.name}")
    print(f"📄 Template: {template_file}")
    print(f"📁 Output: {output_dir}/")
    print("=" * 50)
    
    # Create config file (sử dụng format config của bạn)
    config_path = create_config_file(step_path.name, template_file)
    
    try:
        # Copy input file to input directory if needed
        input_dir = Path("input")
        input_dir.mkdir(exist_ok=True)
        
        target_input = input_dir / step_path.name
        if not target_input.exists() or target_input.stat().st_mtime < step_path.stat().st_mtime:
            import shutil
            shutil.copy2(step_path, target_input)
            print(f"📋 Copied input to: {target_input}")
        
        # Step 1: Chạy FreeCAD TechDraw Core (script gốc của bạn)
        freecad_script = scripts_dir / "freecad_techdraw_core.py"
        if freecad_script.exists():
            if not run_pipeline_step("Step 1: FreeCAD TechDraw Core", freecad_script):
                return 1
        else:
            print(f"❌ FreeCAD script not found: {freecad_script}")
            return 1
        
        # Step 2: Thêm dimensions (script gốc của bạn)
        dim_script = scripts_dir / "dxf_add_dim.py"
        if dim_script.exists():
            if not run_pipeline_step("Step 2: Add Dimensions", dim_script):
                return 1
        else:
            print(f"❌ Dimension script not found: {dim_script}")
            return 1
        
        # Step 3: Render SVG (script gốc của bạn)
        svg_script = scripts_dir / "dxf_render_svg.py"
        template_path = Path("templates") / template_file
        if svg_script.exists():
            if not run_pipeline_step("Step 3: Render SVG", svg_script, str(template_path)):
                return 1
        else:
            print(f"❌ SVG render script not found: {svg_script}")
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
