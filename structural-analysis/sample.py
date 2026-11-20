import math
import numpy as np

# ==============================================================================
# BASE CLASS - Common to ALL Tower Types
# ==============================================================================

class BaseTowerAnalysis:
    """
    Base class containing common functionality for all tower types
    """
    def __init__(self):
        # Material properties
        self.steel_density = 7850  # kg/m³
        self.gravity = 9.81  # m/s²
        
    def calculate_dead_load(self, components):
        """
        Calculate total dead load from all components
        Override in child classes for specific implementations
        """
        raise NotImplementedError("Subclass must implement calculate_dead_load()")
    
    def calculate_kz(self, height_m, exposure='C'):
        """Calculate height-dependent velocity pressure coefficient (ASCE 7)"""
        if exposure == 'C':
            if height_m < 4.6:
                return 0.85
            elif height_m < 6.1:
                return 0.90
            elif height_m < 9.1:
                return 0.98
            elif height_m < 12.2:
                return 1.04
            elif height_m < 15.2:
                return 1.09
            else:
                return 0.85 * (height_m / 4.6) ** (2/9.5)
        elif exposure == 'B':
            if height_m < 9.1:
                return 0.57
            elif height_m < 12.2:
                return 0.62
            elif height_m < 15.2:
                return 0.66
            else:
                return 0.57 * (height_m / 9.1) ** (2/7.0)
        elif exposure == 'D':
            if height_m < 4.6:
                return 1.03
            elif height_m < 6.1:
                return 1.08
            elif height_m < 9.1:
                return 1.16
            else:
                return 1.03 * (height_m / 4.6) ** (2/11.5)
        else:
            return 0.85
    
    def calculate_wind_load(self, wind_speed_ms, exposure='C'):
        """
        Calculate wind loads - override in child classes
        """
        raise NotImplementedError("Subclass must implement calculate_wind_load()")
    
    def calculate_load_combinations(self, dead_load_n, wind_moment_nm, applied_moment_nm, capacity):
        """
        ASCE 7 Load Combinations (common to all towers)
        """
        combinations = {}
        
        # LRFD Combinations
        combinations['LRFD_1.4D'] = {
            'moment': 1.4 * 0,  # Dead load creates no moment for vertical towers
            'utilization': 0
        }
        
        combinations['LRFD_1.2D+1.6W'] = {
            'moment': applied_moment_nm + 1.6 * wind_moment_nm,
            'utilization': (applied_moment_nm + 1.6 * wind_moment_nm) / capacity
        }
        
        combinations['LRFD_1.2D+1.0W'] = {
            'moment': applied_moment_nm + 1.0 * wind_moment_nm,
            'utilization': (applied_moment_nm + 1.0 * wind_moment_nm) / capacity
        }
        
        combinations['LRFD_0.9D+1.6W'] = {
            'moment': applied_moment_nm + 1.6 * wind_moment_nm,
            'utilization': (applied_moment_nm + 1.6 * wind_moment_nm) / capacity
        }
        
        # ASD Combinations
        combinations['ASD_D'] = {
            'moment': 0,
            'utilization': 0
        }
        
        combinations['ASD_D+W'] = {
            'moment': applied_moment_nm + wind_moment_nm,
            'utilization': (applied_moment_nm + wind_moment_nm) / capacity
        }
        
        combinations['ASD_D+0.75W'] = {
            'moment': applied_moment_nm + 0.75 * wind_moment_nm,
            'utilization': (applied_moment_nm + 0.75 * wind_moment_nm) / capacity
        }
        
        combinations['ASD_0.6D+0.6W'] = {
            'moment': applied_moment_nm + 0.6 * wind_moment_nm,
            'utilization': (applied_moment_nm + 0.6 * wind_moment_nm) / capacity
        }
        
        # Find governing combination
        max_utilization = max(combo['utilization'] for combo in combinations.values())
        governing_combo = max(combinations.items(), key=lambda x: x[1]['utilization'])[0]
        
        return combinations, governing_combo, max_utilization
    
    def calculate_foundation_capacity(self, foundation_params):
        """
        Foundation and anchor bolt capacity (common to all towers)
        """
        base_plate_dia = foundation_params['base_plate_diameter'] / 1000  # m
        bolt_circle_dia = foundation_params['bolt_circle_diameter'] / 1000  # m
        num_bolts = foundation_params['number_of_bolts']
        bolt_diameter = foundation_params['bolt_diameter'] / 1000  # m
        bolt_grade = foundation_params['bolt_grade']  # MPa
        
        # Bolt tensile capacity
        bolt_area = math.pi * (bolt_diameter ** 2) / 4  # m²
        bolt_tensile_capacity_per_bolt = bolt_area * bolt_grade * 1e6 * 0.75  # N
        
        # Lever arm and moment capacity
        lever_arm = bolt_circle_dia / 2  # m
        bolts_in_tension = num_bolts / 2
        total_bolt_capacity = bolts_in_tension * bolt_tensile_capacity_per_bolt  # N
        foundation_moment_capacity = total_bolt_capacity * lever_arm  # N⋅m
        
        # Safety factor
        safety_factor = 2.0
        allowable_foundation_moment = foundation_moment_capacity / safety_factor
        
        return allowable_foundation_moment, bolt_tensile_capacity_per_bolt
    
    def analyze(self):
        """
        Main analysis method - override in child classes
        """
        raise NotImplementedError("Subclass must implement analyze()")


