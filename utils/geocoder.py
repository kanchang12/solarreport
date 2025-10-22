import requests

class Geocoder:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    def geocode_address(self, address):
        """Geocode address using Google Geocoding API"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Google API key required. Set GOOGLE_API_KEY in .env',
                    'latitude': None,
                    'longitude': None,
                    'formatted_address': None
                }
            
            print(f"      Geocoding: {address}")
            
            params = {
                'address': address,
                'key': self.api_key
            }
            
            response = requests.get(self.geocode_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Geocoding API error: {response.status_code}',
                    'latitude': None,
                    'longitude': None,
                    'formatted_address': None
                }
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('results'):
                return {
                    'success': False,
                    'error': f"Address not found: {data.get('status', 'Unknown')}. Try full address: Street, City, Postcode, UK",
                    'latitude': None,
                    'longitude': None,
                    'formatted_address': None
                }
            
            result = data['results'][0]
            location = result['geometry']['location']
            
            print(f"      Found: {location['lat']}, {location['lng']}")
            
            return {
                'success': True,
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': result['formatted_address'],
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Geocoding error: {str(e)}',
                'latitude': None,
                'longitude': None,
                'formatted_address': None
            }
    
    def validate_coordinates(self, lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except:
            return False