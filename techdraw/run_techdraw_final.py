import FreeCAD
import Part
import os
import sys
import math
from xml.etree import ElementTree as ET

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
step_file_name = "/home/tis/techdraw/FICHIER PROMPT/SUPPORT/SUPPORT/SUPPORT 2.step"
output_svg_name = "output.svg"
template_name = "A4_TOLERY.svg"

STEP_FILE_PATH = os.path.join(script_dir, "input", step_file_name)
OUTPUT_SVG_PATH = os.path.join(script_dir, "output", output_svg_name)
TEMPLATE_PATH = os.path.join(script_dir, "templates", template_name)

# --- Hole Detection Configuration ---
MIN_HOLE_RADIUS = 0.5
MAX_HOLE_RADIUS = 50
SHOW_CENTER_LINES = True
SHOW_RADIUS_DIMENSIONS = True
SHOW_HOLE_SPACING = True

# --- Thickness Detection Configuration ---
SHOW_THICKNESS_DIMENSION = True

# Check if files exist
if not os.path.exists(STEP_FILE_PATH):
    print(f"Error: STEP file not found at '{STEP_FILE_PATH}'")
    sys.exit(1)
if not os.path.exists(TEMPLATE_PATH):
    print(f"Error: Template file not found at '{TEMPLATE_PATH}'")
    sys.exit(1)

def project_point(point, direction):
    """Project 3D point to 2D based on view direction."""
    if direction == "front":  # Looking along Y axis
        return (point.x, point.z)
    elif direction == "side":  # Looking along X axis (right side)
        return (point.y, point.z)
    elif direction == "top":  # Looking along Z axis
        return (point.x, point.y)
    elif direction == "isometric":
        # True isometric projection (30° angles)
        iso_x = (point.x - point.y) * math.cos(math.radians(30))
        iso_y = point.z + (point.x + point.y) * math.sin(math.radians(30))
        return (iso_x, iso_y)
    return (point.x, point.y)


def create_svg_path_from_edges(edges, direction, scale, offset_x, offset_y, view_vector=None, shape=None):
    """Converts edges to SVG path data for a given projection direction."""
    path_data_list = []
    for edge in edges:
        points = edge.discretize(20)
        path_data = "M " + " L ".join(
            f"{project_point(p, direction)[0] * scale + offset_x:.3f},{-(project_point(p, direction)[1] * scale) + offset_y:.3f}"
            for p in points)

        # Determine if edge is hidden
        is_hidden = False
        if view_vector and shape:
            try:
                mid_param = (edge.FirstParameter + edge.LastParameter) / 2
                mid_point = edge.valueAt(mid_param)

                connected_faces = []
                for face in shape.Faces:
                    for face_edge in face.Edges:
                        if edge.isSame(face_edge):
                            connected_faces.append(face)
                            break

                if connected_faces:
                    all_facing_away = True
                    for face in connected_faces:
                        if hasattr(face.Surface, 'Axis'):
                            normal = face.Surface.Axis
                            if normal.dot(view_vector) > 0:
                                all_facing_away = False
                                break
                    is_hidden = all_facing_away
            except:
                pass

        path_data_list.append((path_data, is_hidden))
    return path_data_list


