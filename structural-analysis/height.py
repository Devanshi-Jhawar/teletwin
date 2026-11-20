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
    
    def calculate_kz(self, height_m, exposure='C'):
        """Calculate height-dependent velocity pressure coefficient"""
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
                # ASCE 7 formula for Exposure C
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
            return 0.85  # Default to Exposure C
    
    def calculate_wind_load(self, sections, wind_speed_ms, exposure='C'):
        """
        Calculate wind load based on ASCE 7 (METRIC VERSION) with height-varying pressure
        wind_speed_ms: wind speed in m/s
        sections: pole sections in mm
        """
        # Other factors
        kzt = 1.0  # Topographic factor (flat terrain)
        kd = 0.95  # Directionality factor
        
        # Force coefficient for round poles
        cf = 0.5  # Smooth circular cylinder
        
        total_wind_force = 0
        wind_moment = 0
        height_cumulative = 0
        
        print("WIND LOAD ANALYSIS (Height-Varying Pressure):")
        print("-" * 40)
        print(f"Wind Speed: {wind_speed_ms} m/s ({wind_speed_ms * 3.6:.1f} km/h)")
        print(f"Exposure Category: {exposure}")
        print()
        
        for i, section in enumerate(sections):
            # Convert mm to meters
            h = section['height'] / 1000  # m
            d_top = section['diameter_top'] / 1000  # m
            d_bottom = section['diameter_bottom'] / 1000  # m
            
            # Average diameter and projected area
            d_avg = (d_top + d_bottom) / 2
            projected_area = d_avg * h  # m²
            
            # Height to center of this section from base
            section_center_height = height_cumulative + h/2
            
            # Calculate Kz at the center height of this section
            kz = self.calculate_kz(section_center_height, exposure)
            
            # Velocity pressure at this height
            # qz = 0.613 * Kz * Kzt * Kd * V²  where V is in m/s
            qz = 0.613 * kz * kzt * kd * (wind_speed_ms ** 2)  # N/m² (Pa)
            
            # Wind force on this section
            wind_force = qz * cf * projected_area  # N
            
            # Moment contribution
            moment_contribution = wind_force * section_center_height  # N⋅m
            
            total_wind_force += wind_force
            wind_moment += moment_contribution
            height_cumulative += h
            
            print(f"Section {i+1}:")
            print(f"  Height Range: {height_cumulative - h:.1f} to {height_cumulative:.1f} m")
            print(f"  Center Height: {section_center_height:.1f} m")
            print(f"  Kz at Center: {kz:.3f}")
            print(f"  Avg Diameter: {d_avg*1000:.0f} mm") 
            print(f"  Projected Area: {projected_area:.2f} m²")
            print(f"  Velocity Pressure: {qz:.1f} Pa")
            print(f"  Wind Force: {wind_force:.0f} N")
            print(f"  Moment: {moment_contribution:.0f} N⋅m")
            print()
        
        print(f"TOTAL WIND FORCE: {total_wind_force:.0f} N")
        print(f"TOTAL WIND MOMENT: {wind_moment:.0f} N⋅m")
        print()
        
        return total_wind_force, wind_moment

    def calculate_moment_capacity(self, diameter_mm, thickness_mm, steel_grade='S355'):
        """
        Calculate bending moment capacity of circular hollow section
        """
        # Steel yield strengths in MPa
        yield_strengths = {
            'A36': 248,      # MPa
            'A572-50': 345,  # MPa
            'A992': 345,     # MPa
            'S355': 355      # MPa (European standard)
        }
        fy_mpa = yield_strengths.get(steel_grade, 355)
        
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
    
    def calculate_foundation_capacity(self, foundation_params):
        """
        Calculate foundation and anchor bolt capacity
        """
        # Extract parameters
        base_plate_dia = foundation_params['base_plate_diameter'] / 1000  # m
        bolt_circle_dia = foundation_params['bolt_circle_diameter'] / 1000  # m
        num_bolts = foundation_params['number_of_bolts']
        bolt_diameter = foundation_params['bolt_diameter'] / 1000  # m
        bolt_grade = foundation_params['bolt_grade']  # MPa
        concrete_strength = foundation_params['concrete_strength']  # MPa
        anchor_length = foundation_params['anchor_length'] / 1000  # m
        
        print("FOUNDATION CAPACITY ANALYSIS:")
        print("-" * 40)
        
        # Bolt tensile capacity
        bolt_area = math.pi * (bolt_diameter ** 2) / 4  # m²
        bolt_tensile_capacity_per_bolt = bolt_area * bolt_grade * 1e6 * 0.75  # N (75% of yield)
        
        # Maximum bolt tension occurs at windward side
        # For circular bolt pattern, effective lever arm
        lever_arm = bolt_circle_dia / 2  # m
        
        # Moment capacity based on anchor bolts
        # Assuming compression side resists through bearing
        # Tension side: T = M / lever_arm
        # Available bolts in tension = num_bolts / 2 (simplified)
        bolts_in_tension = num_bolts / 2
        total_bolt_capacity = bolts_in_tension * bolt_tensile_capacity_per_bolt  # N
        
        # Foundation moment capacity
        foundation_moment_capacity = total_bolt_capacity * lever_arm  # N⋅m
        
        # Apply safety factor
        safety_factor = 2.0
        allowable_foundation_moment = foundation_moment_capacity / safety_factor
        
        print(f"Base Plate Diameter: {base_plate_dia*1000:.0f} mm")
        print(f"Bolt Circle Diameter: {bolt_circle_dia*1000:.0f} mm")
        print(f"Number of Bolts: {num_bolts}")
        print(f"Bolt Diameter: {bolt_diameter*1000:.0f} mm")
        print(f"Bolt Grade: {bolt_grade} MPa")
        print(f"Bolt Area (each): {bolt_area*1e6:.0f} mm²")
        print(f"Bolt Tensile Capacity (each): {bolt_tensile_capacity_per_bolt/1000:.1f} kN")
        print(f"Bolts in Tension: {bolts_in_tension:.0f}")
        print(f"Total Bolt Tension Capacity: {total_bolt_capacity/1000:.1f} kN")
        print(f"Lever Arm: {lever_arm*1000:.0f} mm")
        print(f"Foundation Moment Capacity: {foundation_moment_capacity/1000:.0f} kN⋅m")
        print(f"Allowable Foundation Moment (SF={safety_factor}): {allowable_foundation_moment/1000:.0f} kN⋅m")
        print()
        
        return allowable_foundation_moment, bolt_tensile_capacity_per_bolt
    
    def calculate_load_combinations(self, dead_load_n, wind_moment_nm, applied_moment_nm, governing_moment):
        """
        Calculate utilization for different load combinations per ASCE 7
        """
        print("=" * 70)
        print("LOAD COMBINATIONS ANALYSIS")
        print("=" * 70)
        print()
        
        combinations = {}
        
        # LRFD (Load and Resistance Factor Design) Combinations
        print("LRFD COMBINATIONS:")
        print("-" * 70)
        
        # LC1: 1.4D (Dead load only - but dead load creates no moment!)
        lc1_moment = 1.4 * 0  # Dead load creates no bending moment
        lc1_util = lc1_moment / governing_moment
        combinations['LRFD 1.4D'] = {'moment': lc1_moment, 'utilization': lc1_util}
        print(f"LC1: 1.4D")
        print(f"  Moment: {lc1_moment:.0f} N⋅m")
        print(f"  Utilization: {lc1_util:.3f} ({lc1_util*100:.1f}%)")
        print()
        
        # LC2: 1.2D + 1.6W + 0.5L (Main wind combination)
        lc2_moment = applied_moment_nm + 1.6 * wind_moment_nm
        lc2_util = lc2_moment / governing_moment
        combinations['LRFD 1.2D+1.6W'] = {'moment': lc2_moment, 'utilization': lc2_util}
        print(f"LC2: 1.2D + 1.6W (Main Wind Combination)")
        print(f"  Applied Moment: {applied_moment_nm:.0f} N⋅m")
        print(f"  1.6 × Wind Moment: {1.6 * wind_moment_nm:.0f} N⋅m")
        print(f"  Total Moment: {lc2_moment:.0f} N⋅m")
        print(f"  Utilization: {lc2_util:.3f} ({lc2_util*100:.1f}%)")
        print()
        
        # LC3: 1.2D + 1.0W + 1.0L (Alternate wind combination)
        lc3_moment = applied_moment_nm + 1.0 * wind_moment_nm
        lc3_util = lc3_moment / governing_moment
        combinations['LRFD 1.2D+1.0W'] = {'moment': lc3_moment, 'utilization': lc3_util}
        print(f"LC3: 1.2D + 1.0W + 1.0L (Alternate)")
        print(f"  Applied Moment: {applied_moment_nm:.0f} N⋅m")
        print(f"  1.0 × Wind Moment: {1.0 * wind_moment_nm:.0f} N⋅m")
        print(f"  Total Moment: {lc3_moment:.0f} N⋅m")
        print(f"  Utilization: {lc3_util:.3f} ({lc3_util*100:.1f}%)")
        print()
        
        # LC4: 0.9D + 1.6W (Minimum dead load with wind - uplift check)
        lc4_moment = applied_moment_nm + 1.6 * wind_moment_nm
        lc4_util = lc4_moment / governing_moment
        combinations['LRFD 0.9D+1.6W'] = {'moment': lc4_moment, 'utilization': lc4_util}
        print(f"LC4: 0.9D + 1.6W (Uplift Check)")
        print(f"  Applied Moment: {applied_moment_nm:.0f} N⋅m")
        print(f"  1.6 × Wind Moment: {1.6 * wind_moment_nm:.0f} N⋅m")
        print(f"  Total Moment: {lc4_moment:.0f} N⋅m")
        print(f"  Utilization: {lc4_util:.3f} ({lc4_util*100:.1f}%)")
        print()
        
        # ASD (Allowable Stress Design) Combinations
        print("ASD COMBINATIONS:")
        print("-" * 70)
        
        # LC5: D (Dead load only)
        lc5_moment = 0  # Dead load creates no bending moment
        lc5_util = lc5_moment / governing_moment
        combinations['ASD D'] = {'moment': lc5_moment, 'utilization': lc5_util}
        print(f"LC5: D (Dead Only)")
        print(f"  Moment: {lc5_moment:.0f} N⋅m")
        print(f"  Utilization: {lc5_util:.3f} ({lc5_util*100:.1f}%)")
        print()
        
        # LC6: D + W (Basic wind combination)
        lc6_moment = applied_moment_nm + wind_moment_nm
        lc6_util = lc6_moment / governing_moment
        combinations['ASD D+W'] = {'moment': lc6_moment, 'utilization': lc6_util}
        print(f"LC6: D + W (Basic Wind)")
        print(f"  Applied Moment: {applied_moment_nm:.0f} N⋅m")
        print(f"  Wind Moment: {wind_moment_nm:.0f} N⋅m")
        print(f"  Total Moment: {lc6_moment:.0f} N⋅m")
        print(f"  Utilization: {lc6_util:.3f} ({lc6_util*100:.1f}%)")
        print()
        
        # LC7: D + 0.75W + 0.75L (Alternate combination)
        lc7_moment = applied_moment_nm + 0.75 * wind_moment_nm
        lc7_util = lc7_moment / governing_moment
        combinations['ASD D+0.75W'] = {'moment': lc7_moment, 'utilization': lc7_util}
        print(f"LC7: D + 0.75W + 0.75L (Alternate)")
        print(f"  Applied Moment: {applied_moment_nm:.0f} N⋅m")
        print(f"  0.75 × Wind Moment: {0.75 * wind_moment_nm:.0f} N⋅m")
        print(f"  Total Moment: {lc7_moment:.0f} N⋅m")
        print(f"  Utilization: {lc7_util:.3f} ({lc7_util*100:.1f}%)")
        print()
        
        # LC8: 0.6D + 0.6W (Minimum loads)
        lc8_moment = applied_moment_nm + 0.6 * wind_moment_nm
        lc8_util = lc8_moment / governing_moment
        combinations['ASD 0.6D+0.6W'] = {'moment': lc8_moment, 'utilization': lc8_util}
        print(f"LC8: 0.6D + 0.6W (Minimum)")
        print(f"  Applied Moment: {applied_moment_nm:.0f} N⋅m")
        print(f"  0.6 × Wind Moment: {0.6 * wind_moment_nm:.0f} N⋅m")
        print(f"  Total Moment: {lc8_moment:.0f} N⋅m")
        print(f"  Utilization: {lc8_util:.3f} ({lc8_util*100:.1f}%)")
        print()
        
        # Find governing combination
        max_utilization = 0
        governing_combo = None
        
        for name, data in combinations.items():
            if data['utilization'] > max_utilization:
                max_utilization = data['utilization']
                governing_combo = name
        
        print("=" * 70)
        print("GOVERNING LOAD COMBINATION:")
        print("-" * 70)
        print(f"Combination: {governing_combo}")
        print(f"Moment: {combinations[governing_combo]['moment']:.0f} N⋅m")
        print(f"Utilization: {max_utilization:.3f} ({max_utilization*100:.1f}%)")
        
        if max_utilization > 1.0:
            print("STATUS: FAIL - Structure is overstressed!")
        elif max_utilization > 0.9:
            print("STATUS: CRITICAL - Very high utilization")
        elif max_utilization > 0.8:
            print("STATUS: WARNING - High utilization")
        elif max_utilization > 0.6:
            print("STATUS: GOOD - Adequately designed")
        else:
            print("STATUS: CONSERVATIVE - Significant reserve capacity")
        
        print("=" * 70)
        print()
        
        return combinations, governing_combo, max_utilization
    
    def analyze_monopole(self, sections, applied_load_kg=0, wind_speed_ms=0, exposure='C', steel_grade='S355', foundation_params=None):
        """
        Complete analysis with foundation capacity and load combinations
        """
        print("=" * 70)
        print("MONOPOLE STRUCTURAL ANALYSIS")
        print("=" * 70)
        print()
        
        # 1. Calculate dead load
        dead_load_kg = self.calculate_dead_load(sections)
        dead_load_n = dead_load_kg * self.gravity
        print()
        
        # 2. Calculate total height
        total_height_m = sum(section['height'] for section in sections) / 1000
        
        # 3. Calculate structural capacity (POLE)
        bottom_section = sections[0]
        d_bottom = bottom_section['diameter_bottom']
        thickness = bottom_section['thickness']
        
        pole_moment_capacity, section_modulus = self.calculate_moment_capacity(d_bottom, thickness, steel_grade)
        
        # Apply safety factor
        safety_factor = 2.0
        allowable_pole_moment = pole_moment_capacity / safety_factor
        
        print("POLE STRUCTURAL CAPACITY:")
        print("-" * 40)
        print(f"Bottom Section Diameter: {d_bottom} mm")
        print(f"Wall Thickness: {thickness} mm")
        print(f"Steel Grade: {steel_grade}")
        print(f"Section Modulus: {section_modulus*1e6:.0f} mm³")
        print(f"Moment Capacity: {pole_moment_capacity:.0f} N⋅m")
        print(f"Allowable Moment (SF={safety_factor}): {allowable_pole_moment:.0f} N⋅m")
        print(f"Total Height: {total_height_m:.1f} m")
        print()
        
        # 4. Calculate foundation capacity (if provided)
        if foundation_params:
            allowable_foundation_moment, bolt_capacity = self.calculate_foundation_capacity(foundation_params)
            
            # Governing capacity is the MINIMUM of pole and foundation
            governing_moment = min(allowable_pole_moment, allowable_foundation_moment)
            
            if allowable_foundation_moment < allowable_pole_moment:
                print("FOUNDATION GOVERNS (weaker than pole)")
                governing_element = "FOUNDATION"
            else:
                print("POLE GOVERNS (foundation is stronger)")
                governing_element = "POLE"
            
            print(f"Governing Allowable Moment: {governing_moment:.0f} N⋅m")
            print()
        else:
            governing_moment = allowable_pole_moment
            governing_element = "POLE (no foundation data)"
            allowable_foundation_moment = None
            bolt_capacity = None
        
        # 5. Calculate wind loads
        if wind_speed_ms > 0:
            wind_force, wind_moment = self.calculate_wind_load(sections, wind_speed_ms, exposure)
        else:
            wind_force = 0
            wind_moment = 0
        
        # 6. Calculate applied load moment
        applied_moment = applied_load_kg * self.gravity * total_height_m
        
        # 7. Calculate load combinations
        combinations, governing_combo, max_utilization = self.calculate_load_combinations(
            dead_load_n, wind_moment, applied_moment, governing_moment
        )
        
        # 8. Calculate remaining capacity based on governing combination
        remaining_moment = governing_moment - combinations[governing_combo]['moment']
        if remaining_moment > 0 and total_height_m > 0:
            remaining_load_capacity = remaining_moment / (self.gravity * total_height_m)
        else:
            remaining_load_capacity = 0
        
        print("=" * 70)
        print("FINAL SUMMARY:")
        print("-" * 70)
        print(f"Pole Weight: {dead_load_kg:.1f} kg")
        print(f"Wind Speed: {wind_speed_ms} m/s ({wind_speed_ms * 3.6:.1f} km/h)")
        print(f"Applied Equipment Load: {applied_load_kg:.1f} kg")
        print(f"Governing Element: {governing_element}")
        print(f"Governing Load Combination: {governing_combo}")
        print(f"Maximum Utilization: {max_utilization:.3f} ({max_utilization*100:.1f}%)")
        print(f"Remaining Load Capacity: {remaining_load_capacity:.0f} kg")
        print("=" * 70)
        
        return {
            'dead_load_kg': dead_load_kg,
            'wind_force_n': wind_force,
            'wind_moment_nm': wind_moment,
            'governing_combo': governing_combo,
            'max_utilization': max_utilization,
            'remaining_capacity_kg': remaining_load_capacity,
            'all_combinations': combinations
        }

# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = MonopoleStructuralAnalysis()
    
    # Define monopole sections per your specifications (ALL IN MM)
    monopole_sections = [
        {
            'height': 10921,           # Section 1 (Bottom)
            'diameter_bottom': 1200,   # 1200 mm at bottom
            'diameter_top': 937.9,     # 937.9 mm at top
            'thickness': 5             # 5 mm wall thickness
        },
        {
            'height': 10921,           # Section 2 (Middle)
            'diameter_bottom': 985.3,  # 985.3 mm at bottom
            'diameter_top': 723.2,     # 723.2 mm at top
            'thickness': 5             # 5 mm wall thickness
        },
        {
            'height': 10921,           # Section 3 (Top)
            'diameter_bottom': 762.1,  # 762.1 mm at bottom
            'diameter_top': 500,       # 500 mm at top
            'thickness': 5             # 5 mm wall thickness
        }
    ]
    
    # Analysis parameters
    applied_equipment_load = 0    # kg (NO equipment - empty tower)
    wind_speed = 44.44           # m/s (converted from 160 km/h)
    exposure_category = 'C'      # Open terrain
    steel_grade = 'S355'         # European steel standard
    
    # Foundation parameters based on your specs
    foundation_parameters = {
        'base_plate_diameter': 1560,      # mm
        'bolt_circle_diameter': 1560,     # mm
        'number_of_bolts': 30,            # bolts
        'bolt_diameter': 32,              # mm (M32 bolts)
        'bolt_grade': 420,                # MPa
        'concrete_strength': 21,          # MPa
        'anchor_length': 1300             # mm
    }
    
    # Run analysis WITH foundation and load combinations
    results = analyzer.analyze_monopole(
        monopole_sections, 
        applied_equipment_load, 
        wind_speed, 
        exposure_category, 
        steel_grade,
        foundation_parameters
    )
