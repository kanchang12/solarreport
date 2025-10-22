import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

class EmailSender:
    def __init__(self, gmail_user, gmail_app_password):
        self.gmail_user = gmail_user
        self.gmail_app_password = gmail_app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_report(self, recipient_email, recipient_name, pdf_path, subject=None):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = recipient_email
            msg['Subject'] = subject or f"Your Solar Energy Report - {recipient_name}"
            body = self._create_email_body(recipient_name)
            msg.attach(MIMEText(body, 'html'))
            if not os.path.exists(pdf_path):
                return {'success': False, 'error': f'PDF file not found: {pdf_path}'}
            with open(pdf_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(pdf_path)}')
                msg.attach(part)
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.gmail_user, self.gmail_app_password)
            text = msg.as_string()
            server.sendmail(self.gmail_user, recipient_email, text)
            server.quit()
            return {'success': True, 'error': None}
        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'error': 'Gmail authentication failed. Please check your Gmail credentials and app password.'}
        except smtplib.SMTPException as e:
            return {'success': False, 'error': f'SMTP error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to send email: {str(e)}'}
    
    def _create_email_body(self, recipient_name):
        html = f"""<html><head><style>body{{font-family:Arial,sans-serif;line-height:1.6;color:#333}}.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0}}.content{{padding:30px;background-color:#f9f9f9}}.highlight{{background-color:#fff3cd;padding:15px;border-left:4px solid #ffc107;margin:20px 0}}.footer{{text-align:center;padding:20px;font-size:12px;color:#666;background-color:#f1f1f1;border-radius:0 0 10px 10px}}</style></head><body><div class="header"><h1>Your Solar Energy Report is Ready!</h1></div><div class="content"><p>Dear {recipient_name},</p><p>Thank you for your interest in solar energy! We've analyzed your property and prepared a comprehensive solar potential report just for you.</p><div class="highlight"><strong>Your personalized report includes:</strong><ul><li>Detailed solar potential analysis for your location</li><li>Recommended system size and specifications</li><li>Financial projections and savings estimates</li><li>Environmental impact calculations</li><li>Visual charts and graphs</li><li>Next steps and recommendations</li></ul></div><p>Your complete solar energy report is attached as a PDF file. Please review it carefully and don't hesitate to reach out if you have any questions.</p><p><strong>Next Steps:</strong></p><ol><li>Review your personalized report</li><li>Consider the financial and environmental benefits</li><li>Get quotes from certified solar installers</li><li>Check for available incentives and rebates</li></ol><p>Going solar is an investment in your future and our planet. We hope this report helps you make an informed decision!</p><p>Best regards,<br><strong>Solar Energy Analysis Team</strong></p></div><div class="footer"><p>This is an automated report. The estimates provided are based on available data and standard assumptions. Please consult with certified solar professionals for accurate assessments specific to your property.</p><p>2025 Solar Energy Report System</p></div></body></html>"""
        return html
    
    def test_connection(self):
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.gmail_user, self.gmail_app_password)
            server.quit()
            return {'success': True, 'error': None}
        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'error': 'Authentication failed. Check your Gmail credentials and app password.'}
        except Exception as e:
            return {'success': False, 'error': f'Connection test failed: {str(e)}'}
