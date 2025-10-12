
# ITSM Process Deviation Detection Agent - Complete Standalone Version
# This version automatically creates sample data if not found

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Optional imports with fallbacks
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("Warning: matplotlib/seaborn not found. Visualizations will be skipped.")

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not found. ML anomaly detection will be skipped.")

def create_sample_incidents():
    """Create sample incident data if file doesn't exist"""
    print("Creating sample incident data...")

    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    # Define incident categories and their typical process steps
    incident_categories = ['Network', 'Application', 'Hardware', 'Security', 'User Support']
    priorities = ['Low', 'Medium', 'High', 'Critical']

    # Define standard processes for each category
    standard_processes = {
        'Network': ['Initial Assignment', 'Network Analysis', 'Root Cause Identification', 'Solution Implementation', 'Testing', 'Resolution'],
        'Application': ['Initial Assignment', 'Application Analysis', 'Code Review', 'Bug Fix', 'Testing', 'Deployment', 'Resolution'],
        'Hardware': ['Initial Assignment', 'Hardware Diagnosis', 'Part Ordering', 'Hardware Replacement', 'Testing', 'Resolution'],
        'Security': ['Initial Assignment', 'Security Assessment', 'Threat Analysis', 'Mitigation Implementation', 'Security Validation', 'Resolution'],
        'User Support': ['Initial Assignment', 'User Interview', 'Problem Diagnosis', 'Solution Implementation', 'User Training', 'Resolution']
    }

    # Generate sample incident data
    incidents = []
    for i in range(100):
        incident_id = f"INC{i+1:05d}"
        category = random.choice(incident_categories)
        priority = random.choice(priorities)

        # Generate dates
        created_date = datetime.now() - timedelta(days=random.randint(1, 30))

        # Standard process for this category
        standard_steps = standard_processes[category]

        # Sometimes deviate from standard process (introduce process deviations)
        actual_steps = standard_steps.copy()

        # Introduce deviations (20% chance)
        if random.random() < 0.2:
            deviation_type = random.choice(['skipped_step', 'wrong_order', 'extra_step'])

            if deviation_type == 'skipped_step' and len(actual_steps) > 3:
                skip_index = random.randint(1, len(actual_steps)-2)
                actual_steps.pop(skip_index)

            elif deviation_type == 'wrong_order' and len(actual_steps) > 2:
                swap_index = random.randint(1, len(actual_steps)-2)
                actual_steps[swap_index], actual_steps[swap_index+1] = actual_steps[swap_index+1], actual_steps[swap_index]

            elif deviation_type == 'extra_step':
                extra_steps = ['Management Approval', 'Extended Testing', 'Documentation Review', 'Compliance Check']
                extra_step = random.choice(extra_steps)
                insert_position = random.randint(1, len(actual_steps)-1)
                actual_steps.insert(insert_position, extra_step)

        # Calculate resolution time based on priority and deviations
        base_resolution_hours = {'Low': 48, 'Medium': 24, 'High': 8, 'Critical': 2}
        resolution_hours = base_resolution_hours[priority]

        # Add variation and penalty for deviations
        if len(actual_steps) != len(standard_steps):
            resolution_hours *= random.uniform(1.2, 1.8)
        else:
            resolution_hours *= random.uniform(0.8, 1.2)

        resolved_date = created_date + timedelta(hours=resolution_hours)

        incidents.append({
            'incident_id': incident_id,
            'category': category,
            'priority': priority,
            'status': 'Resolved',
            'created_date': created_date.strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_date': resolved_date.strftime('%Y-%m-%d %H:%M:%S'),
            'resolution_time_hours': round(resolution_hours, 2),
            'standard_process': ' -> '.join(standard_steps),
            'actual_process': ' -> '.join(actual_steps),
            'process_deviation': 'Yes' if len(actual_steps) != len(standard_steps) or actual_steps != standard_steps else 'No',
            'assignee': f"Technician_{random.randint(1, 20)}",
            'description': f"Sample {category.lower()} incident requiring resolution"
        })

    # Create DataFrame and save to Excel
    df = pd.DataFrame(incidents)
    df.to_excel('sample_incidents.xlsx', index=False)

    print(f"✅ Created sample_incidents.xlsx with {len(incidents)} incidents")
    print(f"   - Incidents with process deviations: {df['process_deviation'].value_counts().get('Yes', 0)}")

    return df

