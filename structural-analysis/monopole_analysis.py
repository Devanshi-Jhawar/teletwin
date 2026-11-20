import math

class MonopoleStructuralAnalysis:
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
    
    def calculate_wind_load(self, sections, wind_speed_ms, exposure='C'):
        """
        Calculate wind load based on ASCE 7 (METRIC VERSION)
        wind_speed_ms: wind speed in m/s
        sections: pole sections in mm
        """
        # Exposure coefficients (simplified)
        kz_factors = {'B': 0.7, 'C': 0.85, 'D': 1.0}
        kz = kz_factors.get(exposure, 0.85)
        
        # Other factors
        kzt = 1.0  # Topographic factor (flat terrain)
        kd = 0.95  # Directionality factor
        
        # Velocity pressure (metric formula)
        # qz = 0.613 * Kz * Kzt * Kd * V²  where V is in m/s
        qz = 0.613 * kz * kzt * kd * (wind_speed_ms ** 2)  # N/m² (Pa)
        
        # Force coefficient for round poles
        cf = 0.5  # Smooth circular cylinder
        
        total_wind_force = 0
        wind_moment = 0
        height_cumulative = 0
        
        print("WIND LOAD ANALYSIS:")
        print("-" * 40)
        print(f"Wind Speed: {wind_speed_ms} m/s")
        print(f"Exposure Category: {exposure}")
        print(f"Velocity Pressure qz: {qz:.1f} N/m²")
        print()
        
        for i, section in enumerate(sections):
            # Convert mm to meters
            h = section['height'] / 1000  # m
            d_top = section['diameter_top'] / 1000  # m
            d_bottom = section['diameter_bottom'] / 1000  # m
            
            # Average diameter and projected area
            d_avg = (d_top + d_bottom) / 2
            projected_area = d_avg * h  # m²
            
            # Wind force on this section
            wind_force = qz * cf * projected_area  # N
            
            # Height to center of this section from base
            section_center_height = height_cumulative + h/2
            
            # Moment contribution
            moment_contribution = wind_force * section_center_height  # N⋅m
            
            total_wind_force += wind_force
            wind_moment += moment_contribution
            height_cumulative += h
            
            print(f"Section {i+1}:")
            print(f"  Height: {section['height']} mm")
            print(f"  Avg Diameter: {d_avg*1000:.0f} mm") 
            print(f"  Projected Area: {projected_area:.2f} m²")
            print(f"  Wind Force: {wind_force:.0f} N")
            print(f"  Height to Center: {section_center_height:.1f} m")
            print(f"  Moment: {moment_contribution:.0f} N⋅m")
            print()
        
        print(f"TOTAL WIND FORCE: {total_wind_force:.0f} N")
        print(f"TOTAL WIND MOMENT: {wind_moment:.0f} N⋅m")
        print()
        
        return total_wind_force, wind_moment

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
    
    def analyze_monopole(self, sections, applied_load_kg=0, wind_speed_ms=0, exposure='C', steel_grade='A572-50'):
        """
        Complete analysis with correct structural mechanics
        Dead load creates axial compression, NOT bending moment
        """
        print("=" * 70)
        print("MONOPOLE STRUCTURAL ANALYSIS")
        print("=" * 70)
        print()
        
        # 1. Calculate dead load
        dead_load_kg = self.calculate_dead_load(sections)
        print()
        
        # 2. Calculate total height
        total_height_m = sum(section['height'] for section in sections) / 1000
        
        # 3. Calculate structural capacity
        bottom_section = sections[0]
        d_bottom = bottom_section['diameter_bottom']
        thickness = bottom_section['thickness']
        
        moment_capacity, section_modulus = self.calculate_moment_capacity(d_bottom, thickness, steel_grade)
        
        # Apply safety factor
        safety_factor = 2.0
        allowable_moment = moment_capacity / safety_factor
        
        print("STRUCTURAL CAPACITY:")
        print("-" * 40)
        print(f"Bottom Section Diameter: {d_bottom} mm")
        print(f"Wall Thickness: {thickness} mm")
        print(f"Steel Grade: {steel_grade}")
        print(f"Section Modulus: {section_modulus*1e6:.0f} mm³")
        print(f"Moment Capacity: {moment_capacity:.0f} N⋅m")
        print(f"Allowable Moment (SF={safety_factor}): {allowable_moment:.0f} N⋅m")
        print(f"Total Height: {total_height_m:.1f} m")
        print()
        
        # 4. Calculate axial loads (vertical forces)
        total_axial_load_n = (dead_load_kg + applied_load_kg) * self.gravity
        
        print("AXIAL LOAD ANALYSIS:")
        print("-" * 40)
        print(f"Dead Load: {dead_load_kg:.1f} kg ({dead_load_kg * self.gravity:.0f} N)")
        print(f"Applied Load: {applied_load_kg:.1f} kg ({applied_load_kg * self.gravity:.0f} N)")
        print(f"Total Axial Load: {(dead_load_kg + applied_load_kg):.1f} kg ({total_axial_load_n:.0f} N)")
        print("Note: Axial loads do NOT create bending moment")
        print()
        
        # 5. Case 1: WITHOUT WIND
        print("CASE 1: WITHOUT WIND LOAD")
        print("-" * 40)
        
        # Applied load moment (only horizontal loads or loads at top creating moment)
        applied_load_moment = applied_load_kg * self.gravity * total_height_m
        
        # Total bending moment without wind (only from applied loads)
        total_moment_no_wind = applied_load_moment
        
        # Available moment for additional loads
        available_moment_no_wind = allowable_moment
        max_additional_load_no_wind = available_moment_no_wind / (self.gravity * total_height_m)
        
        # Utilization without wind
        utilization_no_wind = total_moment_no_wind / allowable_moment
        
        print(f"Applied Load Moment: {applied_load_moment:.0f} N⋅m")
        print(f"Total Bending Moment: {total_moment_no_wind:.0f} N⋅m")
        print(f"Available Moment Capacity: {available_moment_no_wind:.0f} N⋅m")
        print(f"Max Additional Load Capacity: {max_additional_load_no_wind:.0f} kg")
        print(f"Utilization Ratio: {utilization_no_wind:.3f} ({utilization_no_wind*100:.1f}%)")
        print()
        
        # 6. Case 2: WITH WIND (if wind speed > 0)
        if wind_speed_ms > 0:
            wind_force, wind_moment = self.calculate_wind_load(sections, wind_speed_ms, exposure)
            
            print("CASE 2: WITH WIND LOAD")
            print("-" * 40)
            
            # Total bending moment with wind
            total_moment_with_wind = applied_load_moment + wind_moment
            
            # Available moment for additional loads (after accounting for wind)
            available_moment_with_wind = allowable_moment - wind_moment
            
            if available_moment_with_wind > 0:
                max_additional_load_with_wind = available_moment_with_wind / (self.gravity * total_height_m)
            else:
                max_additional_load_with_wind = 0
            
            # Utilization with wind
            utilization_with_wind = total_moment_with_wind / allowable_moment
            
            print(f"Applied Load Moment: {applied_load_moment:.0f} N⋅m")
            print(f"Wind Moment: {wind_moment:.0f} N⋅m")
            print(f"Total Bending Moment: {total_moment_with_wind:.0f} N⋅m")
            print(f"Available Moment for Additional Load: {available_moment_with_wind:.0f} N⋅m")
            print(f"Max Additional Load Capacity: {max_additional_load_with_wind:.0f} kg")
            print(f"Utilization Ratio: {utilization_with_wind:.3f} ({utilization_with_wind*100:.1f}%)")
            print()
            
            # Safety assessment
            if utilization_with_wind > 1.0:
                print("⚠️  CRITICAL: Structure is overstressed with wind!")
            elif utilization_with_wind > 0.8:
                print("⚠️  WARNING: High utilization with wind")
            elif utilization_with_wind > 0.6:
                print("✅ GOOD: Structure is adequately designed")
            else:
                print("✅ CONSERVATIVE: Structure has significant reserve capacity")
        else:
            # No wind case
            wind_force = 0
            wind_moment = 0
            max_additional_load_with_wind = max_additional_load_no_wind
            utilization_with_wind = utilization_no_wind
            
            # Safety assessment
            if utilization_no_wind > 1.0:
                print("⚠️  CRITICAL: Structure is overstressed!")
            elif utilization_no_wind > 0.8:
                print("⚠️  WARNING: High utilization")
            elif utilization_no_wind > 0.6:
                print("✅ GOOD: Structure is adequately designed")
            else:
                print("✅ CONSERVATIVE: Structure has significant reserve capacity")
        
        print()
        print("=" * 70)
        print("SUMMARY:")
        print(f"Pole Weight: {dead_load_kg:.1f} kg")
        print(f"Wind Speed: {wind_speed_ms} m/s")
        print(f"Max Additional Load (NO wind): {max_additional_load_no_wind:.0f} kg")
        print(f"Max Additional Load (WITH wind): {max_additional_load_with_wind:.0f} kg")
        print(f"Current Utilization (WITH wind): {utilization_with_wind:.3f}")
        print(f"Reduction due to wind: {max_additional_load_no_wind - max_additional_load_with_wind:.0f} kg")
        print("=" * 70)
        
        return {
            'dead_load_kg': dead_load_kg,
            'wind_force_n': wind_force,
            'wind_moment_nm': wind_moment,
            'max_additional_load_no_wind_kg': max_additional_load_no_wind,
            'max_additional_load_with_wind_kg': max_additional_load_with_wind,
            'utilization_no_wind': utilization_no_wind,
            'utilization_with_wind': utilization_with_wind,
            'allowable_moment': allowable_moment
        }

# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = MonopoleStructuralAnalysis()
    
    # Define monopole sections (ALL IN MM)
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
    applied_equipment_load = 0    # kg (NO equipment - empty tower)
    wind_speed = 30              # m/s (set to 0 for no wind analysis)
    exposure_category = 'C'      # Open terrain
    steel_grade = 'A572-50'
    
    # Run analysis
    results = analyzer.analyze_monopole(
        monopole_sections, 
        applied_equipment_load, 
        wind_speed, 
        exposure_category, 
        steel_grade
    )

