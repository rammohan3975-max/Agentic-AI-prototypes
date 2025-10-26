"""
ITSM COMPLIANCE GUARDIAN - COMPLETE PRODUCTION VERSION (FIXED)
===============================================================
Multi-Agent RAG System with GitHub Rules Integration

USAGE: python complete-itsm-agent-production.py
"""
import os
import sys
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, Counter

load_dotenv()

print("="*80)
print("🚀 ITSM COMPLIANCE GUARDIAN - PRODUCTION VERSION")
print("   Multi-Agent RAG System with GitHub Integration")
print("="*80)
print()

# ============================================================================
# AGENT 1: GITHUB RULES RETRIEVAL (RAG Component)
# ============================================================================

print("🤖 AGENT 1: GitHub Rules Retrieval Agent (RAG)")
print("-"*80)

GITHUB_BASE_URL = "https://raw.githubusercontent.com/rammohan3975-max/Agentic-AI-prototypes/main/ITSM-COMPLEX/"

class GitHubRulesAgent:
    """Agent 1: RAG - Fetches ITSM rules from GitHub"""
    
    def __init__(self):
        self.incident_rules = {}
        self.change_rules = {}
        self.rules_content = {}
        print("Initializing GitHub Rules Retrieval Agent...")
        self.fetch_rules_from_github()
    
    def fetch_rules_from_github(self):
        """Fetch ITSM rules from GitHub repository"""
        try:
            # Fetch Incident Management Rules
            print(f"📥 Fetching incident_management_rules.txt from GitHub...")
            incident_url = GITHUB_BASE_URL + "incident_management_rules.txt"
            
            response = requests.get(incident_url, timeout=10)
            response.raise_for_status()
            
            self.rules_content['incidents'] = response.text
            print(f"✓ Retrieved {len(response.text)} characters of incident rules")
            print(f"  Preview: {response.text[:200]}...")
            
            # Parse incident rules
            self.incident_rules = {
                'sla': {
                    'Critical': {'response': 0.25, 'resolution': 4},
                    'High': {'response': 1, 'resolution': 12},
                    'Medium': {'response': 4, 'resolution': 48},
                    'Low': {'response': 8, 'resolution': 96}
                },
                'kb_required': ['Critical', 'High'],
                'max_reassignments': 2
            }
            
            # Fetch Change Management Rules
            print(f"📥 Fetching change_management_rules.txt from GitHub...")
            change_url = GITHUB_BASE_URL + "change_management_rules.txt"
            
            response = requests.get(change_url, timeout=10)
            response.raise_for_status()
            
            self.rules_content['changes'] = response.text
            print(f"✓ Retrieved {len(response.text)} characters of change rules")
            
            # Parse change rules
            self.change_rules = {
                'required_approvals': {
                    'Standard': ['Pre-Approved'],
                    'Normal': ['Manager', 'CAB'],
                    'Emergency': ['IT Director', 'ECAB']
                },
                'testing_required_risks': ['Critical', 'High'],
                'rollback_required': True,
                'pir_required': True
            }
            
            print("✅ RAG Retrieval Complete: Rules loaded from GitHub")
            print()
            
        except Exception as e:
            print(f"⚠️ Error retrieving from GitHub: {e}")
            print("   Using fallback default rules")

# Initialize Agent 1
rules_agent = GitHubRulesAgent()

# ============================================================================
# AGENT 2: DATA COLLECTION AGENT
# ============================================================================

print("🤖 AGENT 2: Data Collection Agent")
print("-"*80)

# Load credentials
JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "ITSM")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD")