def add_dimension(svg_group, p1, p2, text, position='top', offset=10, text_offset=3):
    """Adds a standard ISO dimension to the SVG group at a specified position."""
    (x1, y1), (x2, y2) = p1, p2
    style = {'stroke': 'black', 'stroke-width': '0.35', 'fill': 'none'}
    dim_group = ET.SubElement(svg_group, 'g', {'class': 'dimension'})

    if position in ['left', 'right']:  # Vertical Dimension
        is_right = position == 'right'
        line_x = (max(x1, x2) + offset) if is_right else (min(x1, x2) - offset)
        ext_length = 8
        ext_x1_start, ext_x1_end = (x1, line_x + ext_length) if is_right else (line_x - ext_length, x1)
        ext_x2_start, ext_x2_end = (x2, line_x + ext_length) if is_right else (line_x - ext_length, x2)

        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {ext_x1_start} {y1} L {ext_x1_end} {y1}'})
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {ext_x2_start} {y2} L {ext_x2_end} {y2}'})
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x1} {y1} L {line_x} {y1}'})
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x2} {y2} L {line_x} {y2}'})
        ET.SubElement(dim_group, 'path',
                      {**style, 'd': f'M {line_x} {y1} L {line_x} {y2}', 'marker-start': 'url(#arrowhead)',
                       'marker-end': 'url(#arrowhead)'})


        # Extension lines từ các cạnh object xuống dimension line
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x1} {y1} L {line_x} {y1}'})
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x2} {y2} L {line_x} {y2}'})

        text_anchor = 'start' if is_right else 'end'
        text_x = line_x + text_offset if is_right else line_x - text_offset
        text_elem = ET.Element('text', {'x': str(text_x), 'y': str((y1 + y2) / 2), 'text-anchor': text_anchor,
                                        'dominant-baseline': 'middle', 'font-family': 'Arial',
                                        'font-size': '15', 'font-weight': 'normal', 'fill': 'black'})
        text_elem.text = text
        dim_group.append(text_elem)
        return True

    elif position in ['top', 'bottom']:  # Horizontal Dimension
        is_bottom = position == 'bottom'
        line_y = (max(y1, y2) + offset) if is_bottom else (min(y1, y2) - offset)
        ext_y1_start, ext_y1_end = (y1, y1 + 2) if is_bottom else (y1 - 2, y1)
        ext_y2_start, ext_y2_end = (y2, y2 + 2) if is_bottom else (y2 - 2, y2)

        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x1} {ext_y1_start} L {x1} {ext_y1_end}'})
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x2} {ext_y2_start} L {x2} {ext_y2_end}'})

        # Extension lines từ các cạnh object xuống dimension line
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x1} {y1} L {x1} {line_y}'})
        ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x2} {y2} L {x2} {line_y}'})
        ET.SubElement(dim_group, 'path',
                      {**style, 'd': f'M {x1} {line_y} L {x2} {line_y}', 'marker-start': 'url(#arrowhead)',
                       'marker-end': 'url(#arrowhead)'})


        text_y = line_y + text_offset if is_bottom else line_y - text_offset
        dominant_baseline = 'hanging' if is_bottom else 'auto'
        text_elem = ET.Element('text', {'x': str((x1 + x2) / 2), 'y': str(text_y), 'text-anchor': 'middle',
                                        'dominant-baseline': dominant_baseline, 'font-family': 'Arial',
                                        'font-size': '15', 'font-weight': 'normal', 'fill': 'black'})
        text_elem.text = text
        dim_group.append(text_elem)
        return True

    return False


def add_hole_center_lines(svg_group, hole_info, view_info, scale, offset_x, offset_y):
    """Adds center lines for a circular hole to the SVG group."""
    center_3d = hole_info['center']
    radius = hole_info['radius']
    normal = hole_info['normal']
    view_dir_str = view_info['dir']

    # Project the center point onto the view plane
    center_2d_proj = project_point(center_3d, view_dir_str)
    center_x = center_2d_proj[0] * scale + offset_x
    center_y = -center_2d_proj[1] * scale + offset_y

    # Determine if the hole is visible in this view
    view_vectors = {
        "front": FreeCAD.Vector(0, 1, 0),
        "top":   FreeCAD.Vector(0, 0, 1),
        "right": FreeCAD.Vector(1, 0, 0)
    }
    view_vector = view_vectors[view_dir_str]

    # Check if the hole's normal is parallel to the view vector (face-on view)
    if abs(normal.dot(view_vector)) > 0.99:
        style = {'stroke': 'black', 'stroke-width': '0.25', 'stroke-dasharray': '4 2'}
        center_group = ET.SubElement(svg_group, 'g', {'class': 'center-lines'})

        # Add center lines (2 perpendicular dashed lines)
        line_length = radius * scale * 1.5
        # Horizontal centerline
        ET.SubElement(center_group, 'path', {**style, 'd': f'M {center_x - line_length} {center_y} L {center_x + line_length} {center_y}'})
        # Vertical centerline
        ET.SubElement(center_group, 'path', {**style, 'd': f'M {center_x} {center_y - line_length} L {center_x} {center_y + line_length}'})


def detect_circular_holes(shape, min_radius=0.5, max_radius=50):
    """Detects circular holes in the shape and returns their properties."""
    holes = []

    for face in shape.Faces:
        if hasattr(face.Surface, 'Radius'):
            radius = face.Surface.Radius

            if min_radius <= radius <= max_radius:
                axis = face.Surface.Axis
                center = face.Surface.Center

                # Check if it's a reversed cylindrical face (hole characteristic)
                if face.Orientation == 'Reversed':
                    # Additional check: ensure it's a complete cylinder (not a fillet)
                    # A hole should have edges that form a complete circle
                    is_complete_cylinder = False

                    for edge in face.Edges:
                        # Check if edge is a complete circle
                        if hasattr(edge.Curve, 'Radius'):
                            try:
                                # A complete circular edge has parameter range close to 2*pi
                                param_range = edge.LastParameter - edge.FirstParameter
                                if abs(param_range - 2 * math.pi) < 0.1:
                                    is_complete_cylinder = True
                                    break
                            except:
                                pass

                    if is_complete_cylinder:
                        hole_info = {
                            'center': center,
                            'radius': radius,
                            'axis': axis,
                            'normal': axis.normalize(),
                            'face': face
                        }
                        holes.append(hole_info)

    unique_holes = []
    for hole in holes:
        is_duplicate = False
        for existing in unique_holes:
            center_dist = hole['center'].distanceToPoint(existing['center'])
            radius_diff = abs(hole['radius'] - existing['radius'])
            if center_dist < 0.1 and radius_diff < 0.01:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_holes.append(hole)

    return unique_holes


