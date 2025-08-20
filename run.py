import FreeCAD as App
import TechDraw
import os
import math

# Mở hoặc tạo một document mới
doc = App.newDocument("ProjectionDrawing")
App.setActiveDocument("ProjectionDrawing")

# Import file STEP
import Import
step_file_path = os.path.join(os.path.dirname(__file__), "input", "sheet.step")
print(f"Đang import file: {step_file_path}")

if os.path.exists(step_file_path):
    Import.insert(step_file_path, "ProjectionDrawing")
    App.ActiveDocument.recompute()
    print("Đã import file STEP thành công!")

    # Lấy tất cả các objects đã import
    imported_objects = []
    for obj in App.ActiveDocument.Objects:
        if hasattr(obj, 'Shape') and obj.Shape:
            imported_objects.append(obj)
            print(f"Tìm thấy object: {obj.Name} - {obj.TypeId}")

    if not imported_objects:
        print("Không tìm thấy object nào có Shape!")
        # Tạo hình hộp backup
        from Part import makeBox
        part = makeBox(10, 20, 5)
        backup_obj = App.ActiveDocument.addObject("Part::Feature", "BackupBox")
        backup_obj.Shape = part
        imported_objects = [backup_obj]
        print("Đã tạo hình hộp backup")
else:
    print(f"Không tìm thấy file: {step_file_path}")
    # Tạo hình hộp backup
    from Part import makeBox
    part = makeBox(10, 20, 5)
    backup_obj = App.ActiveDocument.addObject("Part::Feature", "BackupBox")
    backup_obj.Shape = part
    imported_objects = [backup_obj]
    print("Đã tạo hình hộp backup")

App.ActiveDocument.recompute()

# Tạo trang TechDraw với template đúng cách
page = doc.addObject('TechDraw::DrawPage', 'Page')
template = doc.addObject('TechDraw::DrawSVGTemplate','Template')

# Sử dụng template có sẵn từ TechDraw test
template_path = os.path.join(os.path.dirname(__file__), "TechDraw", "TDTest", "TestTemplate.svg")
if os.path.exists(template_path):
    template.Template = template_path
else:
    # Nếu không tìm thấy template, tạo một template đơn giản
    print("Không tìm thấy template, sử dụng template mặc định")

page.Template = template

# Tạo view (phiên bản chiếu) và thêm vào page
view = doc.addObject('TechDraw::DrawViewPart', 'View1')
view.Source = imported_objects  # Sử dụng objects đã import
page.addView(view)
print(f"Đã tạo view với {len(imported_objects)} object(s)")

# Tùy chỉnh vị trí hoặc tỉ lệ nếu cần
view.X = 0
view.Y = 0
view.Scale = 1.0

# Không xuất DXF nữa - chỉ cần SVG

# Đảm bảo page được tính toán hoàn toàn
doc.recompute()

# Chờ lâu hơn để HLR hoàn thành
import time
print("Chờ TechDraw tính toán...")
time.sleep(5)

# Force recompute và kiểm tra view state
doc.recompute()
print(f"View state: {view.State}")
print(f"View has edges: {hasattr(view, 'getVisibleEdges')}")

# Thử lấy thông tin về shape
try:
    if imported_objects:
        shape = imported_objects[0].Shape
        print(f"Shape type: {shape.ShapeType}")
        print(f"Shape edges: {len(shape.Edges)}")
        print(f"Shape faces: {len(shape.Faces)}")

        # Lấy bounding box
        bbox = shape.BoundBox
        print(f"BoundBox: {bbox.XMin:.2f},{bbox.YMin:.2f},{bbox.ZMin:.2f} to {bbox.XMax:.2f},{bbox.YMax:.2f},{bbox.ZMax:.2f}")
except Exception as e:
    print(f"Lỗi khi lấy thông tin shape: {e}")

# Xuất sang SVG - sử dụng TechDraw thực tế
print("Đang thử xuất SVG...")