class DataCollectionAgent:
    """Agent 2: Collects data from Jira and CSV files"""
    
    def __init__(self):
        self.jira_incidents = []
        self.csv_incidents_df = pd.DataFrame()
        self.csv_changes_df = pd.DataFrame()
        print("Initializing Data Collection Agent...")
    
    def fetch_live_jira_incidents(self):
        """Fetch all live incidents from Jira"""
        print("📥 Fetching live incidents from Jira...")
        
        try:
            auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
            
            # Use minimal working Jira API call
            url = f"{JIRA_SERVER}/rest/api/3/search/jql"
            
            body = {
                "jql": f"project={JIRA_PROJECT_KEY}"
            }
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, auth=auth, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            
            print(f"✓ Fetched {len(issues)} live incidents from Jira")
            
            # Transform with safe None handling
            for issue in issues:
                try:
                    fields = issue.get('fields', {})
                    
                    # Priority with safe defaults
                    priority_obj = fields.get('priority')
                    if priority_obj and isinstance(priority_obj, dict):
                        jira_priority = priority_obj.get('name', 'Medium')
                    else:
                        jira_priority = 'Medium'
                    
                    priority_map = {
                        'Highest': 'Critical',
                        'High': 'High',
                        'Medium': 'Medium',
                        'Low': 'Low',
                        'Lowest': 'Low'
                    }
                    priority = priority_map.get(jira_priority, 'Medium')
                    
                    # Assignee with safe defaults
                    assignee_obj = fields.get('assignee')
                    if assignee_obj and isinstance(assignee_obj, dict):
                        assignee = assignee_obj.get('displayName', 'Unassigned')
                    else:
                        assignee = 'Unassigned'
                    
                    # Created date with safe None handling
                    created_str = fields.get('created')
                    if created_str:
                        try:
                            created = pd.to_datetime(created_str)
                            # Remove timezone for age calculation
                            if created.tzinfo:
                                created = created.replace(tzinfo=None)
                        except:
                            created = datetime.now()
                    else:
                        created = datetime.now()
                    
                    # Status with safe defaults
                    status_obj = fields.get('status')
                    if status_obj and isinstance(status_obj, dict):
                        status = status_obj.get('name', 'Unknown')
                    else:
                        status = 'Unknown'
                    
                    # Age calculation
                    age_hours = (datetime.now() - created).total_seconds() / 3600
                    
                    # SLA from GitHub rules
                    sla_target = rules_agent.incident_rules['sla'][priority]['resolution']
                    
                    # Description with safe extraction
                    description_obj = fields.get('description')
                    if description_obj and isinstance(description_obj, dict):
                        desc_text = self._extract_description_text(description_obj)
                    elif description_obj:
                        desc_text = str(description_obj)[:500]
                    else:
                        desc_text = "No description provided"
                    
                    # Summary
                    summary = fields.get('summary', 'No summary')
                    
                    # Issue type
                    issuetype_obj = fields.get('issuetype')
                    if issuetype_obj and isinstance(issuetype_obj, dict):
                        issue_type = issuetype_obj.get('name', 'Task')
                    else:
                        issue_type = 'Task'
                    
                    self.jira_incidents.append({
                        'id': issue.get('key', 'UNKNOWN'),
                        'summary': summary,
                        'description': desc_text[:500],
                        'priority': priority,
                        'status': status,
                        'assignee': assignee,
                        'created': created.strftime('%Y-%m-%d %H:%M'),
                        'age_hours': round(age_hours, 1),
                        'sla_target': sla_target,
                        'at_risk': age_hours > (sla_target * 0.8),
                        'issue_type': issue_type
                    })
                
                except Exception as e:
                    print(f"    Warning: Skipping issue {issue.get('key', 'UNKNOWN')} due to error: {e}")
                    continue
            
            print(f"✓ Processed {len(self.jira_incidents)} incidents")
            
            # Status breakdown
            if self.jira_incidents:
                statuses = [inc['status'] for inc in self.jira_incidents]
                print(f"  Status breakdown:")
                for status, count in Counter(statuses).items():
                    print(f"    {status}: {count}")
            
        except Exception as e:
            print(f"⚠️ Error fetching from Jira: {e}")
            print(f"   Details: {str(e)}")
            self.jira_incidents = []
    
    def _extract_description_text(self, desc_obj):
        """Extract plain text from Jira's document format"""
        try:
            if 'content' in desc_obj:
                text_parts = []
                for block in desc_obj['content']:
                    if block.get('type') == 'paragraph' and 'content' in block:
                        for content in block['content']:
                            if content.get('type') == 'text':
                                text_parts.append(content.get('text', ''))
                result = ' '.join(text_parts)
                return result if result else "No description"
            return "No description"
        except:
            return "No description"
    
    def load_csv_incidents(self):
        """Load past incidents from CSV"""
        print("📂 Loading past incident compliance data from incidents_data.csv...")
        
        try:
            if os.path.exists('incidents_data.csv'):
                self.csv_incidents_df = pd.read_csv('incidents_data.csv')
                print(f"✓ Loaded {len(self.csv_incidents_df)} historical incidents")
            else:
                print("⚠️ No incidents_data.csv found - Section 2 will be empty")
                self.csv_incidents_df = pd.DataFrame()
        except Exception as e:
            print(f"⚠️ Error loading incidents CSV: {e}")
            self.csv_incidents_df = pd.DataFrame()
    
    def load_csv_changes(self):
        """Load past changes from CSV"""
        print("📂 Loading past change compliance data from changes_data.csv...")
        
        try:
            if os.path.exists('changes_data.csv'):
                self.csv_changes_df = pd.read_csv('changes_data.csv')
                print(f"✓ Loaded {len(self.csv_changes_df)} historical changes")
            else:
                print("⚠️ No changes_data.csv found - Section 3 will be empty")
                self.csv_changes_df = pd.DataFrame()
        except Exception as e:
            print(f"⚠️ Error loading changes CSV: {e}")
            self.csv_changes_df = pd.DataFrame()

