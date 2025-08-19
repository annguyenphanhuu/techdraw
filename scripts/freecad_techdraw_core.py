# scripts/freecad_techdraw_core.py (Final Complete Version)
import sys, os, time, math, json, traceback, xml.etree.ElementTree as ET, re

FREECAD_LIB_PATH = '/usr/lib/freecad/lib'
if FREECAD_LIB_PATH not in sys.path: sys.path.append(FREECAD_LIB_PATH)

import FreeCAD as App, Part, TechDraw
from FreeCAD import Vector, Units, Rotation

class PaperInfoManager:
    # ... (This class remains unchanged)
    @staticmethod
    def get_info_from_svg(svg_path: str) -> dict:
        try:
            conv = {"mm": 1.0, "cm": 10.0, "in": 25.4, "px": 25.4 / 96.0}; pattern = re.compile(r"([0-9.]+)([a-zA-Z]*)")
            def parse_dim(dim_str: str) -> float:
                if not dim_str: return 0.0
                match = pattern.match(dim_str.strip());
                if not match: return float(dim_str) * conv["px"]
                value, unit = float(match.group(1)), match.group(2).lower() or "px"; return value * conv.get(unit, conv["px"])
            root = ET.parse(svg_path).getroot(); width = parse_dim(root.get('width')); height = parse_dim(root.get('height'))
            if not width or not height: raise ValueError("Invalid width/height")
            print(f"[INFO] Read dimensions from template: {width:.2f}mm x {height:.2f}mm")
            margin = 20.0 if max(width, height) > 800 else 10.0; return {'width': width, 'height': height, 'margin': margin}
        except Exception as e:
            print(f"[WARN] Could not read SVG: {e}. Using default A3."); return {'width': 420.0, 'height': 297.0, 'margin': 10.0}

