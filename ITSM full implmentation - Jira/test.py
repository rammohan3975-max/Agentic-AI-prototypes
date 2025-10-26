import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()
server = os.getenv("JIRA_SERVER")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_API_TOKEN")
project = os.getenv("JIRA_PROJECT_KEY", "ITSM")

# Try absolute minimal POST body
url = f"{server}/rest/api/3/search/jql"

# Minimal body - just JQL string
body = {
    "jql": f"project={project}"
}

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

print("Testing minimal JQL POST...")
r = requests.post(url, auth=HTTPBasicAuth(email, token), headers=headers, json=body)
print("Status:", r.status_code)
print("Response:", r.text[:500])