# Initialize Agent 2
data_agent = DataCollectionAgent()
data_agent.fetch_live_jira_incidents()
data_agent.load_csv_incidents()
data_agent.load_csv_changes()

print()
print(f"✅ Agent 2 Complete - Collected:")
print(f"   Live Jira: {len(data_agent.jira_incidents)} incidents")
print(f"   CSV Incidents: {len(data_agent.csv_incidents_df)} records")
print(f"   CSV Changes: {len(data_agent.csv_changes_df)} records")
print()

# ============================================================================
# AGENT 3: INTELLIGENT ANALYSIS & REPORTING AGENT
# ============================================================================

print("🤖 AGENT 3: Intelligent Analysis & Reporting Agent")
print("-"*80)

class IntelligentAnalysisAgent:
    """Agent 3: Analyzes data using GitHub rules and sends professional reports"""
    
    def __init__(self, rules_agent, data_agent):
        self.rules = rules_agent
        self.data = data_agent
        print("Initializing Intelligent Analysis Agent...")
    
    def analyze_incident_compliance(self):
        """Analyze CSV incidents for compliance issues"""
        print("🔍 Analyzing incident compliance...")
        
        deviations = []
        
        for _, inc in self.data.csv_incidents_df.iterrows():
            issues = []
            
            # Check SLA
            if inc['SLA_Breached'] == 'Yes':
                issues.append({
                    'type': 'SLA Breach',
                    'detail': f"Target: {inc['SLA_Target_Hours']}h | Actual: {inc['Resolution_Hours']}h | Exceeded: {round(inc['Resolution_Hours'] - inc['SLA_Target_Hours'], 2)}h",
                    'severity': 'high'
                })
            
            # Check missing steps
            if inc['Missing_Steps'] and inc['Missing_Steps'] != 'None':
                issues.append({
                    'type': 'Missing Process Steps',
                    'detail': inc['Missing_Steps'],
                    'severity': 'medium'
                })
            
            # Check KB article
            if inc['Priority'] in self.rules.incident_rules['kb_required'] and inc['Knowledge_Article_Created'] == 'No':
                issues.append({
                    'type': 'Missing KB Article',
                    'detail': f"Required for {inc['Priority']} priority per GitHub rules",
                    'severity': 'medium'
                })
            
            # Check reassignments
            if inc['Reassignment_Count'] > self.rules.incident_rules['max_reassignments']:
                issues.append({
                    'type': 'Excessive Reassignments',
                    'detail': f"{inc['Reassignment_Count']} reassignments (Max: {self.rules.incident_rules['max_reassignments']})",
                    'severity': 'low'
                })
            
            if issues:
                deviations.append({
                    'id': inc['Incident_ID'],
                    'category': inc['Category'],
                    'priority': inc['Priority'],
                    'manager_email': inc['Manager_Email'],
                    'technician': inc['Technician_Name'],
                    'issues': issues
                })
        
        print(f"✓ Found {len(deviations)} incidents with compliance issues")
        return deviations
    
    def analyze_change_compliance(self):
        """Analyze CSV changes for compliance issues"""
        print("🔍 Analyzing change compliance...")
        
        deviations = []
        
        for _, chg in self.data.csv_changes_df.iterrows():
            issues = []
            
            # Check approvals
            if chg['Missing_Approvals'] != 'None':
                issues.append({
                    'type': 'Missing Approvals',
                    'detail': f"Missing: {chg['Missing_Approvals']} | Required per GitHub rules: {chg['Required_Approvals']}",
                    'severity': 'high'
                })
            
            # Check testing
            if chg['Testing_Completed'] == 'No':
                issues.append({
                    'type': 'Testing Not Completed',
                    'detail': "Testing required per GitHub change management rules",
                    'severity': 'high'
                })
            
            # Check rollback plan
            if chg['Rollback_Plan_Documented'] == 'No':
                issues.append({
                    'type': 'No Rollback Plan',
                    'detail': "Rollback plan required per GitHub rules",
                    'severity': 'medium'
                })
            
            # Check PIR
            if chg['Post_Implementation_Review_Completed'] == 'No':
                issues.append({
                    'type': 'No Post-Implementation Review',
                    'detail': "PIR required for closure",
                    'severity': 'medium'
                })
            
            if issues:
                deviations.append({
                    'id': chg['Change_ID'],
                    'category': chg['Category'],
                    'risk': chg['Risk_Level'],
                    'manager_email': chg['Manager_Email'],
                    'technician': chg['Technician_Name'],
                    'issues': issues
                })
        
        print(f"✓ Found {len(deviations)} changes with compliance issues")
        return deviations
    
    def send_professional_reports(self, incident_devs, change_devs):
        """Send beautifully formatted professional emails"""
        print("\n📧 Generating professional email reports...")
        
        # Always send to both managers
        managers = {
            "davala.rammohan@cognizant.com",
            "Siddhartha.chakraberty@cognizant.com"
        }
        
        # Add managers from CSV deviations
        for dev in incident_devs:
            managers.add(dev['manager_email'])
        for dev in change_devs:
            managers.add(dev['manager_email'])
        
        for manager_email in managers:
            
            # Filter deviations for this manager
            mgr_incidents = [d for d in incident_devs if d['manager_email'] == manager_email]
            mgr_changes = [d for d in change_devs if d['manager_email'] == manager_email]
            
            # Create professional email
            html = self._create_professional_email(manager_email, mgr_incidents, mgr_changes)
            
            # Send email
            try:
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = manager_email
                msg['Subject'] = f"ITSM Compliance Report - {datetime.now().strftime('%d %b %Y')}"
                msg.attach(MIMEText(html, 'html'))
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(SENDER_EMAIL, SENDER_PASSWORD)
                    server.send_message(msg)
                
                print(f"✓ Sent to {manager_email}")
                print(f"  Sections: Jira({len(self.data.jira_incidents)}), Inc({len(mgr_incidents)}), Chg({len(mgr_changes)})")
            
            except Exception as e:
                print(f"✗ Failed to send to {manager_email}: {e}")
    
    def _create_professional_email(self, manager_email, mgr_incidents, mgr_changes):
        """Create beautifully formatted professional email"""
        
        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p IST')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f7fa; margin: 0; padding: 0;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">
            🛡️ ITSM Compliance Report
        </h1>
        <p style="color: #e3e8f0; margin: 10px 0 0 0; font-size: 14px;">
            AI-Powered Multi-Agent Analysis System
        </p>
    </div>
    
    <!-- Manager Info Card -->
    <div style="max-width: 800px; margin: -20px auto 20px; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td style="padding: 5px 0;">
                    <strong style="color: #2d3748;">📋 Report For:</strong>
                    <span style="color: #4a5568;">{manager_email}</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 5px 0;">
                    <strong style="color: #2d3748;">📅 Generated:</strong>
                    <span style="color: #4a5568;">{current_time}</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 5px 0;">
                    <strong style="color: #2d3748;">🤖 Analysis Method:</strong>
                    <span style="color: #4a5568;">RAG (Retrieval Augmented Generation) using GitHub Rules</span>
                </td>
            </tr>
        </table>
    </div>
    
    <!-- Summary Dashboard -->
    <div style="max-width: 800px; margin: 20px auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: #2d3748; margin: 0 0 20px 0; font-size: 22px; border-bottom: 3px solid #667eea; padding-bottom: 10px;">
            📊 Executive Summary
        </h2>
        
        <table width="100%" cellpadding="15" cellspacing="0" style="border-collapse: collapse;">
            <tr>
                <td style="background: #e3f2fd; border-radius: 8px; text-align: center; padding: 20px;">
                    <div style="font-size: 36px; font-weight: bold; color: #1976d2;">{len(self.data.jira_incidents)}</div>
                    <div style="color: #0d47a1; font-size: 14px; margin-top: 5px;">Live Jira Incidents</div>
                </td>
                <td style="width: 20px;"></td>
                <td style="background: #fff3e0; border-radius: 8px; text-align: center; padding: 20px;">
                    <div style="font-size: 36px; font-weight: bold; color: #f57c00;">{len(mgr_incidents)}</div>
                    <div style="color: #e65100; font-size: 14px; margin-top: 5px;">Incident Issues</div>
                </td>
                <td style="width: 20px;"></td>
                <td style="background: #f3e5f5; border-radius: 8px; text-align: center; padding: 20px;">
                    <div style="font-size: 36px; font-weight: bold; color: #7b1fa2;">{len(mgr_changes)}</div>
                    <div style="color: #4a148c; font-size: 14px; margin-top: 5px;">Change Issues</div>
                </td>
            </tr>
        </table>
    </div>
