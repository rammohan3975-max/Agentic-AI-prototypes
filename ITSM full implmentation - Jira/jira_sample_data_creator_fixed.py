"""
Jira Sample Data Creator - Fixed Version
=========================================
Automatically detects available issue types in your Jira project
"""
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
import random
from datetime import datetime, timedelta
import time
import json

load_dotenv()

class JiraSampleDataCreator:
    """Creates sample ITSM incidents in Jira for testing"""

    def __init__(self):
        self.server = os.getenv("JIRA_SERVER", "https://rammohan-itsm.atlassian.net")
        self.email = os.getenv("JIRA_EMAIL", "rammohan3975@gmail.com")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "ITSM")

        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        self.available_issue_types = []

        print("🔗 Jira Sample Data Creator initialized")

    def get_available_issue_types(self):
        """Get available issue types for the project"""
        try:
            url = f"{self.server}/rest/api/3/issue/createmeta"
            params = {
                'projectKeys': self.project_key,
                'expand': 'projects.issuetypes'
            }

            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            if 'projects' in data and len(data['projects']) > 0:
                issue_types = data['projects'][0].get('issuetypes', [])
                self.available_issue_types = [it['name'] for it in issue_types]

                print(f"\n📋 Available issue types in your project:")
                for i, it in enumerate(issue_types, 1):
                    print(f"   {i}. {it['name']} (ID: {it['id']})")

                return issue_types
            else:
                print("\n⚠️  No issue types found. Using default.")
                return []

        except Exception as e:
            print(f"\n⚠️  Error getting issue types: {e}")
            print("   Will try common issue type names...")
            return []

    def select_best_issue_type(self, issue_types):
        """Select the best available issue type for incidents"""

        # Priority order of issue types to use
        preferred_types = [
            'Incident',
            'Service Request', 
            'Bug',
            'Task',
            'Story',
            'Epic'
        ]

        available_names = [it['name'] for it in issue_types]

        for preferred in preferred_types:
            if preferred in available_names:
                for it in issue_types:
                    if it['name'] == preferred:
                        print(f"\n✅ Using issue type: {preferred}")
                        return it

        # If none of preferred types found, use first available
        if issue_types:
            print(f"\n✅ Using issue type: {issue_types[0]['name']}")
            return issue_types[0]

        return None

    def create_sample_incidents(self, count=20):
        """Create sample incidents in Jira"""

        print(f"\n📝 Preparing to create {count} sample incidents in Jira...")

        # Get available issue types first
        issue_types = self.get_available_issue_types()

        if not issue_types:
            print("\n❌ Cannot determine available issue types.")
            print("\n💡 Please create at least one issue manually in Jira first:")
            print("   1. Go to your Jira project")
            print("   2. Click 'Create'")
            print("   3. Create any type of issue")
            print("   4. Then run this script again")
            return 0

        # Select best issue type
        selected_issue_type = self.select_best_issue_type(issue_types)

        if not selected_issue_type:
            print("\n❌ No suitable issue type found.")
            return 0

        print(f"\n🚀 Creating {count} incidents...")
        print("   This will take about 1-2 minutes...\n")

        priorities = ["Highest", "High", "Medium", "Low"]
        categories = ["Network", "Application", "Hardware", "Security", "Database"]

        incident_templates = [
            "Email service not working for {} users",
            "Database performance degradation in {} system",
            "Network connectivity issues in {} location",
            "Application crash affecting {} department",
            "Security alert: Suspicious activity detected",
            "Server {} is down - immediate attention needed",
            "Printer not working in {} office",
            "VPN connection failing for remote users",
            "Website loading very slowly",
            "File share access denied for multiple users",
            "Backup job failed - data at risk",
            "Password reset not working",
            "Slow login times reported by users",
            "Email attachments not opening",
            "Shared drive access denied"
        ]

        created_count = 0
        failed_count = 0

        for i in range(count):
            try:
                # Random incident data
                priority = random.choice(priorities)
                category = random.choice(categories)
                template = random.choice(incident_templates)

                summary = template.format(
                    random.choice(["Finance", "HR", "IT", "Sales", "Support", "Operations"])
                )

                description = f"""Priority: {priority}
Category: {category}

Issue Description:
{summary}

Steps to reproduce:
1. User attempted to access the system
2. Error occurred or service unavailable
3. Multiple users affected

Expected behavior:
System should work normally without errors

Actual behavior:
Service is degraded or unavailable

Impact:
Business operations affected

Reported by: User Department
Time reported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

                # Create incident payload using detected issue type
                payload = {
                    "fields": {
                        "project": {
                            "key": self.project_key
                        },
                        "summary": summary,
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": description
                                        }
                                    ]
                                }
                            ]
                        },
                        "issuetype": {
                            "id": selected_issue_type['id']  # Use ID instead of name
                        },
                        "priority": {
                            "name": priority
                        }
                    }
                }

                url = f"{self.server}/rest/api/3/issue"
                response = requests.post(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 201:
                    issue = response.json()
                    created_count += 1
                    print(f" ✓ Created {created_count}/{count}: {issue['key']} - {summary[:50]}...")
                    time.sleep(0.5)  # Rate limiting
                else:
                    failed_count += 1
                    print(f" ✗ Failed {i+1}: {response.status_code}")
                    if response.status_code == 400:
                        error_detail = response.json()
                        print(f"    Error: {error_detail}")

            except Exception as e:
                failed_count += 1
                print(f" ✗ Error creating incident {i+1}: {e}")

        print(f"\n✅ Completed!")
        print(f"   Created: {created_count} incidents")
        print(f"   Failed: {failed_count} incidents")

        if created_count > 0:
            print(f"\n🎉 Success! You now have {created_count} test incidents in Jira!")
            print(f"   View them at: {self.server}/projects/{self.project_key}")

        return created_count

    def test_connection(self):
        """Test Jira connection"""
        try:
            url = f"{self.server}/rest/api/3/myself"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()

            user = response.json()
            print(f"\n✓ Connected as: {user.get('displayName')}")
            return True
        except Exception as e:
            print(f"\n✗ Connection failed: {e}")
            return False


def main():
    """Main execution"""
    print("="*80)
    print("🚀 JIRA SAMPLE DATA CREATOR - FIXED VERSION")
    print("   Automatically detects your Jira issue types")
    print("="*80)

    creator = JiraSampleDataCreator()

    # Test connection
    print("\n🔍 Testing Jira connection...")
    if not creator.test_connection():
        print("\n❌ Cannot connect to Jira!")
        print("\n📝 Please check:")
        print("   1. JIRA_SERVER in .env (e.g., https://yourname.atlassian.net)")
        print("   2. JIRA_EMAIL in .env (your Jira login email)")
        print("   3. JIRA_API_TOKEN in .env (get from id.atlassian.com)")
        print("   4. JIRA_PROJECT_KEY in .env (your project key like 'ITSM')")
        return

    print("\n" + "="*80)
    print("⚠️  This will create 20 sample incidents in your Jira project.")
    print("="*80)
    response = input("\nContinue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("\nCancelled.")
        return

    # Create incidents
    count = creator.create_sample_incidents(20)

    if count > 0:
        print("\n" + "="*80)
        print("✅ Sample data creation complete!")
        print("\n📊 Next steps:")
        print("   1. python jira_connector.py      # Fetch data from Jira")
        print("   2. python run_itsm_final_clear.py  # Analyze deviations")
        print("="*80)
    else:
        print("\n💡 Troubleshooting:")
        print("   1. Check your Jira project has issue types configured")
        print("   2. Try creating 1 issue manually in Jira first")
        print("   3. Make sure JIRA_PROJECT_KEY in .env matches your project")


if __name__ == "__main__":
    main()
