#!/usr/bin/env python3
"""
Command-line interface for SLA Monitoring Agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database_manager import DatabaseManager
from app.reasoning_engine import SLAReasoningEngine
from app.escalation_manager import EscalationManager
import json
from datetime import datetime
import argparse

def analyze_tickets():
    """Analyze tickets using AI reasoning"""
    db = DatabaseManager()
    reasoning = SLAReasoningEngine()
    
    print("Fetching tickets for analysis...")
    tickets = db.get_tickets(limit=20)
    
    if not tickets:
        print("No tickets found for analysis")
        return
    
    print(f"Analyzing {len(tickets)} tickets...")
    results = reasoning.analyze_batch(tickets)
    
    print(f"\n📊 Analysis Results:")
    print(f"Total tickets analyzed: {results['total_tickets_analyzed']}")
    print(f"Critical tickets: {results['critical_tickets']}")
    print(f"High risk tickets: {results['high_risk_tickets']}")
    print(f"Escalations needed: {results['escalations_needed']}")
    print(f"Average severity: {results['avg_severity_score']:.1f}/10")
    
    print(f"\n🚨 Top 3 Issues:")
    for i, issue in enumerate(results['top_issues'][:3], 1):
        print(f"{i}. {issue['ticket_id']}: Severity {issue['severity_score']}/10 - {issue['risk_level']} risk")

def check_escalations():
    """Check and process escalations"""
    db = DatabaseManager()
    reasoning = SLAReasoningEngine()
    escalation = EscalationManager()
    
    print("Checking for escalations...")
    tickets = db.get_tickets(filters={'sla_status': 'breached'}, limit=10)
    
    if not tickets:
        print("No breached tickets found")
        return
    
    analyses = []
    for ticket in tickets:
        analysis = reasoning.analyze_ticket(ticket)
        analyses.append(analysis)
    
    print(f"Processing {len(analyses)} ticket analyses...")
    escalations = escalation.process_escalations(analyses)
    
    active_escalations = [e for e in escalations if e['escalation_level'] > 0]
    
    print(f"\n📤 Escalation Results:")
    print(f"Total escalations needed: {len(active_escalations)}")
    
    for esc in active_escalations:
        print(f"\nTicket: {esc['ticket_id']}")
        print(f"Escalation Level: {esc['escalation_level']}")
        print(f"Severity: {esc['severity_score']}/10")
        
        if esc['escalation_level'] > 0:
            plan = esc['plan']
            print(f"Target: {plan['target']}")
            print(f"Urgency: {plan['urgency']}")
            print(f"Deadline: {plan['deadline']}")

def generate_report():
    """Generate SLA report"""
    db = DatabaseManager()
    
    print("Generating SLA report...")
    metrics = db.get_sla_metrics(days_back=30)
    
    if not metrics:
        print("Could not generate report")
        return
    
    report = {
        'report_date': datetime.now().isoformat(),
        'period_days': 30,
        'metrics': metrics,
        'generated_by': 'SLA Monitoring Agent CLI'
    }
    
    filename = f"sla_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to {filename}")
    print(f"\n📊 Key Metrics:")
    print(f"Total tickets: {metrics.get('total_tickets', 0)}")
    print(f"SLA compliance: {metrics.get('compliance_rate', 0)}%")
    print(f"Breached tickets: {metrics.get('breached', 0)}")
    print(f"At risk tickets: {metrics.get('at_risk', 0)}")
    print(f"Average delay: {metrics.get('avg_delay_minutes', 0):.1f} minutes")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='SLA Monitoring Agent CLI')
    parser.add_argument('command', choices=['analyze', 'escalate', 'report', 'setup'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    print("🤖 SLA Monitoring Agent CLI")
    print("=" * 40)
    
    if args.command == 'analyze':
        analyze_tickets()
    elif args.command == 'escalate':
        check_escalations()
    elif args.command == 'report':
        generate_report()
    elif args.command == 'setup':
        print("Run: python setup_database.py")
    else:
        print("Invalid command")

if __name__ == "__main__":
    main()
