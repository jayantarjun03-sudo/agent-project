"""
AI Reasoning Engine for SLA Monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SLAReasoningEngine:
    """AI engine for analyzing SLA tickets and generating insights"""
    
    def __init__(self):
        self.history = []
        self.patterns = {}
    
    def analyze_ticket(self, ticket: Dict, context: Optional[Dict] = None) -> Dict:
        """
        Analyze a single ticket and provide insights
        
        Args:
            ticket: Ticket data dictionary
            context: Optional context data (team load, historical patterns, etc.)
        
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing ticket: {ticket.get('ticket_id')}")
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(ticket, context or {})
        
        # Determine SLA status
        sla_status = self._determine_sla_status(ticket, severity_score)
        
        # Generate insights
        insights = self._generate_insights(ticket, severity_score, context or {})
        
        # Recommend actions
        actions = self._recommend_actions(ticket, severity_score, insights)
        
        # Determine escalation need
        needs_escalation = severity_score >= 7
        escalation_level = self._determine_escalation_level(severity_score)
        
        # Build analysis result
        analysis = {
            'ticket_id': ticket.get('ticket_id'),
            'ticket_title': ticket.get('ticket_title'),
            'severity_score': severity_score,
            'sla_status': sla_status,
            'insights': insights,
            'recommended_actions': actions,
            'needs_escalation': needs_escalation,
            'escalation_level': escalation_level,
            'risk_level': self._get_risk_level(severity_score),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Store in history
        self.history.append(analysis)
        
        return analysis
    
    def _calculate_severity_score(self, ticket: Dict, context: Dict) -> int:
        """Calculate severity score (0-10)"""
        score = 0
        
        # 1. Priority factor (0-4 points)
        priority_scores = {'P1': 4, 'P2': 3, 'P3': 2, 'P4': 1, 'P5': 0}
        score += priority_scores.get(ticket.get('priority', 'P3'), 2)
        
        # 2. SLA status factor (0-4 points)
        sla_status_scores = {'breached': 4, 'at_risk': 3, 'delayed': 2, 'within_sla': 0}
        score += sla_status_scores.get(ticket.get('sla_status', 'within_sla'), 0)
        
        # 3. Delay factor (0-2 points)
        delay_minutes = ticket.get('delay_minutes', 0)
        if delay_minutes > 240:  # >4 hours
            score += 2
        elif delay_minutes > 60:  # >1 hour
            score += 1
        
        # 4. Customer tier factor (0-2 points)
        customer_tier = ticket.get('customer_tier', 'Basic')
        tier_scores = {'Platinum': 2, 'Enterprise': 1, 'Premium': 1, 'Basic': 0}
        score += tier_scores.get(customer_tier, 0)
        
        # 5. Service criticality (0-1 point)
        service = ticket.get('service_name', '')
        critical_services = ['Database', 'Security', 'Payment']
        if any(critical in service for critical in critical_services):
            score += 1
        
        # 6. Context factors (team load, time of day, etc.)
        team_load = context.get('team_load', 0)
        if team_load > 150:
            score += 2
        elif team_load > 100:
            score += 1
        
        # Cap at 10
        return min(score, 10)
    
    def _determine_sla_status(self, ticket: Dict, severity_score: int) -> str:
        """Determine current SLA status based on analysis"""
        current_status = ticket.get('sla_status', 'within_sla')
        
        if severity_score >= 8:
            return 'critical_breach'
        elif severity_score >= 6:
            return 'high_risk'
        elif severity_score >= 4:
            return 'medium_risk'
        elif current_status == 'breached':
            return 'breached'
        elif current_status == 'at_risk':
            return 'at_risk'
        elif current_status == 'delayed':
            return 'delayed'
        else:
            return 'within_sla'
    
    def _generate_insights(self, ticket: Dict, severity_score: int, context: Dict) -> List[str]:
        """Generate AI insights about the ticket"""
        insights = []
        
        ticket_id = ticket.get('ticket_id', 'Unknown')
        service = ticket.get('service_name', 'Unknown')
        priority = ticket.get('priority', 'P3')
        delay_minutes = ticket.get('delay_minutes', 0)
        customer_tier = ticket.get('customer_tier', 'Basic')
        
        # Critical severity insights
        if severity_score >= 8:
            insights.append(f"🚨 **CRITICAL**: Ticket {ticket_id} requires immediate attention")
            insights.append(f"🔴 **HIGH IMPACT**: {service} service for {customer_tier} customer at risk")
        
        # High severity insights
        elif severity_score >= 6:
            insights.append(f"⚠️ **HIGH RISK**: {service} service approaching SLA breach")
            if delay_minutes > 120:
                insights.append(f"⏰ **EXTENDED DELAY**: {delay_minutes//60}h {delay_minutes%60}m overdue")
        
        # Medium severity insights
        elif severity_score >= 4:
            insights.append(f"🔶 **MEDIUM RISK**: Monitor {service} ticket closely")
            if priority in ['P1', 'P2']:
                insights.append(f"🎯 **HIGH PRIORITY**: {priority} ticket needs regular updates")
        
        # Pattern-based insights
        team_load = context.get('team_load', 0)
        if team_load > 120:
            insights.append(f"👥 **TEAM CAPACITY**: Assigned team at {team_load}% capacity")
        
        # Time-based insights
        current_hour = datetime.now().hour
        if current_hour in [9, 10, 14, 15]:  # Peak hours
            insights.append("⏰ **PEAK HOUR**: Resolution may be delayed due to high volume")
        
        # Historical pattern insights
        if self._has_recurring_pattern(ticket, context):
            insights.append("📊 **RECURRING PATTERN**: Similar issues occurred previously")
        
        # If no specific insights, provide general one
        if not insights:
            insights.append("✅ **NORMAL**: Ticket within expected parameters")
        
        return insights
    
    def _has_recurring_pattern(self, ticket: Dict, context: Dict) -> bool:
        """Check for recurring patterns"""
        # Simplified pattern detection
        service = ticket.get('service_name', '')
        team = ticket.get('assigned_team', '')
        
        # Check historical patterns (simplified)
        pattern_key = f"{service}_{team}"
        if pattern_key in self.patterns:
            return self.patterns[pattern_key].get('recurring', False)
        
        return False
    
    def _recommend_actions(self, ticket: Dict, severity_score: int, insights: List[str]) -> List[str]:
        """Generate recommended actions based on severity and insights"""
        actions = []
        
        if severity_score >= 8:
            actions.extend([
                "🚨 IMMEDIATE: Escalate to director level",
                "📞 Contact customer personally with update",
                "🔄 Assign senior resources immediately",
                "⏰ Schedule emergency bridge call within 1 hour",
                "📋 Document all actions for post-mortem"
            ])
        elif severity_score >= 6:
            actions.extend([
                "⚠️ URGENT: Notify manager with detailed report",
                "📋 Review with team lead within 2 hours",
                "🔍 Conduct root cause analysis",
                "📝 Update customer with clear timeline",
                "🔄 Consider resource reallocation"
            ])
        elif severity_score >= 4:
            actions.extend([
                "🔶 MONITOR: Notify team lead",
                "📊 Review ticket details and dependencies",
                "⏰ Set reminder for follow-up in 4 hours",
                "📝 Document potential solutions",
                "👥 Check team availability"
            ])
        else:
            actions.extend([
                "✅ NORMAL: Continue standard monitoring",
                "📋 Update ticket regularly",
                "⏰ Follow standard SLA procedures",
                "📊 Track progress against SLA"
            ])
        
        # Add insight-specific actions
        for insight in insights:
            if "TEAM CAPACITY" in insight:
                actions.append("👥 **ACTION**: Review team workload and redistribute if needed")
            elif "RECURRING PATTERN" in insight:
                actions.append("📊 **ACTION**: Schedule root cause analysis meeting")
            elif "PEAK HOUR" in insight:
                actions.append("⏰ **ACTION**: Adjust expectations for resolution time")
        
        return actions[:5]  # Return top 5 actions
    
    def _determine_escalation_level(self, severity_score: int) -> int:
        """Determine appropriate escalation level"""
        if severity_score >= 9:
            return 3  # Director level
        elif severity_score >= 7:
            return 2  # Manager level
        elif severity_score >= 5:
            return 1  # Team lead level
        else:
            return 0  # No escalation
    
    def _get_risk_level(self, severity_score: int) -> str:
        """Get risk level description"""
        if severity_score >= 8:
            return "Critical"
        elif severity_score >= 6:
            return "High"
        elif severity_score >= 4:
            return "Medium"
        else:
            return "Low"
    
    def analyze_batch(self, tickets: List[Dict], context: Optional[Dict] = None) -> Dict:
        """Analyze a batch of tickets and provide aggregated insights"""
        logger.info(f"Analyzing batch of {len(tickets)} tickets")
        
        analyses = []
        for ticket in tickets:
            analysis = self.analyze_ticket(ticket, context)
            analyses.append(analysis)
        
        # Calculate aggregated metrics
        total_tickets = len(analyses)
        critical_tickets = sum(1 for a in analyses if a['severity_score'] >= 8)
        high_risk_tickets = sum(1 for a in analyses if a['severity_score'] >= 6)
        escalations_needed = sum(1 for a in analyses if a['needs_escalation'])
        
        # Find top issues
        top_issues = sorted(analyses, key=lambda x: x['severity_score'], reverse=True)[:5]
        
        # Generate batch insights
        batch_insights = self._generate_batch_insights(analyses)
        
        return {
            'total_tickets_analyzed': total_tickets,
            'critical_tickets': critical_tickets,
            'high_risk_tickets': high_risk_tickets,
            'escalations_needed': escalations_needed,
            'avg_severity_score': sum(a['severity_score'] for a in analyses) / total_tickets if total_tickets > 0 else 0,
            'top_issues': top_issues,
            'batch_insights': batch_insights,
            'analyses': analyses
        }
    
    def _generate_batch_insights(self, analyses: List[Dict]) -> List[str]:
        """Generate insights from batch analysis"""
        insights = []
        
        # Calculate statistics
        severity_scores = [a['severity_score'] for a in analyses]
        avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 0
        
        # Service distribution
        services = {}
        for analysis in analyses:
            service = analysis.get('ticket_title', 'Unknown').split('-')[-1].strip()
            services[service] = services.get(service, 0) + 1
        
        # Generate insights
        if avg_severity >= 7:
            insights.append("🚨 **CRITICAL BATCH**: High average severity detected. Immediate review required.")
        elif avg_severity >= 5:
            insights.append("⚠️ **ELEVATED RISK**: Above-average severity across multiple tickets.")
        
        # Service-specific insights
        if services:
            top_service = max(services.items(), key=lambda x: x[1])
            if top_service[1] > len(analyses) * 0.3:  # More than 30% of tickets
                insights.append(f"🎯 **SERVICE FOCUS**: {top_service[0]} accounts for {top_service[1]} tickets")
        
        # Escalation insights
        escalations = sum(1 for a in analyses if a['needs_escalation'])
        if escalations > 3:
            insights.append(f"📤 **ESCALATION VOLUME**: {escalations} tickets require escalation")
        
        # Time-based insights
        current_hour = datetime.now().hour
        if current_hour in [16, 17, 18]:  # Late afternoon
            insights.append("🌅 **END OF DAY**: Consider prioritizing for next day resolution")
        
        return insights
    
    def learn_from_history(self):
        """Learn patterns from analysis history"""
        if not self.history:
            return
        
        # Simple pattern learning (can be enhanced with ML)
        service_patterns = {}
        
        for analysis in self.history:
            service = analysis.get('ticket_title', 'Unknown').split('-')[-1].strip()
            severity = analysis['severity_score']
            
            if service not in service_patterns:
                service_patterns[service] = {'count': 0, 'total_severity': 0}
            
            service_patterns[service]['count'] += 1
            service_patterns[service]['total_severity'] += severity
        
        # Update patterns
        for service, stats in service_patterns.items():
            avg_severity = stats['total_severity'] / stats['count']
            self.patterns[service] = {
                'avg_severity': avg_severity,
                'recurring': stats['count'] > 3 and avg_severity > 5
            }
        
        logger.info(f"Learned patterns for {len(service_patterns)} services")
