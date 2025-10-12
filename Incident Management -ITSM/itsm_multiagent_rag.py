
# RAG-Based Multi-Agent ITSM Process Deviation Detection System
import pandas as pd
import numpy as np
from datetime import datetime
import re
import os

class DocumentRetrievalAgent:
    """Agent 1: Retrieves and processes ITSM rules from documents"""

    def __init__(self, rules_file):
        self.rules_file = rules_file
        self.rules_db = {}
        print("🤖 Document Retrieval Agent initialized")

    def load_rules_from_document(self):
        """Simulates RAG - retrieves rules from document database"""
        print(f"📄 Loading process rules from {self.rules_file}...")

        with open(self.rules_file, 'r') as f:
            content = f.read()

        # Parse time standards
        time_standards = {}
        time_section = re.search(r'1\. INCIDENT RESOLUTION TIME STANDARDS.*?(?=2\.)', content, re.DOTALL)
        if time_section:
            lines = time_section.group(0).split('\n')
            for line in lines:
                if 'Critical Priority' in line:
                    time_standards['Critical'] = 4
                elif 'High Priority' in line:
                    time_standards['High'] = 12
                elif 'Medium Priority' in line:
                    time_standards['Medium'] = 48
                elif 'Low Priority' in line:
                    time_standards['Low'] = 96

        # Parse required steps for each category
        required_steps = {}
        categories = ['NETWORK', 'APPLICATION', 'HARDWARE', 'SECURITY', 'USER SUPPORT']

        for category in categories:
            pattern = f"{category} INCIDENTS:.*?Required Steps: ([^\\n]+)"
            match = re.search(pattern, content)
            if match:
                steps = [step.strip() for step in match.group(1).split(',')]
                required_steps[category.lower().replace(' ', '_')] = steps

        self.rules_db = {
            'time_standards': time_standards,
            'required_steps': required_steps,
            'deviation_threshold': 0.20  # 20% threshold for time deviations
        }

        print(f"✅ Loaded {len(time_standards)} time standards and {len(required_steps)} process templates")
        return self.rules_db

    def get_rules_for_category(self, category):
        """RAG retrieval: Get specific rules for incident category"""
        category_key = category.lower().replace(' ', '_')
        return {
            'time_standard': self.rules_db['time_standards'].get(category, 24),
            'required_steps': self.rules_db['required_steps'].get(category_key, []),
            'threshold': self.rules_db['deviation_threshold']
        }

