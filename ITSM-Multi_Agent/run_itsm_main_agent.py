"""
Enterprise ITSM Multi-Agent System - Enhanced Email Clarity
==========================================================
Clear deviation details with specific missing items
"""
import os
import re
import json
import smtplib
import pandas as pd
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv(override=True)

GITHUB_BASE_URL = "https://raw.githubusercontent.com/rammohan3975-max/Agentic-AI-prototypes/main/ITSM-COMPLEX/"
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "rammohan3975@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")

print("="*80)
print("🚀 ENTERPRISE ITSM MULTI-AGENT SYSTEM - ENHANCED VERSION")
print("="*80)
print()


class GitHubDocumentAgent:
    """Agent 1: GitHub Document Retrieval"""

    def __init__(self):
        self.incident_rules = {}
        self.change_rules = {}
        print("🤖 [Agent 1] GitHub Document Retrieval Agent initializing...")
        self._fetch_rules_from_github()
        print("✅ GitHub Document Retrieval Agent ready\n")

    def _fetch_rules_from_github(self):
        try:
            print("📥 Fetching incident_management_rules.txt from GitHub...")
            incident_url = GITHUB_BASE_URL + "incident_management_rules.txt"
            response = requests.get(incident_url)
            response.raise_for_status()

            print("\n" + "="*60)
            print("📄 INCIDENT RULES PREVIEW (First 500 chars from GitHub):")
            print("="*60)
            print(response.text[:500])
            print("="*60 + "\n")

            self._parse_incident_rules(response.text)
            print(" ✓ Successfully loaded incident rules from GitHub")

            print("📥 Fetching change_management_rules.txt from GitHub...")
            change_url = GITHUB_BASE_URL + "change_management_rules.txt"
            response = requests.get(change_url)
            response.raise_for_status()

            print("\n" + "="*60)
            print("📄 CHANGE RULES PREVIEW (First 500 chars from GitHub):")
            print("="*60)
            print(response.text[:500])
            print("="*60 + "\n")

            self._parse_change_rules(response.text)
            print(" ✓ Successfully loaded change rules from GitHub\n")

        except Exception as e:
            print(f"❌ Error fetching rules from GitHub: {e}")
            print("⚠️  Falling back to local rules files...")
            self._load_local_rules()

    def _load_local_rules(self):
        try:
            with open('incident_management_rules.txt', 'r', encoding='utf-8') as f:
                self._parse_incident_rules(f.read())
            with open('change_management_rules.txt', 'r', encoding='utf-8') as f:
                self._parse_change_rules(f.read())
            print(" ✓ Loaded rules from local files\n")
        except Exception as e:
            print(f"❌ Error loading local rules: {e}")

    def _parse_incident_rules(self, content):
        self.incident_rules['sla'] = {
            'Critical': {'response': 0.25, 'resolution': 4},
            'High': {'response': 1, 'resolution': 12},
            'Medium': {'response': 4, 'resolution': 48},
            'Low': {'response': 8, 'resolution': 96}
        }

        self.incident_rules['required_steps'] = {
            'network': ['Initial Assessment', 'Network Diagnostics', 'Root Cause Analysis',
                       'Solution Implementation', 'Testing', 'Documentation', 'Closure'],
            'application': ['Initial Assessment', 'Code Review', 'Bug Identification',
                           'Fix Implementation', 'Testing', 'Deployment', 'User Validation', 'Closure'],
            'hardware': ['Initial Assessment', 'Hardware Diagnostics', 'Component Testing',
                        'Replacement/Repair', 'System Testing', 'Documentation', 'Closure'],
            'security': ['Initial Assessment', 'Security Scan', 'Threat Analysis',
                        'Patch Implementation', 'Security Testing', 'Compliance Verification',
                        'Documentation', 'Closure'],
            'database': ['Initial Assessment', 'Query Analysis', 'Performance Check',
                        'Backup Verification', 'Fix Implementation', 'Data Validation',
                        'Documentation', 'Closure']
        }

        self.incident_rules['max_reassignments'] = 2
        self.incident_rules['kb_required_priorities'] = ['Critical', 'High']

    def _parse_change_rules(self, content):
        self.change_rules['required_approvals'] = {
            'Standard': ['Pre-Approved'],
            'Normal': ['Manager', 'CAB'],
            'Emergency': ['IT Director', 'ECAB']
        }

        self.change_rules['testing_required_risks'] = ['Critical', 'High']

    def get_incident_sla(self, priority):
        return self.incident_rules['sla'].get(priority, {})

    def get_required_steps(self, category):
        return self.incident_rules['required_steps'].get(category.lower(), [])

    def get_change_approvals(self, change_type):
        return self.change_rules['required_approvals'].get(change_type, [])

    def is_testing_required(self, risk_level):
        return risk_level in self.change_rules['testing_required_risks']