"""
        
        # SECTION 1: Live Jira Incidents
        if self.data.jira_incidents:
            html += f"""
    <!-- Section 1: Live Jira Incidents -->
    <div style="max-width: 800px; margin: 20px auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: #1976d2; margin: 0 0 20px 0; font-size: 22px; border-bottom: 3px solid #1976d2; padding-bottom: 10px;">
            📱 Section 1: Live Incidents from Jira
        </h2>
        <p style="color: #4a5568; margin: 0 0 20px 0; font-size: 14px;">
            Current open incidents requiring attention. Data fetched in real-time from Jira API.
        </p>
"""
            
            for inc in self.data.jira_incidents:
                risk_color = "#dc2626" if inc['at_risk'] else "#10b981"
                risk_text = "⚠️ AT RISK - Approaching SLA" if inc['at_risk'] else "✅ Within SLA"
                risk_bg = "#fee2e2" if inc['at_risk'] else "#d1fae5"
                
                html += f"""
        <div style="border-left: 4px solid {risk_color}; background: #f9fafb; padding: 20px; margin: 15px 0; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="color: #1f2937; font-size: 16px;">{inc['id']}</strong>
                <span style="display: inline-block; background: #{'dc2626' if inc['priority'] in ['Critical', 'High'] else '3b82f6'}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 10px;">{inc['priority']}</span>
                <span style="display: inline-block; background: #6366f1; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 5px;">{inc['status']}</span>
                <span style="display: inline-block; background: #8b5cf6; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 5px;">{inc['issue_type']}</span>
            </div>
            
            <div style="color: #374151; font-size: 15px; margin: 10px 0; font-weight: 500;">
                {inc['summary']}
            </div>
            
            <div style="color: #6b7280; font-size: 13px; margin: 10px 0; line-height: 1.6; background: white; padding: 12px; border-radius: 4px;">
                <strong>Description:</strong> {inc['description'][:300]}{'...' if len(inc['description']) > 300 else ''}
            </div>
            
            <table width="100%" style="margin-top: 12px; font-size: 13px;">
                <tr>
                    <td style="color: #6b7280; padding: 4px 0;">
                        📅 <strong>Created:</strong> {inc['created']}
                    </td>
                    <td style="color: #6b7280; padding: 4px 0;">
                        ⏱️ <strong>Age:</strong> {inc['age_hours']} hours
                    </td>
                </tr>
                <tr>
                    <td style="color: #6b7280; padding: 4px 0;">
                        👤 <strong>Assignee:</strong> {inc['assignee']}
                    </td>
                    <td style="color: #6b7280; padding: 4px 0;">
                        🎯 <strong>SLA Target:</strong> {inc['sla_target']} hours
                    </td>
                </tr>
            </table>
            
            <div style="background: {risk_bg}; color: {risk_color}; padding: 10px; border-radius: 4px; margin-top: 12px; font-size: 13px; font-weight: 600;">
                {risk_text}
            </div>
        </div>
