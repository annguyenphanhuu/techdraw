# scripts/merge_svg.py (Fixed Typo)
import lxml.etree as ET
import sys
import os
import json
import traceback

def main(template_path: str, content_path: str, output_path: str):
    """
    Extracts geometry groups from the content SVG file and attaches them to the template SVG file.
    """
    print(f"[INFO] Starting SVG extraction and merging process...")
    print(f"  - Template: {template_path}")
    print(f"  - Content: {content_path}")

    try:
        # 1. Register namespace
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        parser = ET.XMLParser(remove_blank_text=True)
        
        # 2. Read template file
        template_tree = ET.parse(template_path, parser)
        template_root = template_tree.getroot()

        # 3. Read file containing projection content
        content_tree = ET.parse(content_path, parser)
        content_root = content_tree.getroot()

        # 4. Find all <g> groups containing drawing paths
        content_groups = content_root.xpath('//svg:g[svg:path]', namespaces=namespaces)
        
        if not content_groups:
            raise ValueError("No group (<g>) containing geometric content (<path>) found in the content.svg file.")

        print(f"[INFO] Extracted {len(content_groups)} geometry groups.")

        # 5. Attach each extracted group to the template file
        for group in content_groups:
            template_root.append(group)

        # 6. Write to the final file
        template_tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
        print(f"✅ [SUCCESS] Created complete SVG file: {output_path}")

    except Exception as e:
        print(f"❌ ERROR during SVG merging: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # --- FIX HERE ---
    # Correct path is /app/config.json
    with open("/app/config.json", 'r') as f: config = json.load(f)
    # --- END FIX ---
    template_input = f"/app/templates/{config['TEMPLATE_FILE']}"
    content_input = "/app/output/drawing_content.svg"
    final_output = "/app/output/final_drawing_with_template.svg"
    main(template_input, content_input, final_output)