def add_diameter_dimension(svg_group, hole_info, view_info, scale, offset_x, offset_y):
    """Adds diameter dimension with symmetric leader lines (ISO standard)."""
    center_3d = hole_info['center']
    radius = hole_info['radius']
    diameter = radius * 2
    normal = hole_info['normal']
    view_dir_str = view_info['dir']

    center_2d_proj = project_point(center_3d, view_dir_str)
    center_x = center_2d_proj[0] * scale + offset_x
    center_y = -center_2d_proj[1] * scale + offset_y

    view_vectors = {
        "front": FreeCAD.Vector(0, 1, 0),
        "side": FreeCAD.Vector(1, 0, 0),
        "top": FreeCAD.Vector(0, 0, 1),
        "isometric": FreeCAD.Vector(1, 1, 1).normalize()
    }
    view_vector = view_vectors.get(view_dir_str, FreeCAD.Vector(0, 0, 1))

    if abs(normal.dot(view_vector)) > 0.999:
        radius_scaled = radius * scale

        # Use 45-degree angle for dimension lines (ISO standard)
        angle = math.pi / 0.3       # 45 degrees (diagonal, top-right direction)

        # Calculate points on circle edge at 45-degree diagonal
        # Bottom-left point (225 degrees)
        bottom_left_x = center_x + radius_scaled * math.cos(angle + math.pi)
        bottom_left_y = center_y + radius_scaled * math.sin(angle + math.pi)
        # Top-right point (45 degrees)
        top_right_x = center_x + radius_scaled * math.cos(angle)
        top_right_y = center_y + radius_scaled * math.sin(angle)

        style = {'stroke': 'black', 'stroke-width': '0.5', 'fill': 'none'}
        dim_group = ET.SubElement(svg_group, 'g', {'class': 'diameter-dimension'})

        # SHORT LINE: from bottom-left edge pointing inward (with arrow)
        short_line_length = 15
        short_end_x = bottom_left_x + short_line_length * math.cos(angle + math.pi)
        short_end_y = bottom_left_y + short_line_length * math.sin(angle + math.pi)

        ET.SubElement(dim_group, 'path', {
            **style,
            'd': f'M {bottom_left_x} {bottom_left_y} L {short_end_x} {short_end_y}',
            'marker-start': 'url(#arrowhead-inward)'
        })

        # LONG LINE: from top-right edge extending outward (with arrow pointing inward)
        long_line_length = 50
        long_end_x = top_right_x + long_line_length * math.cos(angle)
        long_end_y = top_right_y + long_line_length * math.sin(angle)

        ET.SubElement(dim_group, 'path', {
            **style,
            'd': f'M {top_right_x} {top_right_y} L {long_end_x} {long_end_y}',
            'marker-start': 'url(#arrowhead-inward)'
        })

        # Text positioned at end of long line
        text_x = long_end_x + 5
        text_y = long_end_y

        text_elem = ET.Element('text', {
            'x': str(text_x),
            'y': str(text_y),
            'text-anchor': 'start',
            'dominant-baseline': 'middle',
            'font-family': 'Arial',
            'font-size': '15',
            'font-weight': 'normal',
            'fill': 'black'
        })
        text_elem.text = f"Ø{diameter:.0f}"
        dim_group.append(text_elem)
        return True
    return False


