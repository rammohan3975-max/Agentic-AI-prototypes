"""
Jira Connector - FINAL VERSION with Manager Emails
==================================================
Fetches incidents from Jira and adds manager email assignments
"""
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import random

load_dotenv()

class JiraConnector:
    """Connector for Jira with Manager Email Support"""
    
    def __init__(self):
        self.server = os.getenv("JIRA_SERVER")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "ITSM")
        
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Manager list for assignment
        self.managers = [
            {"name": "Rammohan Davala", "email": "davala.rammohan@cognizant.com"},
            {"name": "Siddhartha Chakraborty", "email": "Siddhartha.chakraberty@cognizant.com"}
        ]
        
        print(f"🔗 Jira Connector initialized")
        print(f"   Server: {self.server}")
        print(f"   Project: {self.project_key}")
    
    def test_connection(self):
        """Test Jira connection"""
        print("\n🔍 Testing Jira connection...")
        try:
            url = f"{self.server}/rest/api/3/myself"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            user = response.json()
            print(f" ✓ Connected as: {user.get('displayName')}")
            return True
        except Exception as e:
            print(f" ✗ Connection failed: {e}")
            return False
    
    def fetch_incidents(self, days_back=30):
        """Fetch incidents from Jira with manager emails"""
        print(f"\n📥 Fetching incidents from last {days_back} days...")
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        jql = f'project = {self.project_key} AND created >= "{start_date}"'
        
        try:
            url = f"{self.server}/rest/api/3/search"
            params = {
                'jql': jql,
                'maxResults': 100,
                'fields': 'summary,priority,status,created,resolutiondate,assignee'
            }
            
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            
            print(f" ✓ Fetched {len(issues)} incidents from Jira")
            
            if len(issues) == 0:
                print("\n⚠️  No incidents found in Jira!")
                print("💡 Create incidents first:")
                print("   python jira_sample_data_creator_fixed.py")
                return pd.DataFrame()
            
            df = self._transform_incidents(issues)
            print(f" ✓ Transformed {len(df)} incidents with manager assignments")
            
            return df
            
        except Exception as e:
            print(f" ✗ Error fetching incidents: {e}")
            return pd.DataFrame()
    
    def _transform_incidents(self, issues):
        """Transform Jira issues to standard format with manager emails"""
        transformed = []
        
        for issue in issues:
            fields = issue.get('fields', {})
            
            # Get dates
            created = pd.to_datetime(fields.get('created'))
            resolved = pd.to_datetime(fields.get('resolutiondate')) if fields.get('resolutiondate') else pd.NaT
            
            # Calculate times
            if pd.notna(resolved):
                resolution_hours = (resolved - created).total_seconds() / 3600
            else:
                resolution_hours = 0
            
            # Map priority
            priority_obj = fields.get('priority', {})
            priority = self._map_priority(priority_obj.get('name', 'Medium') if priority_obj else 'Medium')
            
            # Get assignee
            assignee_obj = fields.get('assignee', {})
            assignee_name = assignee_obj.get('displayName', 'Unassigned') if assignee_obj else 'Unassigned'
            
            # SLA targets
            sla_targets = {'Critical': 4, 'High': 12, 'Medium': 48, 'Low': 96}
            sla_target = sla_targets.get(priority, 48)
            
            # Randomly assign manager
            manager = random.choice(self.managers)
            
            # Determine missing steps (simulate deviation)
            all_steps = ['Initial Assessment', 'Root Cause Analysis', 'Solution Implementation', 'Testing', 'Documentation', 'Closure']
            completed_steps = ['Initial Assessment', 'Solution Implementation', 'Closure']
            missing_steps = [s for s in all_steps if s not in completed_steps]
            
            transformed.append({
                'Incident_ID': issue.get('key'),
                'Type': 'Incident',
                'Category': random.choice(['Network', 'Application', 'Hardware', 'Security', 'Database']),
                'Priority': priority,
                'Description': fields.get('summary', ''),
                'Affected_Users': 100,
                'Location': 'Cloud',
                'Technician_Name': assignee_name,
                'Technician_Email': 'rammohan3975@gmail.com',
                'Manager_Name': manager['name'],
                'Manager_Email': manager['email'],
                'Created_Date': created.strftime('%Y-%m-%d %H:%M:%S'),
                'Response_Date': created.strftime('%Y-%m-%d %H:%M:%S'),
                'Resolved_Date': resolved.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(resolved) else '',
                'Response_Hours': 1,
                'Resolution_Hours': round(resolution_hours, 2),
                'SLA_Target_Hours': sla_target,
                'SLA_Breached': 'Yes' if resolution_hours > sla_target else 'No',
                'Steps_Required': ' | '.join(all_steps),
                'Steps_Completed': ' | '.join(completed_steps),
                'Missing_Steps': ' | '.join(missing_steps),
                'Reassignment_Count': random.randint(0, 3),
                'Knowledge_Article_Created': random.choice(['Yes', 'No']),
                'Customer_Satisfaction': 'Satisfied',
                'Business_Impact': f'{priority} priority incident',
                'Root_Cause': 'Under investigation'
            })
        
        return pd.DataFrame(transformed)
    
    def _map_priority(self, jira_priority):
        """Map Jira priority"""
        mapping = {
            'Highest': 'Critical',
            'High': 'High',
            'Medium': 'Medium',
            'Low': 'Low',
            'Lowest': 'Low'
        }
        return mapping.get(jira_priority, 'Medium')


def main():
    """Fetch incidents from Jira and save to CSV"""
    print("="*80)
    print("🚀 JIRA INCIDENT FETCHER - FINAL VERSION")
    print("="*80)
    
    connector = JiraConnector()
    
    if not connector.test_connection():
        print("\n❌ Cannot connect. Check .env file")
        return
    
    incidents_df = connector.fetch_incidents(days_back=30)
    
    if not incidents_df.empty:
        incidents_df.to_csv('incidents_data.csv', index=False)
        print(f"\n💾 Saved {len(incidents_df)} incidents to incidents_data.csv")
        print("\n📊 Manager Assignment:")
        print(incidents_df[['Incident_ID', 'Manager_Email']].head(10))
    
    print("\n✅ Done! Now run: python run_itsm_final_clear.py")


if __name__ == "__main__":
    main()