class ITSMProcessDeviationAgent:
    def __init__(self):
        self.data = None
        self.standard_processes = {}
        self.deviation_model = None

    def load_data(self, file_path='sample_incidents.xlsx'):
        """Load incident data from Excel file - creates sample data if not found"""
        try:
            # Check if file exists in current directory
            if not os.path.exists(file_path):
                print(f"File {file_path} not found. Creating sample data...")
                self.data = create_sample_incidents()
                print(f"✅ Sample data created and loaded! Shape: {self.data.shape}")
                return True
            else:
                self.data = pd.read_excel(file_path)
                print(f"✅ Data loaded successfully! Shape: {self.data.shape}")
                return True

        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            # Try to create sample data as fallback
            try:
                print("Attempting to create sample data as fallback...")
                self.data = create_sample_incidents()
                print(f"✅ Fallback sample data created! Shape: {self.data.shape}")
                return True
            except Exception as e2:
                print(f"❌ Could not create sample data: {str(e2)}")
                return False

    def define_standard_processes(self):
        """Define standard processes for each incident category"""
        self.standard_processes = {
            'Network': ['Initial Assignment', 'Network Analysis', 'Root Cause Identification', 
                       'Solution Implementation', 'Testing', 'Resolution'],
            'Application': ['Initial Assignment', 'Application Analysis', 'Code Review', 
                           'Bug Fix', 'Testing', 'Deployment', 'Resolution'],
            'Hardware': ['Initial Assignment', 'Hardware Diagnosis', 'Part Ordering', 
                        'Hardware Replacement', 'Testing', 'Resolution'],
            'Security': ['Initial Assignment', 'Security Assessment', 'Threat Analysis', 
                        'Mitigation Implementation', 'Security Validation', 'Resolution'],
            'User Support': ['Initial Assignment', 'User Interview', 'Problem Diagnosis', 
                            'Solution Implementation', 'User Training', 'Resolution']
        }
        print("✅ Standard processes defined for all categories")

    def analyze_process_compliance(self):
        """Analyze process compliance and detect deviations"""
        if self.data is None:
            print("❌ No data loaded. Please load data first.")
            return

        print("🔍 Analyzing process compliance...")
        deviation_analysis = []

        for _, incident in self.data.iterrows():
            category = incident['category']
            actual_steps = incident['actual_process'].split(' -> ')
            standard_steps = self.standard_processes.get(category, [])

            # Calculate various deviation metrics
            step_count_deviation = len(actual_steps) - len(standard_steps)
            missing_steps = set(standard_steps) - set(actual_steps)
            extra_steps = set(actual_steps) - set(standard_steps)

            # Sequence deviation (steps in wrong order)
            sequence_deviation = 0
            if len(actual_steps) == len(standard_steps):
                for i, step in enumerate(actual_steps):
                    if i < len(standard_steps) and step != standard_steps[i]:
                        sequence_deviation += 1

            deviation_analysis.append({
                'incident_id': incident['incident_id'],
                'category': category,
                'priority': incident['priority'],
                'step_count_deviation': step_count_deviation,
                'missing_steps_count': len(missing_steps),
                'extra_steps_count': len(extra_steps),
                'sequence_deviation': sequence_deviation,
                'total_deviation_score': abs(step_count_deviation) + len(missing_steps) + 
                                       len(extra_steps) + sequence_deviation,
                'resolution_time_hours': incident['resolution_time_hours'],
                'process_deviation': incident['process_deviation'],
                'missing_steps': ', '.join(missing_steps) if missing_steps else 'None',
                'extra_steps': ', '.join(extra_steps) if extra_steps else 'None'
            })

        self.deviation_df = pd.DataFrame(deviation_analysis)
        print(f"✅ Process compliance analysis completed for {len(self.deviation_df)} incidents")
        return self.deviation_df

    def generate_deviation_report(self):
        """Generate comprehensive deviation analysis report"""
        if not hasattr(self, 'deviation_df'):
            print("❌ Please run analyze_process_compliance() first")
            return

        print("\n" + "="*70)
        print("📊 ITSM PROCESS DEVIATION ANALYSIS REPORT")
        print("="*70)

        # Overall statistics
        total_incidents = len(self.deviation_df)
        deviated_incidents = len(self.deviation_df[self.deviation_df['process_deviation'] == 'Yes'])
        deviation_rate = (deviated_incidents / total_incidents) * 100

        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   Total Incidents Analyzed: {total_incidents}")
        print(f"   Incidents with Process Deviations: {deviated_incidents}")
        print(f"   Process Deviation Rate: {deviation_rate:.2f}%")

        # Deviation by category
        print(f"\n📊 DEVIATION BY CATEGORY:")
        category_deviations = self.deviation_df.groupby('category')['total_deviation_score'].agg(['count', 'mean', 'sum'])
        for category, row in category_deviations.iterrows():
            print(f"   {category:<12}: {row['count']:2d} incidents, Avg Score: {row['mean']:.2f}, Total: {row['sum']:.0f}")

        # Deviation by priority
        print(f"\n⚡ DEVIATION BY PRIORITY:")
        priority_deviations = self.deviation_df.groupby('priority')['total_deviation_score'].agg(['count', 'mean', 'sum'])
        for priority, row in priority_deviations.iterrows():
            print(f"   {priority:<8}: {row['count']:2d} incidents, Avg Score: {row['mean']:.2f}, Total: {row['sum']:.0f}")

        # Impact on resolution time
        print(f"\n⏱️  IMPACT ON RESOLUTION TIME:")
        deviated = self.deviation_df[self.deviation_df['process_deviation'] == 'Yes']['resolution_time_hours'].mean()
        normal = self.deviation_df[self.deviation_df['process_deviation'] == 'No']['resolution_time_hours'].mean()
        impact = ((deviated - normal) / normal * 100)

        print(f"   Average Resolution Time - Deviated Processes: {deviated:.2f} hours")
        print(f"   Average Resolution Time - Standard Processes: {normal:.2f} hours")
        print(f"   Performance Impact: {impact:+.2f}% {'(slower)' if impact > 0 else '(faster)'}")

        # Top deviating incidents
        print(f"\n🚨 TOP 10 INCIDENTS WITH HIGHEST DEVIATION SCORES:")
        top_deviations = self.deviation_df.nlargest(10, 'total_deviation_score')[
            ['incident_id', 'category', 'priority', 'total_deviation_score', 'resolution_time_hours']]

        print(f"   {'ID':<10} {'Category':<12} {'Priority':<8} {'Score':<5} {'Time(hrs)':<10}")
        print(f"   {'-'*10} {'-'*12} {'-'*8} {'-'*5} {'-'*10}")
        for _, row in top_deviations.iterrows():
            print(f"   {row['incident_id']:<10} {row['category']:<12} {row['priority']:<8} "
                  f"{row['total_deviation_score']:<5.0f} {row['resolution_time_hours']:<10.2f}")

        print("\n" + "="*70)

    def export_results(self, filename='deviation_analysis_results.xlsx'):
        """Export analysis results to Excel"""
        if not hasattr(self, 'deviation_df'):
            print("❌ Please run analyze_process_compliance() first")
            return

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main deviation analysis
                self.deviation_df.to_excel(writer, sheet_name='Deviation_Analysis', index=False)

                # Summary statistics
                total_incidents = len(self.deviation_df)
                deviated_incidents = len(self.deviation_df[self.deviation_df['process_deviation'] == 'Yes'])

                summary_stats = pd.DataFrame({
                    'Metric': ['Total Incidents', 'Deviations', 'Deviation Rate (%)', 
                              'Avg Deviation Score', 'Avg Resolution Time (Deviated)', 
                              'Avg Resolution Time (Normal)'],
                    'Value': [
                        total_incidents,
                        deviated_incidents,
                        round((deviated_incidents / total_incidents) * 100, 2),
                        round(self.deviation_df['total_deviation_score'].mean(), 2),
                        round(self.deviation_df[self.deviation_df['process_deviation'] == 'Yes']['resolution_time_hours'].mean(), 2),
                        round(self.deviation_df[self.deviation_df['process_deviation'] == 'No']['resolution_time_hours'].mean(), 2)
                    ]
                })
                summary_stats.to_excel(writer, sheet_name='Summary', index=False)

                # Category analysis
                category_analysis = self.deviation_df.groupby('category').agg({
                    'total_deviation_score': ['count', 'mean', 'sum'],
                    'resolution_time_hours': 'mean'
                }).round(2)
                category_analysis.to_excel(writer, sheet_name='Category_Analysis')

            print(f"✅ Results exported to {filename}")

        except Exception as e:
            print(f"❌ Error exporting results: {str(e)}")

def main():
    """Main function demonstrating the agent usage"""
    print("🚀 ITSM Process Deviation Detection Agent")
    print("=========================================")
    print(f"📍 Working directory: {os.getcwd()}")

    # Initialize the agent
    agent = ITSMProcessDeviationAgent()

    # Load data (creates sample data if not found)
    if agent.load_data():
        # Define standard processes
        agent.define_standard_processes()

        # Analyze process compliance
        deviation_results = agent.analyze_process_compliance()

        # Generate comprehensive report
        agent.generate_deviation_report()

        # Export results
        agent.export_results()

        print("\n🎉 Analysis complete! Files created:")
        print("   - sample_incidents.xlsx (if created)")
        print("   - deviation_analysis_results.xlsx")

        # Show available files
        print("\n📁 Files in current directory:")
        for file in os.listdir('.'):
            if file.endswith(('.xlsx', '.py')):
                print(f"   ✅ {file}")
    else:
        print("❌ Failed to load or create data. Please check the error messages above.")

if __name__ == "__main__":
    main()