def add_hole_spacing_dimensions(svg_group, holes, view_info, scale, offset_x, offset_y):
    """Adds dimensions showing the distance between hole centers."""
    if len(holes) < 2:
        return

    view_dir_str = view_info['dir']

    view_vectors = {
        "front": FreeCAD.Vector(0, 1, 0),
        "side": FreeCAD.Vector(1, 0, 0),
        "top": FreeCAD.Vector(0, 0, 1),
        "isometric": FreeCAD.Vector(1, 1, 1).normalize()
    }
    view_vector = view_vectors.get(view_dir_str, FreeCAD.Vector(0, 0, 1))

    visible_holes = []
    for hole in holes:
        if abs(hole['normal'].dot(view_vector)) > 0.99:
            visible_holes.append(hole)

    if len(visible_holes) < 2:
        return

    holes_2d = []
    for hole in visible_holes:
        center_2d = project_point(hole['center'], view_dir_str)
        center_x = center_2d[0] * scale + offset_x
        center_y = -center_2d[1] * scale + offset_y
        holes_2d.append({
            'hole': hole,
            'x': center_x,
            'y': center_y,
            'center_3d': hole['center']
        })

    if len(holes_2d) >= 2:
        holes_sorted_y = sorted(holes_2d, key=lambda h: h['y'])

        x_variance = max(h['x'] for h in holes_2d) - min(h['x'] for h in holes_2d)
        y_variance = max(h['y'] for h in holes_2d) - min(h['y'] for h in holes_2d)

        style = {'stroke': 'black', 'stroke-width': '0.35', 'fill': 'none'}
        ext_length = 8

        if y_variance > x_variance and y_variance > 20:
            for i in range(len(holes_sorted_y) - 1):
                h1 = holes_sorted_y[i]
                h2 = holes_sorted_y[i + 1]

                distance_3d = h1['center_3d'].distanceToPoint(h2['center_3d'])

                x_offset = 50
                x_dim = max(h1['x'], h2['x']) + x_offset
                y1 = h1['y']
                y2 = h2['y']

                dim_group = ET.SubElement(svg_group, 'g', {'class': 'hole-spacing-dimension'})

                ET.SubElement(dim_group, 'path', {**style, 'd': f'M {h1["x"]} {y1} L {x_dim + ext_length} {y1}'})
                ET.SubElement(dim_group, 'path', {**style, 'd': f'M {h2["x"]} {y2} L {x_dim + ext_length} {y2}'})

                ET.SubElement(dim_group, 'path', {
                    **style,
                    'd': f'M {x_dim} {y1} L {x_dim} {y2}',
                    'marker-start': 'url(#arrowhead)',
                    'marker-end': 'url(#arrowhead)'
                })

                text_elem = ET.Element('text', {
                    'x': str(x_dim + 5),
                    'y': str((y1 + y2) / 2),
                    'text-anchor': 'start',
                    'dominant-baseline': 'middle',
                    'font-family': 'Arial',
                    'font-size': '15',
                    'font-weight': 'normal',
                    'fill': 'black'
                })
                text_elem.text = f"{distance_3d:.0f}"
                dim_group.append(text_elem)

        elif x_variance > 20:
            holes_sorted_x = sorted(holes_2d, key=lambda h: h['x'])

            for i in range(len(holes_sorted_x) - 1):
                h1 = holes_sorted_x[i]
                h2 = holes_sorted_x[i + 1]

                distance_3d = h1['center_3d'].distanceToPoint(h2['center_3d'])

                y_offset = 25
                y_dim = max(h1['y'], h2['y']) + y_offset
                x1 = h1['x']
                x2 = h2['x']

                dim_group = ET.SubElement(svg_group, 'g', {'class': 'hole-spacing-dimension'})

                ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x1} {h1["y"]} L {x1} {y_dim + ext_length}'})
                ET.SubElement(dim_group, 'path', {**style, 'd': f'M {x2} {h2["y"]} L {x2} {y_dim + ext_length}'})

                ET.SubElement(dim_group, 'path', {
                    **style,
                    'd': f'M {x1} {y_dim} L {x2} {y_dim}',
                    'marker-start': 'url(#arrowhead)',
                    'marker-end': 'url(#arrowhead)'
                })

                text_elem = ET.Element('text', {
                    'x': str((x1 + x2) / 2),
                    'y': str(y_dim + 5),
                    'text-anchor': 'middle',
                    'dominant-baseline': 'hanging',
                    'font-family': 'Arial',
                    'font-size': '15',
                    'font-weight': 'normal',
                    'fill': 'black'
                })
                text_elem.text = f"{distance_3d:.0f}"
                dim_group.append(text_elem)


def detect_thickness(shape):
    """Detects the thickness of a sheet metal or profile part."""
    bbox = shape.BoundBox

    dimensions = [bbox.XLength, bbox.YLength, bbox.ZLength]
    sorted_dims = sorted(dimensions)
    if sorted_dims[0] < sorted_dims[1] * 0.2:
        return sorted_dims[0]

    face_thicknesses = []

    for i, face1 in enumerate(shape.Faces):
        if not hasattr(face1.Surface, 'Axis'):
            continue

        try:
            normal1 = face1.Surface.Axis
            area1 = face1.Area

            for j, face2 in enumerate(shape.Faces[i + 1:], i + 1):
                if not hasattr(face2.Surface, 'Axis'):
                    continue

                normal2 = face2.Surface.Axis
                area2 = face2.Area

                if abs(normal1.dot(normal2) + 1.0) < 0.01:
                    if abs(area1 - area2) / max(area1, area2) < 0.1:
                        center1 = face1.CenterOfMass
                        center2 = face2.CenterOfMass
                        distance = center1.distanceToPoint(center2)

                        if 0.5 < distance < 20:
                            face_thicknesses.append(distance)
        except:
            continue

    if face_thicknesses:
        thickness = min(face_thicknesses)
        return round(thickness, 1)

    return None


