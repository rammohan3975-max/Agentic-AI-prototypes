# Real-Time ITSM Integration Guide
## Live Data Connectivity Setup

---

## 📋 Table of Contents
1. Real-Time Integration Architecture
2. ServiceNow Integration Setup
3. Jira Service Management Integration
4. BMC Remedy Integration
5. Generic REST API Integration
6. Database Direct Connection
7. Agent Name Suggestions
8. Complete ITSM Process Coverage
9. Implementation Roadmap

---

## 1. Real-Time Integration Architecture

### Current Setup (Batch Mode)
```
CSV Files → Python Agent → Analysis → Email Reports
```

### Target Setup (Real-Time Mode)
```
ITSM Tool (ServiceNow/Jira) 
    ↓ (REST API)
Python Agent (Scheduled/Triggered)
    ↓
Real-Time Analysis
    ↓
Alerts + Dashboard + Email
```

---

## 2. ServiceNow Integration Setup

### Option A: ServiceNow REST API (Recommended)

#### Step 1: Get ServiceNow Credentials
```python
# ServiceNow Configuration
SERVICENOW_INSTANCE = "your-instance.service-now.com"
SERVICENOW_USERNAME = "api_user"
SERVICENOW_PASSWORD = "api_password"
# OR use OAuth token
SERVICENOW_TOKEN = "Bearer xyz..."
```

#### Step 2: Install ServiceNow Python Client
```bash
pip install pysnow
```

#### Step 3: Create ServiceNow Connector Module

**File: `servicenow_connector.py`**
```python
"""
ServiceNow Real-Time Data Connector
Fetches live incidents and changes from ServiceNow
"""
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta

class ServiceNowConnector:
    def __init__(self, instance, username, password):
        self.instance = instance
        self.base_url = f"https://{instance}/api/now/table"
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def fetch_incidents(self, days_back=7):
        """
        Fetch incidents from last N days
        """
        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # ServiceNow query parameters
        params = {
            'sysparm_query': f'opened_at>={start_date}',
            'sysparm_limit': 1000,
            'sysparm_fields': 'number,priority,category,state,opened_at,closed_at,assigned_to,short_description,sys_updated_by'
        }

        url = f"{self.base_url}/incident"
        response = requests.get(url, auth=self.auth, headers=self.headers, params=params)

        if response.status_code == 200:
            incidents = response.json()['result']
            return self._transform_incidents(incidents)
        else:
            print(f"Error fetching incidents: {response.status_code}")
            return pd.DataFrame()

    def fetch_changes(self, days_back=30):
        """
        Fetch change requests from last N days
        """
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        params = {
            'sysparm_query': f'sys_created_on>={start_date}',
            'sysparm_limit': 500,
            'sysparm_fields': 'number,type,risk,state,start_date,end_date,assigned_to,short_description,approval'
        }

        url = f"{self.base_url}/change_request"
        response = requests.get(url, auth=self.auth, headers=self.headers, params=params)

        if response.status_code == 200:
            changes = response.json()['result']
            return self._transform_changes(changes)
        else:
            print(f"Error fetching changes: {response.status_code}")
            return pd.DataFrame()

    def _transform_incidents(self, incidents):
        """Transform ServiceNow data to our CSV format"""
        transformed = []
        for inc in incidents:
            transformed.append({
                'Incident_ID': inc.get('number'),
                'Priority': self._map_priority(inc.get('priority')),
                'Category': inc.get('category', 'Unknown'),
                'Created_Date': inc.get('opened_at'),
                'Resolved_Date': inc.get('closed_at'),
                'Technician_Name': inc.get('assigned_to', {}).get('display_value', 'Unassigned'),
                'Description': inc.get('short_description'),
                # Map other fields as needed
            })
        return pd.DataFrame(transformed)

    def _transform_changes(self, changes):
        """Transform ServiceNow change data"""
        transformed = []
        for chg in changes:
            transformed.append({
                'Change_ID': chg.get('number'),
                'Type': chg.get('type'),
                'Risk_Level': chg.get('risk'),
                'Created_Date': chg.get('sys_created_on'),
                'Planned_Implementation_Date': chg.get('start_date'),
                # Map other fields
            })
        return pd.DataFrame(transformed)

    def _map_priority(self, snow_priority):
        """Map ServiceNow priority to our format"""
        mapping = {
            '1': 'Critical',
            '2': 'High',
            '3': 'Medium',
            '4': 'Low',
            '5': 'Low'
        }
        return mapping.get(str(snow_priority), 'Medium')

# Usage Example
if __name__ == "__main__":
    connector = ServiceNowConnector(
        instance="dev12345.service-now.com",
        username="api_user",
        password="your_password"
    )

    # Fetch live data
    incidents_df = connector.fetch_incidents(days_back=7)
    changes_df = connector.fetch_changes(days_back=30)

    # Save to CSV for analysis
    incidents_df.to_csv('incidents_data.csv', index=False)
    changes_df.to_csv('changes_data.csv', index=False)

    print(f"Fetched {len(incidents_df)} incidents and {len(changes_df)} changes")
```

