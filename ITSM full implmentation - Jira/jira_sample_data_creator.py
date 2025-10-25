"""
Jira Sample Data Creator
========================
Creates test incidents in your FREE Jira account

This script will create 20 sample incidents in your Jira project
Perfect for testing the ITSM Compliance Guardian!
"""
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
import random
from datetime import datetime, timedelta
import time

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

        print("🔗 Jira Sample Data Creator initialized")

    def create_sample_incidents(self, count=20):
        """Create sample incidents in Jira"""

        print(f"\n📝 Creating {count} sample incidents in Jira...")
        print("   This will take about 1-2 minutes...")

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
            "File share access denied for multiple users"
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
                    random.choice(["Finance", "HR", "IT", "Sales", "Support"])
                )

                description = f"""
                Priority: {priority}
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
                """

                # Create incident payload
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
                            "name": "Task"  # Will work with free Jira, can change to "Incident" if available
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
                    print(f" ✓ Created incident {created_count}/{count}: {issue['key']} - {summary[:50]}...")
                    time.sleep(0.5)  # Rate limiting - be nice to free Jira API
                else:
                    failed_count += 1
                    print(f" ✗ Failed to create incident {i+1}: {response.status_code}")
                    if response.status_code == 400:
                        print(f"    Error: {response.json()}")

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
            return True
        except:
            return False


def main():
    """Main execution"""
    print("="*80)
    print("🚀 JIRA SAMPLE DATA CREATOR")
    print("   Create test incidents for ITSM Compliance Guardian")
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

    print(" ✓ Connected to Jira successfully!")

    # Confirm with user
    print("\n⚠️  This will create 20 sample incidents in your Jira project.")
    response = input("   Continue? (yes/no): ")

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


if __name__ == "__main__":
    main()
