import math

class MonopoleStructuralAnalysis:
    def __init__(self):
        self.steel_density = 7850  # kg/m³
        self.gravity = 9.81  # m/s²
        
    def calculate_dead_load(self, sections):
        """Calculate dead load (weight) of monopole"""
        total_weight_kg = 0
        for section in sections:
            h_m = section['height'] / 1000
            d_avg_m = (section['diameter_top'] + section['diameter_bottom']) / 2000
            t_m = section['thickness'] / 1000
            
            volume = math.pi * h_m * ((d_avg_m/2)**2 - (d_avg_m/2 - t_m)**2)
            total_weight_kg += volume * self.steel_density
        
        return total_weight_kg
    
    def calculate_kz(self, height_m, exposure='C'):
        """Calculate height-dependent velocity pressure coefficient"""
        if exposure == 'C':
            if height_m < 4.6: return 0.85
            elif height_m < 6.1: return 0.90
            elif height_m < 9.1: return 0.98
            elif height_m < 12.2: return 1.04
            elif height_m < 15.2: return 1.09
            else: return 0.85 * (height_m / 4.6) ** (2/9.5)
        elif exposure == 'B':
            if height_m < 9.1: return 0.57
            elif height_m < 12.2: return 0.62
            elif height_m < 15.2: return 0.66
            else: return 0.57 * (height_m / 9.1) ** (2/7.0)
        elif exposure == 'D':
            if height_m < 4.6: return 1.03
            elif height_m < 6.1: return 1.08
            elif height_m < 9.1: return 1.16
            else: return 1.03 * (height_m / 4.6) ** (2/11.5)
        return 0.85
    
    def calculate_wind_load(self, sections, wind_speed_ms, exposure='C'):
        """Calculate wind load with height-varying pressure"""
        kzt, kd, cf = 1.0, 0.95, 0.5
        total_wind_force, wind_moment, height_cumulative = 0, 0, 0
        
        for section in sections:
            h = section['height'] / 1000
            d_avg = (section['diameter_top'] + section['diameter_bottom']) / 2000
            section_center_height = height_cumulative + h/2
            
            kz = self.calculate_kz(section_center_height, exposure)
            qz = 0.613 * kz * kzt * kd * (wind_speed_ms ** 2)
            wind_force = qz * cf * d_avg * h
            
            total_wind_force += wind_force
            wind_moment += wind_force * section_center_height
            height_cumulative += h
        
        return total_wind_force, wind_moment

    def calculate_moment_capacity(self, diameter_mm, thickness_mm, steel_grade='S355'):
        """Calculate bending moment capacity"""
        yield_strengths = {'A36': 248, 'A572-50': 345, 'A992': 345, 'S355': 355}
        fy_mpa = yield_strengths.get(steel_grade, 355)
        
        d_outer, t = diameter_mm / 1000, thickness_mm / 1000
        d_inner = d_outer - 2 * t
        
        section_modulus = (math.pi / 32) * (d_outer**4 - d_inner**4) / d_outer
        moment_capacity = section_modulus * fy_mpa * 1e6
        
        return moment_capacity, section_modulus
    
    def calculate_foundation_capacity(self, foundation_params):
        """Calculate foundation and anchor bolt capacity"""
        bolt_area = math.pi * (foundation_params['bolt_diameter'] / 2000) ** 2
        bolt_capacity = bolt_area * foundation_params['bolt_grade'] * 1e6 * 0.75
        
        lever_arm = foundation_params['bolt_circle_diameter'] / 2000
        bolts_in_tension = foundation_params['number_of_bolts'] / 2
        
        foundation_moment_capacity = bolts_in_tension * bolt_capacity * lever_arm
        allowable_foundation_moment = foundation_moment_capacity / 2.0
        
        return allowable_foundation_moment, bolt_capacity
    
    def calculate_load_combinations(self, wind_moment_nm, applied_moment_nm, governing_moment):
        """Calculate utilization for different load combinations"""
        combinations = {
            'LRFD 1.4D': {'moment': 0, 'utilization': 0},
            'LRFD 1.2D+1.6W': {'moment': applied_moment_nm + 1.6 * wind_moment_nm, 
                               'utilization': (applied_moment_nm + 1.6 * wind_moment_nm) / governing_moment},
            'LRFD 1.2D+1.0W': {'moment': applied_moment_nm + wind_moment_nm, 
                               'utilization': (applied_moment_nm + wind_moment_nm) / governing_moment},
            'LRFD 0.9D+1.6W': {'moment': applied_moment_nm + 1.6 * wind_moment_nm, 
                               'utilization': (applied_moment_nm + 1.6 * wind_moment_nm) / governing_moment},
            'ASD D': {'moment': 0, 'utilization': 0},
            'ASD D+W': {'moment': applied_moment_nm + wind_moment_nm, 
                        'utilization': (applied_moment_nm + wind_moment_nm) / governing_moment},
            'ASD D+0.75W': {'moment': applied_moment_nm + 0.75 * wind_moment_nm, 
                            'utilization': (applied_moment_nm + 0.75 * wind_moment_nm) / governing_moment},
            'ASD 0.6D+0.6W': {'moment': applied_moment_nm + 0.6 * wind_moment_nm, 
                              'utilization': (applied_moment_nm + 0.6 * wind_moment_nm) / governing_moment}
        }
        
        max_utilization = max(data['utilization'] for data in combinations.values())
        governing_combo = max(combinations.items(), key=lambda x: x[1]['utilization'])[0]
        
        return combinations, governing_combo, max_utilization
    
    def analyze_monopole(self, sections, applied_load_kg=0, wind_speed_ms=0, 
                        exposure='C', steel_grade='S355', foundation_params=None):
        """Complete structural analysis"""
        # Calculate loads
        dead_load_kg = self.calculate_dead_load(sections)
        total_height_m = sum(s['height'] for s in sections) / 1000
        
        # Calculate capacities
        bottom_section = sections[0]
        pole_moment_capacity, _ = self.calculate_moment_capacity(
            bottom_section['diameter_bottom'], bottom_section['thickness'], steel_grade)
        allowable_pole_moment = pole_moment_capacity / 2.0
        
        if foundation_params:
            allowable_foundation_moment, _ = self.calculate_foundation_capacity(foundation_params)
            governing_moment = min(allowable_pole_moment, allowable_foundation_moment)
            governing_element = "FOUNDATION" if allowable_foundation_moment < allowable_pole_moment else "POLE"
        else:
            governing_moment = allowable_pole_moment
            governing_element = "POLE"
        
        # Calculate wind loads
        wind_force, wind_moment = (0, 0) if wind_speed_ms == 0 else \
                                   self.calculate_wind_load(sections, wind_speed_ms, exposure)
        
        # Calculate applied moment
        applied_moment = applied_load_kg * self.gravity * total_height_m
        
        # Load combinations
        combinations, governing_combo, max_utilization = self.calculate_load_combinations(
            wind_moment, applied_moment, governing_moment)
        
        # Remaining capacity
        remaining_moment = governing_moment - combinations[governing_combo]['moment']
        remaining_load_capacity = (remaining_moment / (self.gravity * total_height_m)) if remaining_moment > 0 else 0
        
        # Status determination
        if max_utilization > 1.0: status = "FAIL - Overstressed"
        elif max_utilization > 0.9: status = "CRITICAL - Very High Utilization"
        elif max_utilization > 0.8: status = "WARNING - High Utilization"
        elif max_utilization > 0.6: status = "GOOD - Adequately Designed"
        else: status = "CONSERVATIVE - Significant Reserve"
        
        # Print summary
        print("=" * 70)
        print("MONOPOLE STRUCTURAL ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"Pole Weight:              {dead_load_kg:.1f} kg")
        print(f"Total Height:             {total_height_m:.1f} m")
        print(f"Wind Speed:               {wind_speed_ms:.1f} m/s ({wind_speed_ms * 3.6:.1f} km/h)")
        print(f"Applied Equipment Load:   {applied_load_kg:.1f} kg")
        print(f"Steel Grade:              {steel_grade}")
        print(f"Exposure Category:        {exposure}")
        print("-" * 70)
        print(f"Governing Element:        {governing_element}")
        print(f"Governing Combination:    {governing_combo}")
        print(f"Maximum Utilization:      {max_utilization:.3f} ({max_utilization*100:.1f}%)")
        print(f"Remaining Capacity:       {remaining_load_capacity:.0f} kg")
        print(f"Status:                   {status}")
        print("=" * 70)
        
        return {
            'dead_load_kg': dead_load_kg,
            'total_height_m': total_height_m,
            'wind_force_n': wind_force,
            'wind_moment_nm': wind_moment,
            'governing_element': governing_element,
            'governing_combo': governing_combo,
            'max_utilization': max_utilization,
            'remaining_capacity_kg': remaining_load_capacity,
            'status': status,
            'all_combinations': combinations
        }

# Example usage
if __name__ == "__main__":
    analyzer = MonopoleStructuralAnalysis()
    
    monopole_sections = [
        {'height': 10921, 'diameter_bottom': 1200, 'diameter_top': 937.9, 'thickness': 5},
        {'height': 10921, 'diameter_bottom': 985.3, 'diameter_top': 723.2, 'thickness': 5},
        {'height': 10921, 'diameter_bottom': 762.1, 'diameter_top': 500, 'thickness': 5}
    ]
    
    foundation_parameters = {
        'base_plate_diameter': 1560,
        'bolt_circle_diameter': 1560,
        'number_of_bolts': 30,
        'bolt_diameter': 32,
        'bolt_grade': 420,
        'concrete_strength': 21,
        'anchor_length': 1300
    }
    
    results = analyzer.analyze_monopole(
        monopole_sections, 
        applied_load_kg=0,
        wind_speed_ms=44.44,
        exposure ='C',
        steel_grade='S355',
        foundation_params=foundation_parameters
    )