def add_thickness_dimension(svg_group, thickness, shape, view_info, scale, offset_x, offset_y):
    """Adds thickness dimension callout to the view (like in the reference image)."""
    if not thickness or view_info['dir'] != 'front':
        return False

    # Find vertical edges that represent thickness in front view
    view_dir_str = view_info['dir']
    thickness_edges = []

    for edge in shape.Edges:
        try:
            p1 = edge.firstVertex().Point
            p2 = edge.lastVertex().Point

            # Project to 2D
            p1_2d = project_point(p1, view_dir_str)
            p2_2d = project_point(p2, view_dir_str)

            # Check if edge is vertical in front view
            dx = abs(p2_2d[0] - p1_2d[0])
            dy = abs(p2_2d[1] - p1_2d[1])

            # Vertical edge with length close to thickness
            if dx < 0.1 and abs(dy - thickness) <1:
                thickness_edges.append({
                    'edge': edge,
                    'p1_2d': p1_2d,
                    'p2_2d': p2_2d,
                    'length': dy
                })
        except:
            continue

    if not thickness_edges:
        return False

    # Select rightmost vertical edge at the bottom
    rightmost_edge = max(thickness_edges, key=lambda e: e['p1_2d'][0])

    p1_2d = rightmost_edge['p1_2d']
    p2_2d = rightmost_edge['p2_2d']

    # Convert to SVG coordinates
    x1 = p1_2d[0] * scale + offset_x
    y1 = -p1_2d[1] * scale + offset_y
    x2 = p2_2d[0] * scale + offset_x
    y2 = -p2_2d[1] * scale + offset_y

    # Use the bottom point
    if y1 > y2:
        point_x, point_y = x1, y1
    else:
        point_x, point_y = x2, y2

    # Create dimension group
    dim_group = ET.SubElement(svg_group, 'g', {'class': 'thickness-dimension'})

    # Leader line from edge to callout
    leader_length = 60
    leader_end_x = point_x + leader_length
    leader_end_y = point_y

    # Draw leader line
    ET.SubElement(dim_group, 'path', {
        'stroke': 'black',
        'stroke-width': '0.7',
        'fill': 'none',
        'd': f'M {point_x} {point_y} L {leader_end_x} {leader_end_y}'
    })

    # Draw callout box with thickness icon
    box_width = 80
    box_height = 24
    box_x = leader_end_x + 5
    box_y = leader_end_y - box_height / 2

    # Green background box
    ET.SubElement(dim_group, 'rect', {
        'x': str(box_x),
        'y': str(box_y),
        'width': str(box_width),
        'height': str(box_height),
        'fill': '#90EE90',
        'stroke': 'black',
        'stroke-width': '1.0',
        'rx': '3'
    })

    # Thickness icon (wrench/tool symbol)
    icon_x = box_x + 6
    icon_y = box_y + box_height / 2
    icon_size = 12

    # Draw simple thickness icon (two parallel lines)
    ET.SubElement(dim_group, 'path', {
        'stroke': 'black',
        'stroke-width': '1.5',
        'fill': 'none',
        'd': f'M {icon_x} {icon_y - icon_size / 3} L {icon_x + icon_size} {icon_y - icon_size / 3} M {icon_x} {icon_y + icon_size / 3} L {icon_x + icon_size} {icon_y + icon_size / 3}'
    })

    # Text showing thickness value
    text_x = box_x + 24
    text_y = box_y + box_height / 2

    text_elem = ET.Element('text', {
        'x': str(text_x),
        'y': str(text_y),
        'text-anchor': 'start',
        'dominant-baseline': 'middle',
        'font-family': 'Arial',
        'font-size': '15',
        'font-weight': 'normal',
        'fill': 'black'
    })
    text_elem.text = f"{thickness:.2f} mm"
    dim_group.append(text_elem)

    return True


