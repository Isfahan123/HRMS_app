#!/usr/bin/env python3
"""
Email Service for HRMS System
Handles all email notifications for leave management, payslips, and system notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from typing import Dict, List, Optional

class HRMSEmailService:
    def __init__(self):
        # Email configuration - same as your working test setup
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "luminascea123@gmail.com"
        self.sender_password = "mjvp zvud haab krmu"
        self.sender_name = "HRMS System"
        
        # Company information
        self.company_name = "Enigma Technical Solutions Sdn Bhd"
        self.company_address = "56 & 57, Persiaran Venice Sutera 1, Desa Manjung Raya, 32200 Lumut, Perak, Malaysia"
        self.company_phone = "+60-16-508-2114"
        
    def _create_base_message(self, to_email: str, subject: str) -> MIMEMultipart:
        """Create base email message with headers"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.sender_name} <{self.sender_email}>"
        message["To"] = to_email
        return message
    
    def _send_email(self, message: MIMEMultipart, to_email: str) -> bool:
        """Send email using SMTP"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                text = message.as_string()
                server.sendmail(self.sender_email, to_email, text)
            return True
        except Exception as e:
            print(f"DEBUG: Error sending email to {to_email}: {str(e)}")
            return False
    
    def send_leave_request_notification(self, manager_email: str, employee_data: Dict, leave_data: Dict) -> bool:
        """Send leave request notification to manager"""
        try:
            subject = f"Leave Request from {employee_data.get('full_name', 'Employee')} - {leave_data.get('leave_type', 'Leave')}"
            message = self._create_base_message(manager_email, subject)
            
            # Calculate leave duration
            start_date = leave_data.get('start_date', '')
            end_date = leave_data.get('end_date', '')
            title = leave_data.get('title', 'No title provided')
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                  
                  <div style="text-align: center; border-bottom: 3px solid #FFA500; padding-bottom: 20px; margin-bottom: 30px;">
                    <h1 style="color: #FF8C00; margin: 0; font-size: 28px;">📋 Leave Request</h1>
                    <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">{self.company_name}</p>
                  </div>
                  
                  <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 20px; margin: 20px 0;">
                    <h2 style="color: #856404; margin-top: 0;">⏳ New Leave Request Pending Review</h2>
                    <p style="color: #856404; margin-bottom: 0;">A leave request requires your approval.</p>
                  </div>
                  
                  <h3 style="color: #333;">Employee Information:</h3>
                  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Employee Name:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('full_name', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Employee ID:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('employee_id', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Email:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('email', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Department:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('department', 'N/A')}</td>
                    </tr>
                  </table>
                  
                  <h3 style="color: #333;">Leave Details:</h3>
                  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Leave Type:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6; color: #FF8C00; font-weight: bold;">{leave_data.get('leave_type', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Start Date:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{start_date}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">End Date:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{end_date}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Title:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{title}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Submitted:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                  </table>
                  
                  <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin-bottom: 15px;">Please review this request in the HRMS system</p>
                    <div style="background-color: #e8f5e8; border: 1px solid #c3e6cb; border-radius: 4px; padding: 15px;">
                      <p style="margin: 0; color: #155724;">
                        <strong>📌 Action Required:</strong> Log in to HRMS to approve or reject this leave request.
                      </p>
                    </div>
                  </div>
                  
                  <hr style="border: 0; border-top: 2px solid #eee; margin: 30px 0;">
                  
                  <div style="text-align: center;">
                    <p style="color: #666; font-size: 14px; margin-bottom: 5px;">
                      This email was sent automatically by the HRMS Leave Management System
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 0;">
                      {self.company_name} • Human Resources Management System
                    </p>
                  </div>
                  
                </div>
              </body>
            </html>
            """
            
            message.attach(MIMEText(html, "html"))
            success = self._send_email(message, manager_email)
            
            if success:
                print(f"DEBUG: Leave request notification sent to manager: {manager_email}")
            return success
            
        except Exception as e:
            print(f"DEBUG: Error sending leave request notification: {str(e)}")
            return False
    
    def send_leave_status_notification(self, employee_email: str, employee_name: str, leave_data: Dict, status: str, reviewed_by: str) -> bool:
        """Send leave status notification to employee (approved, rejected, or submitted)."""
        try:
            s = (status or "").lower()
            if s == "approved":
                status_title = "✅ Approved"
                status_color = "#28a745"
                status_bg = "#d4edda"
                status_border = "#c3e6cb"
                subject = f"Leave Request Approved - {leave_data.get('leave_type', 'Leave')}"
                headline = "Your leave request has been approved"
                actor_label = "Reviewed By"
            elif s == "rejected":
                status_title = "❌ Rejected"
                status_color = "#dc3545"
                status_bg = "#f8d7da"
                status_border = "#f5c6cb"
                subject = f"Leave Request Rejected - {leave_data.get('leave_type', 'Leave')}"
                headline = "Your leave request has been rejected"
                actor_label = "Reviewed By"
            else:
                # Treat any other value (e.g., submitted/pending) as submitted/pending notification
                status_title = "🕒 Submitted"
                status_color = "#17a2b8"  # info
                status_bg = "#d1ecf1"
                status_border = "#bee5eb"
                subject = f"Leave Request Submitted - {leave_data.get('leave_type', 'Leave')}"
                headline = "Your leave request has been submitted and is pending review"
                actor_label = "Submitted By"

            message = self._create_base_message(employee_email, subject)

            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                  
                  <div style="text-align: center; border-bottom: 3px solid {status_color}; padding-bottom: 20px; margin-bottom: 30px;">
                    <h1 style="color: {status_color}; margin: 0; font-size: 28px;">{status_title}</h1>
                    <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">Leave Request Update</p>
                  </div>
                  
                  <p>Dear {employee_name},</p>
                  
                  <div style="background-color: {status_bg}; border: 1px solid {status_border}; border-radius: 6px; padding: 20px; margin: 20px 0;">
                    <h2 style="color: {status_color}; margin-top: 0;">{headline}</h2>
                    <p style="color: {status_color}; margin-bottom: 0;">
                      {"Enjoy your time off!" if s == "approved" else ("Please contact HR if you have any questions." if s == "rejected" else "You'll receive another email once a decision is made.")}
                    </p>
                  </div>
                  
                  <h3 style="color: #333;">Leave Details:</h3>
                  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Leave Type:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{leave_data.get('leave_type', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Start Date:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{leave_data.get('start_date', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">End Date:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{leave_data.get('end_date', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Title:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{leave_data.get('title', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Status:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6; color: {status_color}; font-weight: bold;">{status.title()}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">{actor_label}:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{reviewed_by}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Reviewed On:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                  </table>
                  
                  {"<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 25px 0;'><p style='margin: 0; color: #856404;'><strong>📅 Reminder:</strong> Please update your calendar and inform your team about your approved leave.</p></div>" if status.lower() == "approved" else "<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 15px; margin: 25px 0;'><p style='margin: 0; color: #721c24;'><strong>📞 Need Help?</strong> Contact HR if you need to discuss this decision or submit a new request.</p></div>"}
                  
                  <hr style="border: 0; border-top: 2px solid #eee; margin: 30px 0;">
                  
                  <div style="text-align: center;">
                    <p style="color: #666; font-size: 14px; margin-bottom: 5px;">
                      This email was sent automatically by the HRMS Leave Management System
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 0;">
                      {self.company_name} • Human Resources Management System
                    </p>
                  </div>
                  
                </div>
              </body>
            </html>
            """
            
            message.attach(MIMEText(html, "html"))
            success = self._send_email(message, employee_email)
            
            if success:
                print(f"DEBUG: Leave status notification sent to employee: {employee_email}")
            return success
            
        except Exception as e:
            print(f"DEBUG: Error sending leave status notification: {str(e)}")
            return False
    
    def send_payslip_notification(self, employee_email: str, employee_name: str, payslip_data: Dict, month: str, year: str) -> bool:
        """Send payslip notification to employee"""
        try:
            subject = f"Payslip Available - {month} {year}"
            message = self._create_base_message(employee_email, subject)
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                  
                  <div style="text-align: center; border-bottom: 3px solid #2E86AB; padding-bottom: 20px; margin-bottom: 30px;">
                    <h1 style="color: #2E86AB; margin: 0; font-size: 28px;">💰 Payslip Ready</h1>
                    <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">{month} {year} Payslip</p>
                  </div>
                  
                  <p>Dear {employee_name},</p>
                  
                  <p>Your payslip for <strong>{month} {year}</strong> is now available for download.</p>
                  
                  <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #155724; margin-top: 0;">📊 Payslip Summary</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                      <tr>
                        <td style="padding: 8px 0; color: #155724;"><strong>Basic Salary:</strong></td>
                        <td style="padding: 8px 0; color: #155724; text-align: right;"><strong>RM {payslip_data.get('basic_salary', '0.00')}</strong></td>
                      </tr>
                      <tr>
                        <td style="padding: 8px 0; color: #155724;">Total Deductions:</td>
                        <td style="padding: 8px 0; color: #155724; text-align: right;">RM {payslip_data.get('total_deductions', '0.00')}</td>
                      </tr>
                      <tr style="border-top: 2px solid #c3e6cb;">
                        <td style="padding: 8px 0; color: #155724; font-size: 18px;"><strong>Net Pay:</strong></td>
                        <td style="padding: 8px 0; color: #155724; text-align: right; font-size: 18px;"><strong>RM {payslip_data.get('net_pay', '0.00')}</strong></td>
                      </tr>
                    </table>
                  </div>
                  
                  <div style="text-align: center; margin: 30px 0;">
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px;">
                      <p style="margin: 0; color: #856404;">
                        <strong>📎 Download:</strong> Log in to HRMS to download your detailed payslip PDF.
                      </p>
                    </div>
                  </div>
                  
                  <hr style="border: 0; border-top: 2px solid #eee; margin: 30px 0;">
                  
                  <div style="text-align: center;">
                    <p style="color: #666; font-size: 14px; margin-bottom: 5px;">
                      This email was sent automatically by the HRMS Payroll System
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 0;">
                      {self.company_name} • Human Resources Management System
                    </p>
                  </div>
                  
                </div>
              </body>
            </html>
            """
            
            message.attach(MIMEText(html, "html"))
            success = self._send_email(message, employee_email)
            
            if success:
                print(f"DEBUG: Payslip notification sent to employee: {employee_email}")
            return success
            
        except Exception as e:
            print(f"DEBUG: Error sending payslip notification: {str(e)}")
            return False
    
    def send_admin_leave_request_notification(self, admin_email: str, employee_data: Dict, leave_data: Dict, submitted_by: str) -> bool:
        """Send leave request notification when admin submits on behalf of employee"""
        try:
            subject = f"Leave Request Submitted by Admin for {employee_data.get('full_name', 'Employee')} - {leave_data.get('leave_type', 'Leave')}"
            message = self._create_base_message(admin_email, subject)
            
            # Calculate leave duration
            start_date = leave_data.get('start_date', '')
            end_date = leave_data.get('end_date', '')
            title = leave_data.get('title', 'No title provided')
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                  
                  <div style="text-align: center; border-bottom: 3px solid #007BFF; padding-bottom: 20px; margin-bottom: 30px;">
                    <h1 style="color: #007BFF; margin: 0; font-size: 28px;">👨‍💼 Admin Leave Submission</h1>
                    <p style="color: #666; margin: 10px 0 0 0; font-size: 16px;">{self.company_name}</p>
                  </div>
                  
                  <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 6px; padding: 20px; margin: 20px 0;">
                    <h2 style="color: #0c5460; margin-top: 0;">📋 Leave Request Submitted by Administrator</h2>
                    <p style="color: #0c5460; margin-bottom: 0;">An administrator has submitted a leave request on behalf of an employee.</p>
                  </div>
                  
                  <h3 style="color: #333;">Submission Details:</h3>
                  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Submitted By:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6; color: #007BFF; font-weight: bold;">{submitted_by}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Submitted On:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                  </table>
                  
                  <h3 style="color: #333;">Employee Information:</h3>
                  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Employee Name:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('full_name', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Employee Email:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('email', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Department:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{employee_data.get('department', 'N/A')}</td>
                    </tr>
                  </table>
                  
                  <h3 style="color: #333;">Leave Details:</h3>
                  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Leave Type:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6; color: #007BFF; font-weight: bold;">{leave_data.get('leave_type', 'N/A')}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Start Date:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{start_date}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">End Date:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{end_date}</td>
                    </tr>
                    <tr>
                      <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Title:</td>
                      <td style="padding: 12px; border: 1px solid #dee2e6;">{title}</td>
                    </tr>
                  </table>
                  
                  <div style="text-align: center; margin: 30px 0;">
                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; padding: 15px;">
                      <p style="margin: 0; color: #155724;">
                        <strong>✅ Status:</strong> Leave request has been automatically approved (submitted by administrator).
                      </p>
                    </div>
                  </div>
                  
                  <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 25px 0;">
                    <p style="margin: 0; color: #856404;">
                      <strong>📌 Note:</strong> This leave request was submitted by an administrator on behalf of the employee. 
                      The employee has been notified and the request is automatically processed.
                    </p>
                  </div>
                  
                  <hr style="border: 0; border-top: 2px solid #eee; margin: 30px 0;">
                  
                  <div style="text-align: center;">
                    <p style="color: #666; font-size: 14px; margin-bottom: 5px;">
                      This email was sent automatically by the HRMS Leave Management System
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 0;">
                      {self.company_name} • Human Resources Management System
                    </p>
                  </div>
                  
                </div>
              </body>
            </html>
            """
            
            message.attach(MIMEText(html, "html"))
            success = self._send_email(message, admin_email)
            
            if success:
                print(f"DEBUG: Admin leave submission notification sent to: {admin_email}")
            return success
            
        except Exception as e:
            print(f"DEBUG: Error sending admin leave submission notification: {str(e)}")
            return False
    
    def test_email_connection(self) -> bool:
        """Test email connection without sending an email"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
            return True
        except Exception as e:
            print(f"DEBUG: Email connection test failed: {str(e)}")
            return False

# Create a global instance for easy import
email_service = HRMSEmailService()
