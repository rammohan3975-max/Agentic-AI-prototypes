"""
Generate Non-Compliant Test Incidents for ITSM Testing
========================================================
Creates incidents with intentional violations:
- SLA breaches
- Missing process steps
- Missing KB articles
- Excessive reassignments

This creates REALISTIC test data to demonstrate the agent's capabilities!

USAGE: python generate_noncompliant_incidents.py
"""
import pandas as pd
from datetime import datetime, timedelta
import random

def generate_noncompliant_incidents(count=20):
    """Generate incidents with intentional compliance violations"""
    
    incidents = []
    current_time = datetime.now()
    
    # Manager emails
    managers = [
        {"name": "Rammohan Davala", "email": "davala.rammohan@cognizant.com"},
        {"name": "Siddhartha Chakraborty", "email": "Siddhartha.chakraberty@cognizant.com"}
    ]
    
    # Categories and their required steps (from GitHub rules)
    required_steps = {
        'Network': ['Initial Assessment', 'Network Diagnostics', 'Root Cause Analysis',
                   'Solution Implementation', 'Testing', 'Documentation', 'Closure'],
        'Application': ['Initial Assessment', 'Code Review', 'Bug Identification',
                       'Fix Implementation', 'Testing', 'Deployment', 'User Validation', 'Closure'],
        'Hardware': ['Initial Assessment', 'Hardware Diagnostics', 'Component Testing',
                    'Replacement/Repair', 'System Testing', 'Documentation', 'Closure'],
        'Security': ['Initial Assessment', 'Security Scan', 'Threat Analysis',
                    'Patch Implementation', 'Security Testing', 'Compliance Verification',
                    'Documentation', 'Closure'],
        'Database': ['Initial Assessment', 'Query Analysis', 'Performance Check',
                    'Backup Verification', 'Fix Implementation', 'Data Validation',
                    'Documentation', 'Closure']
    }
    
    # SLA targets (from GitHub rules)
    sla_targets = {'Critical': 4, 'High': 12, 'Medium': 48, 'Low': 96}
    
    print(f"Generating {count} NON-COMPLIANT incidents for testing...")
    print()
    
    for i in range(count):
        category = random.choice(list(required_steps.keys()))
        priority = random.choice(['Critical', 'High', 'Medium', 'Low'])
        
        # Create dates
        age_days = random.randint(5, 30)
        created = current_time - timedelta(days=age_days, hours=random.randint(0, 23))
        
        # INTENTIONALLY BREACH SLA (70% of the time)
        sla_target = sla_targets[priority]
        if random.random() < 0.7:  # 70% SLA breach rate
            # Make it breach by 20-200%
            resolution_hours = sla_target * random.uniform(1.2, 3.0)
        else:
            # Compliant
            resolution_hours = sla_target * random.uniform(0.5, 0.95)
        
        resolved = created + timedelta(hours=resolution_hours)
        
        # INTENTIONALLY SKIP PROCESS STEPS (80% of the time)
        all_steps = required_steps[category]
        if random.random() < 0.8:  # 80% have missing steps
            # Randomly skip 2-4 steps
            num_to_skip = random.randint(2, 4)
            completed_steps = random.sample(all_steps, len(all_steps) - num_to_skip)
        else:
            # All steps completed
            completed_steps = all_steps.copy()
        
        missing_steps = [s for s in all_steps if s not in completed_steps]
        
        # INTENTIONALLY MISS KB ARTICLE (60% for High/Critical)
        if priority in ['Critical', 'High']:
            kb_created = 'Yes' if random.random() > 0.6 else 'No'  # 60% missing
        else:
            kb_created = random.choice(['Yes', 'No'])
        
        # INTENTIONALLY EXCESSIVE REASSIGNMENTS (40% of the time)
        if random.random() < 0.4:
            reassignments = random.randint(3, 6)  # More than allowed (2)
        else:
            reassignments = random.randint(0, 2)
        
        # Random manager
        manager = random.choice(managers)
        
        # Create incident record
        incidents.append({
            'Incident_ID': f"INC{100000 + i:06d}",
            'Type': 'Incident',
            'Category': category,
            'Priority': priority,
            'Description': f"{category} issue - {random.choice(['System failure', 'Performance degradation', 'Service unavailable', 'Access denied', 'Data corruption'])}",
            'Affected_Users': random.randint(50, 500) if priority in ['Critical', 'High'] else random.randint(1, 50),
            'Location': random.choice(['Mumbai', 'Bangalore', 'Hyderabad', 'Delhi', 'Cloud']),
            'Technician_Name': random.choice(['Rajesh Kumar', 'Priya Sharma', 'Amit Patel', 'Sneha Reddy', 'Vikram Singh']),
            'Technician_Email': 'rammohan3975@gmail.com',
            'Manager_Name': manager['name'],
            'Manager_Email': manager['email'],
            'Created_Date': created.strftime('%Y-%m-%d %H:%M:%S'),
            'Response_Date': (created + timedelta(hours=random.uniform(0.5, 2))).strftime('%Y-%m-%d %H:%M:%S'),
            'Resolved_Date': resolved.strftime('%Y-%m-%d %H:%M:%S'),
            'Response_Hours': round(random.uniform(0.5, 2), 2),
            'Resolution_Hours': round(resolution_hours, 2),
            'SLA_Target_Hours': sla_target,
            'SLA_Breached': 'Yes' if resolution_hours > sla_target else 'No',
            'Steps_Required': ' | '.join(all_steps),
            'Steps_Completed': ' | '.join(completed_steps),
            'Missing_Steps': ' | '.join(missing_steps) if missing_steps else 'None',
            'Reassignment_Count': reassignments,
            'Knowledge_Article_Created': kb_created,
            'Customer_Satisfaction': random.choice(['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied']),
            'Business_Impact': f'{priority} priority - {random.choice(["Major impact", "Moderate impact", "Minor impact"])}',
            'Root_Cause': random.choice(['Configuration error', 'Software bug', 'Hardware failure', 'Network issue', 'Human error'])
        })
    
    return pd.DataFrame(incidents)