def add_flange_dimension(svg_group, shape, view_info, scale, offset_x, offset_y):
    """Adds vertical dimension for short edges (flange height) with extension lines and arrows."""
    if view_info['dir'] != 'front':
        return False

    view_dir_str = view_info['dir']
    vertical_edges = []

    # Find all vertical edges in front view
    for edge in shape.Edges:
        try:
            p1 = edge.firstVertex().Point
            p2 = edge.lastVertex().Point

            # Project to 2D
            p1_2d = project_point(p1, view_dir_str)
            p2_2d = project_point(p2, view_dir_str)

            # Check if edge is vertical
            dx = abs(p2_2d[0] - p1_2d[0])
            dy = abs(p2_2d[1] - p1_2d[1])

            # Vertical edge (dx small, dy significant)
            if dx < 0.1 and dy > 0.5:
                vertical_edges.append({
                    'p1_2d': p1_2d,
                    'p2_2d': p2_2d,
                    'length': dy,
                    'x': p1_2d[0],
                    'y_min': min(p1_2d[1], p2_2d[1]),
                    'y_max': max(p1_2d[1], p2_2d[1])
                })
        except:
            continue

    if not vertical_edges:
        return False

    # Group edges by length to find common short edges (flange)
    edge_lengths = {}
    for edge in vertical_edges:
        length_key = round(edge['length'], 1)
        if length_key not in edge_lengths:
            edge_lengths[length_key] = []
        edge_lengths[length_key].append(edge)

    # Find the shortest edge group (likely the flange)
    if not edge_lengths:
        return False

    shortest_length = min(edge_lengths.keys())

    # Skip if it's too small (likely thickness, not flange)
    if shortest_length < 1.0:
        # Try second shortest
        sorted_lengths = sorted(edge_lengths.keys())
        if len(sorted_lengths) > 1:
            shortest_length = sorted_lengths[1]
        else:
            return False

    flange_edges = edge_lengths[shortest_length]

    # Select rightmost edge for annotation
    rightmost_edge = max(flange_edges, key=lambda e: e['x'])

    p1_2d = rightmost_edge['p1_2d']
    p2_2d = rightmost_edge['p2_2d']
    flange_height = rightmost_edge['length']

    # Convert to SVG coordinates
    x1 = p1_2d[0] * scale + offset_x
    y1 = -p1_2d[1] * scale + offset_y
    x2 = p2_2d[0] * scale + offset_x
    y2 = -p2_2d[1] * scale + offset_y

    # Ensure y1 is top, y2 is bottom
    if y1 > y2:
        y1, y2 = y2, y1

    # Create dimension group
    dim_group = ET.SubElement(svg_group, 'g', {'class': 'flange-dimension'})
    style = {'stroke': 'black', 'stroke-width': '0.7', 'fill': 'none'}

    # Extension lines offset (distance from edge to dimension line)
    ext_offset = 40

    # Dimension line X position (to the right of the edge)
    dim_line_x = x1 + ext_offset

    # Draw extension lines (from edge endpoints extending beyond dimension line)
    ext_overshoot = 5  # Extension beyond dimension line

    # Top extension line
    ET.SubElement(dim_group, 'path', {
        **style,
        'd': f'M {x1} {y1} L {dim_line_x + ext_overshoot} {y1}'
    })

    # Bottom extension line
    ET.SubElement(dim_group, 'path', {
        **style,
        'd': f'M {x1} {y2} L {dim_line_x + ext_overshoot} {y2}'
    })

    # Draw dimension line with arrows pointing inward
    ET.SubElement(dim_group, 'path', {
        **style,
        'd': f'M {dim_line_x} {y1} L {dim_line_x} {y2}',
        'marker-start': 'url(#arrowhead)',
        'marker-end': 'url(#arrowhead)'
    })

    # Add dimension text
    text_x = dim_line_x + 5
    text_y = (y1 + y2) / 2

    text_elem = ET.Element('text', {
        'x': str(text_x),
        'y': str(text_y),
        'text-anchor': 'start',
        'dominant-baseline': 'middle',
        'font-family': 'Arial',
        'font-size': '15',
        'font-weight': 'normal',
        'fill': 'black'
    })
    text_elem.text = f"{flange_height:.0f}"
    dim_group.append(text_elem)

    return True
# --- Main Script ---
doc = FreeCAD.newDocument("TechDrawFinal")
shape = Part.Shape()
shape.read(STEP_FILE_PATH)
part_object = doc.addObject("Part::Feature", "Imported_STEP")
part_object.Shape = shape
doc.recompute()
print("STEP file imported successfully.")

# Detect circular holes
print("Detecting circular holes...")
holes = detect_circular_holes(shape, min_radius=MIN_HOLE_RADIUS, max_radius=MAX_HOLE_RADIUS)
print(f"Found {len(holes)} circular holes")

# Detect thickness
print("Detecting material thickness...")
thickness = detect_thickness(shape)
if thickness:
    print(f"Detected thickness: {thickness:.2f} mm")
else:
    print("No thickness detected")

# Load SVG template
print(f"Loading template: {TEMPLATE_PATH}")
ET.register_namespace('', "http://www.w3.org/2000/svg")

# --- Add Overall Dimensions ---
tree = ET.parse(TEMPLATE_PATH)
root = tree.getroot()

# Find or create defs section and add arrowhead marker
ns = {'svg': 'http://www.w3.org/2000/svg'}
defs = root.find('svg:defs', ns)
if defs is None:
    defs = ET.SubElement(root, 'defs')
arrow_marker = ET.Element('marker',
                          {'id': 'arrowhead', 'viewBox': '0 0 10 10', 'refX': '5', 'refY': '5', 'markerWidth': '6',
                           'markerHeight': '6', 'orient': 'auto-start-reverse'})
ET.SubElement(arrow_marker, 'path', {'d': 'M 0 0 L 10 5 L 0 10 z', 'fill': 'black'})
defs.append(arrow_marker)

