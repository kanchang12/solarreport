from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime
import io

SOLAR_BLUE = colors.HexColor('#1E3A8A')
SOLAR_ORANGE = colors.HexColor('#F59E0B')
LIGHT_GRAY = colors.HexColor('#F3F4F6')
DARK_GRAY = colors.HexColor('#374151')

class PDFReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=60, leftMargin=60, topMargin=100, bottomMargin=60)
        self.styles = getSampleStyleSheet()
        self.story = []
        self._create_styles()
    
    def _create_styles(self):
        self.styles.add(ParagraphStyle(name='CustomHeading', fontSize=18, textColor=SOLAR_BLUE, spaceAfter=12, spaceBefore=20, fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='CustomSubHeading', fontSize=14, textColor=SOLAR_BLUE, spaceAfter=5, spaceBefore=5, fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='CustomBody', fontSize=11, textColor=DARK_GRAY, spaceAfter=12, fontName='Helvetica', leading=16))
        self.styles.add(ParagraphStyle(name='CustomSmall', fontSize=9, textColor=colors.gray, alignment=TA_CENTER, fontName='Helvetica'))

    def _header(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(SOLAR_BLUE)
        canvas.rect(0, A4[1] - 60, A4[0], 60, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawString(60, A4[1] - 35, "Solar Energy Report")
        canvas.setFont('Helvetica', 10)
        canvas.drawRightString(A4[0] - 60, A4[1] - 35, datetime.now().strftime('%d %B %Y'))
        canvas.restoreState()

    def add_title(self, user_data):
        self.story.append(Spacer(1, 0.3*inch))
        
        title_text = (
            f"<font size=28 fontName='Helvetica-Bold' color='{SOLAR_BLUE.rgb()}'>"
            f"Solar Analysis for {user_data['name']}"
            f"</font><br/></br></br>"
            f"<font size=14 fontName='Helvetica' color='{DARK_GRAY.rgb()}'>"
            f"{user_data['address']}"
            f"</font>"
        )
        self.story.append(Paragraph(title_text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.2*inch))

    def add_kpis(self, report_data):
        system = report_data['system']
        financial = report_data['financial']
        
        data = [
            [
                f"{system['actual_size_kw']} kW",
                f"£{financial['annual_savings']:,.0f}",
                f"{financial['payback_period_years']:.1f} years",
                f"£{financial['net_25_year_savings']:,.0f}"
            ],
            [
                Paragraph("System Size", self.styles['CustomSmall']),
                Paragraph("Annual Savings", self.styles['CustomSmall']),
                Paragraph("Payback Period", self.styles['CustomSmall']),
                Paragraph("25-Year Profit", self.styles['CustomSmall'])
            ]
        ]
        
        table = Table(data, colWidths=[2*inch]*4)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT_GRAY),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
            ('FONTSIZE', (0,0), (-1,0), 16),               
            ('TEXTCOLOR', (0,0), (-1,0), SOLAR_BLUE),     
            ('TOPPADDING', (0,0), (-1,0), 15),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),           
            ('BOTTOMPADDING', (0,1), (-1,1), 10),
            ('BOX', (0,0), (-1,-1), 1, colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))

    def add_ai_summary(self, ai_content):
        self.story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        self.story.append(Paragraph(ai_content.get('executive_summary', 'Based on our analysis, this solar system offers excellent returns.'), self.styles['CustomBody']))
        self.story.append(Spacer(1, 0.2*inch))
        
    # --- HELPER 1: SYSTEM FLOWABLES ---
    def _get_system_flowables(self, report_data):
        system = report_data['system']
        production = report_data['production']
        
        # Data for the System Table
        data = [
            [Paragraph("System Specifications", self.styles['CustomSubHeading']), ''],
            ['Number of Panels:', f"{system['num_panels']} panels"],
            ['Panel Wattage:', f"{system['panel_wattage']}W each"],
            ['Total System Size:', f"{system['actual_size_kw']} kW"],
            ['Required Roof Area:', f"{system['required_roof_area_sqm']} m²"],
            ['', ''],
            [Paragraph("Energy Production", self.styles['CustomSubHeading']), ''],
            ['Daily Production:', f"{production['daily_production_kwh']:.1f} kWh"],
            ['Monthly Production:', f"{production['monthly_production_kwh']:,.0f} kWh"],
            ['Annual Production:', f"{production['annual_production_kwh']:,.0f} kWh"],
        ]
        
        table = Table(data, colWidths=[1.8*inch, 1.45*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), SOLAR_BLUE),
            ('BACKGROUND', (0,6), (1,6), SOLAR_BLUE),
            ('TEXTCOLOR', (0,0), (1,0), colors.white),
            ('TEXTCOLOR', (0,6), (1,6), colors.white),
            ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,6), (1,6), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (0,5), 'Helvetica'),
            ('FONTNAME', (0,7), (0,9), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'), # Align values right
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
        ]))
        
        return [
            Paragraph("System Details", self.styles['CustomSubHeading']),
            table
        ]

    # --- HELPER 2: FINANCIAL FLOWABLES ---
    def _get_financial_flowables(self, report_data):
        financial = report_data['financial']
        
        # Data for the Financial Table
        data = [
            [Paragraph("Financial Analysis", self.styles['CustomSubHeading']), ''],
            ['Installation Cost:', f"£{financial['installation_cost']:,.0f}"],
            ['Annual Savings:', f"£{financial['annual_savings']:,.0f}"],
            ['Monthly Savings:', f"£{financial['monthly_savings']:,.0f}"],
            ['Payback Period:', f"{financial['payback_period_years']:.1f} years"],
            ['25-Year Total Savings:', f"£{financial['total_25_year_savings']:,.0f}"],
            ['25-Year Net Profit:', f"£{financial['net_25_year_savings']:,.0f}"],
            ['Return on Investment:', f"{financial['roi_percentage']:.1f}%"],
        ]
        
        table = Table(data, colWidths=[1.8*inch, 1.45*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), SOLAR_ORANGE),
            ('TEXTCOLOR', (0,0), (1,0), colors.white),
            ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,6), (1,7), 'Helvetica-Bold'), # Highlight Net Profit and ROI
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'), # Align values right
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
        ]))
        
        return [
            Paragraph("Financial Breakdown", self.styles['CustomSubHeading']),
            table
        ]
        
    # --- MASTER LAYOUT: COMBINE TWO COLUMNS ---
    def add_system_and_financial_details(self, report_data):
        self.story.append(Paragraph("System & Financial Details", self.styles['CustomHeading']))
        
        system_flowables = self._get_system_flowables(report_data)
        financial_flowables = self._get_financial_flowables(report_data)
        
        # Create wrapper tables for each column to handle the nested flowables
        system_wrapper = Table([[flowable] for flowable in system_flowables], colWidths=[3.25*inch])
        financial_wrapper = Table([[flowable] for flowable in financial_flowables], colWidths=[3.25*inch])
        
        # Combine the two columns into a single ReportLab Table
        master_table = Table(
            [[system_wrapper, financial_wrapper]], 
            colWidths=[3.25*inch, 3.25*inch]
        )
        
        master_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (1, 0), (1, 0), 10), # Space between columns
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
        ]))
        
        self.story.append(master_table)
        self.story.append(Spacer(1, 0.3*inch))


    def create_chart(self, solar_data):
        # ... (Function remains the same)
        # Check for None input
        if solar_data is None or 'monthly' not in solar_data:
             # Return an empty spacer if data is missing
            return Spacer(1, 0.1*inch)
            
        months = [d['month'] for d in solar_data['monthly']]
        irradiance = [d['solar_irradiance'] for d in solar_data['monthly']]
        
        fig, ax = plt.subplots(figsize=(7, 3))
        bars = ax.bar(months, irradiance, color='#1E3A8A', alpha=0.7)
        bars[irradiance.index(max(irradiance))].set_color('#F59E0B')
        
        ax.set_title('Monthly Solar Production', fontsize=12, fontweight='bold', color='#1E3A8A')
        ax.set_ylabel('kWh/m²/day', fontsize=10)
        ax.tick_params(axis='x', rotation=45, labelsize=9)
        ax.tick_params(axis='y', labelsize=9)
        ax.grid(axis='y', alpha=0.3)
        
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        buf.seek(0)
        return Image(buf, width=5*inch, height=2.5*inch)

    def add_environmental(self, report_data):
        env = report_data['environmental']
        
        self.story.append(Paragraph("Environmental Impact", self.styles['CustomHeading']))
        self.story.append(Paragraph(f"<b>Annual CO₂ Offset:</b> {env['co2_offset_annual_tons']:.1f} metric tons<br/><b>Equivalent to planting:</b> {int(env['trees_equivalent'])} trees per year<br/><b>25-Year CO₂ Offset:</b> {env['co2_offset_25_years_tons']:.1f} metric tons", self.styles['CustomBody']))

    def generate(self, user_data, location_data, solar_data, report_data, ai_content=None):
        self.add_title(user_data)
        self.add_kpis(report_data)
        self.add_ai_summary(ai_content or {})
        
        # Add Page Break to start System Details & Financial on a new page (Page 2)
        self.story.append(PageBreak()) 
        
        # FIXED: Call the new master layout function
        self.add_system_and_financial_details(report_data)
        
        # Add Page Break to start Chart & Environmental on a new page (Page 3)
        self.story.append(PageBreak()) 
        
        self.story.append(self.create_chart(solar_data))
        self.story.append(Spacer(1, 0.3*inch))
        self.add_environmental(report_data)
        
        self.story.append(Spacer(1, 0.5*inch))
        self.story.append(Paragraph("This report is for informational purposes only. Consult certified solar professionals for accurate assessments.", self.styles['CustomSmall']))
        
        # Build the document
        self.doc.build(self.story, onFirstPage=self._header, onLaterPages=self._header)
        return self.filename