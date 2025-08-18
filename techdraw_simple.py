#!/usr/bin/env python3
"""
Simple TechDraw Generator
Usage: python techdraw_simple.py input_file.step [template.svg]

Tạo bản vẽ kỹ thuật từ file STEP chỉ với một lệnh duy nhất
"""

import sys
import os
import json
import subprocess
import tempfile
import traceback
from pathlib import Path

def print_usage():
    """In hướng dẫn sử dụng"""
    print("🎯 Simple TechDraw Generator")
    print("=" * 40)
    print("Usage:")
    print("  python techdraw_simple.py input_file.step")
    print("  python techdraw_simple.py input_file.step template.svg")
    print("")
    print("Examples:")
    print("  python techdraw_simple.py input/bend.step")
    print("  python techdraw_simple.py input/tube.step templates/A3_Landscape_ISO5457_advanced.svg")
    print("")
    print("Output:")
    print("  - output/final_drawing.svg (bản vẽ cuối cùng)")
    print("  - output/step1_base_drawing.dxf")
    print("  - output/step2_with_dims.dxf")

def find_default_template():
    """Tìm template mặc định"""
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
            return str(template_path)
    
    # Nếu không tìm thấy, lấy template SVG đầu tiên
    svg_files = list(templates_dir.glob("*.svg"))
    if svg_files:
        return str(svg_files[0])
    
    return None