# Add inward-pointing arrowhead marker
arrow_inward = ET.Element('marker',
                          {'id': 'arrowhead-inward', 'viewBox': '0 0 10 10', 'refX': '0', 'refY': '5',
                           'markerWidth': '6', 'markerHeight': '6', 'orient': 'auto'})
ET.SubElement(arrow_inward, 'path', {'d': 'M 0 5 L 10 0 L 10 10 z', 'fill': 'black'})
defs.append(arrow_inward)
# Create a group for our drawings
drawing_group = ET.SubElement(root, 'g', id='TechDrawViews')

# --- Layout Configuration (2x2 Grid) ---
bbox = shape.BoundBox
length, width, height = bbox.XLength, bbox.YLength, bbox.ZLength

# Drawing area - dịch xuống dưới
drawing_area_x_start = 20
drawing_area_y_start = 60  # Tăng từ 20 lên 60 để dịch xuống
drawing_area_width = 800
drawing_area_height = 440

# Grid layout: 2 columns x 2 rows with reduced gaps
col_gap = 60
row_gap = 50
dimension_space = 60

# Calculate cell dimensions
cell_width = (drawing_area_width - col_gap) / 2
cell_height = (drawing_area_height - row_gap - dimension_space) / 2

# Compute individual view scales with larger multiplier
front_scale = min(cell_width / length, cell_height / height) * 1.2
side_scale = min(cell_width / width, cell_height / height) * 1.2
top_scale = min(cell_width / length, cell_height / width) * 1.2

# Isometric projection dimensions
iso_width = (length + width) * 0.866
iso_height = height + (length + width) * 0.5
iso_scale = min(cell_width / iso_width, cell_height / iso_height) * 1.0

# Use uniform scale for consistency - increase by 30%
scale = min(front_scale, side_scale, top_scale, iso_scale) * 1.3

print(f"Object dimensions (L,W,H): {length:.1f}, {width:.1f}, {height:.1f}")
print(f"Calculated scale: {scale:.3f}")

# Define view positions in 2x2 grid
# Layout:  [FRONT]      [SIDE]
#          [TOP]        [ISOMETRIC]

left_col_x = drawing_area_x_start
right_col_x = drawing_area_x_start + cell_width + col_gap

top_row_y = drawing_area_y_start
bottom_row_y = drawing_area_y_start + cell_height + row_gap

# Views dictionary
views = {
    "front": {"dir": "front", "pos": (left_col_x, top_row_y), "label": "FRONT VIEW"},
    "side": {"dir": "side", "pos": (right_col_x, top_row_y), "label": "SIDE VIEW"},
    "top": {"dir": "top", "pos": (left_col_x, bottom_row_y), "label": "TOP VIEW"},
    "isometric": {"dir": "isometric", "pos": (right_col_x, bottom_row_y), "label": "ISOMETRIC VIEW"}
}

# Track annotated radii globally
annotated_radii = set()

for name, view in views.items():
    print(f"Generating {name} view...")
    view_group = ET.SubElement(drawing_group, 'g', id=f'{name}View', stroke='black', fill='none',
                               **{'stroke-width': '0.7'})  # Nét liền, độ dày đồng nhất

    # Get projected min/max points
    projected_points = [project_point(v.Point, view['dir']) for v in shape.Vertexes]
    projected_min_x = min(p[0] for p in projected_points)
    projected_max_x = max(p[0] for p in projected_points)
    projected_min_y = min(p[1] for p in projected_points)
    projected_max_y = max(p[1] for p in projected_points)

    # Calculate centering offsets within the cell
    projected_width = (projected_max_x - projected_min_x) * scale
    projected_height = (projected_max_y - projected_min_y) * scale

    center_offset_x = (cell_width - projected_width) / 2
    center_offset_y = (cell_height - projected_height) / 2

    # Calculate translation
    trans_x = view['pos'][0] + center_offset_x - projected_min_x * scale
    trans_y = view['pos'][1] + center_offset_y + projected_max_y * scale

    # Get view vector for hidden line detection
    view_vectors = {
        "front": FreeCAD.Vector(0, 1, 0),
        "side": FreeCAD.Vector(1, 0, 0),
        "top": FreeCAD.Vector(0, 0, 1),
        "isometric": FreeCAD.Vector(1, 1, 1).normalize()
    }
    view_vector = view_vectors.get(view['dir'])

    # Create paths - TẤT CẢ ĐỀU NÉT LIỀN
    paths = create_svg_path_from_edges(shape.Edges, view['dir'], scale, trans_x, trans_y, view_vector, shape)
    for path_data, is_hidden in paths:
        # Tất cả đều nét liền, không có nét đứt
        ET.SubElement(view_group, 'path', d=path_data, **{'stroke-width': '0.7', 'stroke': 'black'})

    # Add hole annotations
    if holes:
        for hole in holes:
            if SHOW_CENTER_LINES:
                add_hole_center_lines(view_group, hole, view, scale, trans_x, trans_y)
            if SHOW_RADIUS_DIMENSIONS:
                r_key = round(hole['radius'], 3)
                if r_key not in annotated_radii:
                    added = add_diameter_dimension(view_group, hole, view, scale, trans_x, trans_y)
                    if added:
                        annotated_radii.add(r_key)


        if SHOW_HOLE_SPACING:
            add_hole_spacing_dimensions(view_group, holes, view, scale, trans_x, trans_y)
        # Add thickness dimension for front view
    if SHOW_THICKNESS_DIMENSION and thickness and name == 'front':
        add_thickness_dimension(view_group, thickness, shape, view, scale, trans_x, trans_y)

    # Add flange dimension for front view
    if name == 'front':
        add_flange_dimension(view_group, shape, view, scale, trans_x, trans_y)


