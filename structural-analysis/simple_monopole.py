import math

class SimpleMonopoleAnalysis:
    def __init__(self):
        # Material properties for steel
        self.steel_density = 7850  # kg/m³
        self.gravity = 9.81  # m/s²
        
    def calculate_dead_load(self, sections):
        """
        Calculate dead load (weight) of monopole
        All inputs in mm, output in kg
        """
        total_weight_kg = 0
        
        print("DEAD LOAD CALCULATION:")
        print("-" * 40)
        
        for i, section in enumerate(sections):
            # Convert mm to meters
            height_m = section['height'] / 1000
            d_top_m = section['diameter_top'] / 1000
            d_bottom_m = section['diameter_bottom'] / 1000
            thickness_m = section['thickness'] / 1000
            
            # Average diameter for tapered section
            d_avg_m = (d_top_m + d_bottom_m) / 2
            
            # Calculate steel volume (hollow tapered cylinder)
            # Outer volume
            outer_radius = d_avg_m / 2
            outer_volume = math.pi * (outer_radius ** 2) * height_m
            
            # Inner volume (subtract wall thickness)
            inner_radius = outer_radius - thickness_m
            inner_volume = math.pi * (inner_radius ** 2) * height_m
            
            # Steel volume
            steel_volume_m3 = outer_volume - inner_volume
            
            # Weight calculation
            section_weight_kg = steel_volume_m3 * self.steel_density
            total_weight_kg += section_weight_kg
            
            print(f"Section {i+1}:")
            print(f"  Height: {section['height']} mm")
            print(f"  Avg Diameter: {d_avg_m*1000:.0f} mm")
            print(f"  Wall Thickness: {section['thickness']} mm")
            print(f"  Steel Volume: {steel_volume_m3:.3f} m³")
            print(f"  Weight: {section_weight_kg:.1f} kg")
            print()
        
        print(f"TOTAL DEAD LOAD: {total_weight_kg:.1f} kg")
        return total_weight_kg
    
    def calculate_moment_capacity(self, diameter_mm, thickness_mm, steel_grade='A572-50'):
        """
        Calculate bending moment capacity of circular hollow section
        """
        # Steel yield strengths in MPa
        yield_strengths = {
            'A36': 248,      # MPa
            'A572-50': 345,  # MPa
            'A992': 345      # MPa
        }
        fy_mpa = yield_strengths.get(steel_grade, 345)
        
        # Convert to meters for consistency
        d_outer = diameter_mm / 1000  # m
        thickness = thickness_mm / 1000  # m
        d_inner = d_outer - 2 * thickness  # m
        
        # Section modulus for hollow circular section
        # Formula: S = π/32 * (D_outer⁴ - D_inner⁴) / D_outer
        d_outer_m4 = d_outer ** 4
        d_inner_m4 = d_inner ** 4
        
        section_modulus_m3 = (math.pi / 32) * (d_outer_m4 - d_inner_m4) / d_outer
        
        # Moment capacity: M = S × fy
        # fy in Pa (MPa × 10⁶), S in m³, result in N⋅m
        fy_pa = fy_mpa * 1e6  # Convert MPa to Pa
        moment_capacity_nm = section_modulus_m3 * fy_pa
        
        return moment_capacity_nm, section_modulus_m3
    
    def calculate_max_load_capacity(self, sections, steel_grade='A572-50'):
        """
        Calculate maximum additional load that can be applied at top
        """
        # Use bottom section (critical section with maximum moment)
        bottom_section = sections[0]
        d_bottom = bottom_section['diameter_bottom']
        thickness = bottom_section['thickness']
        
        # Calculate moment capacity of bottom section
        moment_capacity, section_modulus = self.calculate_moment_capacity(d_bottom, thickness, steel_grade)
        
        # Apply safety factor
        safety_factor = 2.0
        allowable_moment = moment_capacity / safety_factor
        
        # Calculate total height
        total_height_m = sum(section['height'] for section in sections) / 1000
        
        # Maximum load at top: F = M / h
        # This assumes load applied at very top of pole
        max_load_n = allowable_moment / total_height_m
        max_load_kg = max_load_n / self.gravity
        
        print("MOMENT CAPACITY ANALYSIS:")
        print("-" * 40)
        print(f"Bottom Section Diameter: {d_bottom} mm")
        print(f"Wall Thickness: {thickness} mm")
        print(f"Steel Grade: {steel_grade}")
        print(f"Section Modulus: {section_modulus*1e6:.0f} mm³")
        print(f"Moment Capacity: {moment_capacity:.0f} N⋅m")
        print(f"Allowable Moment (SF={safety_factor}): {allowable_moment:.0f} N⋅m")
        print(f"Total Height: {total_height_m:.1f} m")
        print(f"Max Load at Top: {max_load_kg:.0f} kg ({max_load_n:.0f} N)")
        print()
        
        return max_load_kg, allowable_moment
    
    def calculate_utilization_from_load(self, applied_load_kg, max_load_kg):
        """
        Calculate utilization ratio for a given applied load
        """
        if max_load_kg <= 0:
            return float('inf')  # Infinite utilization (structure fails)
        
        utilization_ratio = applied_load_kg / max_load_kg
        return utilization_ratio
    
    def analyze_monopole(self, sections, applied_load_kg=0, steel_grade='A572-50'):
        """
        Complete simple analysis
        """
        print("=" * 60)
        print("SIMPLE MONOPOLE STRUCTURAL ANALYSIS")
        print("=" * 60)
        print()
        
        # 1. Calculate dead load
        dead_load_kg = self.calculate_dead_load(sections)
        print()
        
        # 2. Calculate maximum load capacity
        max_load_kg, allowable_moment = self.calculate_max_load_capacity(sections, steel_grade)
        print()
        
        # 3. Calculate utilization ratio
        total_applied_load = dead_load_kg + applied_load_kg
        utilization_ratio = self.calculate_utilization_from_load(total_applied_load, max_load_kg)
        
        print("UTILIZATION ANALYSIS:")
        print("-" * 40)
        print(f"Dead Load: {dead_load_kg:.1f} kg")
        print(f"Applied Load: {applied_load_kg:.1f} kg")
        print(f"Total Load: {total_applied_load:.1f} kg")
        print(f"Maximum Capacity: {max_load_kg:.0f} kg")
        print(f"Utilization Ratio: {utilization_ratio:.3f} ({utilization_ratio*100:.1f}%)")
        print()
        
        # Safety assessment
        if utilization_ratio > 1.0:
            print("⚠️  CRITICAL: Structure is overstressed!")
        elif utilization_ratio > 0.8:
            print("⚠️  WARNING: High utilization - consider larger sections")
        elif utilization_ratio > 0.6:
            print("✅ GOOD: Structure is adequately designed")
        else:
            print("✅ CONSERVATIVE: Structure has significant reserve capacity")
        
        print()
        print("=" * 60)
        print("SUMMARY:")
        print(f"Pole Weight: {dead_load_kg:.1f} kg")
        print(f"Max Additional Load: {max_load_kg - dead_load_kg:.0f} kg")
        print(f"Current Utilization: {utilization_ratio:.3f}")
        print("=" * 60)
        
        return {
            'dead_load_kg': dead_load_kg,
            'max_load_kg': max_load_kg,
            'utilization_ratio': utilization_ratio,
            'allowable_moment': allowable_moment
        }

# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = SimpleMonopoleAnalysis()
    
    # Define monopole sections (ALL IN MM)
    # Realistic example: 15m total pole height, 1200mm base diameter, 8mm wall thickness
    monopole_sections = [
        {
            'height': 7500,            # 7.5m bottom section
            'diameter_bottom': 1200,   # 1.2m diameter at bottom
            'diameter_top': 1000,      # 1.0m diameter at top of section
            'thickness': 10            # 10mm wall thickness
        },
        {
            'height': 7500,            # 7.5m top section  
            'diameter_bottom': 1000,   # 1.0m diameter at bottom
            'diameter_top': 800,       # 0.8m diameter at top
            'thickness': 8             # 8mm wall thickness
        }
    ]
    
    # Analysis parameters
    applied_equipment_load = 0    # kg (NO equipment - empty tower as specified)
    steel_grade = 'A572-50'
    
    # Run analysis
    results = analyzer.analyze_monopole(monopole_sections, applied_equipment_load, steel_grade)
