# scripts/freecad_techdraw_cmd.py (FreeCADCmd Version)
import sys
import os
import json
import subprocess
import traceback
import tempfile
from pathlib import Path

# Thiết lập đường dẫn cho local
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

def create_freecad_script(config, input_file, template_file, output_dxf, page_info_file):
    """Tạo FreeCAD script để chạy với freecadcmd"""
    
    script_content = f'''
import sys
import os
import time
import math
import json
import xml.etree.ElementTree as ET
import re

# Import FreeCAD modules
import FreeCAD as App
import Part
import TechDraw
from FreeCAD import Vector

class PaperInfoManager:
    @staticmethod
    def get_info_from_svg(svg_path):
        try:
            conv = {{"mm": 1.0, "cm": 10.0, "in": 25.4, "px": 25.4 / 96.0}}
            pattern = re.compile(r"([0-9.]+)([a-zA-Z]*)")
            
            def parse_dim(dim_str):
                if not dim_str: return 0.0
                match = pattern.match(dim_str.strip())
                if not match: return float(dim_str) * conv["px"]
                value, unit = float(match.group(1)), match.group(2).lower() or "px"
                return value * conv.get(unit, conv["px"])
            
            root = ET.parse(svg_path).getroot()
            width = parse_dim(root.get('width'))
            height = parse_dim(root.get('height'))
            
            if not width or not height: 
                raise ValueError("Invalid width/height")
            
            print(f"[INFO] Read dimensions from template: {{width:.2f}}mm x {{height:.2f}}mm")
            margin = 20.0 if max(width, height) > 800 else 10.0
            return {{'width': width, 'height': height, 'margin': margin}}
        except Exception as e:
            print(f"[WARN] Could not read SVG: {{e}}. Using default A3.")
            return {{'width': 420.0, 'height': 297.0, 'margin': 10.0}}

class AutoScaleCalculator:
    def __init__(self, part, paper_info):
        self.part = part
        self.paper_info = paper_info
        self.bbox = self.part.Shape.BoundBox
    
    def calculate_optimal_scale(self):
        part_len = self.bbox.XLength
        part_width = self.bbox.YLength
        part_height = self.bbox.ZLength
        
        required_width = part_len + part_width + 100
        required_height = part_height + part_width + 100
        
        usable_width = self.paper_info['width'] - 2 * self.paper_info['margin']
        usable_height = self.paper_info['height'] - 2 * self.paper_info['margin']
        
        scale_x = usable_width / required_width if required_width > 0 else 1.0
        scale_y = usable_height / required_height if required_height > 0 else 1.0
        
        optimal_scale = min(scale_x, scale_y) * 0.85
        standard_scales = [0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        
        for scale in reversed(standard_scales):
            if optimal_scale >= scale:
                return scale
        return 0.05

def enhance_view(view):
    try:
        view.HardHidden = True
        if hasattr(view, 'ViewObject'):
            view.ViewObject.ShowFrame = False
            view.ViewObject.ShowVertices = False
    except Exception as e:
        print(f"[WARN] Could not enhance view: {{e}}")

def estimate_bounds(part, direction, scale):
    bbox = part.Shape.BoundBox
    if direction == Vector(0, 0, 1):  # Top view
        return bbox.XLength * scale, bbox.YLength * scale
    elif direction == Vector(1, 0, 0):  # Right view
        return bbox.YLength * scale, bbox.ZLength * scale
    else:  # Front view
        return bbox.XLength * scale, bbox.ZLength * scale

def calculate_layout(paper_info, views_data):
    margin = paper_info['margin']
    paper_width = paper_info['width']
    paper_height = paper_info['height']
    
    layout = {{}}
    
    if 'Front' in views_data:
        layout['Front'] = {{'x': margin + 50, 'y': paper_height/2}}
    if 'Top' in views_data:
        layout['Top'] = {{'x': margin + 50, 'y': paper_height - margin - 50}}
    if 'Right' in views_data:
        layout['Right'] = {{'x': margin + 150, 'y': paper_height/2}}
    
    return layout

def main():
    print("🚀 Starting FreeCAD TechDraw (FreeCADCmd Version)...")
    
    try:
        # Configuration
        config = {json.dumps(config)}
        input_file = r"{input_file}"
        template_file = r"{template_file}"
        output_dxf = r"{output_dxf}"
        page_info_file = r"{page_info_file}"
        
        print(f"ℹ️ Config: {{config}}")
        print(f"📥 Input: {{input_file}}")
        print(f"📄 Template: {{template_file}}")
        print(f"💾 Output: {{output_dxf}}")
        
        # Tạo document
        doc = App.newDocument("TechDrawDoc")
        print("✅ FreeCAD document created")
        
        # Import STEP file
        print(f"📥 Importing STEP file...")
        Part.insert(input_file, doc.Name)
        doc.recompute()
        
        # Tìm part object
        part = None
        for obj in doc.Objects:
            if hasattr(obj, 'Shape') and obj.Shape.Volume > 0:
                part = obj
                break
        
        if not part:
            print("❌ No valid part found in STEP file")
            sys.exit(1)
        
        print(f"✅ Part imported: {{part.Label}}")
        
        # Đọc thông tin paper từ template
        paper_info = PaperInfoManager.get_info_from_svg(template_file)
        
        # Tính scale
        if config.get('AUTO_SCALE', 'true').lower() == 'true':
            calculator = AutoScaleCalculator(part, paper_info)
            scale_value = calculator.calculate_optimal_scale()
            print(f"🔍 Auto-calculated scale: {{scale_value}}")
        else:
            scale_value = float(config.get('SCALE', 1.0))
            print(f"📏 Manual scale: {{scale_value}}")
        
        # Tạo TechDraw page
        page = doc.addObject("TechDraw::DrawPage", "Page")
        template_obj = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template_obj.Template = template_file
        page.Template = template_obj
        
        print("✅ TechDraw page created")
        
        # Tạo views
        directions = {{
            'Front': Vector(0, -1, 0),
            'Top': Vector(0, 0, 1),
            'Right': Vector(1, 0, 0)
        }}
        
        views = {{}}
        for name, direction in directions.items():
            view = doc.addObject("TechDraw::DrawViewPart", f"{{name}}View")
            view.Source = [part]
            view.Direction = direction
            view.ScaleType = "Custom"
            view.Scale = scale_value
            page.addView(view)
            views[name] = view
        
        print("✅ Views created")
        
        # Recompute và enhance views
        doc.recompute()
        time.sleep(2)
        
        for view in views.values():
            enhance_view(view)
        
        doc.recompute()
        
        # Layout views
        views_data = {{}}
        for name, direction in directions.items():
            w, h = estimate_bounds(part, direction, scale_value)
            views_data[name] = {{'width': w, 'height': h}}
        
        layout = calculate_layout(paper_info, views_data)
        for view_name, position in layout.items():
            if view_name in views:
                views[view_name].X = f"{{position['x']}} mm"
                views[view_name].Y = f"{{position['y']}} mm"
        
        doc.recompute(None, True, True)
        
        # Export DXF
        print(f"💾 Exporting DXF...")
        TechDraw.writeDXFPage(page, output_dxf)
        print("✅ DXF exported successfully")
        
        # Save page info
        page_info = {{"width": paper_info['width'], "height": paper_info['height']}}
        with open(page_info_file, "w") as f:
            json.dump(page_info, f)
        print(f"✅ Page info saved: {{page_info}}")
        
        # Close document
        App.closeDocument(doc.Name)
        print("✅ Document closed")
        
    except Exception as e:
        print(f"❌ ERROR: {{e}}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    return script_content

def main():
    print("🚀 Starting FreeCAD TechDraw (FreeCADCmd Version)...")
    
    try:
        # Đọc config
        config_path = PROJECT_ROOT / "config.json"
        if not config_path.exists():
            print("❌ Config file not found!")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"ℹ️ Config loaded: {config}")
        
        # Đường dẫn files
        input_file = INPUT_DIR / config['INPUT_FILE']
        template_file = TEMPLATES_DIR / config['TEMPLATE_FILE']
        output_dxf = OUTPUT_DIR / "step1_base_drawing.dxf"
        page_info_file = OUTPUT_DIR / "page_info.json"
        
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            sys.exit(1)
        
        if not template_file.exists():
            print(f"❌ Template file not found: {template_file}")
            sys.exit(1)
        
        # Tạo FreeCAD script
        script_content = create_freecad_script(
            config, 
            str(input_file), 
            str(template_file), 
            str(output_dxf), 
            str(page_info_file)
        )
        
        # Lưu script tạm thời
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
            temp_script.write(script_content)
            temp_script_path = temp_script.name
        
        print(f"📝 Created temporary FreeCAD script: {temp_script_path}")
        
        # Chạy freecadcmd
        print("🚀 Running freecadcmd...")
        cmd = ['freecadcmd', temp_script_path]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=PROJECT_ROOT
        )
        
        if result.returncode == 0:
            print("✅ FreeCADCmd completed successfully!")
            if result.stdout:
                print("Output:", result.stdout)
        else:
            print("❌ FreeCADCmd failed!")
            print("Error:", result.stderr)
            if result.stdout:
                print("Output:", result.stdout)
            sys.exit(1)
        
        # Cleanup temp script
        os.unlink(temp_script_path)
        
        # Verify output
        if output_dxf.exists():
            print(f"✅ DXF file created: {output_dxf}")
        else:
            print("❌ DXF file not created!")
            sys.exit(1)
        
        if page_info_file.exists():
            print(f"✅ Page info created: {page_info_file}")
        else:
            print("❌ Page info file not created!")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