# --- Add Overall Dimensions ---
print("Adding overall dimensions...")

# Get view positions for dimensioning
front_view = views['front']
side_view = views['side']
top_view = views['top']

# Front View dimensions (length and height)
front_projected_points = [project_point(v.Point, "front") for v in shape.Vertexes]
front_min_x = min(p[0] for p in front_projected_points)
front_max_x = max(p[0] for p in front_projected_points)
front_min_y = min(p[1] for p in front_projected_points)
front_max_y = max(p[1] for p in front_projected_points)

# Calculate front view actual position
front_projected_width = (front_max_x - front_min_x) * scale
front_projected_height = (front_max_y - front_min_y) * scale
front_center_offset_x = (cell_width - front_projected_width) / 2
front_center_offset_y = (cell_height - front_projected_height) / 2

front_left = front_view['pos'][0] + front_center_offset_x
front_right = front_left + front_projected_width
front_top = front_view['pos'][1] + front_center_offset_y
front_bottom = front_top + front_projected_height

# Add dimensions to front view
p_front_bl = (front_left, front_bottom)
p_front_br = (front_right, front_bottom)
p_front_tl = (front_left, front_top)
add_dimension(drawing_group, p_front_bl, p_front_br, f"{length:.0f}", position='bottom', offset=40)
add_dimension(drawing_group, p_front_tl, p_front_bl, f"{height:.0f}", position='left', offset=40)

# Side View dimensions (width and height)
side_projected_points = [project_point(v.Point, "side") for v in shape.Vertexes]
side_min_x = min(p[0] for p in side_projected_points)
side_max_x = max(p[0] for p in side_projected_points)
side_min_y = min(p[1] for p in side_projected_points)
side_max_y = max(p[1] for p in side_projected_points)

side_projected_width = (side_max_x - side_min_x) * scale
side_projected_height = (side_max_y - side_min_y) * scale
side_center_offset_x = (cell_width - side_projected_width) / 2
side_center_offset_y = (cell_height - side_projected_height) / 2

side_left = side_view['pos'][0] + side_center_offset_x
side_right = side_left + side_projected_width
side_top = side_view['pos'][1] + side_center_offset_y
side_bottom = side_top + side_projected_height

# Add dimensions to side view
p_side_bl = (side_left, side_bottom)
p_side_br = (side_right, side_bottom)
add_dimension(drawing_group, p_side_bl, p_side_br, f"{width:.0f}", position='bottom', offset=40)

# Top View dimensions (length and width)
top_projected_points = [project_point(v.Point, "top") for v in shape.Vertexes]
top_min_x = min(p[0] for p in top_projected_points)
top_max_x = max(p[0] for p in top_projected_points)
top_min_y = min(p[1] for p in top_projected_points)
top_max_y = max(p[1] for p in top_projected_points)

top_projected_width = (top_max_x - top_min_x) * scale
top_projected_height = (top_max_y - top_min_y) * scale
top_center_offset_x = (cell_width - top_projected_width) / 2
top_center_offset_y = (cell_height - top_projected_height) / 2

top_left = top_view['pos'][0] + top_center_offset_x
top_right = top_left + top_projected_width
top_top = top_view['pos'][1] + top_center_offset_y
top_bottom = top_top + top_projected_height

# Add dimensions to top view
p_top_bl = (top_left, top_bottom)
p_top_br = (top_right, top_bottom)
add_dimension(drawing_group, p_top_bl, p_top_br, f"{length:.0f}", position='bottom', offset=40)

# Write final SVG
print(f"Writing final SVG to: {OUTPUT_SVG_PATH}")
tree.write(OUTPUT_SVG_PATH, encoding='utf-8', xml_declaration=True)

print("\nProcess completed successfully!")
print(f"Generated views: Front, Side, Top, Isometric")
print(f"Output file: {OUTPUT_SVG_PATH}")
FreeCAD.closeDocument(doc.Name)
# --- Save SVG output ---
tree.write(OUTPUT_SVG_PATH)
print(f"SVG drawing saved to {OUTPUT_SVG_PATH}")