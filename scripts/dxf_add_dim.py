# scripts/dxf_add_dim_enhanced_v2.py
import ezdxf
import json
import math
import sys
from pathlib import Path
from ezdxf.math import Vec2, Vec3
from ezdxf.tools.standards import setup_dimstyle
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Set, Optional
import itertools

class AdvancedDimStyles:
    """Create advanced dimstyles with custom fonts and arrows"""
    
    @staticmethod
    def create_fusion_style_dimstyle(doc, name="FUSION_STYLE"):
        """Create a dimstyle similar to Fusion 360"""
        if name in doc.dimstyles:
            return doc.dimstyles.get(name)
            
        dimstyle = doc.dimstyles.new(name)
        
        # === FUSION 360 STYLE SETTINGS ===
        dimstyle.dxf.dimtxt = 2.5      # Text height
        dimstyle.dxf.dimasz = 2.5      # Arrow size
        dimstyle.dxf.dimexe = 1.25     # Extension line extension
        dimstyle.dxf.dimexo = 0.625    # Extension line offset
        dimstyle.dxf.dimgap = 0.625    # Gap around text
        dimstyle.dxf.dimtad = 1        # Text above dimension line
        dimstyle.dxf.dimtih = 0        # Text inside horizontal
        dimstyle.dxf.dimtoh = 0        # Text outside horizontal
        dimstyle.dxf.dimtxsty = "Standard"
        
        # === ARROWS AND STYLE ===
        dimstyle.dxf.dimldrblk = "_ARCHTICK"  # Leader block (Fusion style)
        dimstyle.dxf.dimblk = "_ARCHTICK"     # Arrow block
        dimstyle.dxf.dimblk1 = "_ARCHTICK"    # First arrow  
        dimstyle.dxf.dimblk2 = "_ARCHTICK"    # Second arrow
        
        # === COLORS ===
        dimstyle.dxf.dimclrd = 7         # Dimension line color (white/black)
        dimstyle.dxf.dimclre = 7         # Extension line color
        dimstyle.dxf.dimclrt = 7         # Text color
        
        # === PRECISION & UNITS ===
        dimstyle.dxf.dimunit = 2         # Decimal units
        dimstyle.dxf.dimdec = 1          # 1 decimal place (like Fusion)
        dimstyle.dxf.dimlunit = 2        # Linear units (decimal)
        dimstyle.dxf.dimdsep = ord('.')  # Decimal separator
        
        # === TEXT FORMATTING ===
        dimstyle.dxf.dimtfac = 1.0       # Text scale factor
        dimstyle.dxf.dimscale = 1.0      # Overall scale
        dimstyle.dxf.dimlfac = 1.0       # Linear scale factor
        
        return dimstyle