def create_freecad_script(step_file, template_file, output_dir):
    """Tạo FreeCAD script tự động"""
    
    script_content = f'''
import sys
import os
import time
import json
import xml.etree.ElementTree as ET
import re

# Import FreeCAD modules
import FreeCAD as App
import Part
import TechDraw
from FreeCAD import Vector

def get_paper_info_from_svg(svg_path):
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
        
        print(f"[INFO] Template size: {{width:.1f}}mm x {{height:.1f}}mm")
        margin = 20.0 if max(width, height) > 800 else 10.0
        return {{'width': width, 'height': height, 'margin': margin}}
    except Exception as e:
        print(f"[WARN] Using default A3 size: {{e}}")
        return {{'width': 420.0, 'height': 297.0, 'margin': 15.0}}

def calculate_auto_scale(part, paper_info):
    bbox = part.Shape.BoundBox
    part_len = bbox.XLength
    part_width = bbox.YLength
    part_height = bbox.ZLength
    
    required_width = part_len + part_width + 50
    required_height = part_height + part_width + 50
    
    usable_width = paper_info['width'] - 2 * paper_info['margin']
    usable_height = paper_info['height'] - 2 * paper_info['margin']
    
    scale_x = usable_width / required_width if required_width > 0 else 1.0
    scale_y = usable_height / required_height if required_height > 0 else 1.0
    
    optimal_scale = min(scale_x, scale_y) * 0.8
    standard_scales = [0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0]
    
    for scale in reversed(standard_scales):
        if optimal_scale >= scale:
            return scale
    return 0.1

def main():
    print("🚀 Generating TechDraw...")
    
    step_file = r"{step_file}"
    template_file = r"{template_file}"
    output_dir = r"{output_dir}"
    
    try:
        # Tạo document
        doc = App.newDocument("TechDrawDoc")
        print("✅ FreeCAD document created")
        
        # Import STEP file
        print(f"📥 Importing: {{os.path.basename(step_file)}}")
        Part.insert(step_file, doc.Name)
        doc.recompute()
        
        # Tìm part
        part = None
        for obj in doc.Objects:
            if hasattr(obj, 'Shape') and obj.Shape.Volume > 0:
                part = obj
                break
        
        if not part:
            raise Exception("No valid part found in STEP file")
        
        print(f"✅ Part imported: {{part.Label}}")
        
        # Đọc template info
        paper_info = get_paper_info_from_svg(template_file)
        
        # Tính auto scale
        scale_value = calculate_auto_scale(part, paper_info)
        print(f"🔍 Auto scale: {{scale_value}}")
        
        # Tạo TechDraw page
        page = doc.addObject("TechDraw::DrawPage", "Page")
        template_obj = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template_obj.Template = template_file
        page.Template = template_obj
        
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
        
        # Recompute
        doc.recompute()
        time.sleep(1)
        
        # Enhance views
        for view in views.values():
            try:
                view.HardHidden = True
                if hasattr(view, 'ViewObject'):
                    view.ViewObject.ShowFrame = False
                    view.ViewObject.ShowVertices = False
            except:
                pass
        
        doc.recompute()
        
        # Layout views
        margin = paper_info['margin']
        paper_width = paper_info['width']
        paper_height = paper_info['height']
        
        if 'Front' in views:
            views['Front'].X = f"{{margin + 60}} mm"
            views['Front'].Y = f"{{paper_height/2}} mm"
        if 'Top' in views:
            views['Top'].X = f"{{margin + 60}} mm" 
            views['Top'].Y = f"{{paper_height - margin - 60}} mm"
        if 'Right' in views:
            views['Right'].X = f"{{margin + 180}} mm"
            views['Right'].Y = f"{{paper_height/2}} mm"
        
        doc.recompute(None, True, True)
        
        # Export DXF
        output_dxf = os.path.join(output_dir, "step1_base_drawing.dxf")
        TechDraw.writeDXFPage(page, output_dxf)
        print(f"✅ DXF exported: {{os.path.basename(output_dxf)}}")
        
        # Save page info
        page_info = {{"width": paper_info['width'], "height": paper_info['height']}}
        page_info_file = os.path.join(output_dir, "page_info.json")
        with open(page_info_file, "w") as f:
            json.dump(page_info, f)
        
        # Close document
        App.closeDocument(doc.Name)
        print("✅ Step 1 completed")
        
    except Exception as e:
        print(f"❌ ERROR: {{e}}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    return script_content

def run_freecad_step(step_file, template_file, output_dir):
    """Chạy bước 1: FreeCAD TechDraw"""
    print("🚀 Step 1: Creating base drawing with FreeCAD...")
    
    # Tạo script tạm thời
    script_content = create_freecad_script(step_file, template_file, output_dir)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(script_content)
        temp_script_path = temp_script.name
    
    try:
        # Chạy freecadcmd
        cmd = ['freecadcmd', temp_script_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Step 1 completed successfully!")
            return True
        else:
            print("❌ Step 1 failed!")
            print("Error:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Step 1 timeout!")
        return False
    except FileNotFoundError:
        print("❌ freecadcmd not found! Please install FreeCAD and add to PATH")
        return False
    finally:
        # Cleanup
        try:
            os.unlink(temp_script_path)
        except:
            pass

def run_dimension_step(output_dir):
    """Chạy bước 2: Thêm kích thước"""
    print("🚀 Step 2: Adding dimensions...")
    
    try:
        import ezdxf
        from ezdxf.math import Vec2
        
        input_dxf = Path(output_dir) / "step1_base_drawing.dxf"
        output_dxf = Path(output_dir) / "step2_with_dims.dxf"
        
        if not input_dxf.exists():
            print("❌ Base DXF not found!")
            return False
        
        # Đọc DXF
        doc = ezdxf.readfile(str(input_dxf))
        msp = doc.modelspace()
        
        # Tạo dimension style
        if "STANDARD" not in doc.dimstyles:
            dimstyle = doc.dimstyles.new("STANDARD")
            dimstyle.dxf.dimtxt = 2.5
            dimstyle.dxf.dimasz = 2.5
            dimstyle.dxf.dimexe = 1.25
            dimstyle.dxf.dimexo = 0.625
        
        # Tìm bounding box
        points = []
        for entity in msp:
            if entity.dxftype() == 'LINE':
                points.extend([Vec2(entity.dxf.start), Vec2(entity.dxf.end)])
        
        if points:
            min_x = min(p.x for p in points)
            max_x = max(p.x for p in points)
            min_y = min(p.y for p in points)
            max_y = max(p.y for p in points)
            
            offset = 15.0
            
            # Overall width dimension
            p1 = Vec2(min_x, min_y - offset * 2)
            p2 = Vec2(max_x, min_y - offset * 2)
            dim_line = Vec2(min_x, min_y - offset * 3)
            
            msp.add_linear_dim(base=dim_line, p1=p1, p2=p2, dimstyle="STANDARD")
            
            # Overall height dimension  
            p1 = Vec2(max_x + offset * 2, min_y)
            p2 = Vec2(max_x + offset * 2, max_y)
            dim_line = Vec2(max_x + offset * 3, min_y)
            
            msp.add_linear_dim(base=dim_line, p1=p1, p2=p2, dimstyle="STANDARD")
        
        # Lưu file
        doc.saveas(str(output_dxf))
        print("✅ Step 2 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        return False

def run_svg_step(template_file, output_dir):
    """Chạy bước 3: Render SVG"""
    print("🚀 Step 3: Rendering final SVG...")
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        from ezdxf.addons.drawing.config import Configuration, ColorPolicy
        from ezdxf.filemanagement import readfile
        from ezdxf.bbox import extents
        from lxml import etree
        
        input_dxf = Path(output_dir) / "step2_with_dims.dxf"
        output_svg = Path(output_dir) / "final_drawing.svg"
        
        if not input_dxf.exists():
            print("❌ DXF with dimensions not found!")
            return False
        
        # Render DXF
        doc = readfile(str(input_dxf))
        msp = doc.modelspace()
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        config = Configuration.defaults()
        config = config.with_changes(background_policy=ColorPolicy.WHITE)
        
        context = RenderContext(doc)
        backend = MatplotlibBackend(ax)
        frontend = Frontend(context, backend)
        frontend.draw_layout(msp, finalize=True)
        
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Lưu temp SVG
        temp_svg = Path(output_dir) / "temp_drawing.svg"
        plt.savefig(str(temp_svg), format='svg', bbox_inches='tight', pad_inches=0.1)
        plt.close()
        
        # Đọc template và drawing
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        with open(temp_svg, 'r', encoding='utf-8') as f:
            drawing_content = f.read()
        
        # Parse và merge
        template_root = etree.fromstring(template_content.encode('utf-8'))
        drawing_root = etree.fromstring(drawing_content.encode('utf-8'))
        
        # Tạo group cho drawing
        drawing_group = etree.Element('g')
        drawing_group.set('id', 'technical_drawing')
        drawing_group.set('transform', 'translate(50, 50) scale(0.8)')
        
        # Copy drawing elements
        for child in drawing_root:
            if child.tag.endswith(('g', 'path', 'line', 'circle', 'text')):
                drawing_group.append(child)
        
        # Thêm vào template
        template_root.append(drawing_group)
        
        # Lưu final SVG
        with open(output_svg, 'wb') as f:
            f.write(etree.tostring(template_root, pretty_print=True, encoding='utf-8'))
        
        # Cleanup
        temp_svg.unlink()
        
        print("✅ Step 3 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        return False

def main():
    """Main function"""
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
        template_path = Path(template_file)
        if not template_path.exists():
            print(f"❌ Template file not found: {template_file}")
            return 1
    else:
        template_file = find_default_template()
        if not template_file:
            print("❌ No template found! Please specify template file or add templates to 'templates/' folder")
            return 1
        template_path = Path(template_file)
    
    # Setup output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Clean old outputs
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()
    
    print(f"🎯 TechDraw Generator")
    print(f"📥 Input: {step_path.name}")
    print(f"📄 Template: {template_path.name}")
    print(f"📁 Output: {output_dir}/")
    print("=" * 50)
    
    try:
        # Run pipeline
        if not run_freecad_step(str(step_path), str(template_path), str(output_dir)):
            return 1
        
        if not run_dimension_step(str(output_dir)):
            return 1
        
        if not run_svg_step(str(template_path), str(output_dir)):
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
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