# Thử lấy SVG từ TechDraw page
try:
    # Thử các thuộc tính khác nhau để lấy SVG
    svg_content = None

    # Kiểm tra các thuộc tính có thể chứa SVG
    print("Kiểm tra các thuộc tính của page:")
    for attr in dir(page):
        if not attr.startswith('_'):
            try:
                value = getattr(page, attr)
                if isinstance(value, str) and ('svg' in value.lower() or 'xml' in value.lower()):
                    print(f"  {attr}: {len(value)} characters")
                    if len(value) > 100:  # Có vẻ như SVG content
                        svg_content = value
                        print(f"  -> Sử dụng {attr} làm SVG content")
                        break
            except:
                pass

    # Nếu không tìm thấy SVG từ page, tạo SVG từ view geometry
    if not svg_content:
        print("Không tìm thấy SVG từ page, tạo SVG từ view geometry...")

        # Tạo SVG từ shape geometry trực tiếp
        try:
            # Lấy edges từ shape gốc (vì view edges không hoạt động trong console mode)
            edges = []
            if imported_objects:
                shape = imported_objects[0].Shape
                edges = shape.Edges
                print(f"Lấy được {len(edges)} edges từ shape")

                # Phân loại edges theo loại để hiển thị đầy đủ
                top_face_edges = []  # Edges trên mặt phẳng Z=3 (top)
                bottom_face_edges = []  # Edges trên mặt phẳng Z=0 (bottom)
                circular_edges = []  # Edges tròn/cong

                for edge in edges:
                    try:
                        # Kiểm tra loại curve
                        curve = edge.Curve
                        curve_type = str(type(curve)).split('.')[-1].replace("'>", "")

                        if curve_type == "Circle":
                            # Đường tròn - luôn thêm vào để hiển thị
                            circular_edges.append(edge)
                            # Cũng phân loại theo Z để biết thuộc mặt nào
                            center_z = curve.Center.z
                            if abs(center_z - 3.0) < 0.01:
                                top_face_edges.append(edge)
                            elif abs(center_z) < 0.01:
                                bottom_face_edges.append(edge)
                        else:
                            # Đường thẳng - phân loại theo Z
                            if hasattr(edge, 'Vertexes') and len(edge.Vertexes) >= 2:
                                z1 = edge.Vertexes[0].Point.z
                                z2 = edge.Vertexes[1].Point.z

                                # Nếu cả hai điểm đều ở Z=3, đây là edge của mặt trên
                                if abs(z1 - 3.0) < 0.01 and abs(z2 - 3.0) < 0.01:
                                    top_face_edges.append(edge)
                                # Nếu cả hai điểm đều ở Z=0, đây là edge của mặt dưới
                                elif abs(z1) < 0.01 and abs(z2) < 0.01:
                                    bottom_face_edges.append(edge)
                    except Exception as e:
                        print(f"Lỗi phân loại edge: {e}")

                print(f"Top face edges: {len(top_face_edges)}, Bottom face edges: {len(bottom_face_edges)}, Circular edges: {len(circular_edges)}")

                # Sử dụng top face edges cho main view (bao gồm cả đường tròn)
                edges = top_face_edges if top_face_edges else bottom_face_edges

            # Đọc template A4 Landscape ISO 5457
            template_path = os.path.join(os.path.dirname(__file__), "templates", "A4_Landscape_TD.svg")
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                print(f"Đã đọc template: {template_path}")
            else:
                print(f"Không tìm thấy template: {template_path}")
                # Fallback to simple SVG
                svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">
  <!-- Page border -->
  <rect x="5" y="5" width="287" height="200" fill="none" stroke="black" stroke-width="0.5"/>
  <!-- Title block -->
  <rect x="200" y="170" width="87" height="30" fill="none" stroke="black" stroke-width="0.5"/>
  <text x="205" y="185" font-family="Arial" font-size="8">Sheet Drawing</text>
  <text x="205" y="195" font-family="Arial" font-size="6">50x50x3mm from sheet.step</text>
