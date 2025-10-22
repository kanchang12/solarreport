class SolarCalculator:
    def __init__(self, electricity_rate=0.12, panel_efficiency=0.18, installation_cost_per_kw=3000, panel_wattage=400, co2_per_kwh=0.0007):
        # Configuration parameters
        self.electricity_rate = electricity_rate
        self.panel_efficiency = panel_efficiency 
        self.installation_cost_per_kw = installation_cost_per_kw
        self.panel_wattage = panel_wattage
        self.co2_per_kwh = co2_per_kwh
        self.system_lifetime = 25 # Years

    def calculate_system_size(self, annual_consumption_kwh, peak_sun_hours, roof_area=None, derate_factor=0.75):
        if peak_sun_hours <= 0:
            peak_sun_hours = 4.0
        
        # CORRECT FORMULA: Consumption / (365 * Peak Sun Hours * Performance Ratio)
        recommended_size_kw = annual_consumption_kwh / (365 * peak_sun_hours * derate_factor) 
        num_panels = int(recommended_size_kw * 1000 / self.panel_wattage) + 1
        actual_size_kw = (num_panels * self.panel_wattage) / 1000
        
        required_roof_area_sqm = num_panels * 2.0 

        return {
            'recommended_size_kw': round(recommended_size_kw, 2),
            'actual_size_kw': round(actual_size_kw, 2),
            'num_panels': num_panels,
            'panel_wattage': self.panel_wattage,
            'required_roof_area_sqm': round(required_roof_area_sqm, 2)
        }

    def calculate_energy_production(self, system_size_kw, peak_sun_hours, monthly_solar_data=None):
        derate_factor = 0.75 # Standard performance ratio
        
        annual_production_kwh = system_size_kw * 365 * peak_sun_hours * derate_factor

        return {
            'annual_production_kwh': round(annual_production_kwh, 0),
            'daily_production_kwh': round(annual_production_kwh / 365, 1),
            'monthly_production_kwh': round(annual_production_kwh / 12, 0)
        }

    def calculate_financial_analysis(self, annual_consumption_kwh, annual_production_kwh, actual_size_kw, electricity_rate):
        
        # 1. Calculate installation cost dynamically based on system size.
        installation_cost = actual_size_kw * self.installation_cost_per_kw
        
        # 2. Savings are based on the energy offset (capped at consumption)
        offset_kwh = min(annual_production_kwh, annual_consumption_kwh)
        annual_savings = offset_kwh * electricity_rate
        
        # Annuity Factor (for 25 years at 3% escalation)
        rate = 0.03
        n = self.system_lifetime
        annuity_factor = ((1 + rate)**n - 1) / rate
        
        total_25_year_savings = annual_savings * annuity_factor
        
        # 3. Payback Period calculation and clamping
        if annual_savings > 0:
            payback_period_years = installation_cost / annual_savings
        else:
            payback_period_years = self.system_lifetime + 1
            
        # Cap the payback period to the system lifetime (25 years)
        payback_period_years = round(min(payback_period_years, self.system_lifetime), 1)

        # Net Profit & ROI
        net_25_year_savings = total_25_year_savings - installation_cost
        
        if installation_cost > 0:
            roi_percentage = (net_25_year_savings / installation_cost) * 100
        else:
            roi_percentage = 0

        return {
            'installation_cost': round(installation_cost, 0),
            'annual_savings': round(annual_savings, 0),
            'monthly_savings': round(annual_savings / 12, 0),
            'payback_period_years': payback_period_years,
            'total_25_year_savings': round(total_25_year_savings, 0),
            'net_25_year_savings': round(net_25_year_savings, 0),
            'roi_percentage': round(roi_percentage, 1)
        }
    
    def calculate_environmental_impact(self, annual_production_kwh):
        TREES_PER_TON_CO2 = 48 
        
        co2_offset_annual_tons = annual_production_kwh * self.co2_per_kwh
        
        return {
            'co2_offset_annual_tons': round(co2_offset_annual_tons, 1),
            'co2_offset_25_years_tons': round(co2_offset_annual_tons * self.system_lifetime, 1),
            'trees_equivalent': round(co2_offset_annual_tons * TREES_PER_TON_CO2, 0)
        }
        
    # 🚨 MISSING METHOD FIX 🚨
    # This method is called by your app.py to generate the full report data.
    def generate_complete_report(self, annual_consumption_kwh, peak_sun_hours, electricity_rate, monthly_solar_data=None):
        # 1. System Size
        system_data = self.calculate_system_size(annual_consumption_kwh, peak_sun_hours)
        actual_size_kw = system_data['actual_size_kw']

        # 2. Energy Production
        production_data = self.calculate_energy_production(actual_size_kw, peak_sun_hours, monthly_solar_data)
        annual_production_kwh = production_data['annual_production_kwh']

        # 3. Financial Analysis
        financial_data = self.calculate_financial_analysis(annual_consumption_kwh, annual_production_kwh, actual_size_kw, electricity_rate)

        # 4. Environmental Impact
        environmental_data = self.calculate_environmental_impact(annual_production_kwh)
        
        # 5. Compile final report data dictionary
        report_data = {
            'system': system_data,
            'production': production_data,
            'financial': financial_data,
            'environmental': environmental_data
        }
        
        return report_data