#### Step 4: Schedule Regular Fetching

**Option A: Windows Task Scheduler**
```batch
# Create batch file: fetch_servicenow_data.bat
@echo off
cd C:\path	o\project
python servicenow_connector.py
python run_itsm_final_clear.py
```
Schedule to run every 1 hour

**Option B: Linux Cron Job**
```bash
# Add to crontab
0 * * * * cd /path/to/project && python servicenow_connector.py && python run_itsm_final_clear.py
```

**Option C: Python Scheduler (Always Running)**
```python
import schedule
import time

def run_analysis():
    # Fetch data
    connector = ServiceNowConnector(...)
    incidents_df = connector.fetch_incidents()
    changes_df = connector.fetch_changes()

    # Save
    incidents_df.to_csv('incidents_data.csv', index=False)
    changes_df.to_csv('changes_data.csv', index=False)

    # Run analysis
    os.system('python run_itsm_final_clear.py')

# Schedule every hour
schedule.every(1).hours.do(run_analysis)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 3. Jira Service Management Integration

### Setup Jira REST API Connection

**File: `jira_connector.py`**
```python
"""
Jira Service Management Connector
"""
from jira import JIRA
import pandas as pd
from datetime import datetime, timedelta

class JiraConnector:
    def __init__(self, server, email, api_token):
        self.jira = JIRA(
            server=server,
            basic_auth=(email, api_token)
        )

    def fetch_incidents(self, project_key, days_back=7):
        """Fetch issues/incidents from Jira"""
        jql = f'project = {project_key} AND created >= -{days_back}d AND type = "Incident"'

        issues = self.jira.search_issues(jql, maxResults=1000)

        incidents = []
        for issue in issues:
            incidents.append({
                'Incident_ID': issue.key,
                'Priority': issue.fields.priority.name,
                'Category': issue.fields.customfield_10050,  # Adjust field ID
                'Created_Date': issue.fields.created,
                'Resolved_Date': issue.fields.resolutiondate,
                'Technician_Name': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'Description': issue.fields.summary
            })

        return pd.DataFrame(incidents)

    def fetch_changes(self, project_key, days_back=30):
        """Fetch change requests from Jira"""
        jql = f'project = {project_key} AND created >= -{days_back}d AND type = "Change"'

        changes = self.jira.search_issues(jql, maxResults=500)

        change_list = []
        for change in changes:
            change_list.append({
                'Change_ID': change.key,
                'Type': change.fields.customfield_10100,  # Adjust
                'Risk_Level': change.fields.customfield_10101,
                'Created_Date': change.fields.created,
                # Map other fields
            })

        return pd.DataFrame(change_list)

# Installation
# pip install jira

# Usage
connector = JiraConnector(
    server="https://your-domain.atlassian.net",
    email="your-email@company.com",
    api_token="your_jira_api_token"
)