'''

            # Phân tích geometry để xác định loại part
            bbox = imported_objects[0].Shape.BoundBox if imported_objects else None
            part_type = "unknown"
            part_name = "Unknown Part"

            if bbox:
                width = bbox.XMax - bbox.XMin
                height = bbox.YMax - bbox.YMin
                depth = bbox.ZMax - bbox.ZMin

                # Xác định loại part dựa trên tỷ lệ kích thước
                dimensions = sorted([width, height, depth])
                aspect_ratios = [dimensions[1]/dimensions[0], dimensions[2]/dimensions[1]]

                if dimensions[0] < 10 and aspect_ratios[0] > 3:  # Tấm mỏng
                    part_type = "sheet"
                    part_name = f"Sheet {width:.0f}x{height:.0f}x{depth:.0f}mm"
                elif aspect_ratios[0] < 2 and aspect_ratios[1] < 2:  # Khối vuông/tròn
                    part_type = "block"
                    part_name = f"Block {width:.0f}x{height:.0f}x{depth:.0f}mm"
                elif min(aspect_ratios) > 3:  # Ống/thanh dài
                    part_type = "tube"
                    part_name = f"Tube/Rod {width:.0f}x{height:.0f}x{depth:.0f}mm"
                else:
                    part_type = "general"
                    part_name = f"Part {width:.0f}x{height:.0f}x{depth:.0f}mm"

                print(f"Detected part type: {part_type} - {part_name}")
                print(f"Dimensions: {width:.1f} x {height:.1f} x {depth:.1f}")
                print(f"Aspect ratios: {aspect_ratios[0]:.2f}, {aspect_ratios[1]:.2f}")

            # Tính toán auto-scaling và positioning
            # Drawing area available: width=267, height=190 (từ template)
            drawing_area_width = 267
            drawing_area_height = 190

            if bbox:
                # Tính toán kích thước thực tế
                actual_width = bbox.XMax - bbox.XMin
                actual_height = bbox.YMax - bbox.YMin
                actual_depth = bbox.ZMax - bbox.ZMin

                # Tính scale factor để fit geometry trong drawing area
                max_dimension = max(actual_width, actual_height)

                # Dành không gian cho dimensions và text (giảm xuống 40mm mỗi bên)
                margin_for_dimensions = 40
                available_width = drawing_area_width - margin_for_dimensions
                available_height = drawing_area_height - margin_for_dimensions

                # Tính scale factor dựa trên cả width và height
                scale_x = available_width / actual_width if actual_width > 0 else 1.0
                scale_y = available_height / actual_height if actual_height > 0 else 1.0

                # Chọn scale factor nhỏ hơn để đảm bảo fit cả 2 chiều
                auto_scale = min(scale_x, scale_y)

                # Giới hạn scale factor trong khoảng hợp lý và conservative hơn
                auto_scale = max(0.15, min(auto_scale, 1.5))

                # Thêm safety factor để đảm bảo không tràn (dimensions + text + spacing)
                auto_scale *= 0.45  # Tăng scale factor để views lớn hơn

                # Tính font size cho dimensions (thống nhất cho tất cả số)
                base_font_size = 4.0  # Giảm kích thước font dimension xuống một chút
                dimension_font_size = base_font_size / auto_scale
                dimension_font_size = max(3.5, min(dimension_font_size, 7.0))  # Giảm giới hạn tương ứng

                # Tính vị trí dựa trên drawing area thực tế
                # Drawing area: x=20, y=10, width=267, height=190 (từ template)
                drawing_start_x = 20
                drawing_start_y = 10

                # Tính kích thước scaled của từng view
                top_view_width = actual_width * auto_scale
                top_view_height = actual_height * auto_scale
                side_view_width = actual_width * auto_scale
                side_view_height = actual_depth * auto_scale
                front_view_width = actual_height * auto_scale
                front_view_height = actual_depth * auto_scale

                # Tính margin và reserved areas - giảm thêm để tận dụng không gian
                margin_for_dims = 15      # Margin nhỏ hơn nữa cho dimensions
                text_height = 8           # Chiều cao text labels nhỏ hơn
                dimension_space = 10      # Space nhỏ hơn nữa cho dimension lines
                title_block_height = 50   # Reserved space cho title block

                # Tính effective drawing area (tránh title block)
                effective_height = drawing_area_height - title_block_height - margin_for_dims
                effective_width = drawing_area_width - 2 * margin_for_dims

                # Tính total space cần thiết cho tất cả views + dimensions
                total_views_width = top_view_width + side_view_width + dimension_space * 2
                total_views_height = top_view_height + front_view_height + dimension_space * 2

                # Tính spacing để distribute evenly trong available space - giảm thêm
                horizontal_spacing = max(10, (effective_width - total_views_width) / 3)
                vertical_spacing = max(15, (effective_height - total_views_height) / 3)

                # Đảm bảo spacing không quá lớn (để tránh views quá xa nhau)
                horizontal_spacing = min(horizontal_spacing, 20)
                vertical_spacing = min(vertical_spacing, 30)

                # Right Side View: Góc trên trái với margin an toàn (đổi chỗ với Top View)
                side_view_x = drawing_start_x + margin_for_dims + horizontal_spacing
                side_view_y = drawing_start_y + margin_for_dims + text_height + vertical_spacing

                # Front View: Bên phải Right View với spacing an toàn
                front_view_x = side_view_x + side_view_width + dimension_space + horizontal_spacing
                front_view_y = side_view_y  # Cùng baseline với Right View

                # Top View: Dưới Right View với spacing an toàn, tránh title block (đổi chỗ với Right View)
                top_view_x = side_view_x  # Alignment với Right View
                top_view_y = side_view_y + side_view_height + dimension_space + vertical_spacing

                # Kiểm tra và điều chỉnh nếu Top View quá gần title block (đổi chỗ với Right View)
                max_top_y = drawing_start_y + drawing_area_height - title_block_height - margin_for_dims
                if top_view_y + top_view_height > max_top_y:
                    top_view_y = max_top_y - top_view_height - 10  # 10mm buffer

                print(f"Auto-scaling: max_dimension={max_dimension:.1f}, scale={auto_scale:.3f}")
                print(f"Positions: side=({side_view_x:.1f},{side_view_y:.1f}), front=({front_view_x:.1f},{front_view_y:.1f}), top=({top_view_x:.1f},{top_view_y:.1f})")
                print(f"Drawing area: x={drawing_start_x}, y={drawing_start_y}, width={drawing_area_width}, height={drawing_area_height}")
                print(f"Top View boundaries: x={top_view_x:.1f}, y={top_view_y:.1f} to y={top_view_y + actual_height * auto_scale:.1f}")
            else:
                # Fallback values với conservative layout
                auto_scale = 0.5  # Scale nhỏ hơn để an toàn
                dimension_font_size = 4.0  # Giảm kích thước font dimension xuống một chút
                drawing_start_x = 20
                drawing_start_y = 10

                # Fallback dimensions (giả sử part 50x50x5)
                fallback_width = 50 * auto_scale
                fallback_height = 50 * auto_scale
                fallback_depth = 5 * auto_scale

                margin_for_dims = 15
                text_height = 8
                dimension_space = 10
                title_block_height = 50
                horizontal_spacing = 15
                vertical_spacing = 20

                top_view_x = drawing_start_x + margin_for_dims + horizontal_spacing
                top_view_y = drawing_start_y + margin_for_dims + text_height + vertical_spacing
                side_view_x = drawing_start_x + margin_for_dims + horizontal_spacing
                side_view_y = drawing_start_y + margin_for_dims + text_height + vertical_spacing
                front_view_x = side_view_x + fallback_width + dimension_space + horizontal_spacing
                front_view_y = side_view_y
                top_view_x = side_view_x
                top_view_y = min(side_view_y + fallback_depth + dimension_space + vertical_spacing,
                                 drawing_start_y + 190 - title_block_height - margin_for_dims - fallback_height)

            drawing_content = f'''
  <!-- Drawing content -->
  <!-- Center marks for alignment -->
  <g stroke="red" stroke-width="0.2" fill="none" opacity="0.3">
    <!-- Right view center mark -->
    <line x1="{side_view_x-5}" y1="{side_view_y}" x2="{side_view_x+5}" y2="{side_view_y}"/>
    <line x1="{side_view_x}" y1="{side_view_y-5}" x2="{side_view_x}" y2="{side_view_y+5}"/>
    <!-- Front view center mark -->
    <line x1="{front_view_x-5}" y1="{front_view_y}" x2="{front_view_x+5}" y2="{front_view_y}"/>
    <line x1="{front_view_x}" y1="{front_view_y-5}" x2="{front_view_x}" y2="{front_view_y+5}"/>
    <!-- Top view center mark -->
    <line x1="{top_view_x-5}" y1="{top_view_y}" x2="{top_view_x+5}" y2="{top_view_y}"/>
    <line x1="{top_view_x}" y1="{top_view_y-5}" x2="{top_view_x}" y2="{top_view_y+5}"/>
  </g>

  <!-- Top view -->
  <g id="top_view" transform="translate({top_view_x},{top_view_y}) scale({auto_scale})">
