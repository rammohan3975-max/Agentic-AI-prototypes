# Jira Personal Testing Setup - ITSM Compliance Guardian
## Free Personal Account Setup for Testing - No money needed as of now

---

## 📝 **Step-by-Step: Create Free Jira Account**

### **Step 1: Sign Up (2 minutes)**

1. **Go to**: https://www.atlassian.com/software/jira/free
2. **Click**: "Get it free"
3. **Enter**: Your email (ex:- rammohan3975@gmail.com)
4. **Choose**: "Jira Service Management" (for ITSM)
5. **Create**: Your site name (e.g., `rammohan-itsm.atlassian.net`)
6. **Verify**: Email confirmation

### **Step 2: Initial Setup (3 minutes)**

1. **Select**: "IT Service Management" template
2. **Create Project**: Name it "ITSM Testing"
3. **Project Key**: ITSM (this will be used in API)
4. **Skip** team invites (you can add later)

**Your Jira is now ready!** 🎉 and can be used by us now 

---

## 🔑 **How to get Get API Token (Required for Integration)**

### **Generate API Token**

1. **Go to**: https://id.atlassian.com/manage-profile/security/api-tokens
2. **Click**: "Create API token"
3. **Label**: "ITSM Agent"
4. **Copy**: The token (save it securely!)
5. **Important**: This token is like a password - keep it safe!

**Example Token**: `ATATT3xFfGF0qK9mXYZ...` (long string)

---

## 📊 **Create Sample Incidents in Jira**

## 🛠️ **Complete Jira Integration Setup**

### **Step 1: Install Jira Python Library**

```bash
pip install jira pandas python-dotenv requests
```

### **Step 2: Update .env File**

```env
# Email Configuration (existing)
SENDER_EMAIL=rammohan3975@gmail.com
SENDER_APP_PASSWORD=your_gmail_app_password

# Jira Configuration (NEW)
JIRA_SERVER=https://rammohan-itsm.atlassian.net
JIRA_EMAIL=rammohan3975@gmail.com
JIRA_API_TOKEN=your_api_token_here
JIRA_PROJECT_KEY=ITSM
```
---

## 🎬 **Quick Start Commands**

### **One-Time Setup**

```bash
# 1. Create Jira account (web browser)
# 2. Get API token (web browser)
# 3. Update .env file

# 4. Create sample test data in Jira

# 5. Fetch data and analyze
python jira_connector.py - test run to check connection
python run_itsm_final_clear.py
```

### **Daily Testing**

```bash
# Fetch latest data from Jira and analyze
python jira_connector.py && python run_itsm_final_clear.py
```

### **Automated Testing**

```bash
# Run analysis every hour (like production)
python scheduler_jira.py
```

---

## 🔧 **Jira Custom Fields Setup**

### **Add Custom Fields to Jira (Optional but Recommended)**

To track all deviation fields, add these custom fields to your Jira project:

**Go to**: Project Settings → Issue Types → Fields

**Add these fields**:
1. **Manager Email** (Text field)
2. **Technician Email** (Text field)
3. **SLA Target Hours** (Number field)
4. **Process Steps Completed** (Paragraph field)
5. **Knowledge Article Created** (Checkbox)

## 📌 **Jira API Basics**

### **Key Endpoints**

```python
# Get all incidents
GET /rest/api/3/search?jql=project=ITSM AND type=Incident

# Get specific incident
GET /rest/api/3/issue/ITSM-123

# Create incident
POST /rest/api/3/issue

# Update incident
PUT /rest/api/3/issue/ITSM-123
```

### **Authentication**

```python
# Basic Auth with API Token
auth = (
    "rammohan3975@gmail.com",  # Your Jira email
    "your_api_token"           # API token (not password!)
)

Contact & Support
Developer: Ram Mohan
Email: rammohan3975@gmail.com
GitHub: https://github.com/rammohan3975-max/Agentic-AI-prototypes

Document Version: 1.0
Last Updated: October 25, 2025
For: Personal Learning

---

**Document Version**: 1.0  
**Created**: October 25, 2025  
**Purpose**: Personal Testing Setup Guide  
**Cost**: $0 (100% Free)
