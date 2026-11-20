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
    
    def calculate_anchor_embedment_capacity(self, foundation_params, applied_moment):
        """
        Calculate anchor bolt pullout/embedment capacity per ACI 318
        This is often the governing failure mode for monopole foundations
        """
        # Extract parameters
        bolt_dia = foundation_params['bolt_diameter'] / 1000  # m
        anchor_length = foundation_params['anchor_length'] / 1000  # m
        num_bolts = foundation_params['number_of_bolts']
        fc_mpa = foundation_params['concrete_strength']  # MPa
        bolt_circle_dia = foundation_params['bolt_circle_diameter'] / 1000  # m
        
        print("ANCHOR EMBEDMENT CAPACITY (ACI 318):")
        print("-" * 40)
        
        # Effective embedment depth (mm to m already converted)
        hef = anchor_length
        
        # Concrete breakout strength (simplified ACI 318-14 Eq. 17.4.2.2a)
        # Ncb = (Anc/Anco) * ψec * ψed * ψc * ψcp * Nb
        # Where Nb = kc * λa * sqrt(f'c) * hef^1.5
        
        # Basic concrete breakout strength
        kc = 24  # Coefficient for cast-in anchors
        lambda_a = 1.0  # Modification factor for lightweight concrete (normal weight)
        fc_psi = fc_mpa * 145.038  # Convert MPa to psi for ACI formula
        
        # Nb in pounds, then convert to N
        Nb_lbs = kc * lambda_a * (fc_psi ** 0.5) * ((hef * 1000) ** 1.5)  # hef in mm for formula
        Nb_n = Nb_lbs * 4.44822  # Convert lbs to N
        
        # Simplified factors (conservative)
        psi_ec = 1.0  # Eccentricity factor (assume concentric for group)
        psi_ed = 0.7  # Edge distance factor (conservative - assume near edge)
        psi_c = 1.0   # Cracking factor (assume cracked concrete)
        psi_cp = 1.0  # Splitting factor
        
        # Projected area factors (simplified - assume no overlap)
        Anc_Anco = 1.0  # For conservative estimate
        
        # Concrete breakout capacity per bolt
        Ncb_per_bolt = Anc_Anco * psi_ec * psi_ed * psi_c * psi_cp * Nb_n
        
        # Bond/adhesion strength (simplified)
        # Ta = π * db * hef * τ
        # Where τ is bond stress (typically 0.5-1.5 MPa for mechanical anchors)
        tau_mpa = 1.0  # Conservative bond stress
        bond_capacity_per_bolt = math.pi * bolt_dia * hef * tau_mpa * 1e6  # N
        
        # Governing capacity is minimum of breakout and bond
        pullout_capacity_per_bolt = min(Ncb_per_bolt, bond_capacity_per_bolt)
        
        # Apply safety factor
        safety_factor = 4.0  # Higher SF for concrete failure (ACI uses factors ~3-5)
        allowable_pullout_per_bolt = pullout_capacity_per_bolt / safety_factor
        
        # Calculate actual tension demand
        lever_arm = bolt_circle_dia / 2
        bolts_in_tension = num_bolts / 2
        
        if bolts_in_tension > 0 and lever_arm > 0:
            tension_per_bolt = applied_moment / lever_arm / bolts_in_tension
        else:
            tension_per_bolt = 0
        
        # Total capacity for tension bolts
        total_pullout_capacity = allowable_pullout_per_bolt * bolts_in_tension
        total_embedment_moment_capacity = total_pullout_capacity * lever_arm
        
        # Utilization ratio for embedment
        if allowable_pullout_per_bolt > 0:
            embedment_utilization = tension_per_bolt / allowable_pullout_per_bolt
        else:
            embedment_utilization = 0
        
        print(f"Effective Embedment Depth: {hef*1000:.0f} mm")
        print(f"Concrete Strength: {fc_mpa} MPa ({fc_psi:.0f} psi)")
        print(f"Concrete Breakout Capacity/bolt: {Ncb_per_bolt/1000:.1f} kN")
        print(f"Bond/Adhesion Capacity/bolt: {bond_capacity_per_bolt/1000:.1f} kN")
        print(f"Governing Pullout Capacity/bolt: {pullout_capacity_per_bolt/1000:.1f} kN")
        print(f"Allowable Pullout/bolt (SF={safety_factor}): {allowable_pullout_per_bolt/1000:.1f} kN")
        print(f"Applied Tension/bolt: {tension_per_bolt/1000:.1f} kN")
        print(f"Embedment Utilization: {embedment_utilization:.3f} ({embedment_utilization*100:.1f}%)")
        print(f"Embedment Moment Capacity: {total_embedment_moment_capacity/1000:.0f} kN⋅m")
        print()
        
        if embedment_utilization > 0.9:
            print("⚠️  CRITICAL: Anchor embedment is highly utilized!")
        elif embedment_utilization > 0.8:
            print("⚠️  WARNING: High embedment utilization")
        
        return total_embedment_moment_capacity, embedment_utilization
    
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
    
    def analyze_monopole(self, sections, applied_load_kg=0, wind_speed_ms=0, exposure='C', steel_grade='S355', foundation_params=None):
        """
        Complete analysis with foundation capacity
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
        embedment_utilization = 0
        if foundation_params:
            allowable_foundation_moment, bolt_capacity = self.calculate_foundation_capacity(foundation_params)
            
            # Calculate embedment capacity - this often governs!
            # Use a preliminary moment estimate for initial check
            preliminary_moment = wind_speed_ms * 1000 if wind_speed_ms > 0 else 50000
            allowable_embedment_moment, embedment_util_prelim = self.calculate_anchor_embedment_capacity(
                foundation_params, preliminary_moment
            )
            
            # Governing capacity is the MINIMUM of pole, bolt tensile, and embedment
            governing_moment = min(allowable_pole_moment, allowable_foundation_moment, allowable_embedment_moment)
            
            if allowable_embedment_moment < allowable_foundation_moment and allowable_embedment_moment < allowable_pole_moment:
                print("⚠️  ANCHOR EMBEDMENT GOVERNS (weakest element)")
                governing_element = "ANCHOR EMBEDMENT"
            elif allowable_foundation_moment < allowable_pole_moment:
                print("⚠️  FOUNDATION GOVERNS (weaker than pole)")
                governing_element = "FOUNDATION (BOLT TENSILE)"
            else:
                print("✅ POLE GOVERNS (foundation is stronger)")
                governing_element = "POLE"
            
            print(f"Governing Allowable Moment: {governing_moment:.0f} N⋅m")
            print()
        else:
            governing_moment = allowable_pole_moment
            governing_element = "POLE (no foundation data)"
            allowable_foundation_moment = None
            allowable_embedment_moment = None
            bolt_capacity = None
            print("⚠️  No foundation data provided - analyzing pole only")
            print()
        
        # 5. Calculate axial loads (vertical forces)
        total_axial_load_n = (dead_load_kg + applied_load_kg) * self.gravity
        
        print("AXIAL LOAD ANALYSIS:")
        print("-" * 40)
        print(f"Dead Load: {dead_load_kg:.1f} kg ({dead_load_kg * self.gravity:.0f} N)")
        print(f"Applied Load: {applied_load_kg:.1f} kg ({applied_load_kg * self.gravity:.0f} N)")
        print(f"Total Axial Load: {(dead_load_kg + applied_load_kg):.1f} kg ({total_axial_load_n:.0f} N)")
        print("Note: Axial loads do NOT create bending moment")
        print()
        
        # 6. Case 1: WITHOUT WIND
        print("CASE 1: WITHOUT WIND LOAD")
        print("-" * 40)
        
        # Applied load moment (only horizontal loads or loads at top creating moment)
        applied_load_moment = applied_load_kg * self.gravity * total_height_m
        
        # Total bending moment without wind (only from applied loads)
        total_moment_no_wind = applied_load_moment
        
        # Available moment for additional loads
        if total_height_m > 0:
            max_additional_load_no_wind = governing_moment / (self.gravity * total_height_m)
        else:
            max_additional_load_no_wind = 0
        
        # Utilization without wind
        if governing_moment > 0:
            utilization_no_wind = total_moment_no_wind / governing_moment
        else:
            utilization_no_wind = 0
        
        print(f"Applied Load Moment: {applied_load_moment:.0f} N⋅m")
        print(f"Total Bending Moment: {total_moment_no_wind:.0f} N⋅m")
        print(f"Available Moment Capacity: {governing_moment:.0f} N⋅m")
        print(f"Max Additional Load Capacity: {max_additional_load_no_wind:.0f} kg")
        print(f"Utilization Ratio: {utilization_no_wind:.3f} ({utilization_no_wind*100:.1f}%)")
        print()
        
        # 7. Case 2: WITH WIND (if wind speed > 0)
        if wind_speed_ms > 0:
            wind_force, wind_moment = self.calculate_wind_load(sections, wind_speed_ms, exposure)
            
            print("CASE 2: WITH WIND LOAD")
            print("-" * 40)
            
            # Total bending moment with wind
            total_moment_with_wind = applied_load_moment + wind_moment
            
            # Available moment for additional loads (after accounting for wind)
            available_moment_with_wind = governing_moment - wind_moment
            
            if available_moment_with_wind > 0 and total_height_m > 0:
                max_additional_load_with_wind = available_moment_with_wind / (self.gravity * total_height_m)
            else:
                max_additional_load_with_wind = 0
            
            # Utilization with wind
            if governing_moment > 0:
                utilization_with_wind = total_moment_with_wind / governing_moment
            else:
                utilization_with_wind = 0
            
            # Calculate anchor bolt tension (if foundation data provided)
            if foundation_params and bolt_capacity:
                lever_arm = foundation_params['bolt_circle_diameter'] / 2000  # m
                num_bolts_tension = foundation_params['number_of_bolts'] / 2
                if num_bolts_tension > 0:
                    max_bolt_tension = total_moment_with_wind / lever_arm / num_bolts_tension
                    bolt_utilization = max_bolt_tension / bolt_capacity
                    
                    # Recalculate embedment utilization with actual moment
                    _, embedment_utilization = self.calculate_anchor_embedment_capacity(
                        foundation_params, total_moment_with_wind
                    )
                    
                    print(f"Max Anchor Bolt Tension: {max_bolt_tension/1000:.1f} kN")
                    print(f"Bolt Tensile Capacity: {bolt_capacity/1000:.1f} kN")
                    print(f"Bolt Tensile Utilization: {bolt_utilization:.3f} ({bolt_utilization*100:.1f}%)")
                    print(f"Bolt Embedment Utilization: {embedment_utilization:.3f} ({embedment_utilization*100:.1f}%)")
                    print()
            print(f"Applied Load Moment: {applied_load_moment:.0f} N⋅m")
            print(f"Wind Moment: {wind_moment:.0f} N⋅m")
            print(f"Total Bending Moment: {total_moment_with_wind:.0f} N⋅m")
            print(f"Available Moment for Additional Load: {available_moment_with_wind:.0f} N⋅m")
            print(f"Max Additional Load Capacity: {max_additional_load_with_wind:.0f} kg")
            print(f"Utilization Ratio: {utilization_with_wind:.3f} ({utilization_with_wind*100:.1f}%)")
            print(f"Governing Element: {governing_element}")
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
        print(f"Governing Element: {governing_element}")
        if foundation_params and embedment_utilization > 0:
            print(f"Critical Embedment Utilization: {embedment_utilization:.3f} ({embedment_utilization*100:.1f}%)")
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
            'embedment_utilization': embedment_utilization,
            'governing_moment': governing_moment,
            'governing_element': governing_element
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
    wind_speed = 30              # m/s (set to 0 for no wind analysis)
    exposure_category = 'C'      # Open terrain
    steel_grade = 'S355'         # European steel standard
    
    # Foundation parameters based on your specs
    foundation_parameters = {
        'base_plate_diameter': 1560,      # mm (from your specs)
        'bolt_circle_diameter': 1560,     # mm (bolt circle = width from your specs)
        'number_of_bolts': 30,            # From your bolt detail drawing
        'bolt_diameter': 32,              # mm (M32 bolts from your specs)
        'bolt_grade': 420,                # MPa (yield strength, Fy for B7 studs)
        'concrete_strength': 21,          # MPa (from your specs)
        'anchor_length': 1300             # mm (from your anchor assembly)
    }
    
    # Run analysis WITH foundation
    results = analyzer.analyze_monopole(
        monopole_sections, 
        applied_equipment_load, 
        wind_speed, 
        exposure_category, 
        steel_grade,
        foundation_parameters  # Include foundation
    )