class IntelligentAnalysisAgent:
    """Agent 2: Intelligent Deviation Analysis"""

    def __init__(self, doc_agent):
        self.doc_agent = doc_agent
        self.historical_data = []
        print("🤖 [Agent 2] Intelligent Analysis Agent initialized\n")

    def analyze_incident(self, incident):
        deviations = []

        # SLA Analysis
        sla = self.doc_agent.get_incident_sla(incident['Priority'])
        created = pd.to_datetime(incident['Created_Date'])
        resolved = pd.to_datetime(incident['Resolved_Date'])
        resolution_hours = (resolved - created).total_seconds() / 3600

        if resolution_hours > sla['resolution']:
            deviation_pct = round((resolution_hours - sla['resolution']) / sla['resolution'] * 100, 1)
            deviations.append({
                'type': 'SLA_RESOLUTION_BREACH',
                'severity': 'CRITICAL' if incident['Priority'] in ['Critical', 'High'] else 'MEDIUM',
                'expected': sla['resolution'],
                'actual': round(resolution_hours, 2),
                'deviation_pct': deviation_pct,
                'detail': f"Expected: {sla['resolution']} hours | Actual: {round(resolution_hours, 2)} hours | Exceeded by: {round(resolution_hours - sla['resolution'], 2)} hours ({deviation_pct}% over SLA)"
            })

        # Process Steps Analysis
        required_steps = self.doc_agent.get_required_steps(incident['Category'])
        completed_steps = incident['Steps_Completed'].split(' | ')
        missing_steps = [s for s in required_steps if s not in completed_steps]

        if missing_steps:
            deviations.append({
                'type': 'MISSING_PROCESS_STEPS',
                'severity': 'HIGH',
                'missing_steps': missing_steps,
                'detail': f"Missing Steps: {', '.join(missing_steps)}"
            })

        # Reassignment Analysis
        if incident['Reassignment_Count'] > 2:
            deviations.append({
                'type': 'EXCESSIVE_REASSIGNMENTS',
                'severity': 'MEDIUM',
                'count': incident['Reassignment_Count'],
                'detail': f"Reassigned {incident['Reassignment_Count']} times (Maximum allowed: 2)"
            })

        # Knowledge Article Check
        if incident['Priority'] in ['Critical', 'High'] and incident['Knowledge_Article_Created'] == 'No':
            deviations.append({
                'type': 'MISSING_KNOWLEDGE_ARTICLE',
                'severity': 'MEDIUM',
                'detail': f"Knowledge Article required for {incident['Priority']} priority incidents but not created"
            })

        suggested_solution = self._suggest_solution(incident)
        estimated_time = self._estimate_resolution_time(incident)

        return {
            'id': incident['Incident_ID'],
            'type': 'Incident',
            'category': incident['Category'],
            'priority': incident['Priority'],
            'technician': incident['Technician_Name'],
            'email': incident['Technician_Email'],
            'manager_name': incident['Manager_Name'],
            'manager_email': incident['Manager_Email'],
            'deviations': deviations,
            'deviation_count': len(deviations),
            'compliance_status': 'NON-COMPLIANT' if deviations else 'COMPLIANT',
            'suggested_solution': suggested_solution,
            'estimated_resolution_time': estimated_time
        }

    def analyze_change(self, change):
        deviations = []

        # Approval Analysis
        required_approvals = self.doc_agent.get_change_approvals(change['Type'])
        obtained_approvals = change['Obtained_Approvals'].split(' | ')
        missing_approvals = [a for a in required_approvals if a not in obtained_approvals]

        if missing_approvals:
            deviations.append({
                'type': 'MISSING_APPROVALS',
                'severity': 'CRITICAL',
                'missing': missing_approvals,
                'detail': f"Missing Approvals: {', '.join(missing_approvals)} | Required: {', '.join(required_approvals)} | Obtained: {', '.join(obtained_approvals)}"
            })

        # Testing Analysis
        if self.doc_agent.is_testing_required(change['Risk_Level']):
            if change['Testing_Required'] == 'Yes' and change['Testing_Completed'] == 'No':
                deviations.append({
                    'type': 'MISSING_TESTING_EVIDENCE',
                    'severity': 'HIGH',
                    'detail': f"Testing required for {change['Risk_Level']} risk changes but not completed"
                })

        # Rollback Plan
        if change['Rollback_Plan_Documented'] == 'No':
            deviations.append({
                'type': 'MISSING_ROLLBACK_PLAN',
                'severity': 'HIGH',
                'detail': "Rollback plan not documented (Required for all changes)"
            })

        # Blackout Window
        if change['Implemented_During_Blackout'] == 'Yes':
            deviations.append({
                'type': 'BLACKOUT_WINDOW_VIOLATION',
                'severity': 'CRITICAL',
                'detail': "Change implemented during blackout window (Friday 6PM - Monday 6AM or month-end)"
            })

        # Post-Implementation Review
        if change['Post_Implementation_Review_Completed'] == 'No':
            deviations.append({
                'type': 'MISSING_PIR',
                'severity': 'MEDIUM',
                'detail': "Post-Implementation Review not completed"
            })

        # KB Update
        if change['Knowledge_Base_Updated'] == 'No':
            deviations.append({
                'type': 'KB_NOT_UPDATED',
                'severity': 'MEDIUM',
                'detail': "Knowledge Base not updated with change details"
            })

        return {
            'id': change['Change_ID'],
            'type': 'Change',
            'category': change['Category'],
            'risk_level': change['Risk_Level'],
            'technician': change['Technician_Name'],
            'email': change['Technician_Email'],
            'manager_name': change['Manager_Name'],
            'manager_email': change['Manager_Email'],
            'deviations': deviations,
            'deviation_count': len(deviations),
            'compliance_status': 'NON-COMPLIANT' if deviations else 'COMPLIANT'
        }

    def _suggest_solution(self, incident):
        suggestions = {
            'Network': 'Check network connectivity, verify routing tables, restart network services',
            'Application': 'Review application logs, check for code errors, restart application services',
            'Hardware': 'Run hardware diagnostics, check component status, plan replacement if needed',
            'Security': 'Isolate affected systems, apply security patches, conduct security scan',
            'Database': 'Check database logs, optimize queries, verify backup integrity'
        }
        return suggestions.get(incident['Category'], 'Conduct root cause analysis')

    def _estimate_resolution_time(self, incident):
        base_times = {'Critical': 3,'High': 8,'Medium': 24,'Low': 48}
        return f"{base_times.get(incident['Priority'], 24)} hours"

    def predict_sla_breaches(self, incidents_df):
        at_risk = []
        current_time = datetime.now()

        for _, incident in incidents_df.iterrows():
            created = pd.to_datetime(incident['Created_Date'])
            sla = self.doc_agent.get_incident_sla(incident['Priority'])
            sla_deadline = created + timedelta(hours=sla['resolution'])

            if incident.get('Resolved_Date'):
                resolved = pd.to_datetime(incident['Resolved_Date'])
                if resolved > sla_deadline:
                    at_risk.append({
                        'id': incident['Incident_ID'],
                        'priority': incident['Priority'],
                        'manager_email': incident['Manager_Email'],
                        'status': 'BREACHED',
                        'deadline': sla_deadline.strftime('%Y-%m-%d %H:%M:%S')
                    })
            else:
                hours_remaining = (sla_deadline - current_time).total_seconds() / 3600
                if hours_remaining < 2:
                    at_risk.append({
                        'id': incident['Incident_ID'],
                        'priority': incident['Priority'],
                        'manager_email': incident['Manager_Email'],
                        'status': 'AT_RISK',
                        'hours_remaining': round(hours_remaining, 1),
                        'deadline': sla_deadline.strftime('%Y-%m-%d %H:%M:%S')
                    })

        return at_risk