# ==============================================================================
# MONOPOLE TOWER CLASS
# ==============================================================================

class MonopoleTowerAnalysis(BaseTowerAnalysis):
    """
    Analysis for monopole (tubular) towers
    """
    def __init__(self):
        super().__init__()
    
    def calculate_dead_load(self, sections, crown_platforms=None):
        """
        Calculate dead load for monopole sections
        """
        total_weight_kg = 0
        
        # Calculate pole sections
        for section in sections:
            height_m = section['height'] / 1000
            d_top_m = section['diameter_top'] / 1000
            d_bottom_m = section['diameter_bottom'] / 1000
            thickness_m = section['thickness'] / 1000
            
            d_avg_m = (d_top_m + d_bottom_m) / 2
            outer_radius = d_avg_m / 2
            outer_volume = math.pi * (outer_radius ** 2) * height_m
            inner_radius = outer_radius - thickness_m
            inner_volume = math.pi * (inner_radius ** 2) * height_m
            steel_volume_m3 = outer_volume - inner_volume
            section_weight_kg = steel_volume_m3 * self.steel_density
            total_weight_kg += section_weight_kg
        
        # Calculate crown platforms
        crown_weight_kg = 0
        if crown_platforms:
            for platform in crown_platforms:
                platform_weight = platform.get('platform_weight_kg', 0)
                platform_weight += sum(ant.get('weight_kg', 0) for ant in platform.get('antennas', []))
                platform_weight += sum(rru.get('weight_kg', 0) for rru in platform.get('rrus', []))
                platform_weight += sum(eq.get('weight_kg', 0) for eq in platform.get('other_equipment', []))
                crown_weight_kg += platform_weight
        
        return total_weight_kg, crown_weight_kg
    
    def calculate_wind_load(self, sections, wind_speed_ms, exposure='C', crown_platforms=None):
        """
        Calculate wind load on monopole
        """
        kzt = 1.0
        kd = 0.95
        cf = 0.5  # Circular cylinder
        
        total_wind_force = 0
        wind_moment = 0
        height_cumulative = 0
        
        # Wind on pole sections
        for section in sections:
            h = section['height'] / 1000
            d_avg = ((section['diameter_top'] + section['diameter_bottom']) / 2) / 1000
            projected_area = d_avg * h
            section_center_height = height_cumulative + h/2
            
            kz = self.calculate_kz(section_center_height, exposure)
            qz = 0.613 * kz * kzt * kd * (wind_speed_ms ** 2)
            wind_force = qz * cf * projected_area
            moment_contribution = wind_force * section_center_height
            
            total_wind_force += wind_force
            wind_moment += moment_contribution
            height_cumulative += h
        
        # Wind on crown platforms
        if crown_platforms:
            for platform in crown_platforms:
                platform_height = platform['height']
                kz = self.calculate_kz(platform_height, exposure)
                qz = 0.613 * kz * kzt * kd * (wind_speed_ms ** 2)
                
                # Antennas
                for antenna in platform.get('antennas', []):
                    area = antenna.get('wind_area_m2', 0)
                    cf_ant = antenna.get('cf', 1.2)
                    force = qz * cf_ant * area
                    total_wind_force += force
                    wind_moment += force * platform_height
                
                # RRUs and other equipment
                for rru in platform.get('rrus', []):
                    area = rru.get('wind_area_m2', 0)
                    cf_rru = rru.get('cf', 1.0)
                    force = qz * cf_rru * area
                    total_wind_force += force
                    wind_moment += force * platform_height
        
        return total_wind_force, wind_moment
    
    def calculate_moment_capacity(self, diameter_mm, thickness_mm, steel_grade='S355'):
        """
        Bending moment capacity of circular hollow section
        """
        yield_strengths = {
            'A36': 248,
            'A572-50': 345,
            'S355': 355
        }
        fy_mpa = yield_strengths.get(steel_grade, 355)
        
        d_outer = diameter_mm / 1000
        thickness = thickness_mm / 1000
        d_inner = d_outer - 2 * thickness
        
        # Section modulus
        section_modulus_m3 = (math.pi / 32) * (d_outer**4 - d_inner**4) / d_outer
        
        # Moment capacity
        fy_pa = fy_mpa * 1e6
        moment_capacity_nm = section_modulus_m3 * fy_pa
        
        return moment_capacity_nm, section_modulus_m3
    
    def analyze(self, sections, wind_speed_ms, exposure='C', steel_grade='S355', 
                foundation_params=None, crown_platforms=None, applied_load_kg=0):
        """
        Complete monopole analysis
        """
        # 1. Dead load
        pole_weight_kg, crown_weight_kg = self.calculate_dead_load(sections, crown_platforms)
        total_dead_load_kg = pole_weight_kg + crown_weight_kg
        
        # 2. Height
        total_height_m = sum(section['height'] for section in sections) / 1000
        
        # 3. Structural capacity
        bottom_section = sections[0]
        pole_moment_capacity, _ = self.calculate_moment_capacity(
            bottom_section['diameter_bottom'],
            bottom_section['thickness'],
            steel_grade
        )
        allowable_pole_moment = pole_moment_capacity / 2.0  # Safety factor
        
        # 4. Foundation capacity
        if foundation_params:
            allowable_foundation_moment, _ = self.calculate_foundation_capacity(foundation_params)
            governing_moment = min(allowable_pole_moment, allowable_foundation_moment)
        else:
            governing_moment = allowable_pole_moment
        
        # 5. Wind loads
        wind_force, wind_moment = self.calculate_wind_load(sections, wind_speed_ms, exposure, crown_platforms)
        
        # 6. Applied load moment
        applied_moment = applied_load_kg * self.gravity * total_height_m
        
        # 7. Load combinations
        combinations, governing_combo, max_utilization = self.calculate_load_combinations(
            total_dead_load_kg * self.gravity,
            wind_moment,
            applied_moment,
            governing_moment
        )
        
        # 8. Remaining capacity
        remaining_moment = governing_moment - combinations[governing_combo]['moment']
        remaining_load_capacity = remaining_moment / (self.gravity * total_height_m) if total_height_m > 0 else 0
        
        return {
            'tower_type': 'MONOPOLE',
            'pole_weight_kg': pole_weight_kg,
            'crown_weight_kg': crown_weight_kg,
            'total_dead_load_kg': total_dead_load_kg,
            'wind_force_n': wind_force,
            'wind_moment_nm': wind_moment,
            'governing_combo': governing_combo,
            'max_utilization': max_utilization,
            'remaining_capacity_kg': remaining_load_capacity,
            'all_combinations': combinations
        }


