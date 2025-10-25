"""
Automated Scheduler for ITSM Compliance Guardian
================================================
Runs analysis every hour with live ServiceNow data
"""
import schedule
import time
import os
import sys
from datetime import datetime

def run_realtime_analysis():
    """
    Complete workflow: Fetch from ServiceNow → Analyze → Send Emails
    """
    print("\n" + "="*80)
    print(f"🕐 Scheduled Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Step 1: Fetch data from ServiceNow
        print("\n📥 Step 1: Fetching data from ServiceNow...")
        os.system('python servicenow_connector.py')

        # Step 2: Run analysis
        print("\n🔍 Step 2: Running ITSM compliance analysis...")
        os.system('python run_itsm_final_clear.py')

        print("\n" + "="*80)
        print("✅ Scheduled run completed successfully!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error in scheduled run: {e}")
        print("="*80)


def run_on_demand():
    """Run analysis immediately on demand"""
    print("\n🚀 Running on-demand analysis...")
    run_realtime_analysis()


# Schedule configurations
def setup_schedules():
    """Setup different schedule options"""

    # Option 1: Every hour (Recommended for production)
    schedule.every(1).hours.do(run_realtime_analysis)

    # Option 2: Every 30 minutes (High frequency)
    # schedule.every(30).minutes.do(run_realtime_analysis)

    # Option 3: Every day at specific time
    # schedule.every().day.at("09:00").do(run_realtime_analysis)
    # schedule.every().day.at("14:00").do(run_realtime_analysis)

    # Option 4: Every Monday at 8 AM
    # schedule.every().monday.at("08:00").do(run_realtime_analysis)

    print("="*80)
    print("⏰ ITSM Compliance Guardian - Scheduler Started")
    print("="*80)
    print("\n📅 Schedule Configuration:")
    print("   - Frequency: Every 1 hour")
    print("   - Data Source: ServiceNow")
    print("   - Analysis: Real-time deviation detection")
    print("   - Output: Email alerts + CSV reports")
    print("\n🔄 Scheduler is now running... Press Ctrl+C to stop")
    print("="*80 + "\n")


def main():
    """Main scheduler loop"""

    # Setup schedules
    setup_schedules()

    # Run immediately on startup (optional)
    # run_realtime_analysis()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("⏹️  Scheduler stopped by user")
        print("="*80)
        sys.exit(0)


if __name__ == "__main__":
    main()
