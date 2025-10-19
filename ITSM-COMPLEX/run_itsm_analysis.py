
"""
Enterprise ITSM Multi-Agent System with RAG Document Retrieval
Reads rules from documents and analyzes CSV data automatically
"""

from dotenv import load_dotenv
import datetime
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import re
from typing import List, Dict

load_dotenv(override=True)

# Configuration
MANAGER_EMAIL = "rammohan3975@gmail.com"
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "rammohan3975@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")

class DocumentRetrievalAgent:
    """Agent 1: RAG - Retrieves rules from text documents"""

    def __init__(self, incident_rules_file: str, change_rules_file: str):
        self.incident_rules_file = incident_rules_file
        self.change_rules_file = change_rules_file
        self.incident_rules = {}
        self.change_rules = {}

        print("🤖 [Agent 1] Document Retrieval Agent initializing...")
        print(f"📄 Loading incident rules from: {incident_rules_file}")
        print(f"📄 Loading change rules from: {change_rules_file}")

        self._parse_incident_rules()
        self._parse_change_rules()

        print("✅ Document Retrieval Agent ready\n")

    def _parse_incident_rules(self):
        """Parse incident management rules document"""
        with open(self.incident_rules_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract SLA standards
        sla_section = re.search(r'Response Time Requirements:(.*?)Escalation Triggers:', content, re.DOTALL)
        if sla_section:
            sla_text = sla_section.group(1)
            self.incident_rules['sla'] = {
                'Critical': {'response': 0.25, 'resolution': 4},
                'High': {'response': 1, 'resolution': 12},
                'Medium': {'response': 4, 'resolution': 48},
                'Low': {'response': 8, 'resolution': 96}
            }

        # Extract required steps for each category
        self.incident_rules['required_steps'] = {}
        categories = ['NETWORK', 'APPLICATION', 'HARDWARE', 'SECURITY', 'DATABASE']

        for category in categories:
            pattern = f"{category} INCIDENTS.*?\(\d+ Required Steps\):(.*?)(?:\n\n|[A-Z]+ INCIDENTS|3\. MANDATORY)"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                steps_text = match.group(1)
                steps = re.findall(r'\d+\. (.+?)\n', steps_text)
                self.incident_rules['required_steps'][category.lower()] = steps

        # Extract compliance requirements
        self.incident_rules['max_reassignments'] = 2
        self.incident_rules['kb_required_priorities'] = ['Critical', 'High']
        self.incident_rules['satisfaction_threshold'] = 0.80

        print(f"   ✓ Loaded SLA standards for {len(self.incident_rules['sla'])} priorities")
        print(f"   ✓ Loaded process steps for {len(self.incident_rules['required_steps'])} categories")

    def _parse_change_rules(self):
        """Parse change management rules document"""
        with open(self.change_rules_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract approval requirements
        self.change_rules['required_approvals'] = {
            'Standard': ['Pre-Approved'],
            'Normal': ['Manager', 'CAB'],
            'Emergency': ['IT Director', 'ECAB']
        }

        # Extract blackout windows
        blackout_section = re.search(r'BLACKOUT WINDOWS.*?:(.*?)Emergency Change Exception:', content, re.DOTALL)
        if blackout_section:
            self.change_rules['blackout_windows'] = [
                'Friday 6PM - Monday 6AM',
                'Last week of month',
                'Peak business hours'
            ]

        # Extract mandatory documentation
        self.change_rules['mandatory_fields'] = [
            'Impact Assessment', 'Rollback Plan', 'Testing Evidence',
            'Implementation Plan', 'Communication Plan'
        ]

        self.change_rules['testing_required_risks'] = ['Critical', 'High']

        print(f"   ✓ Loaded approval requirements for {len(self.change_rules['required_approvals'])} change types")
        print(f"   ✓ Loaded {len(self.change_rules['blackout_windows'])} blackout window rules")

    def get_incident_sla(self, priority: str) -> Dict:
        """Get SLA standards for incident priority"""
        return self.incident_rules['sla'].get(priority, {})

    def get_required_steps(self, category: str) -> List[str]:
        """Get required process steps for incident category"""
        return self.incident_rules['required_steps'].get(category.lower(), [])

    def get_change_approvals(self, change_type: str) -> List[str]:
        """Get required approvals for change type"""
        return self.change_rules['required_approvals'].get(change_type, [])

    def is_testing_required(self, risk_level: str) -> bool:
        """Check if testing is required for risk level"""
        return risk_level in self.change_rules['testing_required_risks']

class DeviationAnalysisAgent:
    """Agent 2: Analyzes incidents and changes for deviations"""

    def __init__(self, doc_agent: DocumentRetrievalAgent):
        self.doc_agent = doc_agent
        self.results = []
        print("🤖 [Agent 2] Deviation Analysis Agent initialized\n")

    def analyze_incident(self, incident: pd.Series) -> Dict:
        """Analyze single incident for deviations"""
        deviations = []

        # 1. SLA Analysis
        sla = self.doc_agent.get_incident_sla(incident['Priority'])
        created = pd.to_datetime(incident['Created_Date'])
        response = pd.to_datetime(incident['Response_Date'])
        resolved = pd.to_datetime(incident['Resolved_Date'])

        response_hours = (response - created).total_seconds() / 3600
        resolution_hours = (resolved - created).total_seconds() / 3600

        if response_hours > sla['response']:
            deviations.append({
                'type': 'SLA_RESPONSE_BREACH',
                'severity': 'HIGH',
                'expected': sla['response'],
                'actual': round(response_hours, 2),
                'deviation_pct': round((response_hours - sla['response']) / sla['response'] * 100, 1)
            })

        if resolution_hours > sla['resolution']:
            deviations.append({
                'type': 'SLA_RESOLUTION_BREACH',
                'severity': 'CRITICAL' if incident['Priority'] in ['Critical', 'High'] else 'MEDIUM',
                'expected': sla['resolution'],
                'actual': round(resolution_hours, 2),
                'deviation_pct': round((resolution_hours - sla['resolution']) / sla['resolution'] * 100, 1)
            })

        # 2. Process Steps Analysis
        required_steps = self.doc_agent.get_required_steps(incident['Category'])
        completed_steps = incident['Steps_Completed'].split(' | ')
        missing_steps = [s for s in required_steps if s not in completed_steps]

        if missing_steps:
            deviations.append({
                'type': 'MISSING_PROCESS_STEPS',
                'severity': 'HIGH',
                'missing_steps': missing_steps,
                'completion_rate': round(len(completed_steps) / len(required_steps) * 100, 1)
            })

        # 3. Reassignment Analysis
        if incident['Reassignment_Count'] > 2:
            deviations.append({
                'type': 'EXCESSIVE_REASSIGNMENTS',
                'severity': 'MEDIUM',
                'count': incident['Reassignment_Count']
            })

        # 4. Knowledge Article Analysis
        if incident['Priority'] in ['Critical', 'High'] and incident['Knowledge_Article_Created'] == 'No':
            deviations.append({
                'type': 'MISSING_KNOWLEDGE_ARTICLE',
                'severity': 'MEDIUM'
            })

        # 5. Customer Satisfaction Analysis
        if incident['Customer_Satisfaction'] == 'Dissatisfied':
            deviations.append({
                'type': 'POOR_CUSTOMER_SATISFACTION',
                'severity': 'HIGH'
            })

        result = {
            'id': incident['Incident_ID'],
            'type': 'Incident',
            'category': incident['Category'],
            'priority': incident['Priority'],
            'technician': incident['Technician_Name'],
            'email': incident['Technician_Email'],
            'deviations': deviations,
            'deviation_count': len(deviations),
            'compliance_status': 'NON-COMPLIANT' if len(deviations) > 0 else 'COMPLIANT'
        }

        return result

    def analyze_change(self, change: pd.Series) -> Dict:
        """Analyze single change request for deviations"""
        deviations = []

        # 1. Approval Analysis
        required_approvals = self.doc_agent.get_change_approvals(change['Type'])
        obtained_approvals = change['Obtained_Approvals'].split(' | ')
        missing_approvals = [a for a in required_approvals if a not in obtained_approvals]

        if missing_approvals:
            deviations.append({
                'type': 'MISSING_APPROVALS',
                'severity': 'CRITICAL',
                'missing': missing_approvals
            })

        # 2. Testing Analysis
        if self.doc_agent.is_testing_required(change['Risk_Level']):
            if change['Testing_Required'] == 'Yes' and change['Testing_Completed'] == 'No':
                deviations.append({
                    'type': 'MISSING_TESTING_EVIDENCE',
                    'severity': 'HIGH'
                })

        # 3. Rollback Plan Analysis
        if change['Rollback_Plan_Documented'] == 'No':
            deviations.append({
                'type': 'MISSING_ROLLBACK_PLAN',
                'severity': 'HIGH'
            })

        # 4. Blackout Window Analysis
        if change['Implemented_During_Blackout'] == 'Yes':
            deviations.append({
                'type': 'BLACKOUT_WINDOW_VIOLATION',
                'severity': 'CRITICAL'
            })

        # 5. Post-Implementation Review
        if change['Post_Implementation_Review_Completed'] == 'No':
            deviations.append({
                'type': 'MISSING_PIR',
                'severity': 'MEDIUM'
            })

        # 6. Knowledge Base Update
        if change['Knowledge_Base_Updated'] == 'No':
            deviations.append({
                'type': 'KB_NOT_UPDATED',
                'severity': 'MEDIUM'
            })

        result = {
            'id': change['Change_ID'],
            'type': 'Change',
            'category': change['Category'],
            'risk_level': change['Risk_Level'],
            'technician': change['Technician_Name'],
            'email': change['Technician_Email'],
            'deviations': deviations,
            'deviation_count': len(deviations),
            'compliance_status': 'NON-COMPLIANT' if len(deviations) > 0 else 'COMPLIANT'
        }

        return result

def load_csv_data():
    """Load incident and change CSV files"""
    print("📊 Loading CSV data files...")

    try:
        incidents_df = pd.read_csv('incidents_data.csv')
        print(f"   ✓ Loaded {len(incidents_df)} incidents from incidents_data.csv")
    except FileNotFoundError:
        print("   ✗ incidents_data.csv not found - run generate_incidents.py first!")
        incidents_df = pd.DataFrame()

    try:
        changes_df = pd.read_csv('changes_data.csv')
        print(f"   ✓ Loaded {len(changes_df)} changes from changes_data.csv")
    except FileNotFoundError:
        print("   ✗ changes_data.csv not found - run generate_changes.py first!")
        changes_df = pd.DataFrame()

    print()
    return incidents_df, changes_df

def generate_powerbi_export(incident_results: List[Dict], change_results: List[Dict]) -> str:
    """Generate Power BI compatible dataset"""
    print("📈 Generating Power BI dataset...")

    all_data = []

    for result in incident_results:
        row = {
            'ID': result['id'],
            'Type': result['type'],
            'Category': result['category'],
            'Priority_Risk': result.get('priority', result.get('risk_level', '')),
            'Technician': result['technician'],
            'Deviation_Count': result['deviation_count'],
            'Compliance_Status': result['compliance_status'],
            'Has_SLA_Breach': any(d['type'].startswith('SLA_') for d in result['deviations']),
            'Has_Process_Deviation': any('PROCESS' in d['type'] or 'MISSING' in d['type'] for d in result['deviations']),
            'Timestamp': datetime.datetime.now().isoformat()
        }
        all_data.append(row)

    for result in change_results:
        row = {
            'ID': result['id'],
            'Type': result['type'],
            'Category': result['category'],
            'Priority_Risk': result.get('risk_level', ''),
            'Technician': result['technician'],
            'Deviation_Count': result['deviation_count'],
            'Compliance_Status': result['compliance_status'],
            'Has_SLA_Breach': False,
            'Has_Process_Deviation': True if result['deviation_count'] > 0 else False,
            'Timestamp': datetime.datetime.now().isoformat()
        }
        all_data.append(row)

    df = pd.DataFrame(all_data)
    filename = f'itsm_powerbi_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(filename, index=False)

    print(f"   ✓ Created {filename} with {len(df)} records\n")
    return filename

def create_email_report(incident_results: List[Dict], change_results: List[Dict]) -> str:
    """Generate HTML email report"""

    total_items = len(incident_results) + len(change_results)
    total_deviations = sum(r['deviation_count'] for r in incident_results + change_results)
    non_compliant = len([r for r in incident_results + change_results if r['compliance_status'] == 'NON-COMPLIANT'])

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 30px; border-radius: 8px; }}
            .metric {{ display: inline-block; padding: 15px 25px; margin: 10px; 
                      background: #edf2f7; border-radius: 6px; font-weight: bold; }}
            .critical {{ background: #fff5f5; border-left: 4px solid #f56565; padding: 15px; margin: 10px 0; }}
            .warning {{ background: #fffaf0; border-left: 4px solid #ed8936; padding: 15px; margin: 10px 0; }}
            .success {{ background: #f0fff4; border-left: 4px solid #48bb78; padding: 15px; margin: 10px 0; }}
            .item-card {{ background: white; border: 1px solid #e2e8f0; 
                        padding: 20px; margin: 15px 0; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 ITSM Multi-Agent Analysis Report</h1>
            <p>RAG Document Retrieval + Deviation Analysis</p>
            <p><strong>Generated:</strong> {datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p IST")}</p>
        </div>

        <div style="padding: 20px;">
            <h2>📊 Executive Summary</h2>
            <div class="metric">Total Items: {total_items}</div>
            <div class="metric">Deviations: {total_deviations}</div>
            <div class="metric">Non-Compliant: {non_compliant}</div>
            <div class="metric">Compliance Rate: {round((total_items - non_compliant) / total_items * 100, 1)}%</div>

            <h2>🎫 Incident Analysis</h2>
    """

    for result in incident_results:
        if result['deviation_count'] > 0:
            html += f"""
            <div class="item-card">
                <h3>{result['id']} - {result['category']} ({result['priority']})</h3>
                <p><strong>Technician:</strong> {result['technician']}</p>
                <div class="critical">
                    <strong>⚠️ {result['deviation_count']} Deviation(s) Found:</strong>
                    <ul>
            """
            for dev in result['deviations']:
                html += f"<li>[{dev['severity']}] {dev['type']}"
                if 'missing_steps' in dev:
                    html += f" - Missing: {', '.join(dev['missing_steps'])}"
                if 'deviation_pct' in dev:
                    html += f" ({dev['deviation_pct']}% over limit)"
                html += "</li>"
            html += "</ul></div></div>"

    html += "<h2>🔄 Change Request Analysis</h2>"

    for result in change_results:
        if result['deviation_count'] > 0:
            html += f"""
            <div class="item-card">
                <h3>{result['id']} - {result['category']} ({result['risk_level']})</h3>
                <p><strong>Technician:</strong> {result['technician']}</p>
                <div class="warning">
                    <strong>⚠️ {result['deviation_count']} Deviation(s) Found:</strong>
                    <ul>
            """
            for dev in result['deviations']:
                html += f"<li>[{dev['severity']}] {dev['type']}"
                if 'missing' in dev:
                    html += f" - Missing: {', '.join(dev['missing'])}"
                html += "</li>"
            html += "</ul></div></div>"

    html += """
        <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 2px solid #e2e8f0;">
            <h3>📈 Power BI Dashboard Data Attached</h3>
            <p>Import the CSV file into Power BI to create interactive dashboards</p>
            <p><strong>Enterprise ITSM Multi-Agent System</strong><br>
            Powered by RAG Framework & Document Intelligence</p>
        </div>
    </body>
    </html>
    """

    return html

def send_email(subject: str, html_body: str, attachment_path: str = None):
    """Send email notification"""
    print(f"📧 Sending email to {MANAGER_EMAIL}...")

    if not SENDER_PASSWORD:
        print("   ⚠️  Email not configured - showing preview only\n")
        print(f"Subject: {subject}")
        return

    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = MANAGER_EMAIL

        msg.attach(MIMEText(html_body, 'html'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("   ✅ Email sent successfully!\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

def main():
    """Main execution function"""
    print("="*70)
    print("🚀 ENTERPRISE ITSM MULTI-AGENT SYSTEM")
    print("="*70)
    print(f"⏰ Analysis Time: {datetime.datetime.now().strftime('%I:%M %p, %B %d, %Y')}\n")

    # Initialize Document Retrieval Agent (RAG)
    doc_agent = DocumentRetrievalAgent(
        'incident_management_rules.txt',
        'change_management_rules.txt'
    )

    # Initialize Deviation Analysis Agent
    analysis_agent = DeviationAnalysisAgent(doc_agent)

    # Load CSV data
    incidents_df, changes_df = load_csv_data()

    if incidents_df.empty and changes_df.empty:
        print("❌ No data to analyze. Generate data first:")
        print("   python generate_incidents.py")
        print("   python generate_changes.py")
        return

    print("="*70)
    print("🔍 STARTING ANALYSIS")
    print("="*70 + "\n")

    # Analyze incidents
    incident_results = []
    if not incidents_df.empty:
        print(f"Analyzing {len(incidents_df)} incidents...")
        for _, incident in incidents_df.iterrows():
            result = analysis_agent.analyze_incident(incident)
            incident_results.append(result)
            if result['deviation_count'] > 0:
                print(f"  ⚠️  {result['id']}: {result['deviation_count']} deviations")
        print()

    # Analyze changes
    change_results = []
    if not changes_df.empty:
        print(f"Analyzing {len(changes_df)} change requests...")
        for _, change in changes_df.iterrows():
            result = analysis_agent.analyze_change(change)
            change_results.append(result)
            if result['deviation_count'] > 0:
                print(f"  ⚠️  {result['id']}: {result['deviation_count']} deviations")
        print()

    # Generate Power BI export
    powerbi_file = generate_powerbi_export(incident_results, change_results)

    # Create and send report
    print("📝 Generating executive report...")
    html_report = create_email_report(incident_results, change_results)

    total_items = len(incident_results) + len(change_results)
    non_compliant = len([r for r in incident_results + change_results if r['compliance_status'] == 'NON-COMPLIANT'])

    subject = f"🔍 ITSM Analysis: {non_compliant}/{total_items} Items Non-Compliant"
    send_email(subject, html_report, powerbi_file)

    print("="*70)
    print("✅ ANALYSIS COMPLETE")
    print("="*70)
    print(f"Total Analyzed: {total_items}")
    print(f"Non-Compliant: {non_compliant} ({round(non_compliant/total_items*100, 1)}%)")
    print(f"Power BI Export: {powerbi_file}")
    print("="*70)

if __name__ == "__main__":
    main()
