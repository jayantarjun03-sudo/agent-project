"""
Visualization utilities for SLA Monitoring Agent
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

def create_sla_status_chart(data: Dict) -> go.Figure:
    """Create SLA status distribution chart"""
    if not data:
        # Sample data for demo
        data = {
            'within_sla': 85,
            'delayed': 32,
            'at_risk': 18,
            'breached': 15
        }
    
    fig = go.Figure(data=[
        go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=.3,
            marker=dict(
                colors=['#00cc96', '#ffa500', '#ff6b6b', '#ff4b4b'],
                line=dict(color='#fff', width=2)
            )
        )
    ])
    
    fig.update_layout(
        title='SLA Status Distribution',
        showlegend=True,
        annotations=[dict(text='SLA', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    return fig

def create_severity_gauge(severity_score: int) -> go.Figure:
    """Create severity gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=severity_score,
        title={'text': "Severity Score"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 10]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 3], 'color': "green"},
                {'range': [3, 7], 'color': "yellow"},
                {'range': [7, 10], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 7
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_trend_chart(dates: List[str], values: List[float], title: str = "Trend") -> go.Figure:
    """Create trend line chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Trend',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode='x unified',
        showlegend=False
    )
    
    return fig

def create_team_performance_chart(teams_data: List[Dict]) -> go.Figure:
    """Create team performance comparison chart"""
    df = pd.DataFrame(teams_data)
    
    fig = go.Figure(data=[
        go.Bar(
            name='SLA Compliance',
            x=df['team'],
            y=df['compliance'],
            marker_color='#1f77b4',
            text=df['compliance'],
            textposition='auto'
        ),
        go.Bar(
            name='Avg Resolution (h)',
            x=df['team'],
            y=df['resolution_time'],
            marker_color='#ff7f0e',
            text=df['resolution_time'],
            textposition='auto',
            yaxis='y2'
        )
    ])
    
    fig.update_layout(
        title='Team Performance Comparison',
        barmode='group',
        yaxis=dict(title='SLA Compliance %'),
        yaxis2=dict(
            title='Avg Resolution (hours)',
            overlaying='y',
            side='right'
        ),
        showlegend=True
    )
    
    return fig

def create_escalation_heatmap(escalation_data: List[Dict]) -> go.Figure:
    """Create escalation heatmap"""
    # Prepare data for heatmap
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    hours = list(range(24))
    
    # Create empty matrix
    z = [[0 for _ in hours] for _ in days]
    
    # Fill with data
    for esc in escalation_data:
        if 'timestamp' in esc:
            dt = datetime.fromisoformat(esc['timestamp'].replace('Z', '+00:00'))
            day_idx = dt.weekday()  # Monday=0
            hour_idx = dt.hour
            
            if 0 <= day_idx < 7 and 0 <= hour_idx < 24:
                z[day_idx][hour_idx] += 1
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=hours,
        y=days,
        colorscale='reds',
        showscale=True,
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Escalation Heatmap (Last 30 Days)',
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week'
    )
    
    return fig
