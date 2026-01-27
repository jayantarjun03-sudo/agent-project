#!/usr/bin/env python3
"""
AI SLA Monitoring Agent with Database Integration
Test agent for context building, reasoning, and escalation
"""

import mysql.connector
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class SLAStatus(Enum):
    WITHIN_SLA = "within_sla"
    DELAYED = "delayed"
    AT_RISK = "at_risk"
    BREACHED = "breached"

@dataclass
class SLATicket:
    ticket_id: str
    ticket_title: str
    service: str
    priority: str
    creation_time: datetime
    resolution_deadline: datetime
    actual_resolution_time: Optional[datetime]
    assigned_team: str
    sla_status: str
    delay_minutes: int
    current_status: str

class DatabaseAgent:
    def __init__(self, host='localhost', user='root', password='', database='sla_monitoring_test'):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            print("✅ Connected to test database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def get_tickets_for_analysis(self, hours_back=24):
        """Get recent tickets for analysis"""
        query = f"""
        SELECT 
            t.ticket_id,
            t.ticket_title,
            s.service_name,
            t.priority,
            t.creation_time,
            t.resolution_deadline,
            t.actual_resolution_time,
            t.assigned_team,
            t.sla_status,
            t.delay_minutes,
            t.status as current_status
        FROM tickets t
        JOIN services s ON t.service_id = s.service_id
        WHERE t.creation_time >= DATE_SUB(NOW(), INTERVAL {hours_back} HOUR)
        ORDER BY t.priority DESC, t.resolution_deadline ASC
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        tickets_data = cursor.fetchall()
        cursor.close()
        
        # Convert to SLATicket objects
        tickets = []
        for row in tickets_data:
            ticket = SLATicket(
                ticket_id=row['ticket_id'],
                ticket_title=row['ticket_title'],
                service=row['service_name'],
                priority=row['priority'],
                creation_time=row['creation_time'],
                resolution_deadline=row['resolution_deadline'],
                actual_resolution_time=row['actual_resolution_time'],
                assigned_team=row['assigned_team'],
                sla_status=row['sla_status'],
                delay_minutes=row['delay_minutes'],
                current_status=row['current_status']
            )
            tickets.append(ticket)
        
        print(f"📊 Retrieved {len(tickets)} tickets for analysis")
        return tickets
    
    def get_delayed_portions(self, ticket_ids: List[str]):
        """Get delayed portions for specific tickets"""
        if not ticket_ids:
            return []
            
        placeholders = ', '.join(['%s'] * len(ticket_ids))
        query = f"""
        SELECT 
            ticket_id,
            delay_type,
            delay_status,
            delay_duration_minutes,
            impact_score,
            delay_start
        FROM sla_delays
        WHERE ticket_id IN ({placeholders})
        ORDER BY delay_start DESC
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, tuple(ticket_ids))
        delays = cursor.fetchall()
        cursor.close()
        
        return delays
    
    def get_active_escalations(self):
        """Get active escalations"""
        query = """
        SELECT 
            e.ticket_id,
            e.escalation_level,
            e.escalation_reason,
            e.escalation_time,
            e.escalation_status,
            t.ticket_title,
            t.sla_status
        FROM escalations e
        JOIN tickets t ON e.ticket_id = t.ticket_id
        WHERE e.escalation_status = 'active'
        ORDER BY e.escalation_level DESC, e.escalation_time
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        escalations = cursor.fetchall()
        cursor.close()
        
        return escalations

class SLAReasoningEngine:
    def __init__(self, db_agent: DatabaseAgent):
        self.db_agent = db_agent
        self.context = {}
        self.insights = []
        
    def build_context(self, tickets: List[SLATicket]):
        """Build comprehensive context for decision making"""
        print("🧠 Building context...")
        
        # Calculate metrics
        total_tickets = len(tickets)
        delayed_tickets = [t for t in tickets if t.sla_status != 'within_sla']
        
        self.context = {
            'total_tickets': total_tickets,
            'delayed_tickets_count': len(delayed_tickets),
            'delayed_percentage': (len(delayed_tickets) / total_tickets * 100) if total_tickets > 0 else 0,
            'by_priority': self._group_by_priority(tickets),
            'by_service': self._group_by_service(tickets),
            'by_team': self._group_by_team(tickets),
            'avg_delay_minutes': sum(t.delay_minutes for t in tickets) / total_tickets if total_tickets > 0 else 0,
            'time_analysis': self._analyze_time_patterns(tickets)
        }
        
        print(f"✅ Context built: {self.context['delayed_tickets_count']} delayed tickets out of {total_tickets}")
        return self.context
    
    def _group_by_priority(self, tickets: List[SLATicket]) -> Dict:
        """Group tickets by priority"""
        groups = {}
        for ticket in tickets:
            if ticket.priority not in groups:
                groups[ticket.priority] = {'total': 0, 'delayed': 0}
            groups[ticket.priority]['total'] += 1
            if ticket.sla_status != 'within_sla':
                groups[ticket.priority]['delayed'] += 1
        return groups
    
    def _group_by_service(self, tickets: List[SLATicket]) -> Dict:
        """Group tickets by service"""
        groups = {}
        for ticket in tickets:
            if ticket.service not in groups:
                groups[ticket.service] = {'total': 0, 'delayed': 0}
            groups[ticket.service]['total'] += 1
            if ticket.sla_status != 'within_sla':
                groups[ticket.service]['delayed'] += 1
        return groups
    
    def _group_by_team(self, tickets: List[SLATicket]) -> Dict:
        """Group tickets by team"""
        groups = {}
        for ticket in tickets:
            if ticket.assigned_team not in groups:
                groups[ticket.assigned_team] = {'total': 0, 'delayed': 0}
            groups[ticket.assigned_team]['total'] += 1
            if ticket.sla_status != 'within_sla':
                groups[ticket.assigned_team]['delayed'] += 1
        return groups
    
    def _analyze_time_patterns(self, tickets: List[SLATicket]) -> Dict:
        """Analyze time-based patterns"""
        now = datetime.now()
        time_analysis = {
            'breached_within_1_hour': 0,
            'at_risk_next_2_hours': 0,
            'delayed_over_24_hours': 0
        }
        
        for ticket in tickets:
            if ticket.sla_status == 'breached':
                time_analysis['breached_within_1_hour'] += 1
            elif ticket.sla_status == 'at_risk':
                time_analysis['at_risk_next_2_hours'] += 1
            elif ticket.sla_status == 'delayed' and ticket.delay_minutes > 1440:
                time_analysis['delayed_over_24_hours'] += 1
                
        return time_analysis
    
    def reason_about_ticket(self, ticket: SLATicket, delays: List[Dict]) -> Dict:
        """Perform detailed reasoning on a single ticket"""
        now = datetime.now()
        
        # Calculate time metrics
        if ticket.actual_resolution_time:
            resolution_time = ticket.actual_resolution_time
            is_resolved = True
        else:
            resolution_time = None
            is_resolved = False
        
        # Determine severity
        severity = self._calculate_severity(ticket, delays)
        
        # Generate insights
        ticket_insights = []
        if ticket.sla_status == 'breached':
            ticket_insights.append(f"🚨 **CRITICAL**: SLA breached for {ticket.service}")
            if delays:
                total_delay = sum(d['delay_duration_minutes'] for d in delays)
                ticket_insights.append(f"⏱️  Total delay: {total_delay} minutes across {len(delays)} delays")
        
        elif ticket.sla_status == 'at_risk':
            time_to_deadline = (ticket.resolution_deadline - now).total_seconds() / 3600
            ticket_insights.append(f"⚠️  **AT RISK**: {time_to_deadline:.1f} hours to deadline")
            
        elif ticket.sla_status == 'delayed':
            ticket_insights.append(f"🔶 **DELAYED**: {ticket.delay_minutes} minutes overdue")
            
        # Add delay-specific insights
        pending_delays = [d for d in delays if d['delay_status'] in ['pending', 'in_progress']]
        if pending_delays:
            ticket_insights.append(f"⏸️  {len(pending_delays)} active delays ongoing")
            
        return {
            'ticket_id': ticket.ticket_id,
            'severity': severity,
            'insights': ticket_insights,
            'recommended_actions': self._recommend_actions(ticket, severity, delays),
            'needs_escalation': severity >= 8,
            'escalation_level': self._determine_escalation_level(severity)
        }
    
    def _calculate_severity(self, ticket: SLATicket, delays: List[Dict]) -> int:
        """Calculate severity score (1-10)"""
        score = 0
        
        # Priority factor
        priority_scores = {'P1': 4, 'P2': 3, 'P3': 2, 'P4': 1}
        score += priority_scores.get(ticket.priority, 2)
        
        # SLA status factor
        status_scores = {'breached': 4, 'at_risk': 3, 'delayed': 2, 'within_sla': 0}
        score += status_scores.get(ticket.sla_status, 0)
        
        # Delay factor
        if ticket.delay_minutes > 240:  # >4 hours
            score += 2
        elif ticket.delay_minutes > 60:  # >1 hour
            score += 1
            
        # Active delays factor
        active_delays = len([d for d in delays if d['delay_status'] in ['pending', 'in_progress']])
        score += min(active_delays, 2)  # Max 2 points
        
        return min(score, 10)  # Cap at 10
    
    def _recommend_actions(self, ticket: SLATicket, severity: int, delays: List[Dict]) -> List[str]:
        """Generate recommended actions"""
        actions = []
        
        if severity >= 8:
            actions.append("🚨 IMMEDIATE: Escalate to team lead and manager")
            actions.append("📞 Contact customer with status update")
            
        elif severity >= 6:
            actions.append("⚠️  URGENT: Review with assigned agent")
            actions.append("📋 Check for blockers and dependencies")
            
        elif severity >= 4:
            actions.append("🔍 Review ticket progress")
            actions.append("⏰ Set reminder for follow-up")
            
        # Specific actions based on delays
        pending_delays = [d for d in delays if d['delay_status'] == 'pending']
        if pending_delays:
            actions.append(f"⏸️  Address {len(pending_delays)} pending delays")
            
        return actions
    
    def _determine_escalation_level(self, severity: int) -> int:
        """Determine escalation level based on severity"""
        if severity >= 9:
            return 3  # Director level
        elif severity >= 7:
            return 2  # Manager level
        elif severity >= 5:
            return 1  # Team lead level
        else:
            return 0  # No escalation needed

class EscalationManager:
    def __init__(self, db_agent: DatabaseAgent):
        self.db_agent = db_agent
        self.escalation_matrix = {
            1: {"target": "team_lead", "urgency": "high", "timeframe": "1 hour"},
            2: {"target": "manager", "urgency": "urgent", "timeframe": "30 minutes"},
            3: {"target": "director", "urgency": "critical", "timeframe": "15 minutes"}
        }
    
    def process_escalations(self, ticket_decisions: List[Dict]):
        """Process escalations based on ticket decisions"""
        escalations_needed = [t for t in ticket_decisions if t['needs_escalation']]
        
        if not escalations_needed:
            print("✅ No escalations needed")
            return []
        
        print(f"📤 Processing {len(escalations_needed)} escalations...")
        
        escalation_records = []
        for ticket in escalations_needed:
            escalation_record = self._create_escalation_record(ticket)
            escalation_records.append(escalation_record)
            
            # In a real system, you would save to database here
            # self._save_escalation_to_db(escalation_record)
        
        return escalation_records
    
    def _create_escalation_record(self, ticket_decision: Dict) -> Dict:
        """Create escalation record"""
        level = ticket_decision['escalation_level']
        matrix = self.escalation_matrix.get(level, self.escalation_matrix[1])
        
        return {
            'ticket_id': ticket_decision['ticket_id'],
            'escalation_level': level,
            'target': matrix['target'],
            'urgency': matrix['urgency'],
            'timeframe': matrix['timeframe'],
            'reason': f"Severity score: {ticket_decision['severity']}/10",
            'insights': ticket_decision['insights'],
            'actions': ticket_decision['recommended_actions'],
            'timestamp': datetime.now().isoformat()
        }

class DailyOperationsReport:
    def __init__(self, db_agent: DatabaseAgent):
        self.db_agent = db_agent
        
    def generate_daily_report(self, 
                             context: Dict, 
                             ticket_decisions: List[Dict],
                             escalations: List[Dict]) -> Dict:
        """Generate daily operations report"""
        print("📈 Generating daily operations report...")
        
        report = {
            'report_date': datetime.now().date().isoformat(),
            'generated_at': datetime.now().isoformat(),
            'executive_summary': self._generate_executive_summary(context, ticket_decisions),
            'sla_performance': self._calculate_sla_performance(ticket_decisions),
            'critical_issues': self._identify_critical_issues(ticket_decisions),
            'team_analysis': self._analyze_team_performance(context),
            'escalation_analysis': self._analyze_escalations(escalations),
            'recommendations': self._generate_recommendations(context, ticket_decisions),
            'heatmap_data': self._generate_heatmap_data(ticket_decisions)
        }
        
        return report
    
    def _generate_executive_summary(self, context: Dict, ticket_decisions: List[Dict]) -> Dict:
        """Generate executive summary"""
        total_tickets = context['total_tickets']
        delayed_count = context['delayed_tickets_count']
        
        critical_tickets = len([t for t in ticket_decisions if t['severity'] >= 8])
        
        return {
            'total_tickets_monitored': total_tickets,
            'delayed_tickets': delayed_count,
            'delayed_percentage': context['delayed_percentage'],
            'critical_tickets': critical_tickets,
            'overall_health': 'GOOD' if delayed_count/total_tickets < 0.2 else 'WARNING' if delayed_count/total_tickets < 0.4 else 'CRITICAL'
        }
    
    def _calculate_sla_performance(self, ticket_decisions: List[Dict]) -> Dict:
        """Calculate SLA performance metrics"""
        if not ticket_decisions:
            return {}
            
        within_sla = len([t for t in ticket_decisions if t.get('severity', 0) <= 3])
        breached = len([t for t in ticket_decisions if t.get('severity', 0) >= 8])
        
        return {
            'within_sla_count': within_sla,
            'within_sla_percentage': (within_sla / len(ticket_decisions)) * 100,
            'breached_count': breached,
            'breached_percentage': (breached / len(ticket_decisions)) * 100,
            'avg_severity': sum(t.get('severity', 0) for t in ticket_decisions) / len(ticket_decisions)
        }
    
    def _identify_critical_issues(self, ticket_decisions: List[Dict]) -> List[Dict]:
        """Identify critical issues"""
        critical = []
        for ticket in ticket_decisions:
            if ticket['severity'] >= 8:
                critical.append({
                    'ticket_id': ticket['ticket_id'],
                    'severity': ticket['severity'],
                    'top_insight': ticket['insights'][0] if ticket['insights'] else 'No insights',
                    'needs_immediate_action': True
                })
        return critical[:10]  # Top 10 critical issues
    
    def _analyze_team_performance(self, context: Dict) -> List[Dict]:
        """Analyze team performance"""
        team_analysis = []
        for team, data in context['by_team'].items():
            if data['total'] > 0:
                delayed_rate = (data['delayed'] / data['total']) * 100
                team_analysis.append({
                    'team': team,
                    'total_tickets': data['total'],
                    'delayed_tickets': data['delayed'],
                    'delayed_percentage': delayed_rate,
                    'performance': 'GOOD' if delayed_rate < 20 else 'NEEDS_ATTENTION' if delayed_rate < 40 else 'CRITICAL'
                })
        return team_analysis
    
    def _analyze_escalations(self, escalations: List[Dict]) -> Dict:
        """Analyze escalations"""
        if not escalations:
            return {'total': 0, 'by_level': {}, 'summary': 'No escalations needed'}
        
        by_level = {}
        for esc in escalations:
            level = esc['escalation_level']
            by_level[level] = by_level.get(level, 0) + 1
        
        return {
            'total_escalations': len(escalations),
            'by_level': by_level,
            'highest_level': max(by_level.keys()) if by_level else 0,
            'summary': f"{len(escalations)} escalations processed"
        }
    
    def _generate_recommendations(self, context: Dict, ticket_decisions: List[Dict]) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Team-based recommendations
        for team, data in context['by_team'].items():
            if data['total'] > 5 and data['delayed'] / data['total'] > 0.3:
                recommendations.append(f"👥 **Team {team}**: High delay rate ({data['delayed']}/{data['total']}). Consider resource review.")
        
        # Priority-based recommendations
        for priority, data in context['by_priority'].items():
            if data['total'] > 0 and data['delayed'] / data['total'] > 0.4:
                recommendations.append(f"🎯 **Priority {priority}**: {data['delayed']}/{data['total']} delayed. Review prioritization process.")
        
        # Critical tickets recommendation
        critical_count = len([t for t in ticket_decisions if t['severity'] >= 8])
        if critical_count > 3:
            recommendations.append(f"🚨 **Critical Issues**: {critical_count} critical tickets need immediate attention.")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_heatmap_data(self, ticket_decisions: List[Dict]) -> Dict:
        """Generate heatmap data for visualization"""
        severity_distribution = {i: 0 for i in range(1, 11)}
        for ticket in ticket_decisions:
            severity = min(max(int(ticket['severity']), 1), 10)
            severity_distribution[severity] += 1
        
        return severity_distribution

class AI_SLA_Agent:
    def __init__(self):
        self.db_agent = DatabaseAgent()
        self.reasoning_engine = SLAReasoningEngine(self.db_agent)
        self.escalation_manager = EscalationManager(self.db_agent)
        self.report_generator = DailyOperationsReport(self.db_agent)
        
    def run_daily_analysis(self):
        """Main agent execution flow"""
        print("=" * 60)
        print("🤖 AI SLA MONITORING AGENT - DAILY ANALYSIS")
        print("=" * 60)
        
        try:
            # Step 1: Connect to database
            if not self.db_agent.connect():
                return
            
            # Step 2: Get tickets for analysis
            print("\n1️⃣ Fetching tickets for analysis...")
            tickets = self.db_agent.get_tickets_for_analysis(hours_back=24)
            
            if not tickets:
                print("No tickets found for analysis")
                return
            
            # Step 3: Build context
            print("\n2️⃣ Building analysis context...")
            context = self.reasoning_engine.build_context(tickets)
            
            # Step 4: Analyze each ticket
            print("\n3️⃣ Analyzing individual tickets...")
            ticket_decisions = []
            
            for ticket in tickets:
                # Get delays for this ticket
                delays = self.db_agent.get_delayed_portions([ticket.ticket_id])
                
                # Reason about the ticket
                decision = self.reasoning_engine.reason_about_ticket(ticket, delays)
                ticket_decisions.append(decision)
                
                # Show progress
                if len(ticket_decisions) % 10 == 0:
                    print(f"  Analyzed {len(ticket_decisions)}/{len(tickets)} tickets")
            
            # Step 5: Process escalations
            print("\n4️⃣ Processing escalations...")
            escalations = self.escalation_manager.process_escalations(ticket_decisions)
            
            # Step 6: Generate daily report
            print("\n5️⃣ Generating daily operations report...")
            daily_report = self.report_generator.generate_daily_report(context, ticket_decisions, escalations)
            
            # Step 7: Display results
            self._display_results(daily_report, ticket_decisions, escalations)
            
            # Step 8: Save report (optional)
            self._save_report(daily_report)
            
            print("\n" + "=" * 60)
            print("✅ AI AGENT ANALYSIS COMPLETE")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Agent execution failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_results(self, daily_report: Dict, ticket_decisions: List[Dict], escalations: List[Dict]):
        """Display analysis results"""
        print("\n📊 RESULTS SUMMARY:")
        print("-" * 40)
        
        # Executive Summary
        summary = daily_report['executive_summary']
        print(f"📈 Executive Summary:")
        print(f"  • Tickets Monitored: {summary['total_tickets_monitored']}")
        print(f"  • Delayed Tickets: {summary['delayed_tickets']} ({summary['delayed_percentage']:.1f}%)")
        print(f"  • Critical Tickets: {summary['critical_tickets']}")
        print(f"  • Overall Health: {summary['overall_health']}")
        
        # SLA Performance
        sla_perf = daily_report['sla_performance']
        print(f"\n🎯 SLA Performance:")
        print(f"  • Within SLA: {sla_perf['within_sla_count']} ({sla_perf['within_sla_percentage']:.1f}%)")
        print(f"  • Breached: {sla_perf['breached_count']} ({sla_perf['breached_percentage']:.1f}%)")
        print(f"  • Average Severity: {sla_perf['avg_severity']:.1f}/10")
        
        # Critical Issues
        critical_issues = daily_report['critical_issues']
        if critical_issues:
            print(f"\n🚨 Critical Issues (Top {len(critical_issues)}):")
            for issue in critical_issues[:3]:
                print(f"  • {issue['ticket_id']}: Severity {issue['severity']}/10 - {issue['top_insight']}")
        
        # Team Analysis
        team_analysis = daily_report['team_analysis']
        if team_analysis:
            print(f"\n👥 Team Performance:")
            for team in sorted(team_analysis, key=lambda x: x['delayed_percentage'], reverse=True)[:3]:
                print(f"  • {team['team']}: {team['delayed_percentage']:.1f}% delayed ({team['performance']})")
        
        # Escalations
        escalation_analysis = daily_report['escalation_analysis']
        print(f"\n📤 Escalations:")
        print(f"  • Total: {escalation_analysis['total_escalations']}")
        if escalation_analysis['by_level']:
            for level, count in escalation_analysis['by_level'].items():
                print(f"  • Level {level}: {count}")
        
        # Recommendations
        recommendations = daily_report['recommendations']
        if recommendations:
            print(f"\n💡 Top Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
    
    def _save_report(self, daily_report: Dict):
        """Save report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sla_agent_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(daily_report, f, indent=2, default=str)
        
        print(f"\n💾 Report saved to: {filename}")
    
    def run_specific_test(self, test_type="escalation"):
        """Run specific test scenarios"""
        print(f"\n🧪 Running {test_type} test...")
        
        if test_type == "escalation":
            self._test_escalation_logic()
        elif test_type == "context":
            self._test_context_building()
        elif test_type == "reasoning":
            self._test_reasoning_engine()
    
    def _test_escalation_logic(self):
        """Test escalation logic"""
        test_tickets = [
            {
                'ticket_id': 'TEST-001',
                'severity': 9,
                'escalation_level': 3,
                'insights': ['Critical breach detected'],
                'recommended_actions': ['Escalate immediately']
            },
            {
                'ticket_id': 'TEST-002',
                'severity': 6,
                'escalation_level': 1,
                'insights': ['Approaching deadline'],
                'recommended_actions': ['Review with team']
            }
        ]
        
        escalations = self.escalation_manager.process_escalations(test_tickets)
        print(f"✅ Escalation test: {len(escalations)} escalations generated")
        for esc in escalations:
            print(f"  • {esc['ticket_id']} -> Level {esc['escalation_level']} to {esc['target']}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI SLA Monitoring Agent")
    parser.add_argument("--action", choices=["analyze", "test", "setup"], default="analyze",
                       help="Action to perform")
    parser.add_argument("--test-type", choices=["escalation", "context", "reasoning"], 
                       default="escalation", help="Type of test to run")
    
    args = parser.parse_args()
    
    agent = AI_SLA_Agent()
    
    if args.action == "analyze":
        agent.run_daily_analysis()
    elif args.action == "test":
        agent.run_specific_test(args.test_type)
    elif args.action == "setup":
        # Run the database setup
        print("Please run: python setup_test_env.py")
        print("\nOr manually create database:")
        print("1. Install MySQL")
        print("2. Run: mysql -u root -p")
        print("3. CREATE DATABASE sla_monitoring_test;")
        print("4. Run the quick setup script")

if __name__ == "__main__":
    main()