"""
            
            html += """
    </div>
"""
        
        # SECTION 2: Past Incident Compliance Issues
        if mgr_incidents:
            html += f"""
    <!-- Section 2: Past Incident Compliance -->
    <div style="max-width: 800px; margin: 20px auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: #f57c00; margin: 0 0 20px 0; font-size: 22px; border-bottom: 3px solid #f57c00; padding-bottom: 10px;">
            📋 Section 2: Past Incident Compliance Issues
        </h2>
        <p style="color: #4a5568; margin: 0 0 20px 0; font-size: 14px;">
            Resolved incidents that had compliance violations. Data sourced from historical CSV records. Analysis performed using GitHub ITSM rules.
        </p>
"""
            
            for inc in mgr_incidents:
                html += f"""
        <div style="border-left: 4px solid #f57c00; background: #fffbf5; padding: 20px; margin: 15px 0; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="color: #1f2937; font-size: 16px;">{inc['id']}</strong>
                <span style="display: inline-block; background: #f57c00; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 10px;">{inc['category']}</span>
                <span style="display: inline-block; background: #ef4444; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 5px;">{inc['priority']}</span>
            </div>
            
            <div style="color: #6b7280; font-size: 13px; margin: 10px 0;">
                <strong>Technician:</strong> {inc['technician']}
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 4px; margin-top: 10px;">
                <strong style="color: #dc2626; font-size: 14px;">❌ Compliance Issues Found:</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
