import FreeCAD
import Part
import TechDraw
import os
import sys

# --- Configuration ---
# Get the absolute path to the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# --- PLEASE MODIFY THE FOLLOWING LINES ---
# 1. Replace "model.step" with the name of your STEP file.
#    The script assumes the STEP file is in the same directory as the script.
step_file_name = "sheet.step"

# 2. Specify the name for the output SVG file.
output_svg_name = "output.svg"

# 3. (Optional) Change the template if you want a different page size/layout.
#    Common templates: A4_LandscapeTD.svg, A4_PortraitTD.svg, A3_LandscapeTD.svg, etc.
#    You can also provide an absolute path to your custom template file.
# template_name = "A4_LandscapeTD.svg"
# --- END OF MODIFICATION SECTION ---

STEP_FILE_PATH = os.path.join(script_dir, "input", step_file_name)
OUTPUT_SVG_PATH = os.path.join(script_dir, output_svg_name)
TEMPLATE_PATH = os.path.join(script_dir, "templates", "A4_Landscape_TD.svg")

# Check if the STEP file exists
if not os.path.exists(STEP_FILE_PATH):
    print(f"Error: STEP file not found at '{STEP_FILE_PATH}'")
    sys.exit(1) # Exit the script with an error code

# --- Main Script ---

# Create a new document
print("Creating a new document...")
doc = FreeCAD.newDocument("TechDraw_Automation")

# Import the STEP file
print(f"Importing STEP file: {STEP_FILE_PATH}")
shape = Part.Shape()
shape.read(STEP_FILE_PATH)
part_object = doc.addObject("Part::Feature", "Imported_STEP")
part_object.Shape = shape
doc.recompute()
print("STEP file imported successfully.")

# Create a TechDraw page
print(f"Creating TechDraw page with template: {TEMPLATE_PATH}")
page = doc.addObject("TechDraw::DrawPage", "Page")
template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
template.Template = TEMPLATE_PATH
page.Template = template

# Create individual views instead of projection group
print("Creating individual projection views...")

# Front view
print("Creating Front view...")
front_view = doc.addObject("TechDraw::DrawViewPart", "FrontView")
front_view.Source = [part_object]
front_view.Direction = FreeCAD.Vector(0, -1, 0)  # Front view direction
front_view.X = 100
front_view.Y = 150
page.addView(front_view)

# Top view
print("Creating Top view...")
top_view = doc.addObject("TechDraw::DrawViewPart", "TopView")
top_view.Source = [part_object]
top_view.Direction = FreeCAD.Vector(0, 0, 1)  # Top view direction
top_view.X = 100
top_view.Y = 250
page.addView(top_view)

# Left view
print("Creating Left view...")
left_view = doc.addObject("TechDraw::DrawViewPart", "LeftView")
left_view.Source = [part_object]
left_view.Direction = FreeCAD.Vector(-1, 0, 0)  # Left view direction
left_view.X = 200
left_view.Y = 150
page.addView(left_view)

# Recompute the document to update the views
print("Recomputing the document...")
doc.recompute()

# Add a longer delay to allow for hidden line removal (HLR) processing to complete.
import time
print("Waiting for HLR processing to complete...")
time.sleep(15) # Wait for 15 seconds

# Final recompute to ensure everything is updated
print("Final recompute...")
doc.recompute()

# Try to export SVG using Import module
print(f"Attempting to export page to SVG: {OUTPUT_SVG_PATH}")

try:
    import Import
    # Export the page object to SVG
    Import.export([page], OUTPUT_SVG_PATH)

    # Check if file was created and has content
    if os.path.exists(OUTPUT_SVG_PATH):
        file_size = os.path.getsize(OUTPUT_SVG_PATH)
        print(f"SVG file created with size: {file_size} bytes")

        if file_size > 2000:  # Reasonable size for SVG with drawings
            print(f"\nSuccess! SVG exported successfully.")
            print(f"Output saved to: {OUTPUT_SVG_PATH}")
        else:
            print(f"Warning: SVG file seems small, may not contain proper drawings.")
    else:
        print("Error: SVG file was not created.")

except Exception as e:
    print(f"Error during SVG export: {e}")

    # Fallback: Try to create a simple SVG with basic shapes
    print("Attempting fallback method...")
    try:
        # Create a basic SVG template
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="297mm" height="210mm" viewBox="0 0 297 210" xmlns="http://www.w3.org/2000/svg">
  <rect width="297" height="210" fill="white" stroke="black" stroke-width="1"/>
  <text x="148.5" y="20" text-anchor="middle" font-family="Arial" font-size="12">
    Technical Drawing - {step_file_name}
  </text>
  <text x="148.5" y="105" text-anchor="middle" font-family="Arial" font-size="10">
    Views generated but HLR processing failed in headless mode
  </text>
  <text x="148.5" y="120" text-anchor="middle" font-family="Arial" font-size="10">
    Please open the .FCStd file in FreeCAD GUI for proper view generation
  </text>
</svg>'''

        with open(OUTPUT_SVG_PATH, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Fallback SVG created at: {OUTPUT_SVG_PATH}")

    except Exception as fallback_error:
        print(f"Fallback method also failed: {fallback_error}")

print(f"\nProcess completed!")
print(f"Output file: {OUTPUT_SVG_PATH}")

# Close the document
FreeCAD.closeDocument(doc.Name)
