"""
Enhanced Change Request Data Generator - Version 2.0
Generates 30 realistic change request records with manager assignments
"""
import pandas as pd
import random
from datetime import datetime, timedelta

def generate_change_data(count=30):
    """Generate realistic change request data with manager assignments"""
    changes = []
    current_time = datetime.now()

    categories = ["Infrastructure", "Application", "Database", "Network", "Security"]
    risk_levels = ["Critical", "High", "Medium", "Low"]
    change_types = ["Normal", "Standard", "Emergency"]
    locations = ["Mumbai", "Bangalore", "Hyderabad", "Delhi", "Pune", "Chennai", "Kolkata", "Ahmedabad"]

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

    managers = [
        {"name": "Rammohan Davala", "email": "davala.rammohan@cognizant.com"},
        {"name": "Siddhartha Chakraborty", "email": "Siddhartha.chakraberty@cognizant.com"}
    ]

    for i in range(count):
        category = random.choice(categories)
        risk_level = random.choice(risk_levels)
        change_type = random.choice(change_types)
        technician = random.choice(technicians)
        manager = random.choice(managers)

        # Generate timestamps
        age_days = random.randint(1, 45)
        created = current_time - timedelta(days=age_days, hours=random.randint(0, 23))

        # Implementation date
        impl_days_ahead = random.randint(1, 14)
        implemented = created + timedelta(days=impl_days_ahead, hours=random.randint(2, 8))

        # Affected users
        if risk_level == "Critical":
            affected_users = random.randint(1000, 5000)
        elif risk_level == "High":
            affected_users = random.randint(500, 1000)
        elif risk_level == "Medium":
            affected_users = random.randint(100, 500)
        else:
            affected_users = random.randint(10, 100)

        # Approvals
        if change_type == "Standard":
            required_approvals = ["Pre-Approved"]
            obtained_approvals = ["Pre-Approved"]
        elif change_type == "Emergency":
            required_approvals = ["IT Director", "ECAB"]
            if random.random() < 0.2:
                obtained_approvals = random.sample(required_approvals, len(required_approvals) - 1)
            else:
                obtained_approvals = required_approvals
        else:  # Normal
            required_approvals = ["Manager", "CAB"]
            if random.random() < 0.3:
                obtained_approvals = ["Manager"]
            else:
                obtained_approvals = required_approvals

        # Testing evidence
        testing_required = risk_level in ["Critical", "High"]
        if testing_required:
            testing_completed = random.random() > 0.25
        else:
            testing_completed = random.random() > 0.5

        # Rollback plan
        rollback_documented = random.random() > 0.30

        # Blackout window check
        impl_day = implemented.strftime("%A")
        impl_hour = implemented.hour
        during_blackout = (
            (impl_day == "Friday" and impl_hour >= 18) or
            (impl_day in ["Saturday", "Sunday"] and impl_hour < 6) or
            (implemented.day > 24 and random.random() < 0.3)
        )

        # Implementation status
        if random.random() < 0.10:
            impl_status = "Failed"
            success_verified = False
        elif random.random() < 0.05:
            impl_status = "Partial Success"
            success_verified = True
        else:
            impl_status = "Successful"
            success_verified = True

        # Post-implementation review
        pir_completed = random.random() > 0.20

        # KB article updates
        kb_updated = random.random() > 0.35

        # Missing approvals list
        missing_approvals = [a for a in required_approvals if a not in obtained_approvals]

        change = {
            "Change_ID": f"CHG{200000 + i:06d}",
            "Type": change_type,
            "Category": category,
            "Risk_Level": risk_level,
            "Description": f"{category} {change_type.lower()} change - {random.choice(['System upgrade', 'Configuration update', 'Patch deployment', 'Infrastructure migration', 'Performance optimization'])}",
            "Affected_Users": affected_users,
            "Location": random.choice(locations),
            "Technician_Name": technician["name"],
            "Technician_Email": technician["email"],
            "Manager_Name": manager["name"],
            "Manager_Email": manager["email"],
            "Created_Date": created.strftime("%Y-%m-%d %H:%M:%S"),
            "Planned_Implementation_Date": implemented.strftime("%Y-%m-%d %H:%M:%S"),
            "Actual_Implementation_Date": implemented.strftime("%Y-%m-%d %H:%M:%S"),
            "Required_Approvals": " | ".join(required_approvals),
            "Obtained_Approvals": " | ".join(obtained_approvals),
            "Missing_Approvals": " | ".join(missing_approvals) if missing_approvals else "None",
            "Testing_Required": "Yes" if testing_required else "No",
            "Testing_Completed": "Yes" if testing_completed else "No",
            "Rollback_Plan_Documented": "Yes" if rollback_documented else "No",
            "Implemented_During_Blackout": "Yes" if during_blackout else "No",
            "Implementation_Status": impl_status,
            "Success_Criteria_Verified": "Yes" if success_verified else "No",
            "Post_Implementation_Review_Completed": "Yes" if pir_completed else "No",
            "Knowledge_Base_Updated": "Yes" if kb_updated else "No",
            "Business_Justification": f"Required for {random.choice(['performance improvement', 'security compliance', 'bug fix', 'capacity expansion', 'regulatory requirement'])}",
            "Downtime_Minutes": random.randint(0, 120) if impl_status == "Successful" else random.randint(60, 360)
        }

        changes.append(change)

    return pd.DataFrame(changes)

if __name__ == "__main__":
    print("🔄 Generating Enhanced Change Request Data (30 records)...")
    df = generate_change_data(30)
    filename = "changes_data.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Generated {len(df)} change requests")
    print(f"📁 Saved to: {filename}")
    print(f"\nPreview:")
    print(df[["Change_ID", "Type", "Risk_Level", "Manager_Email", "Implementation_Status"]].head(10))
    print(f"\n📊 Statistics:")
    print(f"   - By Type: {dict(df['Type'].value_counts())}")
    print(f"   - By Risk: {dict(df['Risk_Level'].value_counts())}")
