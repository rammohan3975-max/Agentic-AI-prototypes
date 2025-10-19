
"""
Incident Data Generator
Generates realistic incident CSV data for ITSM analysis
"""

import pandas as pd
import random
from datetime import datetime, timedelta

def generate_incident_data(count=20):
    """Generate realistic incident data"""

    incidents = []
    current_time = datetime.now()

    categories = ["Network", "Application", "Hardware", "Security", "Database"]
    priorities = ["Critical", "High", "Medium", "Low"]
    locations = ["Mumbai", "Bangalore", "Hyderabad", "Delhi", "Pune", "Chennai"]

    technicians = [
        {"name": "Rajesh Kumar", "email": "rammohan3975@gmail.com"},
        {"name": "Priya Sharma", "email": "rammohan3975@gmail.com"},
        {"name": "Amit Patel", "email": "rammohan3975@gmail.com"},
        {"name": "Sneha Reddy", "email": "rammohan3975@gmail.com"},
        {"name": "Vikram Singh", "email": "rammohan3975@gmail.com"},
        {"name": "Anita Desai", "email": "rammohan3975@gmail.com"},
        {"name": "Karthik Rao", "email": "rammohan3975@gmail.com"},
        {"name": "Deepa Menon", "email": "rammohan3975@gmail.com"}
    ]

    # Define process steps by category (matching rules document)
    process_steps = {
        "Network": ["Initial Assessment", "Network Diagnostics", "Root Cause Analysis", 
                   "Solution Implementation", "Testing", "Documentation", "Closure"],
        "Application": ["Initial Assessment", "Code Review", "Bug Identification",
                       "Fix Implementation", "Testing", "Deployment", "User Validation", "Closure"],
        "Hardware": ["Initial Assessment", "Hardware Diagnostics", "Component Testing",
                    "Replacement/Repair", "System Testing", "Documentation", "Closure"],
        "Security": ["Initial Assessment", "Security Scan", "Threat Analysis",
                    "Patch Implementation", "Security Testing", "Compliance Verification",
                    "Documentation", "Closure"],
        "Database": ["Initial Assessment", "Query Analysis", "Performance Check",
                    "Backup Verification", "Fix Implementation", "Data Validation",
                    "Documentation", "Closure"]
    }

    satisfaction_ratings = ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"]

    for i in range(count):
        category = random.choice(categories)
        priority = random.choice(priorities)
        technician = random.choice(technicians)

        # Generate timestamps
        age_days = random.randint(1, 30)
        created = current_time - timedelta(days=age_days, hours=random.randint(0, 23))

        # Response time (sometimes late)
        if random.random() < 0.3:  # 30% have late response
            response_delay = random.uniform(1.5, 5) if priority in ["Critical", "High"] else random.uniform(5, 12)
        else:
            response_delay = random.uniform(0.1, 0.5) if priority == "Critical" else random.uniform(0.5, 2)

        response = created + timedelta(hours=response_delay)

        # Resolution time (sometimes breaches SLA)
        sla_targets = {"Critical": 4, "High": 12, "Medium": 48, "Low": 96}
        target = sla_targets[priority]

        if random.random() < 0.35:  # 35% breach SLA
            resolution_hours = target * random.uniform(1.3, 2.5)
        else:
            resolution_hours = target * random.uniform(0.4, 0.95)

        resolved = created + timedelta(hours=resolution_hours)

        # Process steps (sometimes incomplete)
        required_steps = process_steps[category]
        if random.random() < 0.40:  # 40% have missing steps
            num_steps = random.randint(3, len(required_steps) - 2)
            completed_steps = random.sample(required_steps, num_steps)
        else:
            completed_steps = required_steps.copy()

        # Affected users
        if priority == "Critical":
            affected_users = random.randint(500, 2000)
        elif priority == "High":
            affected_users = random.randint(100, 500)
        elif priority == "Medium":
            affected_users = random.randint(20, 100)
        else:
            affected_users = random.randint(1, 20)

        # Reassignments (sometimes excessive)
        if random.random() < 0.25:  # 25% have reassignments
            reassignments = random.randint(1, 4)
        else:
            reassignments = 0

        # Knowledge article (sometimes missing when required)
        if priority in ["Critical", "High"]:
            kb_created = random.random() > 0.3  # 30% don't create KB
        else:
            kb_created = random.random() > 0.7

        # Customer satisfaction (biased toward satisfied)
        sat_weights = [0.3, 0.5, 0.15, 0.05]  # More satisfied customers
        satisfaction = random.choices(satisfaction_ratings, weights=sat_weights)[0]

        # Business impact description
        impact_templates = {
            "Critical": f"{category} system completely down - {affected_users} users cannot work",
            "High": f"Significant {category} issues affecting {affected_users} users - degraded service",
            "Medium": f"{category} problem impacting {affected_users} users - workaround available",
            "Low": f"Minor {category} issue - {affected_users} users affected minimally"
        }

        incident = {
            "Incident_ID": f"INC{100000 + i:06d}",
            "Type": "Incident",
            "Category": category,
            "Priority": priority,
            "Description": f"{category} issue - {random.choice(['Performance degradation', 'System failure', 'Access issue', 'Data corruption', 'Service unavailable'])}",
            "Affected_Users": affected_users,
            "Location": random.choice(locations),
            "Technician_Name": technician["name"],
            "Technician_Email": technician["email"],
            "Created_Date": created.strftime("%Y-%m-%d %H:%M:%S"),
            "Response_Date": response.strftime("%Y-%m-%d %H:%M:%S"),
            "Resolved_Date": resolved.strftime("%Y-%m-%d %H:%M:%S"),
            "Response_Hours": round(response_delay, 2),
            "Resolution_Hours": round(resolution_hours, 2),
            "Steps_Completed": " | ".join(completed_steps),
            "Reassignment_Count": reassignments,
            "Knowledge_Article_Created": "Yes" if kb_created else "No",
            "Customer_Satisfaction": satisfaction,
            "Business_Impact": impact_templates[priority],
            "Root_Cause": random.choice([
                "Configuration error", "Software bug", "Hardware failure",
                "Network congestion", "Security vulnerability", "Human error",
                "Third-party service failure", "Capacity limit reached"
            ])
        }

        incidents.append(incident)

    return pd.DataFrame(incidents)

if __name__ == "__main__":
    print("🔧 Generating Incident Data...")
    df = generate_incident_data(20)

    filename = "incidents_data.csv"
    df.to_csv(filename, index=False)

    print(f"✅ Generated {len(df)} incidents")
    print(f"📁 Saved to: {filename}")
    print(f"\nPreview:")
    print(df[["Incident_ID", "Category", "Priority", "Technician_Name", "Resolution_Hours"]].head())
    print(f"\n📊 Statistics:")
    print(f"  Critical: {len(df[df['Priority']=='Critical'])}")
    print(f"  High: {len(df[df['Priority']=='High'])}")
    print(f"  Medium: {len(df[df['Priority']=='Medium'])}")
    print(f"  Low: {len(df[df['Priority']=='Low'])}")
