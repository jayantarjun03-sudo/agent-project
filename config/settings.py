"""
Configuration settings for SLA Monitoring Agent
"""

import os
from typing import Dict, Any

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'test123'),
    'database': os.getenv('DB_NAME', 'sla_monitoring'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# AI Reasoning configuration
AI_CONFIG = {
    'severity_threshold': int(os.getenv('AI_SEVERITY_THRESHOLD', 7)),
    'confidence_threshold': int(os.getenv('AI_CONFIDENCE_THRESHOLD', 80)),
    'enable_pattern_detection': os.getenv('AI_ENABLE_PATTERNS', 'true').lower() == 'true',
    'enable_predictive_analytics': os.getenv('AI_ENABLE_PREDICTIVE', 'true').lower() == 'true'
}

# Escalation configuration
ESCALATION_CONFIG = {
    'levels': {
        1: {'name': 'Team Lead', 'threshold': 5, 'timeframe': '1h'},
        2: {'name': 'Manager', 'threshold': 7, 'timeframe': '30m'},
        3: {'name': 'Director', 'threshold': 9, 'timeframe': '15m'}
    },
    'notifications': {
        'email': os.getenv('EMAIL_NOTIFICATIONS', 'true').lower() == 'true',
        'slack': os.getenv('SLACK_NOTIFICATIONS', 'true').lower() == 'true',
        'dashboard': True
    }
}

# Application settings
APP_CONFIG = {
    'debug': os.getenv('DEBUG', 'false').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'data_refresh_interval': int(os.getenv('REFRESH_INTERVAL', 300)),  # 5 minutes
    'report_generation_time': os.getenv('REPORT_TIME', '08:00')
}

# SLA thresholds
SLA_THRESHOLDS = {
    'p1': {'response': 1, 'resolution': 4},  # hours
    'p2': {'response': 2, 'resolution': 8},
    'p3': {'response': 4, 'resolution': 24},
    'p4': {'response': 8, 'resolution': 48},
    'p5': {'response': 24, 'resolution': 96}
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration"""
    return {
        'database': DB_CONFIG,
        'ai': AI_CONFIG,
        'escalation': ESCALATION_CONFIG,
        'app': APP_CONFIG,
        'sla_thresholds': SLA_THRESHOLDS
    }