class EmailNotificationAgent:
    """Agent 3: Email Notification with Clear Deviation Details"""

    def __init__(self):
        print("🤖 [Agent 3] Email Notification Agent initialized\n")

    def send_manager_reports(self, results, at_risk_incidents):
        manager_data = defaultdict(lambda: {'incidents': [], 'changes': [], 'at_risk': []})

        for result in results:
            manager_email = result['manager_email']
            if result['type'] == 'Incident':
                manager_data[manager_email]['incidents'].append(result)
            else:
                manager_data[manager_email]['changes'].append(result)

        for at_risk in at_risk_incidents:
            manager_email = at_risk['manager_email']
            manager_data[manager_email]['at_risk'].append(at_risk)

        for manager_email, data in manager_data.items():
            self._send_email(manager_email, data)

    def _send_email(self, manager_email, data):
        incidents = [r for r in data['incidents'] if r['compliance_status'] == 'NON-COMPLIANT']
        changes = [r for r in data['changes'] if r['compliance_status'] == 'NON-COMPLIANT']
        at_risk = data['at_risk']

        if not incidents and not changes and not at_risk:
            print(f" ✓ No deviations for {manager_email} - skipping email")
            return

        html_content = self._generate_professional_html(manager_email, incidents, changes, at_risk)

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = SENDER_EMAIL
            msg['To'] = manager_email
            msg['Subject'] = f"🚨 ITSM Compliance Report - {datetime.now().strftime('%d %B %Y')}"

            msg.attach(MIMEText(html_content, 'html'))

            print(f"📧 Sending email to {manager_email}...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            print(f" ✅ Successfully sent to {manager_email} ({len(incidents)} incidents, {len(changes)} changes, {len(at_risk)} at-risk)\n")

        except Exception as e:
            print(f" ❌ Failed to send email to {manager_email}: {e}\n")

    def _generate_professional_html(self, manager_email, incidents, changes, at_risk):
        """Generate professional HTML with clear deviation details"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: white;
                    padding: 0;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .summary-box {{
                    display: flex;
                    justify-content: space-around;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-bottom: 2px solid #e9ecef;
                }}
                .summary-item {{
                    text-align: center;
                }}
                .summary-number {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .summary-label {{
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                }}
                .section {{
                    padding: 25px;
                    border-bottom: 1px solid #e9ecef;
                }}
                .section-title {{
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 3px solid #667eea;
                }}
                .alert-critical {{
                    background-color: #fff5f5;
                    border-left: 5px solid #f56565;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .alert-high {{
                    background-color: #fffbf0;
                    border-left: 5px solid #ed8936;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .alert-medium {{
                    background-color: #fefcf3;
                    border-left: 5px solid #ecc94b;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin-right: 5px;
                }}
                .badge-critical {{ background-color: #f56565; color: white; }}
                .badge-high {{ background-color: #ed8936; color: white; }}
                .badge-medium {{ background-color: #ecc94b; color: #744210; }}
                .item-header {{
                    font-weight: bold;
                    font-size: 16px;
                    margin-bottom: 10px;
                    color: #2d3748;
                }}
                .deviation-item {{
                    background-color: #fff;
                    border: 1px solid #e2e8f0;
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 4px;
                }}
                .deviation-type {{
                    font-weight: bold;
                    color: #2d3748;
                    margin-bottom: 5px;
                }}
                .deviation-detail {{
                    color: #4a5568;
                    font-size: 13px;
                    padding-left: 10px;
                    border-left: 3px solid #e2e8f0;
                    margin-top: 5px;
                }}
                .solution-box {{
                    background-color: #e6fffa;
                    border-left: 4px solid #38b2ac;
                    padding: 12px;
                    margin-top: 10px;
                    border-radius: 4px;
                }}
                .footer {{
                    background-color: #2d3748;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                }}
                .table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                .table th {{
                    background-color: #4a5568;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-size: 12px;
                }}
                .table td {{
                    padding: 10px 12px;
                    border-bottom: 1px solid #e2e8f0;
                    font-size: 13px;
                }}
                .breached {{ background-color: #fff5f5; }}
                .at-risk {{ background-color: #fffbf0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 ITSM Compliance & Deviation Report</h1>
                    <p>Manager: {manager_email}</p>
                    <p>Report Generated: {datetime.now().strftime('%d %B %Y at %I:%M %p IST')}</p>
                </div>

                <div class="summary-box">
                    <div class="summary-item">
                        <div class="summary-number">{len(at_risk)}</div>
                        <div class="summary-label">SLA At Risk</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{len(incidents)}</div>
                        <div class="summary-label">Incident Deviations</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{len(changes)}</div>
                        <div class="summary-label">Change Deviations</div>
                    </div>
                </div>
        """

        # Section 1: SLA Breaches & At-Risk Incidents
        if at_risk:
            html += """
                <div class="section">
                    <div class="section-title">⚠️ Section 1: SLA Status & Upcoming Breaches</div>
                    <p><strong>Action Required:</strong> Immediate attention needed for incidents approaching or exceeding SLA deadlines.</p>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Incident ID</th>
                                <th>Priority</th>
                                <th>Status</th>
                                <th>SLA Deadline</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            for item in at_risk:
                row_class = 'breached' if item['status'] == 'BREACHED' else 'at-risk'
                html += f"""
                            <tr class="{row_class}">
                                <td><strong>{item['id']}</strong></td>
                                <td><span class="badge badge-critical">{item['priority']}</span></td>
                                <td>{'🔴 BREACHED' if item['status'] == 'BREACHED' else '⚠️ AT RISK'}</td>
                                <td>{item['deadline']}</td>
                            </tr>
                """
            html += """
                        </tbody>
                    </table>
                </div>
            """

        # Section 2: Incident Management Deviations (Past - Already Completed)
        if incidents:
            html += """
                <div class="section">
                    <div class="section-title">📋 Section 2: Incident Deviations (Past Completed Incidents)</div>
                    <p><strong>Review Required:</strong> These incidents are already resolved but contain process deviations.</p>
            """
            for inc in incidents:
                severity_class = 'alert-critical' if any(d['severity'] == 'CRITICAL' for d in inc['deviations']) else 'alert-high'
                html += f"""
                    <div class="{severity_class}">
                        <div class="item-header">
                            {inc['id']} - {inc['category']} 
                            <span class="badge badge-{inc['priority'].lower()}">{inc['priority']}</span>
                        </div>
                        <p><strong>Technician:</strong> {inc['technician']}</p>

                        <p><strong>❌ What Was Missing:</strong></p>
                """

                # Show detailed deviations
                for dev in inc['deviations']:
                    html += f"""
                        <div class="deviation-item">
                            <div class="deviation-type">
                                • {dev['type'].replace('_', ' ')} 
                                <span class="badge badge-{dev['severity'].lower()}">{dev['severity']}</span>
                            </div>
                            <div class="deviation-detail">
                                📌 {dev.get('detail', 'See details above')}
                            </div>
                        </div>
                    """

                html += f"""
                        <div class="solution-box">
                            <p><strong>💡 Recommended Solution for Future Similar Issues:</strong></p>
                            <p>{inc.get('suggested_solution', 'N/A')}</p>
                            <p><strong>⏱️ Estimated Resolution Time:</strong> {inc.get('estimated_resolution_time', 'N/A')}</p>
                        </div>
                    </div>
                """
            html += "</div>"

        # Section 3: Change Management Deviations (Past - Already Implemented)
        if changes:
            html += """
                <div class="section">
                    <div class="section-title">🔄 Section 3: Change Deviations (Past Implemented Changes)</div>
                    <p><strong>Review Required:</strong> These changes are already implemented but contain compliance issues.</p>
            """
            for chg in changes:
                severity_class = 'alert-critical' if any(d['severity'] == 'CRITICAL' for d in chg['deviations']) else 'alert-high'
                html += f"""
                    <div class="{severity_class}">
                        <div class="item-header">
                            {chg['id']} - {chg['category']} 
                            <span class="badge badge-{chg['risk_level'].lower()}">{chg['risk_level']} Risk</span>
                        </div>
                        <p><strong>Technician:</strong> {chg['technician']}</p>

                        <p><strong>❌ What Was Missing:</strong></p>
                """

                # Show detailed deviations for changes
                for dev in chg['deviations']:
                    html += f"""
                        <div class="deviation-item">
                            <div class="deviation-type">
                                • {dev['type'].replace('_', ' ')} 
                                <span class="badge badge-{dev['severity'].lower()}">{dev['severity']}</span>
                            </div>
                            <div class="deviation-detail">
                                📌 {dev.get('detail', 'See details above')}
                            </div>
                        </div>
                    """

                html += """
                    </div>
                """
            html += "</div>"

        html += f"""
                <div class="footer">
                    <p><strong>ITSM Multi-Agent System</strong></p>
                    <p>Powered by AI-based Deviation Detection & GitHub Rule Integration</p>
                    <p>For questions, contact: {SENDER_EMAIL}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


def export_to_csv(incident_results, change_results, at_risk):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    incident_data = []
    for r in incident_results:
        incident_data.append({
            'ID': r['id'],
            'Type': r['type'],
            'Category': r['category'],
            'Priority': r['priority'],
            'Technician': r['technician'],
            'Manager': r['manager_name'],
            'Manager_Email': r['manager_email'],
            'Deviation_Count': r['deviation_count'],
            'Compliance_Status': r['compliance_status'],
            'Suggested_Solution': r.get('suggested_solution', ''),
            'Estimated_Time': r.get('estimated_resolution_time', '')
        })

    file_incidents = f"itsm_analysis_incidents_{timestamp}.csv"
    pd.DataFrame(incident_data).to_csv(file_incidents, index=False)

    change_data = []
    for r in change_results:
        change_data.append({
            'ID': r['id'],
            'Type': r['type'],
            'Category': r['category'],
            'Risk_Level': r['risk_level'],
            'Technician': r['technician'],
            'Manager': r['manager_name'],
            'Manager_Email': r['manager_email'],
            'Deviation_Count': r['deviation_count'],
            'Compliance_Status': r['compliance_status']
        })

    file_changes = f"itsm_analysis_changes_{timestamp}.csv"
    pd.DataFrame(change_data).to_csv(file_changes, index=False)

    file_atrisk = None
    if at_risk:
        file_atrisk = f"itsm_analysis_atrisk_{timestamp}.csv"
        pd.DataFrame(at_risk).to_csv(file_atrisk, index=False)

    print(f"\n📊 CSV exports created:")
    print(f"   - {file_incidents}")
    print(f"   - {file_changes}")
    if file_atrisk:
        print(f"   - {file_atrisk}")

    return file_incidents, file_changes, file_atrisk


def main():
    print("📊 Loading CSV data files...")

    try:
        incidents_df = pd.read_csv('incidents_data.csv')
        print(f" ✓ Loaded {len(incidents_df)} incidents")
    except FileNotFoundError:
        print(" ✗ incidents_data.csv not found!")
        return

    try:
        changes_df = pd.read_csv('changes_data.csv')
        print(f" ✓ Loaded {len(changes_df)} changes\n")
    except FileNotFoundError:
        print(" ✗ changes_data.csv not found!")
        return

    doc_agent = GitHubDocumentAgent()
    analysis_agent = IntelligentAnalysisAgent(doc_agent)
    email_agent = EmailNotificationAgent()

    print("🔍 Analyzing incidents...")
    incident_results = []
    for _, incident in incidents_df.iterrows():
        result = analysis_agent.analyze_incident(incident)
        incident_results.append(result)
    print(f" ✓ Analyzed {len(incident_results)} incidents\n")

    print("🔍 Analyzing changes...")
    change_results = []
    for _, change in changes_df.iterrows():
        result = analysis_agent.analyze_change(change)
        change_results.append(result)
    print(f" ✓ Analyzed {len(change_results)} changes\n")

    print("🔮 Predicting SLA breaches...")
    at_risk = analysis_agent.predict_sla_breaches(incidents_df)
    print(f" ✓ Found {len(at_risk)} at-risk incidents\n")

    files = export_to_csv(incident_results, change_results, at_risk)

    print("\n📧 Sending manager notifications...")
    print("="*60)
    all_results = incident_results + change_results
    email_agent.send_manager_reports(all_results, at_risk)

    print("\n" + "="*80)
    print("📈 FINAL ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total Incidents Analyzed: {len(incident_results)}")
    print(f"Non-Compliant Incidents: {sum(1 for r in incident_results if r['compliance_status'] == 'NON-COMPLIANT')}")
    print(f"Total Changes Analyzed: {len(change_results)}")
    print(f"Non-Compliant Changes: {sum(1 for r in change_results if r['compliance_status'] == 'NON-COMPLIANT')}")
    print(f"At-Risk/Breached Incidents: {len(at_risk)}")
    print(f"\n📁 CSV Reports: {files}")
    print("="*80)
    print("✅ Analysis Complete!")


if __name__ == "__main__":
    main()
