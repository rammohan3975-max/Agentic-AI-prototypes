"""
Jira Connector for ITSM Compliance Guardian
===========================================
FREE Personal Testing - No Enterprise License Needed!

Features:
- Connects to free Jira Cloud account
- Fetches incidents and service requests
- Maps Jira fields to ITSM standard format
- Works with Jira Service Management (free tier)
"""
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json

load_dotenv()

class JiraConnector:
    """
    Connector for Jira Service Management (Free Personal Account)

    Setup Requirements:
    1. Free Jira account at atlassian.com
    2. API token from id.atlassian.com/manage-profile/security/api-tokens
    3. Project created with "ITSM" key
    """

    def __init__(self):
        # Load from environment
        self.server = os.getenv("JIRA_SERVER", "https://rammohan-itsm.atlassian.net")
        self.email = os.getenv("JIRA_EMAIL", "rammohan3975@gmail.com")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "ITSM")

        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        print(f"🔗 Jira Connector initialized")
        print(f"   Server: {self.server}")
        print(f"   Project: {self.project_key}")
        print(f"   Email: {self.email}")

    def test_connection(self):
        """Test if Jira connection works"""
        print("\n🔍 Testing Jira connection...")

        try:
            url = f"{self.server}/rest/api/3/myself"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()

            user = response.json()
            print(f" ✓ Connected successfully!")
            print(f" ✓ Logged in as: {user.get('displayName')}")
            return True

        except requests.exceptions.RequestException as e:
            print(f" ✗ Connection failed: {e}")
            print("\n💡 Troubleshooting:")
            print("   1. Check JIRA_SERVER in .env")
            print("   2. Verify JIRA_API_TOKEN is correct")
            print("   3. Ensure JIRA_EMAIL matches your Jira account")
            return False

    def fetch_incidents(self, days_back=7):
        """
        Fetch incidents/issues from Jira

        In Jira Service Management, these are called "Incidents" or "Service Requests"
        """
        print(f"\n📥 Fetching incidents from last {days_back} days...")

        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # JQL (Jira Query Language)
        jql = f'project = {self.project_key} AND created >= "{start_date}" AND (type = Incident OR type = "Service Request")'

        try:
            url = f"{self.server}/rest/api/3/search"

            params = {
                'jql': jql,
                'maxResults': 100,
                'fields': 'summary,priority,status,created,resolutiondate,assignee,reporter,customfield_10001'  # Adjust field IDs
            }

            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            issues = data.get('issues', [])

            print(f" ✓ Fetched {len(issues)} incidents from Jira")

            if len(issues) == 0:
                print("\n⚠️  No incidents found!")
                print("💡 Create sample incidents in Jira first:")
                print("   python jira_sample_data_creator.py")
                return pd.DataFrame()

            # Transform to standard format
            df = self._transform_incidents(issues)
            print(f" ✓ Transformed {len(df)} incidents to standard format")

            return df

        except requests.exceptions.RequestException as e:
            print(f" ✗ Error fetching incidents: {e}")
            return pd.DataFrame()

    def fetch_changes(self, days_back=30):
        """
        Fetch change requests from Jira

        In Jira, these might be labeled as "Change" issue type
        """
        print(f"\n📥 Fetching changes from last {days_back} days...")

        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # JQL for changes
        jql = f'project = {self.project_key} AND created >= "{start_date}" AND type = Change'

        try:
            url = f"{self.server}/rest/api/3/search"

            params = {
                'jql': jql,
                'maxResults': 50,
                'fields': 'summary,priority,status,created,customfield_10002,assignee'
            }

            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            issues = data.get('issues', [])

            print(f" ✓ Fetched {len(issues)} changes from Jira")

            if len(issues) == 0:
                print("\n⚠️  No changes found - using incidents for demo")
                print("   (You can create Change type issues in Jira)")
                # Return empty DataFrame - will use incidents
                return pd.DataFrame()

            # Transform to standard format
            df = self._transform_changes(issues)
            print(f" ✓ Transformed {len(df)} changes to standard format")

            return df

        except requests.exceptions.RequestException as e:
            print(f" ✗ Error fetching changes: {e}")
            return pd.DataFrame()

    def _transform_incidents(self, issues):
        """Transform Jira issues to our standard CSV format"""
        transformed = []

        # Manager emails for random assignment
        managers = [
            "davala.rammohan@cognizant.com",
            "Siddhartha.chakraberty@cognizant.com"
        ]

        for issue in issues:
            fields = issue.get('fields', {})

            # Get dates
            created = pd.to_datetime(fields.get('created'))
            resolved = pd.to_datetime(fields.get('resolutiondate')) if fields.get('resolutiondate') else pd.NaT

            # Calculate resolution time
            if pd.notna(resolved):
                resolution_hours = (resolved - created).total_seconds() / 3600
            else:
                resolution_hours = 0

            # Map priority
            priority_obj = fields.get('priority', {})
            priority = self._map_priority(priority_obj.get('name', 'Medium'))

            # Get assignee
            assignee_obj = fields.get('assignee', {})
            assignee_name = assignee_obj.get('displayName', 'Unassigned') if assignee_obj else 'Unassigned'

            # SLA targets
            sla_targets = {'Critical': 4, 'High': 12, 'Medium': 48, 'Low': 96}
            sla_target = sla_targets.get(priority, 48)

            # Random manager assignment
            import random
            manager_email = random.choice(managers)

            transformed.append({
                'Incident_ID': issue.get('key', 'Unknown'),
                'Type': 'Incident',
                'Category': 'Application',  # Default, can be from custom field
                'Priority': priority,
                'Description': fields.get('summary', ''),
                'Affected_Users': 100,
                'Location': 'Cloud',
                'Technician_Name': assignee_name,
                'Technician_Email': 'rammohan3975@gmail.com',
                'Manager_Name': 'Manager',
                'Manager_Email': manager_email,
                'Created_Date': created.strftime('%Y-%m-%d %H:%M:%S'),
                'Response_Date': created.strftime('%Y-%m-%d %H:%M:%S'),
                'Resolved_Date': resolved.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(resolved) else '',
                'Response_Hours': 1,
                'Resolution_Hours': round(resolution_hours, 2),
                'SLA_Target_Hours': sla_target,
                'SLA_Breached': 'Yes' if resolution_hours > sla_target else 'No',
                'Steps_Required': 'Initial Assessment | Root Cause Analysis | Solution Implementation | Testing | Documentation | Closure',
                'Steps_Completed': 'Initial Assessment | Solution Implementation | Closure',
                'Missing_Steps': 'Root Cause Analysis | Testing | Documentation',
                'Reassignment_Count': 0,
                'Knowledge_Article_Created': 'No',
                'Customer_Satisfaction': 'Satisfied',
                'Business_Impact': f'{priority} priority incident affecting service',
                'Root_Cause': 'Under investigation'
            })

        return pd.DataFrame(transformed)

    def _transform_changes(self, issues):
        """Transform Jira change issues to standard format"""
        transformed = []

        managers = [
            "davala.rammohan@cognizant.com",
            "Siddhartha.chakraberty@cognizant.com"
        ]

        for issue in issues:
            fields = issue.get('fields', {})

            assignee_obj = fields.get('assignee', {})
            assignee_name = assignee_obj.get('displayName', 'Unassigned') if assignee_obj else 'Unassigned'

            import random
            manager_email = random.choice(managers)

            transformed.append({
                'Change_ID': issue.get('key', 'Unknown'),
                'Type': 'Normal',
                'Category': 'Infrastructure',
                'Risk_Level': 'Medium',
                'Description': fields.get('summary', ''),
                'Affected_Users': 50,
                'Location': 'Cloud',
                'Technician_Name': assignee_name,
                'Technician_Email': 'rammohan3975@gmail.com',
                'Manager_Name': 'Manager',
                'Manager_Email': manager_email,
                'Created_Date': fields.get('created', ''),
                'Planned_Implementation_Date': fields.get('created', ''),
                'Actual_Implementation_Date': fields.get('resolutiondate', ''),
                'Required_Approvals': 'Manager | CAB',
                'Obtained_Approvals': 'Manager',
                'Missing_Approvals': 'CAB',
                'Testing_Required': 'Yes',
                'Testing_Completed': 'No',
                'Rollback_Plan_Documented': 'No',
                'Implemented_During_Blackout': 'No',
                'Implementation_Status': 'Successful',
                'Success_Criteria_Verified': 'Yes',
                'Post_Implementation_Review_Completed': 'No',
                'Knowledge_Base_Updated': 'No',
                'Business_Justification': 'Infrastructure improvement',
                'Downtime_Minutes': 0
            })

        return pd.DataFrame(transformed)

    def _map_priority(self, jira_priority):
        """Map Jira priority to our standard format"""
        mapping = {
            'Highest': 'Critical',
            'High': 'High',
            'Medium': 'Medium',
            'Low': 'Low',
            'Lowest': 'Low'
        }
        return mapping.get(jira_priority, 'Medium')