class IntelligentViewDetector:
    """Detect views intelligently like Fusion 360"""
    
    def __init__(self, tolerance=5.0):
        self.tolerance = tolerance
        self.view_characteristics = {}
        
    def analyze_and_classify_views(self, entities):
        """Analyze and classify views like Fusion 360"""
        # Calculate geometric features
        geometry_features = self._extract_geometry_features(entities)
        
        # Detect views based on density and distribution
        view_regions = self._detect_view_regions(entities)
        
        # Classify each view
        classified_views = {}
        for region_name, entities_in_region in view_regions.items():
            view_type = self._classify_view_type(entities_in_region, geometry_features)
            classified_views[region_name] = {
                'entities': entities_in_region,
                'type': view_type,
                'priority': self._get_view_priority(view_type),
                'bbox': self._get_entities_bbox(entities_in_region)
            }
            
        return classified_views
    
    def _extract_geometry_features(self, entities):
        """Extract geometric features"""
        features = {
            'total_lines': 0,
            'horizontal_lines': 0,
            'vertical_lines': 0,
            'diagonal_lines': 0,
            'circles': 0,
            'arcs': 0,
            'angle_distribution': Counter(),
            'length_distribution': Counter()
        }
        
        for entity in entities:
            if entity.dxftype() == 'LINE':
                features['total_lines'] += 1
                start = Vec2(entity.dxf.start)
                end = Vec2(entity.dxf.end)
                
                direction = end - start
                if direction.magnitude < self.tolerance:
                    continue
                
                angle = math.degrees(math.atan2(direction.y, direction.x))
                angle = abs(angle) % 180  # Normalize to [0, 180)
                
                # Classify angles
                if angle < 10 or angle > 170:
                    features['horizontal_lines'] += 1
                elif 80 < angle < 100:
                    features['vertical_lines'] += 1
                else:
                    features['diagonal_lines'] += 1
                
                # Angle and length statistics
                angle_bucket = round(angle / 15) * 15  # Group by 15°
                features['angle_distribution'][angle_bucket] += 1
                
                length_bucket = round(direction.magnitude / 10) * 10  # Group by 10mm
                features['length_distribution'][length_bucket] += 1
                
            elif entity.dxftype() == 'CIRCLE':
                features['circles'] += 1
            elif entity.dxftype() == 'ARC':
                features['arcs'] += 1
        
        return features
    
    def _detect_view_regions(self, entities):
        """Detect view regions automatically"""
        if not entities:
            return {}
        
        # Get all points
        all_points = []
        for entity in entities:
            points = self._get_entity_points(entity)
            all_points.extend(points)
        
        if not all_points:
            return {}
        
        # Calculate overall bounding box
        xs = [p.x for p in all_points]
        ys = [p.y for p in all_points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Split into a smart grid (2x2 or 3x2 depending on aspect ratio)
        width = max_x - min_x
        height = max_y - min_y
        
        if width / height > 1.5:  # Horizontal layout
            regions = self._create_horizontal_regions(min_x, max_x, min_y, max_y)
        else:  # Square or vertical layout
            regions = self._create_grid_regions(min_x, max_x, min_y, max_y)
        
        # Assign entities to regions
        view_regions = {}
        for region_name, (x1, x2, y1, y2) in regions.items():
            entities_in_region = []
            for entity in entities:
                if self._entity_in_region(entity, x1, x2, y1, y2):
                    entities_in_region.append(entity)
            
            if entities_in_region:  # Only save regions with entities
                view_regions[region_name] = entities_in_region
        
        return view_regions
    
    def _create_grid_regions(self, min_x, max_x, min_y, max_y):
        """Create 2x2 grid regions"""
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        
        return {
            'front_view': (min_x, mid_x, mid_y, max_y),
            'side_view': (mid_x, max_x, mid_y, max_y),
            'top_view': (min_x, mid_x, min_y, mid_y),
            'iso_view': (mid_x, max_x, min_y, mid_y)
        }
    
    def _create_horizontal_regions(self, min_x, max_x, min_y, max_y):
        """Create regions for horizontal layout"""
        third_x = (max_x - min_x) / 3
        
        return {
            'front_view': (min_x, min_x + third_x, min_y, max_y),
            'side_view': (min_x + third_x, min_x + 2 * third_x, min_y, max_y),
            'top_view': (min_x + 2 * third_x, max_x, min_y, max_y)
        }
    
    def _get_entity_points(self, entity):
        """Get all points of an entity"""
        points = []
        
        if entity.dxftype() == 'LINE':
            points = [Vec2(entity.dxf.start), Vec2(entity.dxf.end)]
        elif entity.dxftype() == 'CIRCLE':
            center = Vec2(entity.dxf.center)
            radius = entity.dxf.radius
            points = [
                Vec2(center.x - radius, center.y - radius),
                Vec2(center.x + radius, center.y + radius)
            ]
        elif entity.dxftype() == 'ARC':
            center = Vec2(entity.dxf.center)
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            
            points = [
                center,
                Vec2(center.x + radius * math.cos(start_angle), center.y + radius * math.sin(start_angle)),
                Vec2(center.x + radius * math.cos(end_angle), center.y + radius * math.sin(end_angle))
            ]
        
        return points
    
    def _entity_in_region(self, entity, x1, x2, y1, y2):
        """Check if an entity is in a region"""
        points = self._get_entity_points(entity)
        if not points:
            return False
        
        # Entity is in a region if the majority of its points are
        points_in_region = 0
        for point in points:
            if x1 <= point.x <= x2 and y1 <= point.y <= y2:
                points_in_region += 1
        
        return points_in_region > len(points) / 2
    
    def _classify_view_type(self, entities, global_features):
        """Classify view type based on features"""
        if not entities:
            return 'unknown'
        
        local_features = self._extract_geometry_features(entities)
        
        # Ratio of diagonal vs orthogonal lines
        total_lines = local_features['total_lines']
        if total_lines == 0:
            return 'detail'
        
        diagonal_ratio = local_features['diagonal_lines'] / total_lines
        orthogonal_ratio = (local_features['horizontal_lines'] + local_features['vertical_lines']) / total_lines
        
        # Classification logic
        if diagonal_ratio > 0.3:  # Many diagonal lines
            return 'isometric'
        elif local_features['circles'] > 0:  # Has circles
            return 'front'  # Often the front view
        elif orthogonal_ratio > 0.8:  # Mainly orthogonal lines
            # Differentiate top/side based on H/V ratio
            h_ratio = local_features['horizontal_lines'] / total_lines
            v_ratio = local_features['vertical_lines'] / total_lines
            
            if h_ratio > v_ratio * 1.5:
                return 'top'
            elif v_ratio > h_ratio * 1.5:
                return 'side'
            else:
                return 'front'
        else:
            return 'detail'
    
    def _get_view_priority(self, view_type):
        """Dimensioning priority by view type"""
        priority_map = {
            'front': 1,
            'top': 2,
            'side': 3,
            'detail': 4,
            'isometric': 999,  # Do not dimension ISO
            'unknown': 999
        }
        return priority_map.get(view_type, 999)
    
    def _get_entities_bbox(self, entities):
        """Calculate the bounding box of entities"""
        if not entities:
            return None
        
        all_points = []
        for entity in entities:
            points = self._get_entity_points(entity)
            all_points.extend(points)
        
        if not all_points:
            return None
        
        xs = [p.x for p in all_points]
        ys = [p.y for p in all_points]
        
        return (min(xs), max(xs), min(ys), max(ys))

class FusionStyleDimensioner:
    """Fusion 360 style dimensioning system"""
    
    def __init__(self, msp, config):
        self.msp = msp
        self.config = config
        self.doc = msp.doc
        self.tolerance = 1e-3
        
        # Style setup
        self.dimstyle = AdvancedDimStyles.create_fusion_style_dimstyle(self.doc)
        self.style_name = "FUSION_STYLE"
        
        # Tracking to avoid duplication
        self.dimensioned_features = set()
        self.dimension_positions = []
        self.used_lengths = defaultdict(set)  # Track by view
        self.used_diameters = set()
        self.used_radii = set()
        
        # Fusion-style parameters
        self.dim_offset_major = float(config.get('DIMENSION_OFFSET_MAJOR', '40.0'))
        self.dim_offset_minor = float(config.get('DIMENSION_OFFSET_MINOR', '15.0'))
        self.min_dim_spacing = float(config.get('MIN_DIMENSION_SPACING', '25.0'))
        
        # Helper instance for bbox calculations
        self.view_detector = IntelligentViewDetector()
        
    def dimension_all_views(self, classified_views):
        """Dimension all views in priority order"""
        total_dimensions = 0
        
        # Sort views by priority
        sorted_views = sorted(
            classified_views.items(),
            key=lambda x: x[1]['priority']
        )
        
        for view_name, view_data in sorted_views:
            if view_data['priority'] >= 999:  # Skip ISO and unknown
                print(f"[INFO] Skipping {view_name} (type: {view_data['type']})")
                continue
                
            print(f"[INFO] Dimensioning {view_name} (type: {view_data['type']})...")
            count = self._dimension_single_view(
                view_data['entities'], 
                view_name, 
                view_data['type'], 
                view_data['bbox']
            )
            total_dimensions += count
            print(f"[INFO] Added {count} dimensions for {view_name}")
        
        return total_dimensions
    
    def _dimension_single_view(self, entities, view_name, view_type, bbox):
        """Dimension a single view with Fusion-style logic"""
        lines = [e for e in entities if e.dxftype() == 'LINE']
        circles = [e for e in entities if e.dxftype() == 'CIRCLE']
        arcs = [e for e in entities if e.dxftype() == 'ARC']
        
        dimension_count = 0
        
        # === 1. DIMENSION STRATEGY BY VIEW TYPE ===
        if view_type == 'front':
            # Front view: Prioritize width + height + details
            dimension_count += self._dimension_primary_directions(lines, bbox, ['horizontal', 'vertical'])
            dimension_count += self._dimension_circles_as_diameters(circles, bbox)
            dimension_count += self._dimension_key_details(lines, bbox)
            
        elif view_type == 'top':
            # Top view: Prioritize length + width
            dimension_count += self._dimension_primary_directions(lines, bbox, ['horizontal'])
            dimension_count += self._dimension_holes_and_features(circles, arcs, bbox)
            
        elif view_type == 'side':
            # Side view: Prioritize height + depth
            dimension_count += self._dimension_primary_directions(lines, bbox, ['vertical'])
            dimension_count += self._dimension_profile_features(lines, arcs, bbox)
            
        elif view_type == 'detail':
            # Detail view: Dimension all important features
            dimension_count += self._dimension_all_features(entities, bbox)
        
        # === 2. DIMENSION RADII/ARCS ===
        dimension_count += self._dimension_arcs_intelligent(arcs, lines)
        
        # === 3. POSITION DIMENSIONS (from center to edge) ===
        dimension_count += self._dimension_positions(circles, lines, bbox)
        
        return dimension_count
    
    def _dimension_primary_directions(self, lines, bbox, directions):
        """Dimension primary directions with smart logic"""
        count = 0
        
        # Classify lines by direction
        horizontal_lines, vertical_lines, diagonal_lines = self._classify_lines_by_direction(lines)
        
        for direction in directions:
            if direction == 'horizontal':
                count += self._dimension_lines_in_direction(horizontal_lines, 'horizontal', bbox)
            elif direction == 'vertical':
                count += self._dimension_lines_in_direction(vertical_lines, 'vertical', bbox)
        
        return count
    
    def _dimension_lines_in_direction(self, lines, direction, bbox):
        """Dimension lines in a specific direction"""
        if not lines:
            return 0
        
        count = 0
        
        # Group lines by length and position
        length_groups = self._group_lines_by_length(lines)
        
        for length, grouped_lines in length_groups.items():
            if length < self.config.get('MIN_DIMENSION_LENGTH', 5.0):
                continue
            
            # Select a representative line (prioritize lines at the edge)
            representative_line = self._select_representative_line(grouped_lines, direction, bbox)
            
            if representative_line and self._should_dimension_line(representative_line, direction, length):
                # Determine if it's a major dimension
                is_major = self._is_major_dimension(representative_line, direction, bbox)
                
                # Add dimension
                if self._add_smart_linear_dimension(representative_line, direction, is_major, bbox):
                    count += 1
                    self.used_lengths[direction].add(round(length, 1))
        
        return count
    
    def _add_smart_linear_dimension(self, line, direction, is_major, bbox):
        """Add a smart dimension with Fusion-style positioning"""
        start = Vec2(line.dxf.start)
        end = Vec2(line.dxf.end)
        
        # Calculate offset position
        if is_major:
            offset_pos = self._calculate_major_dim_position(start, end, direction, bbox)
        else:
            offset_pos = self._calculate_minor_dim_position(start, end, direction)
        
        # Check for collision with other dimensions
        if self._check_dimension_collision(offset_pos):
            offset_pos = self._find_alternative_position(start, end, direction, offset_pos)
        
        try:
            # Create a dimension with the correct angle
            angle = 0 if direction == 'horizontal' else 90
            
            dim = self.msp.add_linear_dim(
                base=offset_pos,
                p1=(start.x, start.y),
                p2=(end.x, end.y),
                angle=angle,
                dimstyle=self.style_name
            )
            
            # Render and save position
            dim.render()
            self.dimension_positions.append(offset_pos)
            
            return True
            
        except Exception as e:
            print(f"[WARNING] Could not create dimension: {e}")
            return False
    
    def _calculate_major_dim_position(self, start, end, direction, bbox):
        """Calculate position for major dimensions (outside the shape)"""
        if not bbox:
            mid = (start + end) / 2
            return self._get_default_offset_position(mid, direction, self.dim_offset_major)
        
        xmin, xmax, ymin, ymax = bbox
        mid = (start + end) / 2
        
        if direction == 'horizontal':
            # Place above or below the edge
            if abs(mid.y - ymax) < abs(mid.y - ymin):
                return (mid.x, ymax + self.dim_offset_major)
            else:
                return (mid.x, ymin - self.dim_offset_major)
        else:  # vertical
            # Place to the left or right of the edge
            if abs(mid.x - xmax) < abs(mid.x - xmin):
                return (xmax + self.dim_offset_major, mid.y)
            else:
                return (xmin - self.dim_offset_major, mid.y)
    
    def _calculate_minor_dim_position(self, start, end, direction):
        """Calculate position for minor dimensions (inside the shape)"""
        mid = (start + end) / 2
        return self._get_default_offset_position(mid, direction, self.dim_offset_minor)
    
    def _get_default_offset_position(self, point, direction, offset):
        """Get the default offset position"""
        if direction == 'horizontal':
            return (point.x, point.y - offset)
        else:
            return (point.x - offset, point.y)
    
    def _dimension_circles_as_diameters(self, circles, bbox):
        """Dimension circles like Fusion (prioritize diameter)"""
        count = 0
        
        for circle in circles:
            center = Vec2(circle.dxf.center)
            radius = circle.dxf.radius
            diameter = 2 * radius
            
            # Avoid duplicate diameters
            rounded_dia = round(diameter, 1)
            if rounded_dia in self.used_diameters:
                continue
            
            # Find the best position for the diameter dimension
            dim_angle = self._find_best_diameter_angle(center, radius, bbox)
            
            if self._add_diameter_dimension(center, radius, dim_angle):
                count += 1
                self.used_diameters.add(rounded_dia)
        
        return count
    
    def _add_diameter_dimension(self, center, radius, angle_deg):
        """Add a diameter dimension"""
        try:
            angle_rad = math.radians(angle_deg)
            dx = radius * math.cos(angle_rad)
            dy = radius * math.sin(angle_rad)
            mpoint = (center.x + dx, center.y + dy)
            
            # Check for collision
            if self._check_dimension_collision(mpoint):
                return False
            
            dim = self.msp.add_diameter_dim(
                center=(center.x, center.y),
                radius=radius,
                mpoint=mpoint,
                dimstyle=self.style_name
            )
            
            dim.render()
            self.dimension_positions.append(mpoint)
            return True
            
        except Exception as e:
            print(f"[WARNING] Could not create diameter dimension: {e}")
            return False
    
    def _dimension_positions(self, circles, lines, bbox):
        """Dimension position from features to edges (like Fusion)"""
        count = 0
        
        for circle in circles:
            center = Vec2(circle.dxf.center)
            
            # Find the nearest edges
            nearest_h_line = self._find_nearest_line(center, lines, 'horizontal')
            nearest_v_line = self._find_nearest_line(center, lines, 'vertical')
            
            # Dimension from center to horizontal edge
            if nearest_h_line:
                edge_y = nearest_h_line[0][1]  # Y coordinate of the horizontal line
                if abs(center.y - edge_y) > 5.0:  # Minimum distance threshold
                    if self._add_position_dimension(center, (center.x, edge_y), 'vertical'):
                        count += 1
            
            # Dimension from center to vertical edge  
            if nearest_v_line:
                edge_x = nearest_v_line[0][0]  # X coordinate of the vertical line
                if abs(center.x - edge_x) > 5.0:  # Minimum distance threshold
                    if self._add_position_dimension(center, (edge_x, center.y), 'horizontal'):
                        count += 1
        
        return count
    
    def _add_position_dimension(self, p1, p2, direction):
        """Add a position dimension"""
        try:
            # Calculate offset position
            mid = ((p1.x + p2[0]) / 2, (p1.y + p2[1]) / 2)
            
            if direction == 'horizontal':
                offset_pos = (mid[0], mid[1] - self.dim_offset_minor)
            else:
                offset_pos = (mid[0] - self.dim_offset_minor, mid[1])
            
            # Check for collision
            if self._check_dimension_collision(offset_pos):
                return False
            
            angle = 0 if direction == 'horizontal' else 90
            
            dim = self.msp.add_linear_dim(
                base=offset_pos,
                p1=(p1.x, p1.y),
                p2=p2,
                angle=angle,
                dimstyle=self.style_name
            )
            
            dim.render()
            self.dimension_positions.append(offset_pos)
            return True
            
        except Exception as e:
            print(f"[WARNING] Could not create position dimension: {e}")
            return False
    
    # === HELPER METHODS ===
    def _classify_lines_by_direction(self, lines):
        """Classify lines by direction"""
        horizontal = []
        vertical = []
        diagonal = []
        
        for line in lines:
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            direction = end - start
            
            if direction.magnitude < self.tolerance:
                continue
            
            angle = abs(math.degrees(math.atan2(direction.y, direction.x)))
            
            if angle < 10 or angle > 170:
                horizontal.append(line)
            elif 80 < angle < 100:
                vertical.append(line)
            else:
                diagonal.append(line)
        
        return horizontal, vertical, diagonal
    
    def _group_lines_by_length(self, lines):
        """Group lines by length"""
        length_groups = defaultdict(list)
        
        for line in lines:
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            length = round((end - start).magnitude, 1)
            length_groups[length].append(line)
        
        return length_groups
    
    def _select_representative_line(self, lines, direction, bbox):
        """Select a representative line for a group (prioritize outer edges)"""
        if not lines:
            return None
        
        if not bbox:
            return lines[0]
        
        xmin, xmax, ymin, ymax = bbox
        
        # Find the line closest to the edge
        best_line = None
        best_score = float('inf')
        
        for line in lines:
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            mid = (start + end) / 2
            
            if direction == 'horizontal':
                # Prioritize lines near top/bottom edges
                score = min(abs(mid.y - ymax), abs(mid.y - ymin))
            else:
                # Prioritize lines near left/right edges
                score = min(abs(mid.x - xmax), abs(mid.x - xmin))
            
            if score < best_score:
                best_score = score
                best_line = line
        
        return best_line
    
    def _should_dimension_line(self, line, direction, length):
        """Check if this line should be dimensioned"""
        # Check minimum length
        if length < self.config.get('MIN_DIMENSION_LENGTH', 5.0):
            return False
        
        # Check for duplication
        rounded_length = round(length, 1)
        if rounded_length in self.used_lengths[direction]:
            return False
        
        return True
    
    def _is_major_dimension(self, line, direction, bbox):
        """Check if it is a major dimension"""
        if not bbox:
            return False
        
        start = Vec2(line.dxf.start)
        end = Vec2(line.dxf.end)
        length = (end - start).magnitude
        
        xmin, xmax, ymin, ymax = bbox
        view_width = xmax - xmin
        view_height = ymax - ymin
        
        # Major if length >= 70% of view size
        if direction == 'horizontal':
            return length >= 0.7 * view_width
        else:
            return length >= 0.7 * view_height
    
    def _find_best_diameter_angle(self, center, radius, bbox):
        """Find the best angle for a diameter dimension"""
        candidate_angles = [45, 135, -45, -135, 90, -90, 0, 180]
        
        for angle in candidate_angles:
            angle_rad = math.radians(angle)
            dx = radius * math.cos(angle_rad)
            dy = radius * math.sin(angle_rad)
            test_point = (center.x + dx, center.y + dy)
            
            if not self._check_dimension_collision(test_point):
                return angle
        
        return 45  # Default angle
    
    def _find_nearest_line(self, point, lines, direction):
        """Find the nearest line in a given direction"""
        min_distance = float('inf')
        nearest_line = None
        
        for line in lines:
            start = Vec2(line.dxf.start)
            end = Vec2(line.dxf.end)
            
            if direction == 'horizontal':
                # Find a horizontal line
                if abs((end - start).y) < self.tolerance:
                    distance = abs(point.y - start.y)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_line = ((start.x, start.y), (end.x, end.y))
            else:
                # Find a vertical line
                if abs((end - start).x) < self.tolerance:
                    distance = abs(point.x - start.x)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_line = ((start.x, start.y), (end.x, end.y))
        
        return nearest_line
    
    def _check_dimension_collision(self, position, min_distance=None):
        """Check for collision with other dimensions"""
        if min_distance is None:
            min_distance = self.min_dim_spacing
        
        for existing_pos in self.dimension_positions:
            distance = math.sqrt((position[0] - existing_pos[0])**2 + (position[1] - existing_pos[1])**2)
            if distance < min_distance:
                return True
        return False
    
    def _find_alternative_position(self, start, end, direction, original_pos):
        """Find an alternative position when a collision occurs"""
        mid = (start + end) / 2
        
        # Try different offsets
        offsets = [self.dim_offset_minor * 1.5, self.dim_offset_minor * 2.0, self.dim_offset_minor * 2.5]
        
        for offset in offsets:
            if direction == 'horizontal':
                test_positions = [
                    (mid.x, mid.y - offset),
                    (mid.x, mid.y + offset)
                ]
            else:
                test_positions = [
                    (mid.x - offset, mid.y),
                    (mid.x + offset, mid.y)
                ]
            
            for pos in test_positions:
                if not self._check_dimension_collision(pos):
                    return pos
        
        return original_pos  # Fallback
    
    def _dimension_key_details(self, lines, bbox):
        """Dimension important details (holes, slots, etc.)"""
        count = 0
        
        # Find special features (e.g., short segments that could be chamfers, fillets)
        short_lines = [line for line in lines if self._get_line_length(line) < 20.0]
        
        for line in short_lines:
            if self._is_important_detail(line, lines):
                start = Vec2(line.dxf.start)
                end = Vec2(line.dxf.end)
                direction = 'horizontal' if abs((end - start).y) < self.tolerance else 'vertical'
                
                if self._add_smart_linear_dimension(line, direction, False, bbox):
                    count += 1
        
        return count
    
    def _dimension_holes_and_features(self, circles, arcs, bbox):
        """Dimension holes and features (for top view)"""
        count = 0
        
        # Dimension all circles as holes
        for circle in circles:
            center = Vec2(circle.dxf.center)
            radius = circle.dxf.radius
            diameter = 2 * radius
            
            rounded_dia = round(diameter, 1)
            if rounded_dia not in self.used_diameters:
                angle = self._find_best_diameter_angle(center, radius, bbox)
                if self._add_diameter_dimension(center, radius, angle):
                    count += 1
                    self.used_diameters.add(rounded_dia)
        
        # Dimension arcs as radii
        count += self._dimension_arcs_intelligent(arcs, [])
        
        return count
    
    def _dimension_profile_features(self, lines, arcs, bbox):
        """Dimension profile features (for side view)"""
        count = 0
        
        # Prioritize dimensioning vertical lines (height)
        vertical_lines = [line for line in lines if self._is_vertical_line(line)]
        
        length_groups = self._group_lines_by_length(vertical_lines)
        
        for length, grouped_lines in length_groups.items():
            if length >= 5.0:  # Minimum height
                representative = self._select_representative_line(grouped_lines, 'vertical', bbox)
                if representative and self._should_dimension_line(representative, 'vertical', length):
                    is_major = self._is_major_dimension(representative, 'vertical', bbox)
                    if self._add_smart_linear_dimension(representative, 'vertical', is_major, bbox):
                        count += 1
                        self.used_lengths['vertical'].add(round(length, 1))
        
        # Dimension arcs
        count += self._dimension_arcs_intelligent(arcs, lines)
        
        return count
    
    def _dimension_all_features(self, entities, bbox):
        """Dimension all important features (for detail view)"""
        count = 0
        
        lines = [e for e in entities if e.dxftype() == 'LINE']
        circles = [e for e in entities if e.dxftype() == 'CIRCLE']
        arcs = [e for e in entities if e.dxftype() == 'ARC']
        
        # Dimension all meaningful lines
        horizontal_lines, vertical_lines, diagonal_lines = self._classify_lines_by_direction(lines)
        
        count += self._dimension_lines_in_direction(horizontal_lines, 'horizontal', bbox)
        count += self._dimension_lines_in_direction(vertical_lines, 'vertical', bbox)
        
        # Dimension circles and arcs
        count += self._dimension_circles_as_diameters(circles, bbox)
        count += self._dimension_arcs_intelligent(arcs, lines)
        
        return count
    
    def _dimension_arcs_intelligent(self, arcs, lines):
        """Dimension arcs intelligently"""
        count = 0
        
        for arc in arcs:
            center = Vec2(arc.dxf.center)
            radius = arc.dxf.radius
            
            # Avoid duplicate radii
            rounded_radius = round(radius, 1)
            if rounded_radius in self.used_radii:
                continue
            
            # Only dimension outer arcs (largest radius at the same center)
            if not self._is_outer_arc(arc, arcs):
                continue
            
            # Find the best angle for the radius dimension
            best_angle = self._find_best_radius_angle(arc)
            
            if self._add_radius_dimension(center, radius, best_angle):
                count += 1
                self.used_radii.add(rounded_radius)
        
        return count
    
    def _add_radius_dimension(self, center, radius, angle_deg):
        """Add a radius dimension"""
        try:
            angle_rad = math.radians(angle_deg)
            dx = radius * math.cos(angle_rad)
            dy = radius * math.sin(angle_rad)
            mpoint = (center.x + dx, center.y + dy)
            
            if self._check_dimension_collision(mpoint):
                return False
            
            dim = self.msp.add_radius_dim(
                center=(center.x, center.y),
                radius=radius,
                mpoint=mpoint,
                dimstyle=self.style_name
            )
            
            dim.render()
            self.dimension_positions.append(mpoint)
            return True
            
        except Exception as e:
            print(f"[WARNING] Could not create radius dimension: {e}")
            return False
    
    def _find_best_radius_angle(self, arc):
        """Find the best angle for a radius dimension"""
        start_angle = arc.dxf.start_angle
        end_angle = arc.dxf.end_angle
        
        # Normalize angles
        if end_angle < start_angle:
            end_angle += 360
        
        # Try the middle of the arc first
        mid_angle = (start_angle + end_angle) / 2
        if not self._check_angle_collision(arc.dxf.center, arc.dxf.radius, mid_angle):
            return mid_angle
        
        # Try other preferred angles within the range
        preferred_angles = [45, 135, -45, -135, 90, -90, 0, 180]
        
        for angle in preferred_angles:
            normalized_angle = angle % 360
            if start_angle <= normalized_angle <= end_angle:
                if not self._check_angle_collision(arc.dxf.center, arc.dxf.radius, angle):
                    return angle
        
        return mid_angle  # Fallback
    
    def _check_angle_collision(self, center, radius, angle_deg):
        """Check for collision for an angle position"""
        angle_rad = math.radians(angle_deg)
        dx = radius * math.cos(angle_rad)
        dy = radius * math.sin(angle_rad)
        test_point = (center[0] + dx, center[1] + dy)
        
        return self._check_dimension_collision(test_point)
    
    def _is_outer_arc(self, arc, all_arcs):
        """Check if it is an outer arc"""
        center = Vec2(arc.dxf.center)
        radius = arc.dxf.radius
        
        # Find all arcs with the same center
        same_center_arcs = []
        for other_arc in all_arcs:
            other_center = Vec2(other_arc.dxf.center)
            if (center - other_center).magnitude < self.tolerance:
                same_center_arcs.append(other_arc)
        
        if len(same_center_arcs) <= 1:
            return True
        
        # Check if it has the largest radius
        max_radius = max(a.dxf.radius for a in same_center_arcs)
        return abs(radius - max_radius) < self.tolerance
    
    def _get_line_length(self, line):
        """Get the length of a line"""
        start = Vec2(line.dxf.start)
        end = Vec2(line.dxf.end)
        return (end - start).magnitude
    
    def _is_vertical_line(self, line):
        """Check if a line is vertical"""
        start = Vec2(line.dxf.start)
        end = Vec2(line.dxf.end)
        return abs((end - start).x) < self.tolerance
    
    def _is_horizontal_line(self, line):
        """Check if a line is horizontal"""
        start = Vec2(line.dxf.start)
        end = Vec2(line.dxf.end)
        return abs((end - start).y) < self.tolerance
    
    def _is_important_detail(self, line, all_lines):
        """Check if a line is an important detail"""
        length = self._get_line_length(line)
        
        # An important detail if:
        # 1. Length is between 2-20mm (could be a chamfer, fillet)
        # 2. Not parallel to the majority of lines
        if not (2.0 <= length <= 20.0):
            return False
        
        # Check orientation against the majority
        start = Vec2(line.dxf.start)
        end = Vec2(line.dxf.end)
        line_angle = math.degrees(math.atan2((end - start).y, (end - start).x))
        
        # Count major angles in the drawing
        angle_counter = Counter()
        for other_line in all_lines:
            other_start = Vec2(other_line.dxf.start)
            other_end = Vec2(other_line.dxf.end)
            other_angle = math.degrees(math.atan2((other_end - other_start).y, (other_end - other_start).x))
            angle_bucket = round(other_angle / 15) * 15  # Bucket by 15 degrees
            angle_counter[angle_bucket] += 1
        
        # If the line's angle is not a major angle -> could be a detail
        line_bucket = round(line_angle / 15) * 15
        most_common_angles = [angle for angle, count in angle_counter.most_common(3)]
        
        return line_bucket not in most_common_angles
    
    def _get_entities_bbox(self, entities):
        """Calculate the bounding box of entities - use the view_detector helper"""
        return self.view_detector._get_entities_bbox(entities)


class EnhancedAutoScaler:
    """Auto scaling based on CAD standards"""
    
    STANDARD_SCALES = [0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    
    PAPER_SIZES = {
        'A0': (841, 1189),
        'A1': (594, 841), 
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210)
    }
    
    @staticmethod
    def calculate_fusion_style_scale(geometry_bounds, paper_size='A3', title_block_height=50):
        """Calculate Fusion 360 style scale with a title block"""
        if paper_size not in EnhancedAutoScaler.PAPER_SIZES:
            return 1.0
        
        paper_width, paper_height = EnhancedAutoScaler.PAPER_SIZES[paper_size]
        
        # Subtract margins and title block
        margin = 20  # mm
        usable_width = paper_width - 2 * margin
        usable_height = paper_height - 2 * margin - title_block_height
        
        geometry_width, geometry_height = geometry_bounds
        
        if geometry_width <= 0 or geometry_height <= 0:
            return 1.0
        
        # Calculate the required ratio
        scale_x = usable_width / geometry_width
        scale_y = usable_height / geometry_height
        
        required_scale = min(scale_x, scale_y)
        
        # Choose the appropriate standard scale
        for scale in reversed(EnhancedAutoScaler.STANDARD_SCALES):
            if required_scale >= scale:
                return scale
        
        return EnhancedAutoScaler.STANDARD_SCALES[0]


def main():
    """Main function with Enhanced Auto-Dimensioning"""
    print("=== Enhanced Auto-Dimensioning System (Fusion 360 Style) ===")
    
    INPUT_DXF = "/app/output/step1_base_drawing.dxf"
    OUTPUT_DXF = "/app/output/step2_with_dims.dxf"
    CONFIG_PATH = "/app/output/page_info.json"
    
    try:
        # Read configuration
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        
        print(f"[INFO] Initializing Enhanced Auto-Dimensioning System...")
        
        # Read DXF file
        doc = ezdxf.readfile(INPUT_DXF)
        msp = doc.modelspace()
        
        # Get all entities
        all_entities = list(msp.query("LINE CIRCLE ARC"))
        print(f"[INFO] Found {len(all_entities)} geometric objects")
        
        if not all_entities:
            print("[WARNING] No objects found for dimensioning")
            return
        
        # === STEP 1: DETECT AND CLASSIFY VIEWS ===
        print(f"[INFO] Analyzing and classifying views...")
        
        view_detector = IntelligentViewDetector()
        classified_views = view_detector.analyze_and_classify_views(all_entities)
        
        print(f"[INFO] Detected {len(classified_views)} views:")
        for view_name, view_data in classified_views.items():
            print(f"  • {view_name}: {view_data['type']} ({len(view_data['entities'])} entities)")
        
        # === STEP 2: SMART AUTO-DIMENSIONING ===
        print(f"[INFO] Starting auto-dimensioning...")
        
        dimensioner = FusionStyleDimensioner(msp, config)
        total_dimensions = dimensioner.dimension_all_views(classified_views)
        
        # === STEP 3: AUTO-SCALING (optional) ===
        if config.get('AUTO_SCALE', 'false').lower() == 'true':
            print(f"[INFO] Calculating auto-scaling...")
            
            # Calculate geometry bounds - FIX the slicing issue
            all_points = []
            for entity in all_entities:
                if entity.dxftype() == 'LINE':
                    # Convert Vec3 to tuple properly
                    start_point = entity.dxf.start
                    end_point = entity.dxf.end
                    all_points.extend([
                        (start_point.x, start_point.y),
                        (end_point.x, end_point.y)
                    ])
                elif entity.dxftype() in ['CIRCLE', 'ARC']:
                    # Convert Vec3 to tuple properly
                    center_point = entity.dxf.center
                    radius = entity.dxf.radius
                    center = (center_point.x, center_point.y)
                    all_points.extend([
                        (center[0] - radius, center[1] - radius),
                        (center[0] + radius, center[1] + radius)
                    ])
            
            if all_points:
                xs = [p[0] for p in all_points]
                ys = [p[1] for p in all_points]
                geometry_bounds = (max(xs) - min(xs), max(ys) - min(ys))
                
                paper_size = config.get('PAPER_SIZE', 'A3')
                optimal_scale = EnhancedAutoScaler.calculate_fusion_style_scale(
                    geometry_bounds, paper_size
                )
                
                print(f"[INFO] Optimal scale: 1:{optimal_scale} for {paper_size} size")
        
        # === STEP 4: SAVE FILE ===
        doc.saveas(OUTPUT_DXF)
        
        print(f"✅ [SUCCESS] Enhanced Auto-Dimensioning complete!")
        print(f"   • Added {total_dimensions} automatic dimensions")
        print(f"   • Used Fusion 360 style formatting")
        print(f"   • Output file: {OUTPUT_DXF}")
        
        # === DETAILED STATISTICS ===
        print(f"\n📊 DETAILED STATISTICS:")
        print(f"   • Total entities: {len(all_entities)}")
        print(f"   • Views analyzed: {len(classified_views)}")
        print(f"   • Dimensions created: {total_dimensions}")
        print(f"   • Style used: Fusion 360 Enhanced")
        
    except Exception as e:
        print(f"❌ [ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()