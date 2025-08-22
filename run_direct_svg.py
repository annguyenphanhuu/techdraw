import FreeCAD
import Part
import os
import sys
import math

# Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
step_file_name = "sheet.step"
output_svg_name = "output.svg"

STEP_FILE_PATH = os.path.join(script_dir, "input", step_file_name)
OUTPUT_SVG_PATH = os.path.join(script_dir, output_svg_name)

# Check if the STEP file exists
if not os.path.exists(STEP_FILE_PATH):
    print(f"Error: STEP file not found at '{STEP_FILE_PATH}'")
    sys.exit(1)

def project_point(point, direction):
    """Project a 3D point onto a 2D plane based on view direction"""
    if direction == "front":  # Looking along Y axis
        return (point.x, point.z)
    elif direction == "top":  # Looking along Z axis  
        return (point.x, point.y)
    elif direction == "left":  # Looking along X axis
        return (point.y, point.z)
    return (point.x, point.y)

def get_bounding_box_2d(edges, direction):
    """Get 2D bounding box of projected edges"""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for edge in edges:
        points = edge.discretize(20)  # Get points along the edge
        for point in points:
            x, y = project_point(point, direction)
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
    
    return min_x, min_y, max_x, max_y

def create_svg_path_from_edges(edges, direction, scale=1, offset_x=0, offset_y=0):
    """Create SVG path from edges"""
    paths = []
    
    for edge in edges:
        points = edge.discretize(10)  # Get points along the edge
        if len(points) < 2:
            continue
            
        path_data = []
        for i, point in enumerate(points):
            x, y = project_point(point, direction)
            x = x * scale + offset_x
            y = -y * scale + offset_y  # Flip Y axis for SVG
            
            if i == 0:
                path_data.append(f"M {x:.2f} {y:.2f}")
            else:
                path_data.append(f"L {x:.2f} {y:.2f}")
        
        if path_data:
            paths.append(" ".join(path_data))
    
    return paths

# Create a new document
print("Creating a new document...")
doc = FreeCAD.newDocument("DirectSVG")

# Import the STEP file
print(f"Importing STEP file: {STEP_FILE_PATH}")
shape = Part.Shape()
shape.read(STEP_FILE_PATH)
part_object = doc.addObject("Part::Feature", "Imported_STEP")
part_object.Shape = shape
doc.recompute()
print("STEP file imported successfully.")

# Get all edges from the shape
edges = shape.Edges
print(f"Found {len(edges)} edges in the shape")

# Calculate scale and positions for three views
view_width = 80
view_height = 60
margin = 20

# Create SVG content
svg_width = 297  # A4 width in mm
svg_height = 210  # A4 height in mm

svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{svg_width}mm" height="{svg_height}mm" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{svg_width}" height="{svg_height}" fill="white" stroke="black" stroke-width="0.5"/>
  
  <!-- Title -->
  <text x="{svg_width/2}" y="15" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold">
    Technical Drawing - {step_file_name}
  </text>
  
  <!-- View labels -->
  <text x="60" y="35" text-anchor="middle" font-family="Arial" font-size="10">Front View</text>
  <text x="150" y="35" text-anchor="middle" font-family="Arial" font-size="10">Top View</text>
  <text x="240" y="35" text-anchor="middle" font-family="Arial" font-size="10">Left View</text>
'''

# Generate three views
views = [
    ("front", 60, 120),   # Front view position
    ("top", 150, 120),    # Top view position  
    ("left", 240, 120)    # Left view position
]

for view_name, center_x, center_y in views:
    print(f"Generating {view_name} view...")
    
    # Get bounding box for this view
    min_x, min_y, max_x, max_y = get_bounding_box_2d(edges, view_name)
    
    if max_x > min_x and max_y > min_y:
        # Calculate scale to fit in view area
        width = max_x - min_x
        height = max_y - min_y
        scale = min(view_width / width, view_height / height) * 0.8
        
        # Calculate offset to center the view
        offset_x = center_x - (min_x + max_x) * scale / 2
        offset_y = center_y - (min_y + max_y) * scale / 2
        
        # Create paths for this view
        paths = create_svg_path_from_edges(edges, view_name, scale, offset_x, offset_y)
        
        # Add view border
        svg_content += f'''
  <!-- {view_name.title()} view border -->
  <rect x="{center_x - view_width/2}" y="{center_y - view_height/2}" 
        width="{view_width}" height="{view_height}" 
        fill="none" stroke="gray" stroke-width="0.3" stroke-dasharray="2,2"/>
'''
        
        # Add paths to SVG
        for path in paths:
            svg_content += f'''
  <path d="{path}" fill="none" stroke="black" stroke-width="0.5"/>'''

svg_content += '''
</svg>'''

# Write SVG file
print(f"Writing SVG to: {OUTPUT_SVG_PATH}")
with open(OUTPUT_SVG_PATH, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"\nProcess completed successfully!")
print(f"Output saved to: {OUTPUT_SVG_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_SVG_PATH)} bytes")

# Close the document
FreeCAD.closeDocument(doc.Name)