# ==============================================================================
# LATTICE TOWER CLASS
# ==============================================================================

class LatticeTowerAnalysis(BaseTowerAnalysis):
    """
    Analysis for lattice (truss) towers - 3-legged or 4-legged
    """
    def __init__(self):
        super().__init__()
        self.nodes = {}  # Node coordinates
        self.members = []  # Member connectivity
        self.member_forces = {}  # Calculated member forces
    
    def setup_geometry(self, geometry_data):
        """
        Setup tower geometry - nodes and member connectivity
        geometry_data: dict with 'nodes' and 'members'
        """
        self.nodes = geometry_data['nodes']
        self.members = geometry_data['members']
    
    def calculate_dead_load(self, members_data, crown_platforms=None):
        """
        Calculate dead load for all lattice members
        members_data: list of dicts with member properties
        """
        total_weight_kg = 0
        
        for member in members_data:
            # Member properties
            length_m = member['length'] / 1000
            section_type = member['section_type']  # 'angle', 'tube', etc.
            
            if section_type == 'angle':
                size = member['size']  # e.g., 'L100x100x10'
                area_mm2 = member['area_mm2']
                area_m2 = area_mm2 / 1e6
                volume_m3 = area_m2 * length_m
                weight_kg = volume_m3 * self.steel_density
                total_weight_kg += weight_kg
            
            elif section_type == 'tube':
                diameter_mm = member['diameter']
                thickness_mm = member['thickness']
                d_outer_m = diameter_mm / 1000
                d_inner_m = (diameter_mm - 2 * thickness_mm) / 1000
                area_m2 = math.pi * (d_outer_m**2 - d_inner_m**2) / 4
                volume_m3 = area_m2 * length_m
                weight_kg = volume_m3 * self.steel_density
                total_weight_kg += weight_kg
        
        # Crown platforms
        crown_weight_kg = 0
        if crown_platforms:
            for platform in crown_platforms:
                crown_weight_kg += platform.get('total_weight_kg', 0)
        
        return total_weight_kg, crown_weight_kg
    
    def calculate_wind_load(self, panels, wind_speed_ms, exposure='C'):
        """
        Calculate wind load on lattice panels
        panels: list of dicts with panel geometry and height
        """
        total_wind_force = 0
        wind_moment = 0
        
        kzt = 1.0
        kd = 0.95
        
        for panel in panels:
            panel_height_m = panel['center_height']
            projected_area_m2 = panel['projected_area']
            cf = panel.get('cf', 1.6)  # Force coefficient for lattice
            
            kz = self.calculate_kz(panel_height_m, exposure)
            qz = 0.613 * kz * kzt * kd * (wind_speed_ms ** 2)
            wind_force = qz * cf * projected_area_m2
            
            total_wind_force += wind_force
            wind_moment += wind_force * panel_height_m
        
        return total_wind_force, wind_moment
    
    def solve_truss(self, loads):
        """
        Solve truss structure using matrix stiffness method
        loads: dict of applied loads at nodes
        Returns: member forces (axial)
        """
        # THIS IS A PLACEHOLDER - Full implementation requires:
        # 1. Build global stiffness matrix
        # 2. Apply boundary conditions
        # 3. Solve K*d = F for displacements
        # 4. Calculate member forces from displacements
        
        print("Truss analysis - Matrix solver to be implemented")
        
        # For now, return empty dict
        self.member_forces = {}
        return self.member_forces
    
    def calculate_buckling_capacity(self, member):
        """
        Calculate buckling capacity for compression members
        member: dict with member properties
        """
        # Member properties
        length_m = member['length'] / 1000
        area_mm2 = member['area_mm2']
        area_m2 = area_mm2 / 1e6
        radius_of_gyration_mm = member['radius_of_gyration']
        r_m = radius_of_gyration_mm / 1000
        fy_mpa = member.get('yield_strength', 355)
        E_mpa = 200000  # Steel modulus
        
        # Effective length factor
        K = member.get('K_factor', 1.0)
        effective_length = K * length_m
        
        # Slenderness ratio
        slenderness = effective_length / r_m
        
        # Euler buckling load
        P_euler = (math.pi**2 * E_mpa * 1e6 * area_m2) / (slenderness**2)
        
        # Apply safety factor
        safety_factor = 1.67  # AISC
        allowable_buckling = P_euler / safety_factor
        
        return allowable_buckling, slenderness
    
    def check_member_utilization(self, member, axial_force):
        """
        Check utilization ratio for a member
        """
        area_mm2 = member['area_mm2']
        area_m2 = area_mm2 / 1e6
        fy_mpa = member.get('yield_strength', 355)
        
        if axial_force >= 0:  # Tension
            capacity = area_m2 * fy_mpa * 1e6 / 1.67
            utilization = axial_force / capacity
        else:  # Compression
            capacity, _ = self.calculate_buckling_capacity(member)
            utilization = abs(axial_force) / capacity
        
        return utilization, capacity
    
    def check_connections(self, connection):
        """
        Check bolt/weld capacity at connections
        connection: dict with connection details
        """
        # PLACEHOLDER - implement bolt shear, bearing, gusset checks
        print("Connection checks to be implemented")
        return True
    
    def analyze(self, geometry_data, members_data, panels, wind_speed_ms, 
                exposure='C', foundation_params=None, crown_platforms=None, applied_loads=None):
        """
        Complete lattice tower analysis
        """
        # 1. Setup geometry
        self.setup_geometry(geometry_data)
        
        # 2. Dead load
        tower_weight_kg, crown_weight_kg = self.calculate_dead_load(members_data, crown_platforms)
        total_dead_load_kg = tower_weight_kg + crown_weight_kg
        
        # 3. Wind loads
        wind_force, wind_moment = self.calculate_wind_load(panels, wind_speed_ms, exposure)
        
        # 4. Solve truss for member forces
        loads = applied_loads or {}
        self.solve_truss(loads)
        
        # 5. Check each member
        member_utilizations = []
        for i, member_data in enumerate(members_data):
            member_force = self.member_forces.get(i, 0)
            utilization, capacity = self.check_member_utilization(member_data, member_force)
            member_utilizations.append({
                'member_id': i,
                'force': member_force,
                'capacity': capacity,
                'utilization': utilization
            })
        
        # 6. Find maximum utilization
        max_utilization = max([m['utilization'] for m in member_utilizations]) if member_utilizations else 0
        
        # 7. Foundation check (if provided)
        foundation_ok = True
        if foundation_params:
            foundation_capacity, _ = self.calculate_foundation_capacity(foundation_params)
            foundation_utilization = wind_moment / foundation_capacity
            foundation_ok = foundation_utilization < 1.0
        
        return {
            'tower_type': 'LATTICE',
            'tower_weight_kg': tower_weight_kg,
            'crown_weight_kg': crown_weight_kg,
            'total_dead_load_kg': total_dead_load_kg,
            'wind_force_n': wind_force,
            'wind_moment_nm': wind_moment,
            'max_member_utilization': max_utilization,
            'member_utilizations': member_utilizations,
            'foundation_ok': foundation_ok
        }


