# scripts/dxf_render_svg.py
# Version V14 - Final Solution, based on actual rendered image size and no Y-axis flip

import sys
import os
import json
import traceback
from io import BytesIO

# Add necessary imports
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext, matplotlib
from ezdxf.addons.drawing.config import Configuration, ColorPolicy

from ezdxf.filemanagement import readfile
from ezdxf.bbox import extents
from lxml import etree

# --- KEEP PATH DECLARATION BLOCK AS REQUESTED ---
DXF_INPUT_PATH = "/app/output/step2_with_dims.dxf"
SVG_OUTPUT_PATH = "/app/output/final_drawing_with_template.svg"
PAGE_INFO_PATH = "/app/output/page_info.json"
# ----------------------------------------------------

def main(template_path):
    print("--- Starting dxf_render_svg.py (Final, correct version) ---")
    
    if not os.path.exists(DXF_INPUT_PATH) or not os.path.exists(PAGE_INFO_PATH):
        print(f"❌ ERROR: DXF file or JSON file not found.")
        sys.exit(1)
        
    try:
        # --- STEP A: RENDER DXF TO SVG IMAGE IN MEMORY ---
        doc = readfile(DXF_INPUT_PATH)
        msp = doc.modelspace()
        if not msp: raise ValueError("Modelspace is empty.")

        print("[INFO] Rendering DXF content to memory using Matplotlib...")
        fig, ax = plt.subplots()
        config = Configuration.defaults().with_changes(color_policy=ColorPolicy.BLACK)
        backend = matplotlib.MatplotlibBackend(ax)
        Frontend(RenderContext(doc), backend, config=config).draw_layout(msp)
        
        ax.set_aspect('equal')
        ax.axis('off')
        fig.tight_layout(pad=0)

        drawing_buffer = BytesIO()
        fig.savefig(drawing_buffer, format='svg', transparent=True, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        drawing_buffer.seek(0)
        drawing_svg_string = drawing_buffer.read()
        print("[INFO] Rendering to memory successful.")

        # --- STEP B: MERGE BASED ON RENDERED IMAGE SIZE ---
        print("[INFO] Starting SVG merging...")
        parser = etree.XMLParser(remove_blank_text=True, recover=True)
        
        # Read paper size info from JSON file
        with open(PAGE_INFO_PATH, 'r') as f:
            page_info = json.load(f)
        page_width, page_height = page_info['width'], page_info['height']
        print(f"[INFO] Page size read from JSON file (WxH): {page_width:.2f} x {page_height:.2f}")

        # Read template and the rendered SVG image
        template_tree = etree.parse(template_path, parser)
        template_root = template_tree.getroot()
        drawing_root = etree.fromstring(drawing_svg_string, parser=parser)
        
        # --- CORRECT CALCULATION LOGIC ---

        # 1. Get the actual dimensions of the rendered SVG image
        rendered_width_str = drawing_root.get('width').replace('pt', '')
        rendered_height_str = drawing_root.get('height').replace('pt', '')
        rendered_width = float(rendered_width_str)
        rendered_height = float(rendered_height_str)
        print(f"[INFO] Actual rendered image size (WxH): {rendered_width:.2f} x {rendered_height:.2f} pt")

        # 2. Calculate the scale to fit within the title block (with margins)
        margin = 50
        target_w = page_width - 2 * margin
        target_h = page_height - 2 * margin
        scale = min(target_w / rendered_width, target_h / rendered_height)

        # 3. Calculate the final dimensions on the page
        scaled_w = rendered_width * scale
        scaled_h = rendered_height * scale

        # 4. Calculate the position for centering
        translate_x = (page_width - scaled_w) / 2
        translate_y = (page_height - scaled_h) / 2
        
        # 5. Build the final transform string as per your request (no flip)
        transform_str = f"translate({translate_x:.4f}, {translate_y:.4f}) scale({scale:.5f}, {scale:.5f})"
        
        print(f"[INFO] Applying final transform: {transform_str}")
        
        # 6. Create a new group and apply the transform
        final_drawing_group = etree.Element("g", id="FinalDrawingContent")
        final_drawing_group.set('transform', transform_str)

        # 7. Copy content from the rendered image into the new group
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        content_group = drawing_root.find('svg:g', namespaces=ns)
        if content_group is not None:
            for element in content_group:
                final_drawing_group.append(element)
            
            # 8. Add the final group to the template and save the file
            template_root.append(final_drawing_group)
            template_tree.write(SVG_OUTPUT_PATH, pretty_print=True, encoding='utf-8', xml_declaration=True)
            print(f"✅ Merged and exported complete SVG at: {SVG_OUTPUT_PATH}")
        else:
            print("[WARNING] No geometric content found in the rendered SVG.")

    except Exception as e:
        print(f"❌ ERROR in dxf_render_svg.py: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2: print("❌ Error: Template path must be provided."); sys.exit(1)
    main(sys.argv[1])