from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from utils.geocoder import Geocoder
from utils.nasa_api import NasaPowerAPI
from utils.calculations import SolarCalculator
from utils.pdf_generator import PDFReportGenerator
from utils.email_sender import EmailSender
from utils.ai_generator import AIContentGenerator
import traceback
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

DEFAULT_ELECTRICITY_RATE = float(os.getenv('DEFAULT_ELECTRICITY_RATE', 0.25))
INSTALLATION_COST_PER_KW = float(os.getenv('INSTALLATION_COST_PER_KW', 3000))
# FIX: Rename for clarity, as this 0.75 is typically a Performance Ratio/Derate Factor, not panel efficiency
SYSTEM_PERFORMANCE_RATIO = float(os.getenv('SOLAR_PANEL_EFFICIENCY', 0.75)) 

geocoder = Geocoder(GOOGLE_API_KEY)
nasa_api = NasaPowerAPI(GOOGLE_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        latitude_input = request.form.get('latitude', '').strip()
        longitude_input = request.form.get('longitude', '').strip()
        
        monthly_bill_str = request.form.get('monthly_bill', '').strip()
        monthly_bill = float(monthly_bill_str) if monthly_bill_str else 0.0
        
        roof_area_str = request.form.get('roof_area', '').strip()
        roof_area = float(roof_area_str) if roof_area_str else None
        
        electricity_rate_str = request.form.get('electricity_rate', '').strip()
        electricity_rate = float(electricity_rate_str) if electricity_rate_str else DEFAULT_ELECTRICITY_RATE
        
        if not name or not email or not address or monthly_bill <= 0:
            return jsonify({
                'success': False,
                'error': 'Name, Email, Address and Monthly Bill (>£0) are required'
            }), 400
        
        if '@' not in email:
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        print(f"\n{'='*60}")
        print(f"Processing: {name} | {address}")
        print(f"{'='*60}")
        
        # Step 1: Get coordinates
        if latitude_input and longitude_input:
            latitude = float(latitude_input)
            longitude = float(longitude_input)
            formatted_address = address
            print(f"[1/6] Using coordinates: {latitude}, {longitude}")
        else:
            print(f"[1/6] Geocoding address...")
            location_result = geocoder.geocode_address(address)
            if not location_result['success']:
                return jsonify({
                    'success': False,
                    'error': f"Address not found: {location_result['error']}"
                }), 400
            latitude = location_result['latitude']
            longitude = location_result['longitude']
            formatted_address = location_result['formatted_address']
            print(f"      → {latitude}, {longitude}")
        
        # Step 2: Get solar data
        print(f"[2/6] Fetching solar data from Google Solar API...")
        solar_result = nasa_api.get_solar_data(latitude, longitude)
        
        if not solar_result['success']:
            return jsonify({
                'success': False,
                'error': f"Solar data error: {solar_result['error']}"
            }), 500
        
        peak_sun_hours = solar_result['data']['annual_average_kwh_m2_day']
        print(f"      → Peak sun: {peak_sun_hours} kWh/m²/day")
        
        # Step 3: Calculate system
        print(f"[3/6] Calculating solar system...")
        # FIX: Use SYSTEM_PERFORMANCE_RATIO (0.75) for the panel_efficiency parameter.
        # This aligns with the fixed SolarCalculator which uses the value of this parameter as the derate factor.
        calculator = SolarCalculator(
            electricity_rate=electricity_rate,
            panel_efficiency=SYSTEM_PERFORMANCE_RATIO, 
            installation_cost_per_kw=INSTALLATION_COST_PER_KW
        )
        
        annual_consumption_kwh = (monthly_bill / DEFAULT_ELECTRICITY_RATE) * 12
        print(f"      → Annual Consumption (estimated): {annual_consumption_kwh:,.0f} kWh")

        report_data = calculator.generate_complete_report(
            annual_consumption_kwh=annual_consumption_kwh,
            peak_sun_hours=peak_sun_hours,
            electricity_rate=electricity_rate,
            monthly_solar_data=solar_result['data']['monthly']
        )
        
        print(f"      → System: {report_data['system']['actual_size_kw']} kW")
        print(f"      → Production: {report_data['production']['annual_production_kwh']:,.0f} kWh/year")
        print(f"      → Savings: £{report_data['financial']['annual_savings']:,.2f}/year")
        
        # Step 4: Generate AI content
        ai_content = {}
        if OPENAI_API_KEY:
            print(f"[4/6] Generating AI content...")
            try:
                ai_generator = AIContentGenerator(OPENAI_API_KEY)
                ai_content = ai_generator.generate_report_content(
                    report_data, formatted_address, peak_sun_hours
                )
                print(f"      → AI content generated")
            except Exception as e:
                print(f"      → AI failed: {str(e)}")
                ai_content = {}
        else:
            print(f"[4/6] Skipping AI (no API key)")
        
        # Step 5: Generate PDF
        print(f"[5/6] Creating PDF report...")
        try:
            user_data = {
                'name': name,
                'email': email,
                'address': formatted_address
            }
            location_data = {
                'latitude': latitude,
                'longitude': longitude,
                'annual_average': peak_sun_hours
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temp/solar_report_{name.replace(' ', '_')}_{timestamp}.pdf"
            
            pdf_generator = PDFReportGenerator(filename)
            pdf_generator.generate(
                user_data, location_data, 
                solar_result['data'], report_data, ai_content
            )
            print(f"      → PDF created: {filename}")
            
        except Exception as pdf_error:
            print(f"      → PDF ERROR: {str(pdf_error)}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'PDF generation failed: {str(pdf_error)}'
            }), 500
        
        # Step 6: Send email
        if GMAIL_USER and GMAIL_APP_PASSWORD:
            print(f"[6/6] Sending email to {email}...")
            try:
                email_sender = EmailSender(GMAIL_USER, GMAIL_APP_PASSWORD)
                email_result = email_sender.send_report(email, name, filename)
                if email_result['success']:
                    print(f"      → Email sent!")
                else:
                    print(f"      → Email failed: {email_result['error']}")
            except Exception as email_error:
                print(f"      → Email ERROR: {str(email_error)}")
        else:
            print(f"[6/6] Email skipped (not configured)")
        
        print(f"{'='*60}\n")
        
        # Return success
        return jsonify({
            'success': True,
            'message': f'Solar report generated and sent to {email}!',
            'summary': {
                'system_size': report_data['system']['actual_size_kw'],
                'num_panels': report_data['system']['num_panels'],
                'annual_production': round(report_data['production']['annual_production_kwh'], 2),
                'annual_savings': round(report_data['financial']['annual_savings'], 2),
                'payback_period': report_data['financial']['payback_period_years'],
                'co2_offset': report_data['environmental']['co2_offset_annual_tons']
            }
        }), 200
    
    except ValueError as e:
        error_msg = f'Invalid input: {str(e)}'
        print(f"\nVALUE ERROR: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 400
        
    except Exception as e:
        error_msg = f'Server error: {str(e)}'
        print(f"\nSERVER ERROR: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/test-email', methods=['GET'])
def test_email():
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return jsonify({'success': False, 'error': 'Gmail not configured'}), 400
    email_sender = EmailSender(GMAIL_USER, GMAIL_APP_PASSWORD)
    return jsonify(email_sender.test_connection())

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'gmail': '✓' if GMAIL_USER and GMAIL_APP_PASSWORD else '✗',
        'openai': '✓' if OPENAI_API_KEY else '✗',
        'google': '✓' if GOOGLE_API_KEY else '✗',
        'timestamp': datetime.now().isoformat()
    })
os.makedirs('temp', exist_ok=True)

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    print("\n" + "="*60)
    print("SOLAR ENERGY REPORT SYSTEM (GOOGLE SOLAR API)")
    print("="*60)
    print(f"Gmail:   {'✓' if GMAIL_USER and GMAIL_APP_PASSWORD else '✗'}")
    print(f"OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
    print(f"Google: {'✓' if GOOGLE_API_KEY else '✗ REQUIRED'}")
    print(f"Rate:    £{DEFAULT_ELECTRICITY_RATE}/kWh")
    print(f"Cost:    £{INSTALLATION_COST_PER_KW}/kW")
    print(f"Performance Ratio: {SYSTEM_PERFORMANCE_RATIO*100}%") 
    print("="*60)
    print("Server: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