# ==============================================================================
# FACTORY FUNCTION - Single Entry Point
# ==============================================================================

def create_tower_analyzer(tower_type):
    """
    Factory function to create appropriate tower analyzer
    tower_type: 'monopole' or 'lattice'
    """
    if tower_type.lower() == 'monopole':
        return MonopoleTowerAnalysis()
    elif tower_type.lower() == 'lattice':
        return LatticeTowerAnalysis()
    else:
        raise ValueError(f"Unknown tower type: {tower_type}")


# ==============================================================================
# EXAMPLE USAGE
# ==============================================================================

if __name__ == "__main__":
    
    # Example 1: Monopole Tower
    print("="*70)
    print("MONOPOLE TOWER ANALYSIS")
    print("="*70)
    
    monopole = create_tower_analyzer('monopole')
    
    monopole_sections = [
        {'height': 10000, 'diameter_bottom': 1200, 'diameter_top': 900, 'thickness': 5},
        {'height': 10000, 'diameter_bottom': 900, 'diameter_top': 600, 'thickness': 5},
    ]
    
    results_monopole = monopole.analyze(
        sections=monopole_sections,
        wind_speed_ms=25,
        exposure='C',
        steel_grade='S355'
    )
    
    print(f"\nResults: {results_monopole}")
    
    
    # Example 2: Lattice Tower
    print("\n" + "="*70)
    print("LATTICE TOWER ANALYSIS")
    print("="*70)
    
    lattice = create_tower_analyzer('lattice')
    
    # Geometry data (simplified example)
    geometry = {
        'nodes': {
            0: {'x': 0, 'y': 0, 'z': 0},
            1: {'x': 2, 'y': 0, 'z': 0},
            2: {'x': 1, 'y': 1.732, 'z': 0},
            3: {'x': 0.5, 'y': 0.866, 'z': 10},
        },
        'members': [
            {'start': 0, 'end': 3},  # Leg
            {'start': 1, 'end': 3},  # Leg
            {'start': 2, 'end': 3},  # Leg
        ]
    }
    
    members_data = [
        {'length': 10000, 'section_type': 'angle', 'area_mm2': 2000, 'radius_of_gyration': 40},
        {'length': 10000, 'section_type': 'angle', 'area_mm2': 2000, 'radius_of_gyration': 40},
        {'length': 10000, 'section_type': 'angle', 'area_mm2': 2000, 'radius_of_gyration': 40},
    ]
    
    panels = [
        {'center_height': 5, 'projected_area': 20, 'cf': 1.6},
    ]
    
    results_lattice = lattice.analyze(
        geometry_data=geometry,
        members_data=members_data,
        panels=panels,
        wind_speed_ms=25,
        exposure='C'
    )
    
    print(f"\nResults: {results_lattice}")
