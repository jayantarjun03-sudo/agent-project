"""
Utility functions for SLA Monitoring Agent
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_timedelta(td: timedelta) -> str:
    """Format timedelta to human readable string"""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def calculate_sla_compliance(within_sla: int, total: int) -> float:
    """Calculate SLA compliance percentage"""
    if total == 0:
        return 0.0
    return round((within_sla / total) * 100, 2)

def get_risk_color(severity: int) -> str:
    """Get color based on severity score"""
    if severity >= 8:
        return "#ff4b4b"  # Red
    elif severity >= 6:
        return "#ffa500"  # Orange
    elif severity >= 4:
        return "#ffd700"  # Yellow
    else:
        return "#00cc96"  # Green

def validate_ticket_data(ticket: Dict) -> List[str]:
    """Validate ticket data and return list of errors"""
    errors = []
    
    required_fields = ['ticket_id', 'ticket_title', 'priority', 'creation_time']
    for field in required_fields:
        if field not in ticket:
            errors.append(f"Missing required field: {field}")
    
    if 'priority' in ticket and ticket['priority'] not in ['P1', 'P2', 'P3', 'P4', 'P5']:
        errors.append(f"Invalid priority: {ticket['priority']}")
    
    if 'sla_status' in ticket and ticket['sla_status'] not in ['within_sla', 'delayed', 'at_risk', 'breached']:
        errors.append(f"Invalid SLA status: {ticket['sla_status']}")
    
    return errors

def generate_ticket_id(prefix: str = "TKT") -> str:
    """Generate unique ticket ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(hash(timestamp))[-4:]
    return f"{prefix}-{timestamp}-{random_suffix}"

def load_config(config_path: str = "config/settings.json") -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return {}

def save_config(config: Dict, config_path: str = "config/settings.json") -> bool:
    """Save configuration to JSON file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False

def calculate_metrics(tickets: List[Dict]) -> Dict[str, Any]:
    """Calculate SLA metrics from tickets"""
    if not tickets:
        return {}
    
    total = len(tickets)
    within_sla = sum(1 for t in tickets if t.get('sla_status') == 'within_sla')
    breached = sum(1 for t in tickets if t.get('sla_status') == 'breached')
    delayed = sum(1 for t in tickets if t.get('sla_status') == 'delayed')
    at_risk = sum(1 for t in tickets if t.get('sla_status') == 'at_risk')
    
    avg_delay = sum(t.get('delay_minutes', 0) for t in tickets) / total if total > 0 else 0
    
    return {
        'total_tickets': total,
        'within_sla': within_sla,
        'breached': breached,
        'delayed': delayed,
        'at_risk': at_risk,
        'compliance_rate': calculate_sla_compliance(within_sla, total),
        'avg_delay_minutes': round(avg_delay, 2)
    }

def format_datetime(dt: Any, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    
    return str(dt)

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string to datetime object"""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

def filter_tickets(tickets: List[Dict], filters: Dict) -> List[Dict]:
    """Filter tickets based on criteria"""
    filtered = tickets.copy()
    
    for key, value in filters.items():
        if value is not None:
            if key == 'start_date':
                filtered = [t for t in filtered if 
                           parse_datetime(t.get('creation_time', '')) >= value]
            elif key == 'end_date':
                filtered = [t for t in filtered if 
                           parse_datetime(t.get('creation_time', '')) <= value]
            elif key == 'priority':
                filtered = [t for t in filtered if t.get('priority') == value]
            elif key == 'sla_status':
                filtered = [t for t in filtered if t.get('sla_status') == value]
            elif key == 'assigned_team':
                filtered = [t for t in filtered if t.get('assigned_team') == value]
    
    return filtered