incidents_df = connector.fetch_incidents('ITSM', days_back=7)
changes_df = connector.fetch_changes('ITSM', days_back=30)
```

---

## 4. BMC Remedy Integration

### Setup BMC Remedy REST API

**File: `remedy_connector.py`**
```python
"""
BMC Remedy Connector via REST API
"""
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

class RemedyConnector:
    def __init__(self, server, username, password):
        self.server = server
        self.base_url = f"https://{server}/api/arsys/v1/entry"
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            'Content-Type': 'application/json'
        }

    def fetch_incidents(self):
        """Fetch incidents from HPD:Help Desk form"""
        url = f"{self.base_url}/HPD:Help Desk"

        params = {
            'q': "'Status'<"Closed"",  # Query for open incidents
            'fields': 'values(Incident Number,Priority,Status,Submit Date,Last Modified Date,Assignee)'
        }

        response = requests.get(url, auth=self.auth, headers=self.headers, params=params)

        if response.status_code == 200:
            data = response.json()['entries']
            return self._transform_remedy_data(data)
        else:
            print(f"Error: {response.status_code}")
            return pd.DataFrame()

    def _transform_remedy_data(self, data):
        """Transform Remedy data to CSV format"""
        transformed = []
        for entry in data:
            values = entry['values']
            transformed.append({
                'Incident_ID': values.get('Incident Number'),
                'Priority': values.get('Priority'),
                'Created_Date': values.get('Submit Date'),
                # Map other fields
            })
        return pd.DataFrame(transformed)

# Usage
connector = RemedyConnector(
    server="remedy.company.com",
    username="api_user",
    password="password"
)

incidents_df = connector.fetch_incidents()
```

---

## 5. Generic REST API Integration Template

### Universal ITSM Tool Connector

**File: `generic_itsm_connector.py`**
```python
"""
Generic ITSM Tool Connector
Works with any tool that has REST API
"""
import requests
import pandas as pd