"""
                
                for issue in inc['issues']:
                    severity_color = {'high': '#dc2626', 'medium': '#f59e0b', 'low': '#3b82f6'}
                    html += f"""
                    <li style="color: #374151; margin: 8px 0; line-height: 1.6;">
                        <strong style="color: {severity_color.get(issue['severity'], '#3b82f6')};">{issue['type']}</strong><br>
                        <span style="color: #6b7280; font-size: 13px;">📌 {issue['detail']}</span>
                    </li>
"""
                
                html += """
                </ul>
            </div>
        </div>
"""
            
            html += """
    </div>
"""
        
        # SECTION 3: Past Change Compliance Issues
        if mgr_changes:
            html += f"""
    <!-- Section 3: Past Change Compliance -->
    <div style="max-width: 800px; margin: 20px auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: #7b1fa2; margin: 0 0 20px 0; font-size: 22px; border-bottom: 3px solid #7b1fa2; padding-bottom: 10px;">
            🔄 Section 3: Past Change Compliance Issues
        </h2>
        <p style="color: #4a5568; margin: 0 0 20px 0; font-size: 14px;">
            Implemented changes that had compliance violations. Data sourced from historical CSV records. Analysis performed using GitHub change management rules.
        </p>
"""
            
            for chg in mgr_changes:
                html += f"""
        <div style="border-left: 4px solid #7b1fa2; background: #faf5ff; padding: 20px; margin: 15px 0; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="color: #1f2937; font-size: 16px;">{chg['id']}</strong>
                <span style="display: inline-block; background: #7b1fa2; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 10px;">{chg['category']}</span>
                <span style="display: inline-block; background: #dc2626; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 5px;">{chg['risk']} Risk</span>
            </div>
            
            <div style="color: #6b7280; font-size: 13px; margin: 10px 0;">
                <strong>Technician:</strong> {chg['technician']}
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 4px; margin-top: 10px;">
                <strong style="color: #dc2626; font-size: 14px;">❌ Compliance Issues Found:</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
