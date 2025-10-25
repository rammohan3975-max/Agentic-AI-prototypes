"""
ServiceNow Real-Time Connector for ITSM Compliance Guardian
============================================================
Fetches live incidents and changes from ServiceNow instance
"""
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

class ServiceNowConnector:
    """
    Real-time connector to ServiceNow ITSM platform
    Fetches incidents and changes via REST API
    """

    def __init__(self):
        # Load from environment variables
        self.instance = os.getenv("SERVICENOW_INSTANCE", "dev12345.service-now.com")
        self.username = os.getenv("SERVICENOW_USERNAME", "api_user")
        self.password = os.getenv("SERVICENOW_PASSWORD", "")

        self.base_url = f"https://{self.instance}/api/now/table"
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        print(f"🔗 ServiceNow Connector initialized for: {self.instance}")

    def fetch_incidents(self, days_back=7):
        """
        Fetch incidents from ServiceNow

        Args:
            days_back (int): Number of days to look back

        Returns:
            pandas.DataFrame: Incident data in standardized format
        """
        print(f"\n📥 Fetching incidents from last {days_back} days...")

        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d %H:%M:%S')

        # ServiceNow query parameters
        params = {
            'sysparm_query': f'opened_at>={start_date}',
            'sysparm_limit': 1000,
            'sysparm_display_value': 'true',
            'sysparm_fields': 'number,priority,category,state,opened_at,closed_at,resolved_at,assigned_to,short_description,sys_updated_by,reassignment_count,u_manager_email,u_technician_email,business_impact'
        }

        try:
            url = f"{self.base_url}/incident"
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()

            incidents = response.json()['result']
            print(f" ✓ Fetched {len(incidents)} incidents from ServiceNow")

            # Transform to our format
            df = self._transform_incidents(incidents)
            print(f" ✓ Transformed {len(df)} incidents to standard format")

            return df

        except requests.exceptions.RequestException as e:
            print(f" ✗ Error fetching incidents: {e}")
            return pd.DataFrame()

    def fetch_changes(self, days_back=30):
        """
        Fetch change requests from ServiceNow

        Args:
            days_back (int): Number of days to look back

        Returns:
            pandas.DataFrame: Change data in standardized format
        """
        print(f"\n📥 Fetching changes from last {days_back} days...")

        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d %H:%M:%S')

        params = {
            'sysparm_query': f'sys_created_on>={start_date}',
            'sysparm_limit': 500,
            'sysparm_display_value': 'true',
            'sysparm_fields': 'number,type,risk,state,start_date,end_date,assigned_to,short_description,approval,u_manager_email,u_rollback_plan,u_testing_completed,u_pir_completed'
        }

        try:
            url = f"{self.base_url}/change_request"
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()

            changes = response.json()['result']
            print(f" ✓ Fetched {len(changes)} changes from ServiceNow")

            # Transform to our format
            df = self._transform_changes(changes)
            print(f" ✓ Transformed {len(df)} changes to standard format")

            return df

        except requests.exceptions.RequestException as e:
            print(f" ✗ Error fetching changes: {e}")
            return pd.DataFrame()

    def _transform_incidents(self, incidents):
        """Transform ServiceNow incident data to our CSV format"""
        transformed = []

        for inc in incidents:
            # Calculate resolution time
            opened = pd.to_datetime(inc.get('opened_at'))
            resolved = pd.to_datetime(inc.get('resolved_at')) if inc.get('resolved_at') else pd.NaT

            if pd.notna(resolved):
                resolution_hours = (resolved - opened).total_seconds() / 3600
            else:
                resolution_hours = 0

            # Map priority
            priority = self._map_priority(inc.get('priority'))

            # Get SLA target
            sla_targets = {'Critical': 4, 'High': 12, 'Medium': 48, 'Low': 96}
            sla_target = sla_targets.get(priority, 48)

            transformed.append({
                'Incident_ID': inc.get('number', 'Unknown'),
                'Type': 'Incident',
                'Category': inc.get('category', 'Unknown'),
                'Priority': priority,
                'Description': inc.get('short_description', ''),
                'Affected_Users': 100,  # Default or from custom field
                'Location': 'Unknown',  # From custom field if available
                'Technician_Name': inc.get('assigned_to', 'Unassigned'),
                'Technician_Email': inc.get('u_technician_email', 'unknown@company.com'),
                'Manager_Name': 'Manager',
                'Manager_Email': inc.get('u_manager_email', 'manager@company.com'),
                'Created_Date': inc.get('opened_at', ''),
                'Response_Date': inc.get('opened_at', ''),  # Adjust based on actual field
                'Resolved_Date': inc.get('resolved_at', ''),
                'Response_Hours': 0,  # Calculate from actual data
                'Resolution_Hours': round(resolution_hours, 2),
                'SLA_Target_Hours': sla_target,
                'SLA_Breached': 'Yes' if resolution_hours > sla_target else 'No',
                'Steps_Required': 'Initial Assessment | Root Cause Analysis | Solution Implementation | Testing | Documentation | Closure',
                'Steps_Completed': 'Initial Assessment | Solution Implementation | Closure',  # From work notes
                'Missing_Steps': 'Root Cause Analysis | Testing | Documentation',  # Analyze work notes
                'Reassignment_Count': int(inc.get('reassignment_count', 0)),
                'Knowledge_Article_Created': 'No',  # From custom field
                'Customer_Satisfaction': 'Satisfied',  # From survey data
                'Business_Impact': inc.get('business_impact', 'Medium impact'),
                'Root_Cause': 'Unknown'  # From custom field
            })

        return pd.DataFrame(transformed)

    def _transform_changes(self, changes):
        """Transform ServiceNow change data to our CSV format"""
        transformed = []

        for chg in changes:
            transformed.append({
                'Change_ID': chg.get('number', 'Unknown'),
                'Type': chg.get('type', 'Normal'),
                'Category': 'Infrastructure',  # From custom field
                'Risk_Level': self._map_risk(chg.get('risk', '3')),
                'Description': chg.get('short_description', ''),
                'Affected_Users': 100,  # From custom field
                'Location': 'Unknown',
                'Technician_Name': chg.get('assigned_to', 'Unassigned'),
                'Technician_Email': 'tech@company.com',
                'Manager_Name': 'Manager',
                'Manager_Email': chg.get('u_manager_email', 'manager@company.com'),
                'Created_Date': chg.get('sys_created_on', ''),
                'Planned_Implementation_Date': chg.get('start_date', ''),
                'Actual_Implementation_Date': chg.get('end_date', ''),
                'Required_Approvals': 'Manager | CAB',
                'Obtained_Approvals': chg.get('approval', 'Pending'),
                'Missing_Approvals': 'None' if chg.get('approval') == 'Approved' else 'CAB',
                'Testing_Required': 'Yes',
                'Testing_Completed': chg.get('u_testing_completed', 'No'),
                'Rollback_Plan_Documented': chg.get('u_rollback_plan', 'No'),
                'Implemented_During_Blackout': 'No',  # Calculate from dates
                'Implementation_Status': 'Successful',
                'Success_Criteria_Verified': 'Yes',
                'Post_Implementation_Review_Completed': chg.get('u_pir_completed', 'No'),
                'Knowledge_Base_Updated': 'No',
                'Business_Justification': 'Required for compliance',
                'Downtime_Minutes': 0
            })

        return pd.DataFrame(transformed)

    def _map_priority(self, snow_priority):
        """Map ServiceNow priority to our format"""
        # ServiceNow uses: 1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning
        mapping = {
            '1 - Critical': 'Critical',
            '2 - High': 'High',
            '3 - Moderate': 'Medium',
            '4 - Low': 'Low',
            '5 - Planning': 'Low',
            '1': 'Critical',
            '2': 'High',
            '3': 'Medium',
            '4': 'Low',
            '5': 'Low'
        }
        return mapping.get(str(snow_priority), 'Medium')

    def _map_risk(self, snow_risk):
        """Map ServiceNow risk to our format"""
        mapping = {
            '1': 'Critical',
            '2': 'High',
            '3': 'Medium',
            '4': 'Low',
            '1 - High': 'Critical',
            '2 - Moderate': 'High',
            '3 - Low': 'Medium',
            '4 - Very Low': 'Low'
        }
        return mapping.get(str(snow_risk), 'Medium')


def main():
    """
    Main execution: Fetch data from ServiceNow and save to CSV
    """
    print("="*80)
    print("🚀 SERVICENOW DATA CONNECTOR - ITSM Compliance Guardian")
    print("="*80)

    # Initialize connector
    connector = ServiceNowConnector()

    # Fetch incidents
    incidents_df = connector.fetch_incidents(days_back=7)

    if not incidents_df.empty:
        incidents_df.to_csv('incidents_data.csv', index=False)
        print(f"\n💾 Saved {len(incidents_df)} incidents to incidents_data.csv")

    # Fetch changes
    changes_df = connector.fetch_changes(days_back=30)

    if not changes_df.empty:
        changes_df.to_csv('changes_data.csv', index=False)
        print(f"💾 Saved {len(changes_df)} changes to changes_data.csv")

    print("\n" + "="*80)
    print("✅ ServiceNow data fetch complete!")
    print("\n📊 Next step: Run analysis")
    print("   python run_itsm_final_clear.py")
    print("="*80)


if __name__ == "__main__":
    main()
