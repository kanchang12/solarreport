import requests

class NasaPowerAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.solar_api_url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
    
    def get_solar_data(self, latitude, longitude):
        """Fetch solar data from Google Solar API"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Google API key required. Set GOOGLE_API_KEY in .env',
                    'data': None
                }
            
            print(f"      Fetching from Google Solar API...")
            
            params = {
                'location.latitude': latitude,
                'location.longitude': longitude,
                'requiredQuality': 'LOW',
                'key': self.api_key
            }
            
            response = requests.get(self.solar_api_url, params=params, timeout=30)
            
            if response.status_code == 400:
                return {
                    'success': False,
                    'error': 'No building data at this location. Try a different address or enter exact building coordinates from Google Maps.',
                    'data': None
                }
            
            if response.status_code == 403:
                return {
                    'success': False,
                    'error': 'Google API access denied. Enable Solar API and billing at console.cloud.google.com',
                    'data': None
                }
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Google API error ({response.status_code})',
                    'data': None
                }
            
            data = response.json()
            solar_potential = data.get('solarPotential', {})
            
            if not solar_potential:
                return {
                    'success': False,
                    'error': 'No solar data available for this location',
                    'data': None
                }
            
            # CRITICAL FIX: Convert ALL values to float
            max_array_panels_count = int(solar_potential.get('maxArrayPanelsCount', 0))
            max_array_area_meters2 = float(solar_potential.get('maxArrayAreaMeters2', 0))
            max_sunshine_hours_per_year = float(solar_potential.get('maxSunshineHoursPerYear', 0))
            
            solar_panel_configs = solar_potential.get('solarPanelConfigs', [])
            if not solar_panel_configs:
                return {
                    'success': False,
                    'error': 'No solar panel configuration available',
                    'data': None
                }
            
            # Get best configuration
            best_config = max(solar_panel_configs, key=lambda x: float(x.get('yearlyEnergyDcKwh', 0)))
            yearly_energy_dc_kwh = float(best_config.get('yearlyEnergyDcKwh', 0))
            panels_count = int(best_config.get('panelsCount', 0))
            
            if yearly_energy_dc_kwh == 0 or max_array_area_meters2 == 0:
                return {
                    'success': False,
                    'error': 'Invalid solar data returned from Google API',
                    'data': None
                }
            
            # Generate monthly data
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # UK solar distribution (winter low, summer high)
            uk_monthly_factors = [0.5, 0.7, 1.0, 1.3, 1.5, 1.6, 1.5, 1.3, 1.1, 0.8, 0.5, 0.4]
            total_factor = sum(uk_monthly_factors)
            
            monthly_production = []
            for i, month in enumerate(months):
                month_kwh = (yearly_energy_dc_kwh * uk_monthly_factors[i]) / total_factor
                solar_irradiance = month_kwh / max_array_area_meters2 / 30.0
                
                monthly_production.append({
                    'month': month,
                    'solar_irradiance': round(solar_irradiance, 2),
                    'production_kwh': round(month_kwh, 2),
                    'clear_sky_irradiance': 0,
                    'temperature': 0
                })
            
            # Calculate peak sun hours (kWh/m²/day)
            annual_avg_kwh_m2_day = yearly_energy_dc_kwh / max_array_area_meters2 / 365.0
            
            print(f"      → Panels: {max_array_panels_count}")
            print(f"      → Roof: {max_array_area_meters2:.1f} m²")
            print(f"      → Yearly: {yearly_energy_dc_kwh:,.0f} kWh")
            print(f"      → Peak sun: {annual_avg_kwh_m2_day:.2f} kWh/m²/day")
            
            return {
                'success': True,
                'error': None,
                'data': {
                    'monthly': monthly_production,
                    'annual_average_kwh_m2_day': round(annual_avg_kwh_m2_day, 2),
                    'annual_total_kwh_m2': round(annual_avg_kwh_m2_day * 365, 2),
                    'yearly_energy_dc_kwh': round(yearly_energy_dc_kwh, 2),
                    'max_array_panels_count': max_array_panels_count,
                    'max_array_area_meters2': round(max_array_area_meters2, 2),
                    'max_sunshine_hours_per_year': round(max_sunshine_hours_per_year, 2),
                    'panels_count': panels_count,
                    'location': {
                        'latitude': latitude,
                        'longitude': longitude
                    },
                    'best_month': max(monthly_production, key=lambda x: x['production_kwh']),
                    'worst_month': min(monthly_production, key=lambda x: x['production_kwh'])
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': f'Data conversion error: {str(e)}',
                'data': None
            }
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'data': None
            }
    
    def get_peak_sun_hours(self, latitude, longitude):
        solar_data = self.get_solar_data(latitude, longitude)
        if solar_data['success']:
            return solar_data['data']['annual_average_kwh_m2_day']
        return None