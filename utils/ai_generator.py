from openai import OpenAI
import json

class AIContentGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def generate_report_content(self, report_data, address, peak_sun_hours):
        """Generate AI-powered content for the solar report"""
        
        try:
            system = report_data['system']
            production = report_data['production']
            financial = report_data['financial']
            environmental = report_data['environmental']
            
            prompt = f"""Generate 4 short paragraphs for a solar energy report:

Location: {address}
System: {system['actual_size_kw']} kW ({system['num_panels']} panels)
Annual Production: {production['annual_production_kwh']:,.0f} kWh
Installation Cost: £{financial['installation_cost']:,.0f}
Annual Savings: £{financial['annual_savings']:,.0f}
Payback: {financial['payback_period_years']} years
25-Year Profit: £{financial['net_25_year_savings']:,.0f}
CO2 Offset: {environmental['co2_offset_annual_tons']} tons/year

Return ONLY valid JSON with these keys:
{{
  "executive_summary": "2-3 sentences about system benefits and ROI",
  "financial_insight": "2-3 sentences about costs and savings",
  "environmental_impact": "2-3 sentences about CO2 and environmental benefits",
  "recommendations": "2-3 sentences about next steps"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a solar energy consultant. Return ONLY valid JSON, no markdown, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if '```' in content:
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            # Parse JSON
            parsed = json.loads(content)
            
            return {
                'executive_summary': parsed.get('executive_summary', ''),
                'financial_insight': parsed.get('financial_insight', ''),
                'environmental_impact': parsed.get('environmental_impact', ''),
                'recommendations': parsed.get('recommendations', '')
            }
            
        except json.JSONDecodeError as e:
            print(f"[AI] JSON parse error: {str(e)}")
            print(f"[AI] Content: {content[:200]}")
            return self._get_fallback_content(report_data, address)
        except Exception as e:
            print(f"[AI] Error: {str(e)}")
            return self._get_fallback_content(report_data, address)
    
    def _get_fallback_content(self, report_data, address):
        """Fallback content if AI fails"""
        system = report_data['system']
        financial = report_data['financial']
        environmental = report_data['environmental']
        
        return {
            'executive_summary': f"Based on analysis for {address}, a {system['actual_size_kw']} kW solar system with {system['num_panels']} panels is recommended. This system offers excellent returns with a {financial['payback_period_years']}-year payback and £{financial['net_25_year_savings']:,.0f} net profit over 25 years.",
            
            'financial_insight': f"Installation cost: £{financial['installation_cost']:,.0f}. Annual savings: £{financial['annual_savings']:,.0f}. Investment recovered in {financial['payback_period_years']} years with {financial['roi_percentage']}% ROI over system lifetime.",
            
            'environmental_impact': f"Annual CO2 offset: {environmental['co2_offset_annual_tons']} metric tons, equivalent to planting {int(environmental['trees_equivalent'])} trees yearly. Significant long-term carbon footprint reduction.",
            
            'recommendations': "Get quotes from 3+ certified installers. Check UK government solar incentives and grants. Consider battery storage. Verify roof structural capacity for 25+ year installation."
        }