class GenericITSMConnector:
    def __init__(self, base_url, auth_token=None, username=None, password=None):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}

        # Setup authentication
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
            self.auth = None
        elif username and password:
            self.auth = (username, password)
        else:
            self.auth = None

    def fetch_data(self, endpoint, params=None):
        """Generic fetch method"""
        url = f"{self.base_url}/{endpoint}"

        response = requests.get(
            url, 
            headers=self.headers, 
            auth=self.auth,
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

    def fetch_incidents(self, endpoint='incidents', date_field='created_date'):
        """Fetch incidents from any ITSM tool"""
        data = self.fetch_data(endpoint)
        return pd.DataFrame(data)

    def fetch_changes(self, endpoint='changes'):
        """Fetch changes from any ITSM tool"""
        data = self.fetch_data(endpoint)
        return pd.DataFrame(data)

# Usage for any ITSM tool
connector = GenericITSMConnector(
    base_url="https://itsm-tool.company.com/api/v1",
    auth_token="your_api_token"
)

incidents = connector.fetch_incidents()
```

---

## 6. Database Direct Connection

### Option: Direct SQL Database Query

**File: `database_connector.py`**
```python
"""
Direct Database Connection to ITSM Tool Database
(If API not available or for faster access)
"""
import pyodbc
import pandas as pd
from sqlalchemy import create_engine

class ITSMDatabaseConnector:
    def __init__(self, server, database, username, password, driver='SQL Server'):
        self.connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        self.engine = create_engine(
            f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        )

    def fetch_incidents(self):
        """Query incidents directly from database"""
        query = """
        SELECT 
            incident_id,
            priority,
            category,
            created_date,
            resolved_date,
            assigned_to,
            manager_email,
            status
        FROM incident_table
        WHERE created_date >= DATEADD(day, -7, GETDATE())
        """

        df = pd.read_sql(query, self.engine)
        return df

    def fetch_changes(self):
        """Query changes directly from database"""
        query = """
        SELECT 
            change_id,
            type,
            risk_level,
            created_date,
            implementation_date,
            assigned_to,
            approval_status
        FROM change_request_table
        WHERE created_date >= DATEADD(day, -30, GETDATE())
        """

        df = pd.read_sql(query, self.engine)
        return df

# Installation
# pip install pyodbc sqlalchemy

# Usage
connector = ITSMDatabaseConnector(
    server="sql-server.company.com",
    database="ITSM_Database",
    username="readonly_user",
    password="password"
)

incidents = connector.fetch_incidents()
changes = connector.fetch_changes()
```

---

## 7. Agent Name Suggestions

### Professional Agent Names

#### Option 1: Process-Focused Names
1. **ITSM Compliance Guardian** - Broad compliance monitoring
2. **Process Deviation Detective** - Focus on deviations
3. **SLA Sentinel** - SLA monitoring focused
4. **Change Compliance Checker** - Change-specific
5. **Incident Quality Inspector** - Incident-specific

#### Option 2: AI/Tech-Focused Names
1. **ITSM Autopilot** - Autonomous monitoring
2. **ITOps Intelligence Agent** - Intelligent operations
3. **Service Assurance AI** - AI-powered assurance
4. **Compliance Copilot** - Assists with compliance
5. **Process Optimizer Bot** - Optimization focus

#### Option 3: Descriptive Names
1. **Multi-Agent ITSM Analyzer**
2. **Real-Time Process Monitor**
3. **ITSM Governance Agent**
4. **Service Excellence Tracker**
5. **IT Process Validator**

#### Recommended Name (Professional & Clear):
**"ITSM Compliance Guardian"**
- Professional
- Clear purpose
- Scalable to other processes
- Easy to remember

---

## 8. Complete ITSM Process Coverage

### Processes You Can Build Agents For

#### ✅ **Already Built**
1. **Incident Management**
   - SLA compliance
   - Process step validation
   - Knowledge article creation
   - Reassignment tracking
   - Priority vs resolution time

2. **Change Management**
   - Approval workflow compliance
   - Testing validation
   - Rollback plan checks
   - Blackout window violations
   - Post-implementation review
   - Risk assessment alignment

#### 🚀 **Expand to These Processes**

### **3. Problem Management**
**Deviations to Track:**
- ❌ Multiple incidents not linked to problem
- ❌ Root cause analysis not documented
- ❌ No workaround documented
- ❌ Problem ticket not created for recurring incidents
- ❌ Known error database not updated
- ❌ No permanent solution implemented within SLA
- ❌ Problem priority misalignment with incident count

**Agent Features:**
- Identify incident patterns (same root cause)
- Track problem resolution SLA
- Validate RCA documentation
- Monitor workaround effectiveness

---

### **4. Service Request Management**
**Deviations to Track:**
- ❌ Service catalog item not followed
- ❌ Approval bypassed
- ❌ SLA breach for standard requests
- ❌ No customer feedback collected
- ❌ Wrong fulfillment process used
- ❌ Pricing not validated

**Agent Features:**
- Validate catalog item compliance
- Track request fulfillment time
- Monitor approval chains
- Ensure proper categorization

---

### **5. Configuration Management (CMDB)**
**Deviations to Track:**
- ❌ CI not updated after change
- ❌ Asset relationships not mapped
- ❌ Configuration items missing mandatory attributes
- ❌ CI ownership not assigned
- ❌ License compliance violations
- ❌ Duplicate CIs
- ❌ CI status not updated

**Agent Features:**
- Validate CI updates post-change
- Check relationship accuracy
- Monitor CMDB data quality
- Track configuration drift

---

### **6. Knowledge Management**
**Deviations to Track:**
- ❌ KB article not created for Critical/High incidents
- ❌ KB articles not reviewed/updated regularly
- ❌ No knowledge linked to resolved incidents
- ❌ Outdated articles not archived
- ❌ Missing search keywords
- ❌ No owner assigned to article

**Agent Features:**
- Track KB article creation rate
- Monitor article usage and effectiveness
- Identify knowledge gaps
- Suggest article creation from incident patterns

---

### **7. Asset & License Management**
**Deviations to Track:**
- ❌ Software installed without license
- ❌ License expiration not tracked
- ❌ Asset not assigned to owner
- ❌ Hardware refresh overdue
- ❌ Asset disposal not documented
- ❌ Over-licensing or under-licensing
- ❌ Contract renewal missed

**Agent Features:**
- Monitor license compliance
- Track asset lifecycle
- Predict license needs
- Alert on expiration

---

### **8. Service Level Management (SLM)**
**Deviations to Track:**
- ❌ SLA targets not met consistently
- ❌ No SLA escalation triggered
- ❌ Service review meetings not conducted
- ❌ SLA reporting delayed
- ❌ Wrong SLA assigned to ticket
- ❌ No operational level agreements (OLA) defined

**Agent Features:**
- Real-time SLA breach prediction
- Trend analysis for SLA performance
- Identify problematic service categories
- Recommend SLA target adjustments

---

### **9. Release & Deployment Management**
**Deviations to Track:**
- ❌ Release not linked to changes
- ❌ Rollback plan missing
- ❌ No release testing documented
- ❌ Deployment window violated
- ❌ Post-release review not done
- ❌ Version control not maintained
- ❌ Communication plan not executed

**Agent Features:**
- Validate release readiness
- Track deployment success rate
- Monitor rollback execution
- Ensure proper documentation

---

### **10. Availability & Capacity Management**
**Deviations to Track:**
- ❌ Service availability below target
- ❌ Capacity threshold breach not alerted
- ❌ No capacity planning for growth
- ❌ Performance degradation not addressed
- ❌ Monitoring gaps identified
- ❌ No proactive capacity measures

**Agent Features:**
- Monitor service uptime
- Predict capacity needs
- Identify performance trends
- Recommend infrastructure scaling

---

### **11. Vendor & Contract Management**
**Deviations to Track:**
- ❌ Vendor SLA not monitored
- ❌ Contract renewal missed
- ❌ Invoices not reconciled
- ❌ Vendor performance below expectations
- ❌ No vendor risk assessment
- ❌ Purchase order not raised

**Agent Features:**
- Track vendor SLA compliance
- Monitor contract expiry dates
- Validate invoice accuracy
- Assess vendor performance

---

### **12. Security Incident & Event Management (SIEM)**
**Deviations to Track:**
- ❌ Security incident not escalated
- ❌ No forensic analysis performed
- ❌ Security patch not applied within SLA
- ❌ Compliance requirements not met
- ❌ User access not revoked
- ❌ No post-incident security review

**Agent Features:**
- Track security incident response time
- Monitor patch compliance
- Validate access control changes
- Ensure audit trail

---

### **13. Workforce & Resource Management**
**Deviations to Track:**
- ❌ Technician overloaded (too many assignments)
- ❌ Skills mismatch for assignment
- ❌ No backup resource identified
- ❌ Training requirements not met
- ❌ Uneven workload distribution
- ❌ On-call rotation not followed

**Agent Features:**
- Balance workload across team
- Match skills to ticket requirements
- Predict resource needs
- Track training completion

---

### **14. Continual Service Improvement (CSI)**
**Deviations to Track:**
- ❌ No improvement initiatives logged
- ❌ Process metrics not tracked
- ❌ Customer feedback not acted upon
- ❌ Lessons learned not documented
- ❌ No improvement plan created
- ❌ ROI not measured for improvements

**Agent Features:**
- Identify improvement opportunities
- Track metric trends
- Monitor initiative progress
- Calculate improvement ROI

---

### **15. Business Service Management**
**Deviations to Track:**
- ❌ Business impact not assessed
- ❌ Service dependency not mapped
- ❌ Business owner not notified
- ❌ Service value not measured
- ❌ Customer journey not tracked

**Agent Features:**
- Map business service dependencies
- Track business impact of incidents
- Monitor service value delivery
- Ensure business alignment

---

## 9. Implementation Roadmap

### Phase 1: Current State (Week 1-2)
✅ Incident Management deviation detection (Done)
✅ Change Management deviation detection (Done)
✅ Email notifications (Done)
✅ CSV export for Power BI (Done)

### Phase 2: Real-Time Integration (Week 3-4)
🔧 Choose ITSM tool connector (ServiceNow/Jira/Remedy)
🔧 Implement API integration
🔧 Setup automated scheduling (hourly/daily)
🔧 Test with live data

### Phase 3: Process Expansion (Week 5-8)
📋 Problem Management agent
📋 Service Request agent
📋 Knowledge Management agent
📋 CMDB compliance agent

### Phase 4: Advanced Features (Week 9-12)
🚀 Machine learning predictions
🚀 Dashboard creation (Power BI/Tableau)
🚀 WhatsApp/Teams integration
🚀 Automated remediation workflows

### Phase 5: Enterprise Deployment (Week 13-16)
🏢 Production deployment
🏢 User training
🏢 Documentation
🏢 Support setup

---

## 10. Recommended Full Setup

### **Agent Name: "ITSM Compliance Guardian"**

### **Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│         ITSM Compliance Guardian - Full Suite           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Agent 1: Data Ingestion Engine                         │
│  ├─ ServiceNow Connector                                │
│  ├─ Jira Connector                                      │
│  ├─ Database Connector                                  │
│  └─ CSV Import                                          │
│                                                          │
│  Agent 2: Rules & Policy Engine                         │
│  ├─ GitHub Rules Fetcher                                │
│  ├─ Policy Validator                                    │
│  └─ Compliance Checker                                  │
│                                                          │
│  Agent 3: Intelligence Engine                           │
│  ├─ Deviation Analyzer                                  │
│  ├─ SLA Predictor                                       │
│  ├─ Pattern Detector                                    │
│  └─ Solution Recommender                                │
│                                                          │
│  Agent 4: Notification Engine                           │
│  ├─ Email Sender                                        │
│  ├─ Teams/Slack Integrator                              │
│  ├─ WhatsApp Sender                                     │
│  └─ Dashboard Updater                                   │
│                                                          │
│  Agent 5: Reporting Engine                              │
│  ├─ CSV Exporter                                        │
│  ├─ Power BI Connector                                  │
│  ├─ Metric Calculator                                   │
│  └─ Trend Analyzer                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### **Process Coverage Priority:**
1. ✅ Incident Management (Done)
2. ✅ Change Management (Done)
3. 🔜 Problem Management (Next)
4. 🔜 Service Request Management
5. 🔜 Knowledge Management
6. 🔜 SLA Management
7. 🔜 Asset Management
8. 🔜 CMDB Compliance

---

## 11. Quick Start Commands

### Install All Dependencies
```bash
pip install requests pandas python-dotenv schedule pysnow jira pyodbc sqlalchemy openpyxl
```

### Create Full Project Structure
```
ITSM-Compliance-Guardian/
├── connectors/
│   ├── servicenow_connector.py
│   ├── jira_connector.py
│   ├── remedy_connector.py
│   └── database_connector.py
├── agents/
│   ├── incident_agent.py
│   ├── change_agent.py
│   ├── problem_agent.py
│   └── service_request_agent.py
├── rules/
│   ├── incident_rules.txt (from GitHub)
│   ├── change_rules.txt (from GitHub)
│   └── problem_rules.txt
├── outputs/
│   ├── reports/
│   ├── emails/
│   └── dashboards/
├── config/
│   ├── .env
│   └── settings.py
├── generate_incidents_v2.py
├── generate_changes_v2.py
├── run_itsm_final_clear.py
├── scheduler.py
└── README.md
```

---

## Contact & Support

For implementation assistance:
- Email: rammohan3975@gmail.com
- GitHub: https://github.com/rammohan3975-max/Agentic-AI-prototypes

---

**Document Version:** 1.0
**Created:** October 25, 2025
**Purpose:** Real-Time ITSM Integration Guide