def print_statistics(df):
    """Print statistics about the generated data"""
    print("="*70)
    print("📊 GENERATED TEST DATA STATISTICS")
    print("="*70)
    print()
    
    # SLA statistics
    sla_breached = df[df['SLA_Breached'] == 'Yes']
    print(f"🚨 SLA Breaches:")
    print(f"   Total: {len(sla_breached)} out of {len(df)} ({len(sla_breached)/len(df)*100:.1f}%)")
    print(f"   By Priority:")
    for priority in ['Critical', 'High', 'Medium', 'Low']:
        count = len(sla_breached[sla_breached['Priority'] == priority])
        print(f"      {priority}: {count}")
    print()
    
    # Missing steps
    missing_steps = df[df['Missing_Steps'] != 'None']
    print(f"📋 Missing Process Steps:")
    print(f"   Total: {len(missing_steps)} incidents ({len(missing_steps)/len(df)*100:.1f}%)")
    print()
    
    # Missing KB
    missing_kb = df[(df['Priority'].isin(['Critical', 'High'])) & (df['Knowledge_Article_Created'] == 'No')]
    print(f"📚 Missing Knowledge Articles:")
    print(f"   Critical/High incidents without KB: {len(missing_kb)}")
    print()
    
    # Excessive reassignments
    excessive = df[df['Reassignment_Count'] > 2]
    print(f"🔄 Excessive Reassignments (>2):")
    print(f"   Total: {len(excessive)} incidents")
    print()
    
    # Manager distribution
    print(f"👥 Manager Distribution:")
    for manager_email in df['Manager_Email'].unique():
        count = len(df[df['Manager_Email'] == manager_email])
        print(f"   {manager_email}: {count} incidents")
    print()
    
    print("="*70)
    print("✅ This data will generate MANY deviations for testing!")
    print("="*70)


def main():
    print("="*70)
    print("🔧 NON-COMPLIANT TEST INCIDENT GENERATOR")
    print("="*70)
    print()
    print("This generates incidents with intentional violations:")
    print("  ✓ SLA breaches (70% breach rate)")
    print("  ✓ Missing process steps (80% have gaps)")
    print("  ✓ Missing KB articles (60% for High/Critical)")
    print("  ✓ Excessive reassignments (40% over limit)")
    print()
    
    # Generate data
    df = generate_noncompliant_incidents(20)
    
    # Save to CSV
    filename = 'incidents_data.csv'
    df.to_csv(filename, index=False)
    
    print(f"💾 Saved {len(df)} incidents to {filename}")
    print()
    
    # Print statistics
    print_statistics(df)
    
    print()
    print("🎯 Next Steps:")
    print("   1. This file has replaced incidents_data.csv")
    print("   2. Run: python complete-multi-agent.py")
    print("   3. You'll see LOTS of deviations now!")
    print()
    print("="*70)


if __name__ == "__main__":
    main()
