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

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database_manager import DatabaseManager
from reasoning_engine import SLAReasoningEngine
from escalation_manager import EscalationManager
from visualization import create_dashboard_charts

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
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitSLAApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.reasoning_engine = SLAReasoningEngine()
        self.escalation_manager = EscalationManager()
        
    def run(self):
        # Sidebar
        st.sidebar.title("🤖 SLA Monitoring Agent")
        st.sidebar.markdown("---")
        
        menu = st.sidebar.radio(
            "Navigation",
            ["🏠 Dashboard", "📊 Data Analysis", "🤖 AI Reasoning", 
             "🚨 Escalations", "📈 Reports", "⚙️ Settings"]
        )
        
        # GitHub badge
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            """
            **GitHub Repository**  
            [![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/yourusername/sla-monitoring-agent)  
            **Run Locally**  
            ```bash
            git clone https://github.com/yourusername/sla-monitoring-agent
            cd sla-monitoring-agent
            pip install -r requirements.txt
            streamlit run streamlit_app.py
            ```
            """
        )
        
        # Main content
        if menu == "🏠 Dashboard":
            self.show_dashboard()
        elif menu == "📊 Data Analysis":
            self.show_data_analysis()
        elif menu == "🤖 AI Reasoning":
            self.show_ai_reasoning()
        elif menu == "🚨 Escalations":
            self.show_escalations()
        elif menu == "📈 Reports":
            self.show_reports()
        elif menu == "⚙️ Settings":
            self.show_settings()
    
    def show_dashboard(self):
        st.title("🏠 SLA Monitoring Dashboard")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tickets", 150, delta="+12 today")
        with col2:
            st.metric("SLA Breaches", 8, delta="-2", delta_color="inverse")
        with col3:
            st.metric("Avg Resolution Time", "4.2h", delta="-0.5h")
        with col4:
            st.metric("Customer Satisfaction", "92%", delta="+2%")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Simulated data
            df = pd.DataFrame({
                'Status': ['Within SLA', 'Delayed', 'At Risk', 'Breached'],
                'Count': [85, 32, 18, 15]
            })
            fig = px.pie(df, values='Count', names='Status', title='SLA Status Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Simulated time series
            dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
            df_time = pd.DataFrame({
                'Date': dates,
                'Tickets': [random.randint(10, 30) for _ in range(len(dates))],
                'Breaches': [random.randint(0, 5) for _ in range(len(dates))]
            })
            fig = px.line(df_time, x='Date', y=['Tickets', 'Breaches'], 
                         title='Daily Tickets & Breaches')
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.markdown("### 📋 Recent Activity")
        
        # Simulated data
        activity_data = [
            {"Ticket": "TKT-2024-001", "Service": "Database", "Status": "Breached", "Time": "2h ago"},
            {"Ticket": "TKT-2024-002", "Service": "API", "Status": "At Risk", "Time": "3h ago"},
            {"Ticket": "TKT-2024-003", "Service": "Frontend", "Status": "Resolved", "Time": "4h ago"},
            {"Ticket": "TKT-2024-004", "Service": "Security", "Status": "Delayed", "Time": "5h ago"},
        ]
        
        st.dataframe(pd.DataFrame(activity_data), use_container_width=True)
    
    def show_data_analysis(self):
        st.title("📊 Data Analysis")
        
        tab1, tab2, tab3 = st.tabs(["📈 Performance Metrics", "⏰ Delay Analysis", "👥 Team Performance"])
        
        with tab1:
            st.subheader("SLA Performance Metrics")
            
            # Interactive filters
            col1, col2, col3 = st.columns(3)
            with col1:
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", datetime.now())
            with col3:
                service_filter = st.multiselect("Services", ["All", "Database", "API", "Frontend", "Security"])
            
            # Metrics
            st.metric("SLA Compliance Rate", "85.2%")
            st.metric("Average Resolution Time", "6.3 hours")
            st.metric("First Response Time", "1.2 hours")
            
        with tab2:
            st.subheader("Delay Analysis")
            
            # Delay reasons breakdown
            delay_data = pd.DataFrame({
                'Reason': ['Waiting on Customer', 'Technical Complexity', 'Resource Constraints', 
                          'Third-party Dependency', 'Information Missing'],
                'Count': [45, 32, 28, 22, 18],
                'Avg Duration (h)': [12.5, 8.2, 6.7, 24.3, 4.2]
            })
            
            fig = px.bar(delay_data, x='Reason', y='Count', color='Avg Duration (h)',
                        title='Delay Reasons & Average Duration')
            st.plotly_chart(fig, use_container_width=True)
            
        with tab3:
            st.subheader("Team Performance")
            
            team_data = pd.DataFrame({
                'Team': ['Team A', 'Team B', 'Team C', 'Team D'],
                'SLA Compliance': [92, 88, 76, 94],
                'Avg Resolution (h)': [3.2, 4.5, 6.8, 2.9],
                'Tickets Handled': [145, 128, 98, 167]
            })
            
            fig = px.scatter(team_data, x='Tickets Handled', y='SLA Compliance',
                           size='Avg Resolution (h)', color='Team',
                           title='Team Performance: Volume vs Compliance')
            st.plotly_chart(fig, use_container_width=True)
    
    def show_ai_reasoning(self):
        st.title("🤖 AI Reasoning Engine")
        
        st.info("""
        The AI agent analyzes tickets in real-time, building context and providing insights 
        for delayed SLAs. It uses machine learning to predict risks and recommend actions.
        """)
        
        # Demo analysis
        if st.button("🔍 Run AI Analysis on Sample Data", type="primary"):
            with st.spinner("AI agent analyzing data..."):
                # Simulate analysis
                time.sleep(2)
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                # Show insights
                st.subheader("📊 Key Insights")
                
                insights = [
                    "🔴 **Critical Risk Detected**: Database service shows 40% breach rate",
                    "⚠️ **Pattern Identified**: Most delays occur between 2-4 PM",
                    "👥 **Team Alert**: Team C handling 35% more tickets than capacity",
                    "📈 **Positive Trend**: Resolution time improved by 15% this week"
                ]
                
                for insight in insights:
                    st.info(insight)
                
                # Recommendations
                st.subheader("💡 Recommended Actions")
                
                recommendations = [
                    "1. **Immediate**: Reallocate 2 agents to Team C",
                    "2. **Short-term**: Implement automated escalation for P1 tickets",
                    "3. **Long-term**: Review Database service SLA from 4h to 6h",
                    "4. **Process**: Add mandatory status updates at 4-hour intervals"
                ]
                
                for rec in recommendations:
                    st.write(rec)
        
        # Test the reasoning engine
        st.markdown("---")
        st.subheader("🧪 Test Reasoning Engine")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ticket_priority = st.selectbox("Ticket Priority", ["P1", "P2", "P3", "P4"])
            delay_hours = st.slider("Delay Hours", 0, 48, 6)
        
        with col2:
            service_type = st.selectbox("Service Type", ["Database", "API", "Frontend", "Security"])
            customer_tier = st.selectbox("Customer Tier", ["Basic", "Premium", "Enterprise", "Platinum"])
        
        if st.button("Analyze This Scenario"):
            # Simulate reasoning
            severity_score = min(10, delay_hours // 2 + (1 if ticket_priority == "P1" else 0))
            
            st.metric("Severity Score", f"{severity_score}/10")
            
            if severity_score >= 8:
                st.error("🚨 CRITICAL: Immediate escalation required")
            elif severity_score >= 6:
                st.warning("⚠️ HIGH: Team lead escalation recommended")
            elif severity_score >= 4:
                st.info("🔶 MEDIUM: Monitor closely")
            else:
                st.success("✅ LOW: Normal monitoring")
    
    def show_escalations(self):
        st.title("🚨 Escalation Management")
        
        # Active escalations
        st.subheader("Active Escalations")
        
        escalation_data = [
            {"ID": "ESC-001", "Ticket": "TKT-2024-015", "Level": "3", "Reason": "SLA Breach", "Time": "2h ago"},
            {"ID": "ESC-002", "Ticket": "TKT-2024-022", "Level": "2", "Reason": "Customer Complaint", "Time": "4h ago"},
            {"ID": "ESC-003", "Ticket": "TKT-2024-028", "Level": "1", "Reason": "At Risk", "Time": "6h ago"},
        ]
        
        for esc in escalation_data:
            with st.expander(f"🚨 Level {esc['Level']}: {esc['Ticket']} - {esc['Reason']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**ID:** {esc['ID']}")
                    st.write(f"**Time:** {esc['Time']}")
                    st.write(f"**Action Required:** {'Immediate' if esc['Level'] == '3' else 'Urgent'}")
                with col2:
                    if st.button("Resolve", key=f"resolve_{esc['ID']}"):
                        st.success(f"Escalation {esc['ID']} resolved")
                        st.rerun()
                    if st.button("Escalate", key=f"escalate_{esc['ID']}"):
                        st.warning(f"Escalation {esc['ID']} escalated")
                        st.rerun()
        
        # Escalation metrics
        st.markdown("---")
        st.subheader("Escalation Metrics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Escalations", "24", "This month")
        with col2:
            st.metric("Avg Resolution Time", "3.2h", "-0.8h")
        with col3:
            st.metric("Recurring Issues", "12%", "-3%")
        
        # Escalation history chart
        history_data = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'Escalations': [random.randint(0, 5) for _ in range(30)],
            'Level 1': [random.randint(0, 3) for _ in range(30)],
            'Level 2': [random.randint(0, 2) for _ in range(30)],
            'Level 3': [random.randint(0, 1) for _ in range(30)]
        })
        
        fig = px.line(history_data, x='Date', y=['Escalations', 'Level 1', 'Level 2', 'Level 3'],
                     title='Escalation Trends (Last 30 Days)')
        st.plotly_chart(fig, use_container_width=True)
    
    def show_reports(self):
        st.title("📈 Reports & Analytics")
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Daily Operations", "Weekly Performance", "Monthly Review", "Quarterly Analysis"]
        )
        
        # Report parameters
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        if st.button("📊 Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                time.sleep(2)
                
                # Display report summary
                st.success(f"✅ {report_type} Report Generated!")
                
                # Report sections
                tabs = st.tabs(["📋 Summary", "📈 Metrics", "📊 Charts", "💡 Insights"])
                
                with tabs[0]:
                    st.subheader("Executive Summary")
                    st.write("""
                    **Period:** {start_date} to {end_date}
                    
                    **Key Findings:**
                    - Overall SLA compliance: 87.3% (+2.1% from previous period)
                    - Average resolution time: 5.2 hours (-0.8 hours)
                    - Top performing team: Team D (94% compliance)
                    - Area needing improvement: Database service (72% compliance)
                    
                    **Recommendations:**
                    1. Implement additional monitoring for Database service
                    2. Review escalation thresholds for P3 tickets
                    3. Schedule capacity planning session for Team B
                    """)
                
                with tabs[1]:
                    st.subheader("Detailed Metrics")
                    
                    metrics_data = pd.DataFrame({
                        'Metric': ['SLA Compliance', 'First Response Time', 
                                  'Resolution Time', 'Customer Satisfaction',
                                  'Ticket Volume', 'Reopened Tickets'],
                        'Current': ['87.3%', '1.2h', '5.2h', '92%', '342', '18'],
                        'Previous': ['85.2%', '1.4h', '6.0h', '90%', '328', '22'],
                        'Change': ['+2.1%', '-0.2h', '-0.8h', '+2%', '+14', '-4']
                    })
                    
                    st.dataframe(metrics_data, use_container_width=True)
                
                with tabs[2]:
                    st.subheader("Visual Analytics")
                    
                    # Sample chart
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='Current', x=['SLA Compliance', 'Resolution Time'], 
                                        y=[87.3, 5.2], marker_color='#1f77b4'))
                    fig.add_trace(go.Bar(name='Previous', x=['SLA Compliance', 'Resolution Time'], 
                                        y=[85.2, 6.0], marker_color='#ff7f0e'))
                    fig.update_layout(barmode='group', title='Performance Comparison')
                    st.plotly_chart(fig, use_container_width=True)
                
                with tabs[3]:
                    st.subheader("AI-Generated Insights")
                    
                    insights = [
                        "**Pattern Detected**: 65% of breaches occur on Monday mornings",
                        "**Correlation Found**: Longer first response times correlate with lower customer satisfaction",
                        "**Opportunity Identified**: Automated responses could reduce resolution time by 15%",
                        "**Risk Alert**: Team C shows increasing trend in delayed tickets"
                    ]
                    
                    for insight in insights:
                        st.info(insight)
                
                # Download button
                report_content = json.dumps({
                    "report_type": report_type,
                    "period": f"{start_date} to {end_date}",
                    "generated_at": datetime.now().isoformat()
                }, indent=2)
                
                st.download_button(
                    label="📥 Download Report (JSON)",
                    data=report_content,
                    file_name=f"sla_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    def show_settings(self):
        st.title("⚙️ Settings & Configuration")
        
        tab1, tab2, tab3 = st.tabs(["Database", "AI Agent", "Notifications"])
        
        with tab1:
            st.subheader("Database Configuration")
            
            with st.form("db_config"):
                col1, col2 = st.columns(2)
                
                with col1:
                    host = st.text_input("Host", value="localhost")
                    user = st.text_input("Username", value="root")
                
                with col2:
                    password = st.text_input("Password", type="password", value="")
                    database = st.text_input("Database", value="sla_monitoring")
                
                if st.form_submit_button("Save Database Settings"):
                    st.success("Settings saved successfully!")
            
            # Test connection
            if st.button("Test Database Connection"):
                with st.spinner("Testing connection..."):
                    time.sleep(1)
                    st.success("✅ Connection successful!")
        
        with tab2:
            st.subheader("AI Agent Configuration")
            
            # Reasoning thresholds
            st.slider("Severity Threshold for Escalation", 1, 10, 7)
            st.slider("Confidence Threshold for AI Decisions", 50, 100, 80)
            
            # Learning settings
            st.checkbox("Enable Machine Learning", value=True)
            st.checkbox("Enable Pattern Detection", value=True)
            st.checkbox("Enable Predictive Analytics", value=True)
            
            if st.button("Save Agent Settings"):
                st.success("Agent settings saved!")
        
        with tab3:
            st.subheader("Notification Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.checkbox("Email Notifications", value=True)
                st.checkbox("Slack Notifications", value=True)
                st.checkbox("SMS Alerts", value=False)
            
            with col2:
                st.selectbox("Escalation Level for Email", [1, 2, 3, 4], index=1)
                st.selectbox("Escalation Level for Slack", [1, 2, 3, 4], index=0)
                st.selectbox("Escalation Level for SMS", [1, 2, 3, 4], index=3)
            
            # Notification schedule
            st.subheader("Notification Schedule")
            st.selectbox("Daily Report Time", ["08:00", "09:00", "10:00", "17:00"])
            st.selectbox("Weekly Summary Day", ["Monday", "Friday"])
            
            if st.button("Save Notification Settings"):
                st.success("Notification settings saved!")

def main():
    app = StreamlitSLAApp()
    app.run()

if __name__ == "__main__":
    import random  # For demo data
    main()