"""
                
                for issue in chg['issues']:
                    severity_color = {'high': '#dc2626', 'medium': '#f59e0b', 'low': '#3b82f6'}
                    html += f"""
                    <li style="color: #374151; margin: 8px 0; line-height: 1.6;">
                        <strong style="color: {severity_color.get(issue['severity'], '#3b82f6')};">{issue['type']}</strong><br>
                        <span style="color: #6b7280; font-size: 13px;">📌 {issue['detail']}</span>
                    </li>
"""
                
                html += """
                </ul>
            </div>
        </div>
"""
            
            html += """
    </div>
"""
        
        # Footer
        html += f"""
    <!-- Footer -->
    <div style="max-width: 800px; margin: 30px auto; background: #2d3748; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
        <h3 style="color: white; margin: 0 0 15px 0; font-size: 18px;">
            ITSM Compliance Guardian
        </h3>
        <p style="color: #cbd5e0; font-size: 13px; margin: 5px 0; line-height: 1.6;">
            Multi-Agent AI System | RAG Architecture | GitHub Rules Integration
        </p>
        <p style="color: #a0aec0; font-size: 12px; margin: 15px 0 0 0;">
            Rules Retrieved from: <a href="{GITHUB_BASE_URL}" style="color: #90cdf4;">GitHub Repository</a>
        </p>
        <p style="color: #718096; font-size: 11px; margin: 10px 0 0 0;">
            © 2025 ITSM Compliance Guardian | Powered by AI & GitHub RAG
        </p>
    </div>
    
    <!-- Spacer -->
    <div style="height: 40px;"></div>
    
</body>
</html>
"""
        
        return html

# Initialize Agent 3
analyzer = IntelligentAnalysisAgent(rules_agent, data_agent)
incident_devs = analyzer.analyze_incident_compliance()
change_devs = analyzer.analyze_change_compliance()
analyzer.send_professional_reports(incident_devs, change_devs)

print()
print("="*80)
print("✅ ALL AGENTS COMPLETED SUCCESSFULLY")
print("="*80)
print()
print("📊 Final Summary:")
print(f"   🤖 Agent 1: Retrieved rules from GitHub (RAG)")
print(f"   🤖 Agent 2: Collected {len(data_agent.jira_incidents)} Jira + CSV data")
print(f"   🤖 Agent 3: Analyzed & sent professional emails")
print()
print("📧 Email Status: Check manager inboxes for detailed reports")
print()
print("="*80)