class AutoScaleCalculator:
    # ... (This class remains unchanged)
    def __init__(self, part, paper_info): self.part = part; self.paper_info = paper_info; self.bbox = self.part.Shape.BoundBox
    def calculate_optimal_scale(self):
        part_len = self.bbox.XLength; part_width = self.bbox.YLength; part_height = self.bbox.ZLength
        required_width = part_len + part_width + 100; required_height = part_height + part_width + 100
        usable_width = self.paper_info['width'] - 2 * self.paper_info['margin']; usable_height = self.paper_info['height'] - 2 * self.paper_info['margin']
        scale_x = usable_width / required_width if required_width > 0 else 1.0; scale_y = usable_height / required_height if required_height > 0 else 1.0
        optimal_scale = min(scale_x, scale_y) * 0.85; standard_scales = [0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        for scale in reversed(standard_scales):
            if optimal_scale >= scale: return scale
        return 0.05

class TechDrawEnhancer:
    @staticmethod
    def enhance_view(view):
        try:
            # Enable hidden line calculation
            view.HardHidden = True
            
            # Disable frames and vertices via ViewObject
            if hasattr(view, 'ViewObject'):
                view.ViewObject.ShowFrame = False
                view.ViewObject.ShowVertices = False
                print(f"[INFO] Cleaned up and enabled hidden lines for {view.Name}")
            else:
                print(f"[WARN] No ViewObject found for {view.Name}, cannot disable frame.")
        except Exception as e:
            print(f"[WARNING] Error enhancing view {view.Name}: {e}")

# Assuming other classes and configuration exist

class SmartLayoutManager:
    # ... (This class remains unchanged)
    def __init__(self, paper_info, config): self.paper_width = paper_info['width']; self.paper_height = paper_info['height']; self.margin = paper_info['margin']; self.config = config
    def calculate_layout(self, views_data: dict):
        spacing = float(self.config.get('MIN_SPACING', 30.0));
        front_w = views_data['Front']['width']; front_h = views_data['Front']['height']; top_h = views_data['Top']['height']; right_w = views_data['Right']['width']; iso_w = views_data['Iso']['width']; iso_h = views_data['Iso']['height']
        block_width = front_w + spacing + right_w; block_height = front_h + spacing + top_h;
        available_width_for_main = self.paper_width - iso_w - 2 * self.margin - spacing
        start_x = self.margin + (available_width_for_main - block_width) / 2; start_y = self.margin + (self.paper_height - 2 * self.margin - block_height) / 2
        front_x = start_x + front_w / 2; front_y = start_y + front_h / 2
        layout = {}; layout['Front'] = {'x': front_x, 'y': front_y + front_h/2 + spacing + top_h/2}; layout['Top'] = {'x': front_x, 'y': front_y}; layout['Right'] = {'x': front_x + front_w/2 + spacing + right_w/2, 'y': front_y + front_h/2 + spacing + top_h/2}; layout['Iso'] = {'x': 1.5 * (self.paper_width - self.margin - iso_w/2), 'y': 1.5 * (self.paper_height - self.margin - iso_h/2)}
        return layout

def estimate_bounds(obj, direction, scale):
    # ... (This class remains unchanged)
    bbox = obj.Shape.BoundBox
    if direction.z == -1: w, h = bbox.XLength, bbox.YLength
    elif direction.y == -1: w, h = bbox.XLength, bbox.ZLength
    elif direction.x == -1: w, h = bbox.YLength, bbox.ZLength
    else: w, h = (bbox.XLength + bbox.ZLength) * 0.707, (bbox.YLength + bbox.ZLength) * 0.707
    return w * scale, h * scale

def main():
    doc = None
    try:
        print("[INFO] Starting FreeCAD TechDraw (Stable Process)...")
        with open("/app/config.json", 'r') as f: config = json.load(f)
        
        template_path = os.path.join("/app/templates", config.get("TEMPLATE_FILE", "")); step_file_path = os.path.join("/app/input", config["INPUT_FILE"])
        doc = App.newDocument("StableDrawing"); Part.insert(step_file_path, doc.Name); doc.recompute(); part = doc.Objects[0]
        page = doc.addObject("TechDraw::DrawPage", "Page"); template = doc.addObject("TechDraw::DrawSVGTemplate", "Template"); template.Template = template_path; page.Template = template
        paper_info = PaperInfoManager.get_info_from_svg(template_path)
        
        if config.get('AUTO_SCALE', 'true').lower() == 'true':
            scale_value = AutoScaleCalculator(part, paper_info).calculate_optimal_scale()
        else:
            scale_value = float(config.get("SCALE", 1.0))
        print(f"[INFO] Using scale: {scale_value}")

        directions = {"Front": Vector(0,-1,0), "Top": Vector(0,0,-1), "Right": Vector(-1,0,0), "Iso": Vector(1,1,1).normalize()}; views = {}
        for name, direction in directions.items():
            view = doc.addObject("TechDraw::DrawViewPart", f"{name}View"); view.Source = [part]; view.Direction = direction; view.ScaleType = "Custom"; view.Scale = scale_value
            page.addView(view); views[name] = view
        
        # --- IMPORTANT CHANGE: Recompute BEFORE accessing ViewObject ---
        print("[INFO] Recomputing document to create ViewObjects...")
        doc.recompute()
        time.sleep(2) # Add a longer pause to ensure FreeCAD has finished processing

        for view in views.values():
            TechDrawEnhancer.enhance_view(view)
        doc.recompute()
        
        views_data = {};
        for name, direction in directions.items(): w, h = estimate_bounds(part, direction, scale_value); views_data[name] = {'width': w, 'height': h}
        layout = SmartLayoutManager(paper_info, config).calculate_layout(views_data)
        for view_name, position in layout.items():
            if view_name in views:
                views[view_name].X = f"{position['x']} mm"; views[view_name].Y = f"{position['y']} mm"
        doc.recompute(None, True, True)
        
        output_path_dxf = "/app/output/step1_base_drawing.dxf"

        TechDraw.writeDXFPage(page, output_path_dxf)
        print(f"✅ [SUCCESS] DXF drawing created at: {output_path_dxf}")
        
        page_info = {"width": paper_info['width'], "height": paper_info['height']}
        with open("/app/output/page_info.json", "w") as f: json.dump(page_info, f)
        print(f"✅ Page info written: {page_info}")
        
    except Exception as e:
        sys.stderr.write(f"\n❌ ERROR in freecad_techdraw_core.py: {e}\n"); traceback.print_exc(); sys.exit(1)
    finally:
        if doc: App.closeDocument(doc.Name)

if __name__ == "__main__":
    main()