def main():
    """
    Main execution: Fetch data from Jira and save to CSV
    """
    print("="*80)
    print("🚀 JIRA CONNECTOR - ITSM Compliance Guardian")
    print("   FREE Personal Testing Version")
    print("="*80)

    # Initialize connector
    connector = JiraConnector()

    # Test connection first
    if not connector.test_connection():
        print("\n❌ Cannot connect to Jira. Please check your credentials.")
        print("\n📝 Setup Instructions:")
        print("   1. Create free account: https://www.atlassian.com/software/jira/free")
        print("   2. Get API token: https://id.atlassian.com/manage-profile/security/api-tokens")
        print("   3. Update .env file with your credentials")
        return

    # Fetch incidents
    incidents_df = connector.fetch_incidents(days_back=30)

    if not incidents_df.empty:
        incidents_df.to_csv('incidents_data.csv', index=False)
        print(f"\n💾 Saved {len(incidents_df)} incidents to incidents_data.csv")

    # Fetch changes (or use generated data if no changes exist)
    changes_df = connector.fetch_changes(days_back=30)

    if changes_df.empty:
        print("\n💡 No changes in Jira - generating sample change data...")
        import sys
        sys.path.append('.')
        try:
            from generate_changes_v2 import generate_change_data
            changes_df = generate_change_data(15)
            changes_df.to_csv('changes_data.csv', index=False)
            print(f"💾 Generated and saved {len(changes_df)} sample changes")
        except:
            print("   Run: python generate_changes_v2.py")
    else:
        changes_df.to_csv('changes_data.csv', index=False)
        print(f"💾 Saved {len(changes_df)} changes to changes_data.csv")

    print("\n" + "="*80)
    print("✅ Jira data fetch complete!")
    print("\n📊 Next step: Run analysis")
    print("   python run_itsm_final_clear.py")
    print("="*80)


if __name__ == "__main__":
    main()
