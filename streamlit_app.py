#!/usr/bin/env python3
"""
Streamlit App for SLA Monitoring Agent
Deploy to: https://share.streamlit.io/
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sys
import os
import random

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database_manager import DatabaseManager
from reasoning_engine import SLAReasoningEngine
from escalation_manager import EscalationManager

# Page config
st.set_page_config(
    page_title="SLA Monitoring AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .severity-high {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
    }
    .severity-medium {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
    }
    .severity-low {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
</style>
""", unsafe_allow_html=True)

def display_metric_card(label, value, delta=None, severity_class=""):
    """Display a metric card"""
    card_class = f"metric-card {severity_class}"
    html = f"""
    <div class="{card_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div style="font-size: 0.8rem;">{delta}</div>' if delta else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

class StreamlitSLAApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.reasoning_engine = SLAReasoningEngine()
        self.escalation_manager = EscalationManager()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            'setup_complete': False,
            'analysis_run': False,
            'ticket_data': None,
            'analysis_results': None,
            'escalations': []
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def run(self):
        """Main application runner"""
        # Sidebar
        st.sidebar.title("🤖 SLA Monitoring Agent")
        st.sidebar.markdown("---")
        
        menu = st.sidebar.radio(
            "Navigation",
            ["🏠 Dashboard", "🔧 Setup", "📊 Analysis", 
             "🤖 AI Reasoning", "🚨 Escalations", "📈 Reports"]
        )
        
        # Show current status
        if st.session_state.setup_complete:
            st.sidebar.success("✅ Database Ready")
        
        # Main content
        if menu == "🏠 Dashboard":
            self.show_dashboard()
        elif menu == "🔧 Setup":
            self.show_setup()
        elif menu == "📊 Analysis":
            self.show_analysis()
        elif menu == "🤖 AI Reasoning":
            self.show_ai_reasoning()
        elif menu == "🚨 Escalations":
            self.show_escalations()
        elif menu == "📈 Reports":
            self.show_reports()
    
    def show_dashboard(self):
        """Display main dashboard"""
        st.title("🏠 SLA Monitoring Dashboard")
        
        # Quick stats row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            display_metric_card("Total Tickets", "156", "+12 today")
        
        with col2:
            display_metric_card("SLA Breaches", "8", "-2", "severity-high")
        
        with col3:
            display_metric_card("Avg Resolution", "4.2h", "-0.5h", "severity-medium")
        
        with col4:
            display_metric_card("Satisfaction", "92%", "+2%", "severity-low")
        
        st.markdown("---")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self.display_sla_status_chart()
        
        with col2:
            self.display_escalation_trends()
        
        # Recent tickets table
        st.markdown("### 📋 Recent Delayed Tickets")
        
        recent_data = [
            {"Ticket": "TKT-2024-001", "Service": "Database", "Priority": "P1", 
             "SLA Status": "Breached", "Delay": "4.2h", "Assigned": "Team A"},
            {"Ticket": "TKT-2024-002", "Service": "API", "Priority": "P2", 
             "SLA Status": "At Risk", "Delay": "1.5h", "Assigned": "Team B"},
            {"Ticket": "TKT-2024-003", "Service": "Frontend", "Priority": "P3", 
             "SLA Status": "Delayed", "Delay": "2.8h", "Assigned": "Team C"},
            {"Ticket": "TKT-2024-004", "Service": "Security", "Priority": "P1", 
             "SLA Status": "Breached", "Delay": "6.1h", "Assigned": "Team A"},
        ]
        
        df_recent = pd.DataFrame(recent_data)
        st.dataframe(df_recent, use_container_width=True)
    
    def display_sla_status_chart(self):
        """Display SLA status distribution chart"""
        data = {
            'Status': ['Within SLA', 'Delayed', 'At Risk', 'Breached'],
            'Count': [85, 32, 18, 15],
            'Color': ['#00cc96', '#ffa500', '#ff6b6b', '#ff4b4b']
        }
        
        df = pd.DataFrame(data)
        fig = px.pie(
            df, 
            values='Count', 
            names='Status',
            title='SLA Status Distribution',
            color='Status',
            color_discrete_map={
                'Within SLA': '#00cc96',
                'Delayed': '#ffa500',
                'At Risk': '#ff6b6b',
                'Breached': '#ff4b4b'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def display_escalation_trends(self):
        """Display escalation trends chart"""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'Date': dates,
            'Escalations': [random.randint(0, 5) for _ in range(30)],
            'Breaches': [random.randint(0, 3) for _ in range(30)]
        })
        
        fig = px.line(
            df, 
            x='Date', 
            y=['Escalations', 'Breaches'],
            title='Escalation Trends (Last 30 Days)',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def show_setup(self):
        """Display setup interface"""
        st.title("🔧 Setup & Configuration")
        
        tab1, tab2, tab3 = st.tabs(["Database", "Test Data", "AI Model"])
        
        with tab1:
            st.subheader("Database Configuration")
            
            with st.form("db_config"):
                col1, col2 = st.columns(2)
                
                with col1:
                    host = st.text_input("Host", value="localhost")
                    user = st.text_input("Username", value="root")
                
                with col2:
                    password = st.text_input("Password", type="password", value="test123")
                    database = st.text_input("Database", value="sla_monitoring")
                
                if st.form_submit_button("Save Configuration"):
                    st.session_state.db_config = {
                        'host': host,
                        'user': user,
                        'password': password,
                        'database': database
                    }
                    st.success("Database configuration saved!")
            
            # Test connection
            if st.button("Test Connection"):
                with st.spinner("Testing connection..."):
                    try:
                        result = self.db.test_connection()
                        if result:
                            st.success("✅ Connection successful!")
                        else:
                            st.error("❌ Connection failed")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with tab2:
            st.subheader("Generate Test Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                num_tickets = st.slider("Number of tickets", 10, 200, 50)
                include_delays = st.checkbox("Include delayed portions", value=True)
            
            with col2:
                include_escalations = st.checkbox("Include escalations", value=True)
                data_type = st.selectbox("Data type", ["Realistic", "Random", "Edge Cases"])
            
            if st.button("Generate Test Data", type="primary"):
                with st.spinner("Generating test data..."):
                    try:
                        success = self.generate_test_data(
                            num_tickets=num_tickets,
                            include_delays=include_delays,
                            include_escalations=include_escalations
                        )
                        if success:
                            st.session_state.setup_complete = True
                            st.success("✅ Test data generated successfully!")
                            st.balloons()
                        else:
                            st.error("Failed to generate test data")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with tab3:
            st.subheader("AI Model Configuration")
            
            # Reasoning thresholds
            severity_threshold = st.slider(
                "Severity threshold for escalation",
                min_value=1,
                max_value=10,
                value=7,
                help="Tickets with severity above this will be escalated"
            )
            
            confidence_threshold = st.slider(
                "AI confidence threshold",
                min_value=50,
                max_value=100,
                value=80,
                help="Minimum confidence for AI recommendations"
            )
            
            # Model settings
            st.checkbox("Enable pattern detection", value=True)
            st.checkbox("Enable predictive analytics", value=True)
            st.checkbox("Enable historical analysis", value=True)
            
            if st.button("Save AI Settings"):
                st.success("AI settings saved!")
    
    def generate_test_data(self, num_tickets=50, include_delays=True, include_escalations=True):
        """Generate test data for demonstration"""
        # This would connect to your actual database
        # For demo, we'll just update session state
        st.session_state.test_data_generated = True
        return True
    
    def show_analysis(self):
        """Display data analysis interface"""
        st.title("📊 Data Analysis")
        
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["SLA Performance", "Delay Patterns", "Team Metrics", "Customer Impact"]
        )
        
        if analysis_type == "SLA Performance":
            self.show_sla_performance_analysis()
        elif analysis_type == "Delay Patterns":
            self.show_delay_patterns_analysis()
        elif analysis_type == "Team Metrics":
            self.show_team_metrics_analysis()
        elif analysis_type == "Customer Impact":
            self.show_customer_impact_analysis()
    
    def show_sla_performance_analysis(self):
        """Display SLA performance analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Compliance over time
            st.subheader("SLA Compliance Trend")
            
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            df = pd.DataFrame({
                'Date': dates,
                'Compliance %': [random.uniform(80, 95) for _ in range(30)],
                'Target': [90] * 30
            })
            
            fig = px.line(df, x='Date', y=['Compliance %', 'Target'],
                         title='Daily SLA Compliance',
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Breach reasons
            st.subheader("Top Breach Reasons")
            
            reasons = pd.DataFrame({
                'Reason': ['Technical Complexity', 'Resource Constraints', 
                          'Customer Dependency', 'Third-party Delay', 
                          'Information Missing'],
                'Count': [45, 32, 28, 22, 18],
                'Avg Hours': [6.2, 4.8, 8.5, 12.3, 3.7]
            })
            
            fig = px.bar(reasons, x='Reason', y='Count',
                        color='Avg Hours',
                        title='Breach Reasons & Average Duration',
                        color_continuous_scale='reds')
            st.plotly_chart(fig, use_container_width=True)
    
    def show_delay_patterns_analysis(self):
        """Display delay patterns analysis"""
        st.subheader("⏰ Delay Patterns Analysis")
        
        # Time-based patterns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Delays by Hour of Day**")
            
            hours = list(range(24))
            delays = [random.randint(0, 20) for _ in hours]
            
            fig = px.bar(x=hours, y=delays,
                        labels={'x': 'Hour of Day', 'y': 'Number of Delays'},
                        title='Delays by Time of Day')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Delays by Day of Week**")
            
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            delays = [random.randint(10, 40) for _ in days]
            
            fig = px.bar(x=days, y=delays,
                        labels={'x': 'Day of Week', 'y': 'Number of Delays'},
                        title='Delays by Day of Week')
            st.plotly_chart(fig, use_container_width=True)
        
        # Delay duration distribution
        st.markdown("**Delay Duration Distribution**")
        
        durations = [random.expovariate(1/4) for _ in range(100)]  # Exponential distribution
        fig = px.histogram(x=durations, nbins=20,
                          labels={'x': 'Delay Duration (hours)', 'y': 'Count'},
                          title='Distribution of Delay Durations')
        st.plotly_chart(fig, use_container_width=True)
    
    def show_team_metrics_analysis(self):
        """Display team metrics analysis"""
        st.subheader("👥 Team Performance Analysis")
        
        # Team comparison
        teams_data = pd.DataFrame({
            'Team': ['Team A', 'Team B', 'Team C', 'Team D', 'Team E'],
            'SLA Compliance %': [92.5, 88.2, 76.8, 94.1, 85.3],
            'Avg Resolution (hours)': [3.2, 4.5, 6.8, 2.9, 5.1],
            'Tickets Handled': [145, 128, 98, 167, 112],
            'Customer Satisfaction %': [94, 89, 82, 96, 87]
        })
        
        # Interactive filters
        col1, col2 = st.columns(2)
        with col1:
            min_compliance = st.slider("Minimum Compliance %", 70, 100, 80)
        with col2:
            max_resolution = st.slider("Maximum Resolution (hours)", 2, 10, 8)
        
        # Filter data
        filtered_data = teams_data[
            (teams_data['SLA Compliance %'] >= min_compliance) &
            (teams_data['Avg Resolution (hours)'] <= max_resolution)
        ]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        metrics = [
            ("Top Performing Team", filtered_data.loc[filtered_data['SLA Compliance %'].idxmax(), 'Team']),
            ("Best Resolution Time", f"{filtered_data['Avg Resolution (hours)'].min():.1f}h"),
            ("Most Tickets", filtered_data.loc[filtered_data['Tickets Handled'].idxmax(), 'Team']),
            ("Highest Satisfaction", f"{filtered_data['Customer Satisfaction %'].max()}%")
        ]
        
        for col, (label, value) in zip([col1, col2, col3, col4], metrics):
            with col:
                st.metric(label, value)
        
        # Team comparison chart
        fig = px.scatter(filtered_data, 
                        x='Tickets Handled',
                        y='SLA Compliance %',
                        size='Avg Resolution (hours)',
                        color='Team',
                        hover_name='Team',
                        hover_data=['Customer Satisfaction %'],
                        title='Team Performance: Volume vs Compliance',
                        size_max=30)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.markdown("### Detailed Team Metrics")
        st.dataframe(
            filtered_data.style.format({
                'SLA Compliance %': '{:.1f}%',
                'Avg Resolution (hours)': '{:.1f}h',
                'Customer Satisfaction %': '{:.0f}%'
            }).background_gradient(subset=['SLA Compliance %'], cmap='RdYlGn'),
            use_container_width=True
        )
    
    def show_customer_impact_analysis(self):
        """Display customer impact analysis"""
        st.subheader("👥 Customer Impact Analysis")
        
        # Customer tier analysis
        tiers_data = pd.DataFrame({
            'Customer Tier': ['Platinum', 'Enterprise', 'Premium', 'Basic'],
            'Number of Tickets': [45, 128, 89, 56],
            'SLA Breaches': [2, 8, 12, 18],
            'Breach Rate %': [4.4, 6.3, 13.5, 32.1],
            'Avg Resolution (hours)': [2.8, 3.5, 5.2, 7.8],
            'Satisfaction Score': [95, 92, 85, 72]
        })
        
        # Impact metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Customers", sum(tiers_data['Number of Tickets']))
        with col2:
            st.metric("Overall Breach Rate", f"{tiers_data['Breach Rate %'].mean():.1f}%")
        with col3:
            st.metric("Avg Satisfaction", f"{tiers_data['Satisfaction Score'].mean():.0f}/100")
        
        # Customer tier comparison
        fig = px.bar(tiers_data, 
                    x='Customer Tier',
                    y='Breach Rate %',
                    color='Satisfaction Score',
                    title='Breach Rate by Customer Tier',
                    color_continuous_scale='RdYlGn_r',
                    labels={'Breach Rate %': 'Breach Rate (%)'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Customer impact matrix
        st.markdown("### Customer Impact Matrix")
        
        impact_data = pd.DataFrame({
            'Customer': [f'Customer {i}' for i in range(1, 11)],
            'Ticket Volume': [random.randint(5, 50) for _ in range(10)],
            'Breach Count': [random.randint(0, 10) for _ in range(10)],
            'Avg Delay (hours)': [random.uniform(0, 15) for _ in range(10)],
            'Priority': random.choices(['High', 'Medium', 'Low'], k=10),
            'Last 30 Days': [random.randint(0, 20) for _ in range(10)]
        })
        
        impact_data['Breach Rate %'] = (impact_data['Breach Count'] / impact_data['Ticket Volume'] * 100).round(1)
        impact_data['Impact Score'] = (
            impact_data['Breach Rate %'] * 0.4 +
            impact_data['Avg Delay (hours)'] * 0.3 +
            (impact_data['Last 30 Days'] / impact_data['Ticket Volume']) * 0.3
        ).round(1)
        
        # Sort by impact score
        impact_data = impact_data.sort_values('Impact Score', ascending=False)
        
        # Display impact matrix
        st.dataframe(
            impact_data.style.format({
                'Avg Delay (hours)': '{:.1f}h',
                'Breach Rate %': '{:.1f}%',
                'Impact Score': '{:.1f}'
            }).bar(subset=['Impact Score'], color='#ff6b6b'),
            use_container_width=True
        )
        
        # Recommendations based on analysis
        st.markdown("### 💡 Customer Impact Recommendations")
        
        high_impact_customers = impact_data[impact_data['Impact Score'] > 60]
        if not high_impact_customers.empty:
            st.warning(f"**High Impact Alert**: {len(high_impact_customers)} customers with high impact scores detected")
            
            recommendations = [
                "1. **Immediate review** required for high-impact customers",
                "2. **Proactive communication** for customers with increasing breach rates",
                "3. **Priority support** allocation for top 5 impacted customers",
                "4. **Regular check-ins** for customers with multiple recent breaches"
            ]
            
            for rec in recommendations:
                st.info(rec)
        else:
            st.success("✅ No high-impact customers detected. Current customer management is effective.")
    
    def show_ai_reasoning(self):
        """Display AI reasoning interface"""
        st.title("🤖 AI Reasoning Engine")
        
        st.info("""
        The AI agent analyzes tickets in real-time, building context and providing insights 
        for delayed SLAs. Test the reasoning engine with different scenarios.
        """)
        
        # Test scenarios
        st.subheader("🧪 Test AI Reasoning")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ticket_id = st.text_input("Ticket ID", "TKT-2024-001")
            service = st.selectbox("Service", ["Database", "API", "Frontend", "Security", "Payment"])
            priority = st.select_slider("Priority", options=["P5", "P4", "P3", "P2", "P1"], value="P2")
        
        with col2:
            delay_hours = st.slider("Delay (hours)", 0, 48, 6)
            customer_tier = st.selectbox("Customer Tier", ["Basic", "Premium", "Enterprise", "Platinum"])
            has_history = st.checkbox("Has history of delays", value=False)
        
        # Additional context
        with st.expander("Additional Context"):
            col1, col2 = st.columns(2)
            with col1:
                team_load = st.slider("Team current load (%)", 0, 200, 85)
                time_of_day = st.selectbox("Time of creation", ["Morning", "Afternoon", "Evening", "Night"])
            with col2:
                is_weekend = st.checkbox("Created on weekend")
                has_dependencies = st.checkbox("Has dependencies", value=True)
        
        # Run AI analysis
        if st.button("🔍 Analyze with AI", type="primary"):
            with st.spinner("AI agent analyzing scenario..."):
                # Simulate AI analysis
                severity = self.calculate_severity_score(
                    priority=priority,
                    delay_hours=delay_hours,
                    customer_tier=customer_tier,
                    team_load=team_load,
                    has_history=has_history
                )
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                # Show severity
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Severity Score", f"{severity}/10")
                with col2:
                    escalation_level = self.get_escalation_level(severity)
                    st.metric("Escalation Level", escalation_level)
                with col3:
                    risk_level = "High" if severity >= 8 else "Medium" if severity >= 5 else "Low"
                    st.metric("Risk Level", risk_level)
                
                # Show gauge chart for severity
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=severity,
                    title={'text': "Severity Score"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 10]},
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
                st.plotly_chart(fig, use_container_width=True)
                
                # AI Insights
                st.subheader("🧠 AI Insights")
                
                insights = self.generate_insights(
                    severity=severity,
                    service=service,
                    delay_hours=delay_hours,
                    customer_tier=customer_tier,
                    team_load=team_load
                )
                
                for insight in insights:
                    if "🚨" in insight:
                        st.error(insight)
                    elif "⚠️" in insight:
                        st.warning(insight)
                    else:
                        st.info(insight)
                
                # Recommended Actions
                st.subheader("💡 Recommended Actions")
                
                actions = self.get_recommended_actions(
                    severity=severity,
                    escalation_level=escalation_level,
                    service=service
                )
                
                for i, action in enumerate(actions, 1):
                    st.write(f"{i}. {action}")
    
    def calculate_severity_score(self, priority, delay_hours, customer_tier, team_load, has_history):
        """Calculate severity score (simulated)"""
        score = 0
        
        # Priority factor
        priority_scores = {"P1": 4, "P2": 3, "P3": 2, "P4": 1, "P5": 0}
        score += priority_scores.get(priority, 2)
        
        # Delay factor
        if delay_hours > 24:
            score += 4
        elif delay_hours > 12:
            score += 3
        elif delay_hours > 6:
            score += 2
        elif delay_hours > 2:
            score += 1
        
        # Customer tier factor
        tier_scores = {"Platinum": 3, "Enterprise": 2, "Premium": 1, "Basic": 0}
        score += tier_scores.get(customer_tier, 0)
        
        # Team load factor
        if team_load > 150:
            score += 2
        elif team_load > 100:
            score += 1
        
        # History factor
        if has_history:
            score += 1
        
        return min(score, 10)
    
    def get_escalation_level(self, severity):
        """Get escalation level based on severity"""
        if severity >= 9:
            return "Level 3 (Director)"
        elif severity >= 7:
            return "Level 2 (Manager)"
        elif severity >= 5:
            return "Level 1 (Team Lead)"
        else:
            return "No escalation"
    
    def generate_insights(self, severity, service, delay_hours, customer_tier, team_load):
        """Generate AI insights"""
        insights = []
        
        if severity >= 8:
            insights.append("🚨 **CRITICAL**: Immediate attention required. High risk of SLA breach.")
        
        if delay_hours > 12:
            insights.append(f"⚠️ **EXTENDED DELAY**: {delay_hours}h delay indicates systemic issue with {service}")
        
        if customer_tier in ["Platinum", "Enterprise"] and severity >= 6:
            insights.append(f"👥 **KEY CUSTOMER**: {customer_tier} customer affected. High business impact.")
        
        if team_load > 120:
            insights.append("👥 **TEAM OVERLOAD**: Team capacity exceeded. Consider resource reallocation.")
        
        if severity >= 7 and delay_hours > 6:
            insights.append("📊 **PATTERN DETECTED**: Similar issues occurred 3 times this week. Root cause analysis needed.")
        
        if not insights:
            insights.append("✅ **LOW RISK**: Current parameters indicate manageable situation.")
        
        return insights
    
    def get_recommended_actions(self, severity, escalation_level, service):
        """Get recommended actions"""
        actions = []
        
        if "Level 3" in escalation_level:
            actions.extend([
                "🚨 IMMEDIATE: Escalate to director with full context",
                "📞 Contact customer personally with update",
                "🔄 Assign senior resources immediately",
                "⏰ Set up emergency bridge call within 1 hour"
            ])
        elif "Level 2" in escalation_level:
            actions.extend([
                "⚠️ URGENT: Notify manager with detailed report",
                "📋 Review with team lead within 2 hours",
                "🔍 Conduct root cause analysis",
                "📝 Update customer with timeline"
            ])
        elif "Level 1" in escalation_level:
            actions.extend([
                "🔶 MONITOR: Notify team lead",
                "📊 Review ticket details",
                "⏰ Set reminder for follow-up",
                "📝 Document potential solutions"
            ])
        else:
            actions.extend([
                "✅ NORMAL: Continue standard monitoring",
                "📋 Update ticket regularly",
                "⏰ Follow standard SLA procedures"
            ])
        
        # Service-specific actions
        if service == "Database":
            actions.append("💾 Check database backups and performance metrics")
        elif service == "Payment":
            actions.append("💰 Verify transaction logs and payment gateway status")
        
        return actions
    
    def show_escalations(self):
        """Display escalations interface"""
        st.title("🚨 Escalation Management")
        
        # Active escalations
        st.subheader("Active Escalations")
        
        escalations = [
            {
                "id": "ESC-001",
                "ticket": "TKT-2024-015",
                "level": 3,
                "reason": "SLA Breach - Platinum Customer",
                "time": "2h ago",
                "severity": 9,
                "assigned": "Director"
            },
            {
                "id": "ESC-002",
                "ticket": "TKT-2024-022",
                "level": 2,
                "reason": "Multiple Delays - Critical Service",
                "time": "4h ago",
                "severity": 7,
                "assigned": "Manager"
            },
            {
                "id": "ESC-003",
                "ticket": "TKT-2024-028",
                "level": 1,
                "reason": "Approaching Deadline - High Priority",
                "time": "6h ago",
                "severity": 6,
                "assigned": "Team Lead"
            },
        ]
        
        for esc in escalations:
            with st.expander(f"🚨 Level {esc['level']}: {esc['ticket']} - {esc['reason']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Escalation ID:** {esc['id']}")
                    st.write(f"**Time:** {esc['time']}")
                    st.write(f"**Severity:** {esc['severity']}/10")
                    st.write(f"**Assigned to:** {esc['assigned']}")
                    
                    # Show progress
                    progress = min(100, (6 - int(esc['time'].split('h')[0])) * 20)
                    st.progress(progress)
                
                with col2:
                    if st.button("✅ Resolve", key=f"resolve_{esc['id']}"):
                        st.success(f"Escalation {esc['id']} resolved")
                        st.rerun()
                    
                    if st.button("📈 Escalate", key=f"escalate_{esc['id']}"):
                        st.warning(f"Escalation {esc['id']} escalated to next level")
                        st.rerun()
                    
                    if st.button("📋 Details", key=f"details_{esc['id']}"):
                        st.info(f"Showing details for {esc['id']}")
        
        # Escalation metrics
        st.markdown("---")
        st.subheader("Escalation Analytics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Escalations", "24", "+3 this week")
        with col2:
            st.metric("Avg Resolution Time", "3.2h", "-0.8h")
        with col3:
            st.metric("Recurring Issues", "12%", "-3%")
        
        # Escalation trends
        st.markdown("### 📈 Escalation Trends")
        
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Level 1': [random.randint(0, 3) for _ in range(30)],
            'Level 2': [random.randint(0, 2) for _ in range(30)],
            'Level 3': [random.randint(0, 1) for _ in range(30)]
        })
        
        fig = px.line(trend_data, x='Date', y=['Level 1', 'Level 2', 'Level 3'],
                     title='Escalation Levels Over Time',
                     markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    def show_reports(self):
        """Display reports interface"""
        st.title("📈 Reports & Analytics")
        
        # Report type selection
        report_type = st.selectbox(
            "Select Report Type",
            ["Daily Operations", "Weekly Performance", "Monthly Review", 
             "Quarterly Analysis", "Custom Report"]
        )
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Additional filters
        with st.expander("Advanced Filters"):
            col1, col2, col3 = st.columns(3)
            with col1:
                services = st.multiselect(
                    "Services",
                    ["All", "Database", "API", "Frontend", "Security", "Payment"],
                    default=["All"]
                )
            with col2:
                teams = st.multiselect(
                    "Teams",
                    ["All", "Team A", "Team B", "Team C", "Team D"],
                    default=["All"]
                )
            with col3:
                priorities = st.multiselect(
                    "Priorities",
                    ["All", "P1", "P2", "P3", "P4", "P5"],
                    default=["All"]
                )
        
        # Generate report
        if st.button("📊 Generate Report", type="primary"):
            with st.spinner(f"Generating {report_type} report..."):
                # Simulate report generation
                time.sleep(2)
                
                # Display report
                st.success(f"✅ {report_type} Report Generated!")
                
                # Report tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "📈 Metrics", "📊 Charts", "💡 Insights"])
                
                with tab1:
                    self.show_report_summary(report_type, start_date, end_date)
                
                with tab2:
                    self.show_report_metrics()
                
                with tab3:
                    self.show_report_charts()
                
                with tab4:
                    self.show_report_insights()
                
                # Download options
                st.markdown("---")
                st.subheader("📥 Export Report")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Download as CSV"):
                        st.success("CSV download started")
                with col2:
                    if st.button("Download as PDF"):
                        st.success("PDF download started")
                with col3:
                    if st.button("Download as JSON"):
                        # Create sample JSON
                        report_data = {
                            "report_type": report_type,
                            "period": f"{start_date} to {end_date}",
                            "generated_at": datetime.now().isoformat(),
                            "metrics": {
                                "sla_compliance": 87.3,
                                "avg_resolution_time": 5.2,
                                "ticket_volume": 342
                            }
                        }
                        
                        st.download_button(
                            label="Download JSON",
                            data=json.dumps(report_data, indent=2),
                            file_name=f"sla_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
    
    def show_report_summary(self, report_type, start_date, end_date):
        """Display report summary"""
        st.subheader("Executive Summary")
        
        summary = f"""
        **Report Period:** {start_date} to {end_date}
        **Report Type:** {report_type}
        **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        **Key Highlights:**
        - Overall SLA compliance: **87.3%** (+2.1% from previous period)
        - Average resolution time: **5.2 hours** (-0.8 hours improvement)
        - Total tickets handled: **342** (+14 from previous period)
        - Customer satisfaction: **92%** (+2% improvement)
        
        **Top Performing Team:** Team D (94% compliance rate)
        **Area Needing Attention:** Database service (72% compliance rate)
        
        **Critical Findings:**
        1. 65% of SLA breaches occur between 2-4 PM
        2. Database service shows consistent underperformance
        3. Team C is handling 35% above capacity
        
        **Recommendations:**
        1. Implement additional monitoring for Database service during peak hours
        2. Review resource allocation for Team C
        3. Consider adjusting SLA for complex database operations
        """
        
        st.markdown(summary)
    
    def show_report_metrics(self):
        """Display report metrics"""
        st.subheader("Detailed Metrics")
        
        metrics_data = pd.DataFrame({
            'Metric': ['SLA Compliance Rate', 'First Response Time', 
                      'Average Resolution Time', 'Customer Satisfaction Score',
                      'Ticket Volume', 'Reopened Tickets', 'Escalation Rate',
                      'Mean Time To Resolution (MTTR)'],
            'Current Period': ['87.3%', '1.2h', '5.2h', '92%', '342', '18', '7%', '4.8h'],
            'Previous Period': ['85.2%', '1.4h', '6.0h', '90%', '328', '22', '9%', '5.6h'],
            'Change': ['+2.1%', '-0.2h', '-0.8h', '+2%', '+14', '-4', '-2%', '-0.8h'],
            'Target': ['≥90%', '≤1h', '≤6h', '≥90%', 'N/A', '≤20', '≤8%', '≤5h']
        })
        
        st.dataframe(
            metrics_data.style.apply(
                lambda x: ['background-color: #e6f7f0' if '≥' in str(x['Target']) and str(x['Current Period']).replace('%', '').replace('h', '') >= str(x['Target']).replace('≥', '').replace('%', '').replace('h', '') 
                          else 'background-color: #ffe6e6' if '≤' in str(x['Target']) and str(x['Current Period']).replace('%', '').replace('h', '') > str(x['Target']).replace('≤', '').replace('%', '').replace('h', '')
                          else '' for _ in x],
                axis=1
            ),
            use_container_width=True,
            hide_index=True
        )
    
    def show_report_charts(self):
        """Display report charts"""
        st.subheader("Visual Analytics")
        
        # Performance comparison
        fig = go.Figure(data=[
            go.Bar(name='Current', x=['SLA Compliance', 'Resolution Time', 'Satisfaction'], 
                  y=[87.3, 5.2, 92], marker_color='#1f77b4'),
            go.Bar(name='Previous', x=['SLA Compliance', 'Resolution Time', 'Satisfaction'], 
                  y=[85.2, 6.0, 90], marker_color='#ff7f0e'),
            go.Bar(name='Target', x=['SLA Compliance', 'Resolution Time', 'Satisfaction'], 
                  y=[90, 6, 90], marker_color='#2ca02c', opacity=0.3)
        ])
        
        fig.update_layout(
            barmode='group',
            title='Key Metrics: Current vs Previous vs Target',
            yaxis_title="Value",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Trend analysis
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Compliance': [random.uniform(80, 95) for _ in range(30)],
            'Resolution Time': [random.uniform(3, 8) for _ in range(30)],
            'Ticket Volume': [random.randint(8, 15) for _ in range(30)]
        })
        
        fig = px.line(trend_data, x='Date', y=['Compliance', 'Resolution Time', 'Ticket Volume'],
                     title='30-Day Performance Trends',
                     markers=True)
        
        fig.update_layout(
            yaxis_title="Value",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def show_report_insights(self):
        """Display AI-generated insights"""
        st.subheader("AI-Generated Insights")
        
        insights = [
            {
                "insight": "🚨 **Critical Pattern Detected**",
                "description": "65% of SLA breaches occur on Monday mornings between 9-11 AM",
                "confidence": "92%",
                "impact": "High"
            },
            {
                "insight": "📊 **Strong Correlation Found**",
                "description": "Longer first response times (>2h) correlate with 40% lower customer satisfaction",
                "confidence": "88%",
                "impact": "Medium"
            },
            {
                "insight": "💡 **Optimization Opportunity**",
                "description": "Automated responses could reduce resolution time by 15% for P3/P4 tickets",
                "confidence": "85%",
                "impact": "High"
            },
            {
                "insight": "👥 **Resource Alert**",
                "description": "Team C shows 35% higher workload than capacity, affecting SLA compliance",
                "confidence": "94%",
                "impact": "Medium"
            },
            {
                "insight": "🔄 **Process Improvement**",
                "description": "Implementing SLA checkpoints at 50% and 75% of deadline could prevent 30% of breaches",
                "confidence": "79%",
                "impact": "High"
            }
        ]
        
        for insight in insights:
            with st.expander(f"{insight['insight']} (Confidence: {insight['confidence']})"):
                st.write(insight['description'])
                st.write(f"**Impact:** {insight['impact']}")
                
                if insight['impact'] == "High":
                    st.error("⚠️ Requires immediate attention")
                elif insight['impact'] == "Medium":
                    st.warning("📋 Schedule for review")
                else:
                    st.info("📝 Monitor for changes")

def main():
    app = StreamlitSLAApp()
    app.run()

if __name__ == "__main__":
    import time
    main()
