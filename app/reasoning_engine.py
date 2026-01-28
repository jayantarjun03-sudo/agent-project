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
       