class DeviationAnalysisAgent:
    """Agent 2: Analyzes incidents for process deviations using retrieved rules"""

    def __init__(self, document_agent):
        self.document_agent = document_agent
        self.incidents_data = None
        self.deviation_results = []
        print("🤖 Deviation Analysis Agent initialized")

    def load_incidents(self, incidents_file):
        """Load incident data from CSV file"""
        print(f"📊 Loading incidents from {incidents_file}...")
        self.incidents_data = pd.read_csv(incidents_file)
        print(f"✅ Loaded {len(self.incidents_data)} incidents for analysis")

    def analyze_time_deviations(self):
        """Analyze incidents for time-based deviations"""
        print("⏱️  Analyzing time-based deviations...")
        time_deviations = []

        for _, incident in self.incidents_data.iterrows():
            category = incident['category']
            priority = incident['priority']
            actual_time = incident['resolution_time_hours']

            # Get rules for this category/priority
            rules = self.document_agent.get_rules_for_category(category)
            expected_time = rules['time_standard']
            threshold = rules['threshold']

            # Check if actual time exceeds expected by more than threshold
            deviation_percent = (actual_time - expected_time) / expected_time
            if deviation_percent > threshold:
                time_deviations.append({
                    'incident_id': incident['incident_id'],
                    'category': category,
                    'priority': priority,
                    'technician': incident['technician'],
                    'expected_hours': expected_time,
                    'actual_hours': actual_time,
                    'deviation_percent': round(deviation_percent * 100, 2),
                    'deviation_type': 'Time Exceeded'
                })

        print(f"⚠️  Found {len(time_deviations)} time-based deviations")
        return time_deviations

    def analyze_process_deviations(self):
        """Analyze incidents for process step deviations"""
        print("📋 Analyzing process step deviations...")
        process_deviations = []

        for _, incident in self.incidents_data.iterrows():
            category = incident['category']
            steps_taken = incident['steps_taken'].split(' | ')

            # Get required steps from rules
            rules = self.document_agent.get_rules_for_category(category)
            required_steps = rules['required_steps']

            # Check for missing required steps
            missing_steps = []
            for required_step in required_steps:
                if not any(required_step.lower() in step.lower() for step in steps_taken):
                    missing_steps.append(required_step)

            if missing_steps:
                process_deviations.append({
                    'incident_id': incident['incident_id'],
                    'category': category,
                    'technician': incident['technician'],
                    'missing_steps': ', '.join(missing_steps),
                    'steps_taken': incident['steps_taken'],
                    'deviation_type': 'Missing Required Steps'
                })

        print(f"⚠️  Found {len(process_deviations)} process step deviations")
        return process_deviations

    def analyze_technician_performance(self):
        """Analyze technician-level performance deviations"""
        print("👤 Analyzing technician performance deviations...")
        tech_stats = {}

        for _, incident in self.incidents_data.iterrows():
            tech = incident['technician']
            if tech not in tech_stats:
                tech_stats[tech] = {
                    'incidents': 0,
                    'total_time': 0,
                    'satisfied_customers': 0,
                    'dissatisfied_customers': 0
                }

            tech_stats[tech]['incidents'] += 1
            tech_stats[tech]['total_time'] += incident['resolution_time_hours']

            if incident['customer_satisfaction'] in ['Very Satisfied', 'Satisfied']:
                tech_stats[tech]['satisfied_customers'] += 1
            elif incident['customer_satisfaction'] == 'Dissatisfied':
                tech_stats[tech]['dissatisfied_customers'] += 1

        # Identify performance deviations
        performance_deviations = []
        for tech, stats in tech_stats.items():
            avg_time = stats['total_time'] / stats['incidents']
            satisfaction_rate = stats['satisfied_customers'] / stats['incidents']
            dissatisfaction_rate = stats['dissatisfied_customers'] / stats['incidents']

            deviations = []
            if satisfaction_rate < 0.80:  # Less than 80% satisfaction
                deviations.append(f"Low satisfaction rate: {satisfaction_rate:.1%}")

            if dissatisfaction_rate > 0.10:  # More than 10% dissatisfied
                deviations.append(f"High dissatisfaction rate: {dissatisfaction_rate:.1%}")

            if avg_time > 50:  # Arbitrary threshold for demo
                deviations.append(f"High average resolution time: {avg_time:.1f} hours")

            if deviations:
                performance_deviations.append({
                    'technician': tech,
                    'incidents_handled': stats['incidents'],
                    'avg_resolution_time': round(avg_time, 2),
                    'satisfaction_rate': f"{satisfaction_rate:.1%}",
                    'deviations': '; '.join(deviations),
                    'deviation_type': 'Performance Issue'
                })

        print(f"⚠️  Found {len(performance_deviations)} technician performance deviations")
        return performance_deviations

    def generate_deviation_report(self):
        """Generate comprehensive deviation analysis report"""
        print("\n" + "="*60)
        print("🔍 RAG-BASED ITSM PROCESS DEVIATION ANALYSIS REPORT")
        print("="*60)

        # Analyze all deviation types
        time_devs = self.analyze_time_deviations()
        process_devs = self.analyze_process_deviations()
        tech_devs = self.analyze_technician_performance()

        # Summary statistics
        total_incidents = len(self.incidents_data)
        total_deviations = len(time_devs) + len(process_devs) + len(tech_devs)
        deviation_rate = (total_deviations / total_incidents) * 100

        print(f"\n📊 SUMMARY:")
        print(f"Total Incidents Analyzed: {total_incidents}")
        print(f"Total Deviations Found: {total_deviations}")
        print(f"Overall Deviation Rate: {deviation_rate:.2f}%")

        print(f"\n📈 DEVIATION BREAKDOWN:")
        print(f"• Time-based Deviations: {len(time_devs)}")
        print(f"• Process Step Deviations: {len(process_devs)}")
        print(f"• Technician Performance Issues: {len(tech_devs)}")

        # Export all results
        all_results = []
        for dev in time_devs:
            all_results.append(dev)
        for dev in process_devs:
            all_results.append(dev)
        for dev in tech_devs:
            all_results.append(dev)

        if all_results:
            results_df = pd.DataFrame(all_results)
            results_df.to_csv('itsm_deviation_analysis.csv', index=False)
            print(f"\n📄 Results exported to: itsm_deviation_analysis.csv")

            # Show top deviating technicians
            tech_deviation_counts = {}
            for result in all_results:
                if 'technician' in result:
                    tech = result['technician']
                    tech_deviation_counts[tech] = tech_deviation_counts.get(tech, 0) + 1

            if tech_deviation_counts:
                print(f"\n👥 TOP DEVIATING TECHNICIANS:")
                sorted_techs = sorted(tech_deviation_counts.items(), key=lambda x: x[1], reverse=True)
                for tech, count in sorted_techs[:10]:
                    print(f"• {tech}: {count} deviations")

        print("\n" + "="*60)

# Main execution function
def main():
    print("🚀 Starting RAG-Based Multi-Agent ITSM Analysis System")
    print("=" * 50)

    # Initialize agents
    doc_agent = DocumentRetrievalAgent('itsm_deviation_rules.txt')
    analysis_agent = DeviationAnalysisAgent(doc_agent)

    # Agent 1: Load rules from documents (RAG simulation)
    doc_agent.load_rules_from_document()

    # Agent 2: Load incidents and perform analysis
    analysis_agent.load_incidents('sample_incidents_rag.csv')

    # Generate comprehensive analysis
    analysis_agent.generate_deviation_report()

    print("\n🎉 Multi-Agent Analysis Complete!")

if __name__ == "__main__":
    main()
