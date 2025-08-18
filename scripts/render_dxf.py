# scripts/dxf_render_svg.py (Version V14 - Definitive XML Solution)

import os
import sys
import traceback
from io import BytesIO

import ezdxf
from ezdxf.bbox import extents
from lxml import etree # Using the powerful lxml library

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy


# File paths are correct
DXF_INPUT_PATH = "/app/output/step2_with_dims.dxf" 
SVG_OUTPUT_PATH = "/app/output/final_drawing_with_template.svg"
PAGE_INFO_PATH = "/app/output/page_info.json"

def main(template_path):
    print("--- Starting dxf_render_svg.py (Render and Merge V14 - Complete) ---")
    
    if not os.path.exists(DXF_INPUT_PATH):
        print(f"❌ ERROR: Input DXF file not found at '{DXF_INPUT_PATH}'.")
        sys.exit(1)
        
    try:
        # This part works perfectly, keep as is
        print(f"[INFO] Reading and processing DXF file: {DXF_INPUT_PATH}")
        doc = ezdxf.readfile(DXF_INPUT_PATH)
        msp = doc.modelspace()
        if not msp: raise ValueError("Modelspace is empty.")
        bbox = extents(msp)
        if not bbox.has_data: raise ValueError("Could not calculate bounding box.")
        cw, ch = bbox.size.x, bbox.size.y
        print(f"[INFO] Drawing dimensions (W x H): {cw:.2f} x {ch:.2f} DXF units")
        temp_svg_path = "/app/output/temp_drawing_content.svg"
        matplotlib.qsave(msp, temp_svg_path)
        print(f"[INFO] DXF content safely rendered to temporary file.")

        # --- DEFINITIVE FIX AND UPGRADE SECTION ---
        # Using powerful lxml library for direct and reliable XML merging
        
        with open(PAGE_INFO_PATH, 'r') as f: page_info = json.load(f)
        template_width, template_height, margin = page_info['width'], page_info['height'], 30

        if cw == 0 or ch == 0: raise ValueError("Drawing dimensions are zero.")

        # SVG has origin at top-left, Y-axis points downwards
        # DXF has origin at bottom-left, Y-axis points upwards
        # We need to flip the Y-axis by using negative scale
        scale = min((template_width - 2 * margin) / cw, (template_height - 2 * margin) / ch)
        trans_x = (template_width / 2) - (bbox.center.x) * scale
        trans_y = (template_height / 2) + (bbox.center.y) * scale # Translate up and then flip
        transform_str = f"translate({trans_x:.3f}, {trans_y:.3f}) scale({scale:.3f}, {-scale:.3f})"

        # 1. Read both SVG files as XML trees
        parser = etree.XMLParser(remove_blank_text=True)
        template_tree = etree.parse(template_path, parser)
        template_root = template_tree.getroot()
        
        content_tree = etree.parse(temp_svg_path, parser)
        content_root = content_tree.getroot()

        # 2. Find the <g> group containing all paths in the content file
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        content_group = content_root.find('svg:g', namespaces=ns)

        if content_group is not None:
            # 3. Apply transform to the <g> group
            content_group.set('transform', transform_str)
            
            # 4. Append the transformed <g> group to the template's XML tree
            template_root.append(content_group)
            
            # 5. Write the result
            template_tree.write(SVG_OUTPUT_PATH, pretty_print=True, encoding='utf-8', xml_declaration=True)
            print(f"✅ Merged projection with transform: {transform_str}")
            print(f"✅ Exported complete SVG to: {SVG_OUTPUT_PATH}")
        else:
            print("[WARNING] No geometric content found in temporary SVG file.")

        os.remove(temp_svg_path)

    except Exception as e:
        print(f"❌ ERROR in dxf_render_svg.py: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2: print("❌ Error: Template path required."); sys.exit(1)
    main(sys.argv[1])