'''

            # Vẽ geometry vào drawing content
            if edges:
                for i, edge in enumerate(edges):
                    try:
                        # Kiểm tra loại edge
                        curve = edge.Curve
                        curve_type = str(type(curve)).split('.')[-1].replace("'>", "")
                        print(f"Edge {i}: {curve_type}")

                        if curve_type == "Line":
                            # Xử lý đường thẳng
                            if hasattr(edge, 'Vertexes') and len(edge.Vertexes) >= 2:
                                start = edge.Vertexes[0].Point
                                end = edge.Vertexes[1].Point

                                # Project lên XY plane - vẽ hình xuống dưới trục tọa độ
                                x1 = start.x   # X: từ trái sang phải
                                y1 = start.y   # Y: xuống dưới (y>0 trong SVG)
                                x2 = end.x     # X: từ trái sang phải
                                y2 = end.y     # Y: xuống dưới

                                drawing_content += f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="black" stroke-width="0.5"/>\n'

                        elif curve_type == "Circle":
                            # Kiểm tra xem đây là circle hoàn chỉnh hay chỉ là arc (bo góc)
                            center = curve.Center
                            radius = curve.Radius

                            # Kiểm tra góc của edge để phân biệt circle và arc
                            if hasattr(edge, 'FirstParameter') and hasattr(edge, 'LastParameter'):
                                first_param = edge.FirstParameter
                                last_param = edge.LastParameter
                                angle_span = abs(last_param - first_param)

                                # Project center lên XY plane - vẽ hình xuống dưới
                                cx = center.x   # X: từ trái sang phải
                                cy = center.y   # Y: xuống dưới (y>0 trong SVG)

                                if angle_span >= 6.28:  # 2π (full circle) - chính xác hơn
                                    # Đây là lỗ tròn hoàn chỉnh
                                    drawing_content += f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                    print(f"  Full Circle (hole): center=({cx:.2f},{cy:.2f}), radius={radius:.2f}")
                                else:
                                    # Đây là arc (bo góc) - sử dụng actual vertex positions
                                    if hasattr(edge, 'Vertexes') and len(edge.Vertexes) >= 2:
                                        # Lấy điểm bắt đầu và kết thúc thực tế từ edge
                                        start_point = edge.Vertexes[0].Point
                                        end_point = edge.Vertexes[1].Point

                                        # Project lên XY plane - vẽ hình xuống dưới
                                        start_x = start_point.x   # X: từ trái sang phải
                                        start_y = start_point.y   # Y: xuống dưới
                                        end_x = end_point.x       # X: từ trái sang phải
                                        end_y = end_point.y       # Y: xuống dưới

                                        # Tính sweep direction dựa trên geometry thực tế
                                        # Vector từ center đến start point trong coordinate system mới
                                        start_vec_x = start_point.x - center.x
                                        start_vec_y = start_point.y - center.y
                                        end_vec_x = end_point.x - center.x
                                        end_vec_y = end_point.y - center.y

                                        # Cross product để xác định direction
                                        # Vì Y axis không flip nữa, cần điều chỉnh logic
                                        cross_z = start_vec_x * end_vec_y - start_vec_y * end_vec_x
                                        sweep_flag = 1 if cross_z > 0 else 0  # Đảo ngược logic cho coordinate system mới

                                        # Large arc flag
                                        large_arc = 1 if angle_span > math.pi else 0

                                        drawing_content += f'    <path d="M {start_x:.2f},{start_y:.2f} A {radius:.2f},{radius:.2f} 0 {large_arc},{sweep_flag} {end_x:.2f},{end_y:.2f}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                        print(f"  Arc (fillet): center=({cx:.2f},{cy:.2f}), radius={radius:.2f}, angle={math.degrees(angle_span):.1f}°, sweep={sweep_flag}, large={large_arc}")
                                        print(f"    Start: ({start_x:.2f},{start_y:.2f}), End: ({end_x:.2f},{end_y:.2f})")
                                    else:
                                        # Fallback: sử dụng parameter-based calculation
                                        start_angle = first_param
                                        end_angle = last_param

                                        start_x = cx + radius * math.cos(start_angle)
                                        start_y = cy + radius * math.sin(start_angle)  # Y: xuống dưới
                                        end_x = cx + radius * math.cos(end_angle)
                                        end_y = cy + radius * math.sin(end_angle)

                                        large_arc = 1 if angle_span > math.pi else 0
                                        # Tính sweep direction cho fallback case
                                        if end_angle > start_angle:
                                            sweep_flag = 1  # Clockwise
                                        else:
                                            sweep_flag = 0  # Counterclockwise

                                        drawing_content += f'    <path d="M {start_x:.2f},{start_y:.2f} A {radius:.2f},{radius:.2f} 0 {large_arc},{sweep_flag} {end_x:.2f},{end_y:.2f}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                        print(f"  Arc (fillet fallback): center=({cx:.2f},{cy:.2f}), radius={radius:.2f}, angle={math.degrees(angle_span):.1f}°")
                            else:
                                # Fallback: vẽ như circle - hình xuống dưới
                                cx = center.x   # X: từ trái sang phải
                                cy = center.y   # Y: xuống dưới
                                drawing_content += f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                print(f"  Circle (fallback): center=({cx:.2f},{cy:.2f}), radius={radius:.2f}")

                        elif curve_type in ["BSplineCurve", "BezierCurve"]:
                            # Xử lý đường cong B-spline/Bezier bằng cách discretize
                            try:
                                # Lấy các điểm trên đường cong
                                points = edge.discretize(20)  # 20 điểm
                                path_data = ""
                                for j, point in enumerate(points):
                                    x = point.x   # X: từ trái sang phải
                                    y = point.y   # Y: xuống dưới
                                    if j == 0:
                                        path_data += f"M {x:.2f},{y:.2f}"
                                    else:
                                        path_data += f" L {x:.2f},{y:.2f}"

                                drawing_content += f'    <path d="{path_data}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                print(f"  Curve discretized with {len(points)} points")
                            except:
                                print(f"  Failed to discretize curve")

                        elif curve_type == "Ellipse":
                            # Xử lý ellipse
                            try:
                                center = curve.Center
                                major_radius = curve.MajorRadius
                                minor_radius = curve.MinorRadius

                                cx = center.x   # X: từ trái sang phải
                                cy = center.y   # Y: xuống dưới

                                drawing_content += f'    <ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{major_radius:.2f}" ry="{minor_radius:.2f}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                print(f"  Ellipse: center=({cx:.2f},{cy:.2f}), rx={major_radius:.2f}, ry={minor_radius:.2f}")
                            except:
                                print(f"  Failed to process ellipse")

                        else:
                            # Fallback: discretize bất kỳ đường cong nào khác
                            try:
                                points = edge.discretize(20)
                                if len(points) >= 2:
                                    path_data = ""
                                    for j, point in enumerate(points):
                                        x = point.x   # X: từ trái sang phải
                                        y = point.y   # Y: xuống dưới
                                        if j == 0:
                                            path_data += f"M {x:.2f},{y:.2f}"
                                        else:
                                            path_data += f" L {x:.2f},{y:.2f}"

                                    drawing_content += f'    <path d="{path_data}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                                    print(f"  Unknown curve type discretized with {len(points)} points")
                            except Exception as e2:
                                print(f"  Failed to process unknown curve: {e2}")

                    except Exception as e:
                        print(f"Lỗi xử lý edge {i}: {e}")
            else:
                # Fallback: vẽ hình chữ nhật - hình xuống dưới
                if bbox:
                    fallback_width = bbox.XMax - bbox.XMin
                    fallback_height = bbox.YMax - bbox.YMin
                    drawing_content += f'    <rect x="0" y="0" width="{fallback_width}" height="{fallback_height}" fill="none" stroke="black" stroke-width="0.5"/>\n'
                else:
                    drawing_content += '    <rect x="0" y="0" width="50" height="50" fill="none" stroke="black" stroke-width="0.5"/>\n'

            # Tạo dimensions tự động dựa trên geometry thực tế
            if bbox:

                # Tìm tâm của các lỗ tròn thực sự (không phải bo góc) và các bo góc
                hole_centers = []
                hole_radii = []
                fillet_centers = []
                fillet_radii = []
                unique_fillet_radii = []  # Để theo dõi các bán kính bo góc duy nhất

                if edges:
                    for i, edge in enumerate(edges):
                        try:
                            curve = edge.Curve
                            curve_type = str(type(curve)).split('.')[-1].replace("'>", "")
                            if curve_type == "Circle":
                                # Kiểm tra xem đây có phải là circle hoàn chỉnh không
                                if hasattr(edge, 'FirstParameter') and hasattr(edge, 'LastParameter'):
                                    first_param = edge.FirstParameter
                                    last_param = edge.LastParameter
                                    angle_span = abs(last_param - first_param)

                                    if angle_span >= 6.28:  # 2π (full circle) - đây là lỗ thực sự
                                        center = curve.Center
                                        radius = curve.Radius
                                        hole_centers.append((center.x, center.y))  # Hình xuống dưới
                                        hole_radii.append(radius)
                                    else:  # Đây là arc (bo góc)
                                        center = curve.Center
                                        radius = curve.Radius
                                        fillet_centers.append((center.x, center.y))
                                        fillet_radii.append(radius)

                                        # Thêm vào danh sách bán kính duy nhất nếu chưa có
                                        radius_rounded = round(radius, 2)  # Làm tròn để so sánh
                                        if radius_rounded not in unique_fillet_radii:
                                            unique_fillet_radii.append(radius_rounded)
                        except:
                            pass

                drawing_content += f'''
    <!-- Dimensions for Top View (Auto-generated) - hình vẽ xuống dưới -->
    <g stroke="blue" stroke-width="0.25" fill="none">
      <!-- Width dimension -->
      <line x1="0" y1="-10" x2="{actual_width}" y2="-10"/>
      <line x1="0" y1="-8" x2="0" y2="-2" stroke-width="0.18"/>
      <line x1="{actual_width}" y1="-8" x2="{actual_width}" y2="-2" stroke-width="0.18"/>
      <polygon points="0,-10 1.0,-9 1.0,-11" fill="blue"/>
      <polygon points="{actual_width},-10 {actual_width-1.0},-9 {actual_width-1.0},-11" fill="blue"/>
      <text x="{actual_width/2}" y="-17" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}" text-anchor="middle">{actual_width:.0f}</text>

      <!-- Height dimension -->
      <line x1="{actual_width + 10}" y1="0" x2="{actual_width + 10}" y2="{actual_height}"/>
      <line x1="{actual_width + 8}" y1="0" x2="{actual_width + 2}" y2="0" stroke-width="0.18"/>
      <line x1="{actual_width + 8}" y1="{actual_height}" x2="{actual_width + 2}" y2="{actual_height}" stroke-width="0.18"/>
      <polygon points="{actual_width + 10},0 {actual_width + 9},1.0 {actual_width + 11},1.0" fill="blue"/>
      <polygon points="{actual_width + 10},{actual_height} {actual_width + 9},{actual_height-1.0} {actual_width + 11},{actual_height-1.0}" fill="blue"/>
      <text x="{actual_width + 17}" y="{actual_height/2}" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}" text-anchor="middle" transform="rotate(-90,{actual_width + 17},{actual_height/2})">{actual_height:.0f}</text>'''

                # Thêm dimensions cho lỗ (nếu có) - hình vẽ xuống dưới
                if hole_centers and hole_radii:
                    for i, ((hx, hy), hr) in enumerate(zip(hole_centers, hole_radii)):
                        drawing_content += f'''
      <!-- Hole {i+1} diameter dimension -->
      <line x1="{hx + hr*0.7}" y1="{hy + hr*0.7}" x2="{hx + hr*0.7 + 10}" y2="{hy + hr*0.7 + 10}"/>
      <polygon points="{hx + hr*0.7 + 10},{hy + hr*0.7 + 10} {hx + hr*0.7 + 9.0},{hy + hr*0.7 + 9.5} {hx + hr*0.7 + 9.0},{hy + hr*0.7 + 10.5}" fill="blue"/>
      <text x="{hx + hr*0.7 + 13}" y="{hy + hr*0.7 + 7}" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}">Ø{hr*2:.0f}</text>'''

                # Thêm dimensions cho bán kính bo góc (chỉ hiển thị 1 lần cho mỗi bán kính duy nhất)
                if unique_fillet_radii and fillet_centers and fillet_radii:
                    print(f"Adding radius dimensions for {len(unique_fillet_radii)} unique fillet radii")
                    # Tìm vị trí tốt nhất để đặt dimension cho mỗi bán kính duy nhất
                    for i, unique_radius in enumerate(unique_fillet_radii):
                        # Tìm bo góc đầu tiên có bán kính này
                        for j, ((fx, fy), fr) in enumerate(zip(fillet_centers, fillet_radii)):
                            if abs(fr - unique_radius) < 0.01:  # So sánh với tolerance
                                # Tính vị trí dimension line cho bo góc này
                                # Đặt dimension ở góc 45 độ từ tâm bo góc để tránh chồng lấp
                                dim_offset = fr + 8  # Khoảng cách từ tâm đến dimension line
                                dim_x = fx + dim_offset * 0.707  # cos(45°) ≈ 0.707
                                dim_y = fy + dim_offset * 0.707  # sin(45°) ≈ 0.707

                                # Vẽ dimension line từ điểm dimension về tâm bo góc với mũi tên chỉ vào tâm
                                # Tính vector hướng từ text về tâm để vẽ mũi tên đúng hướng
                                arrow_vec_x = fx - dim_x
                                arrow_vec_y = fy - dim_y
                                arrow_length = (arrow_vec_x**2 + arrow_vec_y**2)**0.5

                                # Normalize vector và tính điểm mũi tên
                                if arrow_length > 0:
                                    arrow_unit_x = arrow_vec_x / arrow_length
                                    arrow_unit_y = arrow_vec_y / arrow_length

                                    # Mũi tên chỉ vào tâm bo góc
                                    arrow_tip_x = fx
                                    arrow_tip_y = fy
                                    arrow_base_x = fx - arrow_unit_x * 2.0
                                    arrow_base_y = fy - arrow_unit_y * 2.0

                                    # Tính điểm cánh mũi tên (perpendicular)
                                    perp_x = -arrow_unit_y * 0.8
                                    perp_y = arrow_unit_x * 0.8

                                    arrow_wing1_x = arrow_base_x + perp_x
                                    arrow_wing1_y = arrow_base_y + perp_y
                                    arrow_wing2_x = arrow_base_x - perp_x
                                    arrow_wing2_y = arrow_base_y - perp_y

                                drawing_content += f'''
      <!-- Fillet radius dimension R{unique_radius:.0f} -->
      <line x1="{dim_x}" y1="{dim_y}" x2="{fx}" y2="{fy}" stroke="blue" stroke-width="0.25"/>
      <polygon points="{arrow_tip_x},{arrow_tip_y} {arrow_wing1_x},{arrow_wing1_y} {arrow_wing2_x},{arrow_wing2_y}" fill="blue"/>
      <text x="{dim_x + 2}" y="{dim_y - 1}" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}">R{unique_radius:.0f}</text>'''
                                print(f"Added radius dimension R{unique_radius:.0f} at fillet center ({fx:.1f},{fy:.1f})")
                                break  # Chỉ vẽ dimension cho bo góc đầu tiên có bán kính này

                # Thêm center lines cho lỗ - hình vẽ xuống dưới
                if hole_centers:
                    drawing_content += '''
      <!-- Center lines for holes -->
      <g stroke="gray" stroke-width="0.25" stroke-dasharray="6,0.75,0.125,0.75">'''
                    for hx, hy in hole_centers:
                        drawing_content += f'''
        <line x1="{hx-10}" y1="{hy}" x2="{hx+10}" y2="{hy}"/>
        <line x1="{hx}" y1="{hy-10}" x2="{hx}" y2="{hy+10}"/>'''
                    drawing_content += '''
      </g>'''

                # Close the dimensions group
                drawing_content += '''
    </g>
  </g>'''
            else:
                # Fallback dimensions
                drawing_content += f'''
    <!-- Fallback Dimensions -->
    <g stroke="blue" stroke-width="0.35" fill="none">
      <line x1="0" y1="10" x2="50" y2="10"/>
      <polygon points="0,10 1.0,9 1.0,11" fill="blue"/>
      <polygon points="50,10 49.0,9 49.0,11" fill="blue"/>
      <text x="25" y="17" font-family="osifont" font-size="{dimension_font_size:.1f}" text-anchor="middle">50</text>
    </g>
  </g>'''

            # Thêm Right Side View
            drawing_content += f'''
  <!-- Right side view showing thickness -->
  <g id="side_view" transform="translate({side_view_x},{side_view_y}) scale({auto_scale})">'''

            # Tự động tạo Right Side View dựa trên geometry
            if bbox:
                side_width = actual_width
                side_height = actual_depth
                # Vẽ trên trục tọa độ (y âm vì SVG Y axis flipped)
                side_y_offset = -side_height
                drawing_content += f'''
    <rect x="0" y="{side_y_offset}" width="{side_width}" height="{side_height}" fill="none" stroke="black" stroke-width="0.7"/>'''

                # Thêm lỗ như hidden lines (nếu có)
                if hole_centers and hole_radii:
                    for (hx, hy), hr in zip(hole_centers, hole_radii):
                        drawing_content += f'''
    <line x1="{hx-hr}" y1="{side_y_offset}" x2="{hx+hr}" y2="{side_y_offset}" stroke="gray" stroke-width="0.25" stroke-dasharray="3,1"/>
    <line x1="{hx-hr}" y1="0" x2="{hx+hr}" y2="0" stroke="gray" stroke-width="0.25" stroke-dasharray="3,1"/>'''

                # Thickness dimension
                drawing_content += f'''
    <!-- Thickness dimension -->
    <g stroke="blue" stroke-width="0.35" fill="none">
      <line x1="{side_width + 5}" y1="{side_y_offset}" x2="{side_width + 5}" y2="0"/>
      <line x1="{side_width + 3}" y1="{side_y_offset}" x2="{side_width + 7}" y2="{side_y_offset}"/>
      <line x1="{side_width + 3}" y1="0" x2="{side_width + 7}" y2="0"/>
      <polygon points="{side_width + 5},{side_y_offset} {side_width + 4.5},{side_y_offset + 1.0} {side_width + 5.5},{side_y_offset + 1.0}" fill="blue"/>
      <polygon points="{side_width + 5},0 {side_width + 4.5},-1.0 {side_width + 5.5},-1.0" fill="blue"/>
      <text x="{side_width + 12}" y="{side_y_offset/2}" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}" text-anchor="middle" transform="rotate(-90,{side_width + 12},{side_y_offset/2})">{side_height:.0f}</text>
    </g>'''
            else:
                # Fallback - vẽ trên trục tọa độ
                fallback_side_height = 3
                fallback_y_offset = -fallback_side_height
                drawing_content += f'''
    <rect x="0" y="{fallback_y_offset}" width="50" height="{fallback_side_height}" fill="none" stroke="black" stroke-width="0.7"/>
    <g stroke="blue" stroke-width="0.35" fill="none">
      <text x="37" y="{fallback_y_offset/2}" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}" text-anchor="middle" transform="rotate(-90,37,{fallback_y_offset/2})">3</text>
    </g>'''

            # Sử dụng string formatting để đảm bảo variables được thay thế đúng
            front_view_transform = f"translate({front_view_x},{front_view_y}) scale({auto_scale})"
            drawing_content += f'''
  </g>

  <!-- Front view -->
  <g id="front_view" transform="{front_view_transform}">'''

            # Tự động tạo Front View dựa trên geometry - vẽ hướng lên
            if bbox:
                front_width = actual_height  # Xoay 90 độ so với top view
                front_height = actual_depth
                # Vẽ hướng lên (y âm)
                drawing_content += f'''
    <rect x="0" y="-{front_height}" width="{front_width}" height="{front_height}" fill="none" stroke="black" stroke-width="0.7"/>'''

                # Thêm lỗ như hidden lines (nếu có)
                if hole_centers and hole_radii:
                    for (hx, hy), hr in zip(hole_centers, hole_radii):
                        # Trong front view, lỗ xuất hiện tại vị trí Y của top view
                        hole_y_in_front = hy  # Sử dụng Y coordinate từ top view
                        drawing_content += f'''
    <line x1="{hole_y_in_front-hr}" y1="-{front_height}" x2="{hole_y_in_front+hr}" y2="-{front_height}" stroke="gray" stroke-width="0.35" stroke-dasharray="3,1"/>
    <line x1="{hole_y_in_front-hr}" y1="0" x2="{hole_y_in_front+hr}" y2="0" stroke="gray" stroke-width="0.35" stroke-dasharray="3,1"/>'''

                # Width dimension cho front view
                drawing_content += f'''
    <!-- Width dimension -->
    <g stroke="blue" stroke-width="0.35" fill="none">
      <line x1="0" y1="5" x2="{front_width}" y2="5"/>
      <line x1="0" y1="3" x2="0" y2="-1"/>
      <line x1="{front_width}" y1="3" x2="{front_width}" y2="-1"/>
      <polygon points="0,5 1.0,4 1.0,6" fill="blue"/>
      <polygon points="{front_width},5 {front_width-1.0},4 {front_width-1.0},6" fill="blue"/>
      <text x="{front_width/2}" y="10" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}" text-anchor="middle">{front_width:.0f}</text>
    </g>'''
            else:
                # Fallback - vẽ hướng lên
                fallback_front_height = 3
                drawing_content += f'''
    <rect x="0" y="-{fallback_front_height}" width="50" height="{fallback_front_height}" fill="none" stroke="black" stroke-width="0.7"/>
    <g stroke="blue" stroke-width="0.35" fill="none">
      <text x="25" y="10" font-family="Arial, sans-serif" font-size="{dimension_font_size:.1f}" text-anchor="middle">50</text>
    </g>'''

            drawing_content += f'''
  </g>

'''

            # Cập nhật title block với thông tin part tự động
            if bbox:
                # Tạo mô tả part
                part_description = f"{actual_width:.0f}x{actual_height:.0f}x{actual_depth:.0f}mm"
                if hole_centers and hole_radii:
                    hole_desc = ", ".join([f"Ø{hr*2:.0f}mm hole" for hr in hole_radii])
                    part_description += f" with {hole_desc}"

                # Không thêm custom title data nữa
                drawing_content += '''

'''
            else:
                # Không thêm fallback title data nữa
                drawing_content += '''

'''

            # Chèn drawing content vào template (trước thẻ đóng </svg>)
            svg_content = svg_content.replace('</svg>', drawing_content + '</svg>')

        except Exception as e:
            print(f"Lỗi khi tạo SVG từ geometry: {e}")
            # Fallback SVG với lỗ tròn
            svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">
  <!-- Page border -->
  <rect x="5" y="5" width="287" height="200" fill="none" stroke="black" stroke-width="0.5"/>

  <!-- Title block -->
  <rect x="200" y="170" width="87" height="30" fill="none" stroke="black" stroke-width="0.5"/>
  <text x="205" y="185" font-family="Arial" font-size="8">Sheet Drawing (Fallback)</text>
  <text x="205" y="195" font-family="Arial" font-size="6">50x50x3mm with Ø12 hole</text>

  <!-- Main view -->
  <g transform="translate(150,105)">
    <rect x="-25" y="-25" width="50" height="50" fill="none" stroke="black" stroke-width="1"/>
    <circle cx="0" cy="0" r="6" fill="none" stroke="black" stroke-width="1"/>
    <text x="0" y="-35" font-family="Arial" font-size="8" text-anchor="middle">Top View</text>
  </g>
</svg>'''

    # Tạo thư mục output nếu chưa có
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Ghi file SVG vào thư mục output
    output_path = os.path.join(output_dir, "sheet_drawing.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Đã tạo file SVG thành công: {output_path}")

except Exception as e:
    print(f"Lỗi khi tạo SVG: {e}")

# Không lưu project FreeCAD - chỉ cần file SVG

print("Script hoàn thành!")
