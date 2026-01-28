#!/usr/bin/env python3
"""
Streamlit App for SLA Monitoring Agent
Run with: streamlit run sla_streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import sys
import subprocess
import time
from typing import Dict, List, Optional
import random

# Set page config
st.set_page_config(
    page_title="SLA Monitoring AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .stButton > button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 10px;
    }
    .critical {
        border-left-color: #ff4b4b !important;
        background-color: #ffe6e6 !important;
    }
    .warning {
        border-left-color: #ffa500 !important;
        background-color: #fff3cd !important;
    }
    .success {
        border-left-color: #00cc96 !important;
        background-color: #e6f7f0 !important;
    }
</style>
""", unsafe_allow_html=True)

class DatabaseManager:
    """Database connection and operations"""
    
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': st.secrets.get("DB_PASSWORD", "") if hasattr(st, 'secrets') else "",
            'database': 'sla_monitoring_test'
        }
    
    def connect(self):
        try:
            conn = mysql.connector.connect(**self.config)
            return conn
        except Error as e:
            st.error(f"Database connection failed: {e}")
            return None
    
    def execute_query(self, query, params=None):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                conn.close()
                return results
            except Error as e:
                st.error(f"Query execution failed: {e}")
                return []
        return []
    
    def execute_update(self, query, params=None):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Error as e:
                st.error(f"Update failed: {e}")
                return False
        return False

class SLAReasoningEngine:
    """AI Reasoning Engine for SLA Analysis"""
    
    def analyze_ticket(self, ticket_data, delays=None):
        """Analyze a single ticket"""
        severity = self._calculate_severity(ticket_data, delays or [])
        
        insights = []
        if ticket_data['sla_status'] == 'breached':
            insights.append(f"🚨 **CRITICAL**: SLA breached for {ticket_data.get('service_name', 'service')}")
        elif ticket_data['sla_status'] == 'at_risk':
            time_to_deadline = self._get_hours_to_deadline(ticket_data['resolution_deadline'])
            insights.append(f"⚠️ **AT RISK**: {time_to_deadline:.1f} hours to deadline")
        elif ticket_data['sla_status'] == 'delayed':
            insights.append(f"🔶 **DELAYED**: {ticket_data.get('delay_minutes', 0)} minutes overdue")
        
        return {
            'severity': severity,
            'insights': insights,
            'actions': self._get_recommended_actions(severity, ticket_data),
            'needs_escalation': severity >= 7
        }
    
    def _calculate_severity(self, ticket_data, delays):
        """Calculate severity score (1-10)"""
        score = 0
        
        # Priority factor
        priority_scores = {'P1': 4, 'P2': 3, 'P3': 2, 'P4': 1}
        score += priority_scores.get(ticket_data['priority'], 2)
        
        # SLA status factor
        status_scores = {'breached': 4, 'at_risk': 3, 'delayed': 2, 'within_sla': 0}
        score += status_scores.get(ticket_data['sla_status'], 0)
        
        # Delay factor
        delay_minutes = ticket_data.get('delay_minutes', 0)
        if delay_minutes > 240:
            score += 2
        elif delay_minutes > 60:
            score += 1
            
        return min(score, 10)
    
    def _get_hours_to_deadline(self, deadline):
        """Calculate hours to deadline"""
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(str(deadline).replace('Z', '+00:00'))
        now = datetime.now()
        return max(0, (deadline - now).total_seconds() / 3600)
    
    def _get_recommended_actions(self, severity, ticket_data):
        """Get recommended actions based on severity"""
        actions = []
        
        if severity >= 8:
            actions.extend([
                "🚨 IMMEDIATE: Escalate to team lead and manager",
                "📞 Contact customer with status update",
                "🔄 Assign additional resources"
            ])
        elif severity >= 6:
            actions.extend([
                "⚠️ URGENT: Review with assigned agent",
                "📋 Check for blockers and dependencies",
                "⏰ Set follow-up reminder for 2 hours"
            ])
        elif severity >= 4:
            actions.extend([
                "🔍 Review ticket progress",
                "📝 Update customer on status",
                "⏰ Set reminder for next check"
            ])
        
        return actions

class StreamlitSLAApp:
    """Main Streamlit Application"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.reasoning_engine = SLAReasoningEngine()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'setup_complete' not in st.session_state:
            st.session_state.setup_complete = False
        if 'analysis_run' not in st.session_state:
            st.session_state.analysis_run = False
        if 'ticket_data' not in st.session_state:
            st.session_state.ticket_data = None
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
    
    def run(self):
        """Main application runner"""
        
        # Sidebar navigation
        st.sidebar.title("🤖 SLA Monitoring Agent")
        
        menu = st.sidebar.selectbox(
            "Navigation",
            ["🏠 Dashboard", "🔧 Setup Database", "📊 Data Analysis", 
             "🤖 AI Reasoning", "📈 Reports", "⚙️ Settings"]
        )
        
        st.sidebar.markdown("---")
        st.sidebar.info(
            "**SLA Monitoring AI Agent**\n\n"
            "Test context building, reasoning, and escalation workflows "
            "for delayed SLAs with focused insights."
        )
        
        # Main content based on menu selection
        if menu == "🏠 Dashboard":
            self.show_dashboard()
        elif menu == "🔧 Setup Database":
            self.show_setup()
        elif menu == "📊 Data Analysis":
            self.show_data_analysis()
        elif menu == "🤖 AI Reasoning":
            self.show_ai_reasoning()
        elif menu == "📈 Reports":
            self.show_reports()
        elif menu == "⚙️ Settings":
            self.show_settings()
    
    def show_dashboard(self):
        """Display main dashboard"""
        st.title("🏠 SLA Monitoring Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.display_metric_card(
                "Total Tickets", 
                self.get_total_tickets(), 
                "📋"
            )
        
        with col2:
            delayed = self.get_delayed_tickets()
            self.display_metric_card(
                "Delayed Tickets", 
                f"{delayed}",
                "⚠️",
                "warning" if delayed > 10 else "success"
            )
        
        with col3:
            breached = self.get_breached_tickets()
            self.display_metric_card(
                "SLA Breaches", 
                f"{breached}",
                "🚨",
                "critical" if breached > 5 else "success"
            )
        
        with col4:
            active_esc = self.get_active_escalations()
            self.display_metric_card(
                "Active Escalations", 
                f"{active_esc}",
                "📤",
                "warning" if active_esc > 3 else "success"
            )
        
        st.markdown("---")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self.display_sla_status_chart()
        
        with col2:
            self.display_priority_chart()
        
        # Recent tickets
        st.markdown("### 📋 Recent Delayed Tickets")
        recent_tickets = self.get_recent_tickets(limit=10)
        if recent_tickets:
            df = pd.DataFrame(recent_tickets)
            st.dataframe(df[['ticket_id', 'ticket_title', 'priority', 'sla_status', 'assigned_team']])
        else:
            st.info("No tickets found. Please set up the database first.")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🤖 Run AI Analysis", use_container_width=True):
                st.session_state.analysis_run = False  # Reset to trigger analysis
                st.switch_page("🤖 AI Reasoning")
        
        with col3:
            if st.button("📊 Generate Report", use_container_width=True):
                st.switch_page("📈 Reports")
    
    def display_metric_card(self, title, value, icon, status="normal"):
        """Display a metric card"""
        status_class = {
            "normal": "",
            "success": "success",
            "warning": "warning",
            "critical": "critical"
        }.get(status, "")
        
        html = f"""
        <div class="metric-card {status_class}">
            <h3 style="margin: 0; color: #666; font-size: 14px;">{title}</h3>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <span style="font-size: 24px; margin-right: 10px;">{icon}</span>
                <span style="font-size: 32px; font-weight: bold;">{value}</span>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
    
    def display_sla_status_chart(self):
        """Display SLA status distribution chart"""
        query = """
        SELECT sla_status, COUNT(*) as count 
        FROM tickets 
        GROUP BY sla_status
        """
        data = self.db.execute_query(query)
        
        if data:
            df = pd.DataFrame(data)
            fig = px.pie(
                df, 
                values='count', 
                names='sla_status',
                title='SLA Status Distribution',
                color='sla_status',
                color_discrete_map={
                    'within_sla': '#00cc96',
                    'delayed': '#ffa500',
                    'at_risk': '#ff6b6b',
                    'breached': '#ff4b4b'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for SLA status chart")
    
    def display_priority_chart(self):
        """Display priority distribution chart"""
        query = """
        SELECT priority, sla_status, COUNT(*) as count 
        FROM tickets 
        GROUP BY priority, sla_status
        """
        data = self.db.execute_query(query)
        
        if data:
            df = pd.DataFrame(data)
            fig = px.bar(
                df,
                x='priority',
                y='count',
                color='sla_status',
                title='Tickets by Priority & SLA Status',
                barmode='stack',
                color_discrete_map={
                    'within_sla': '#00cc96',
                    'delayed': '#ffa500',
                    'at_risk': '#ff6b6b',
                    'breached': '#ff4b4b'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for priority chart")
    
    def show_setup(self):
        """Display database setup interface"""
        st.title("🔧 Database Setup")
        
        st.info(
            "This will create a test database with sample SLA data including "
            "delayed portions with success, failure, and pending statuses."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Quick Setup")
            if st.button("🚀 Run Quick Setup", type="primary", use_container_width=True):
                with st.spinner("Setting up test database..."):
                    success = self.run_quick_setup()
                    if success:
                        st.session_state.setup_complete = True
                        st.success("✅ Database setup completed successfully!")
                        st.rerun()
        
        with col2:
            st.markdown("### Manual Setup")
            with st.expander("Show SQL Commands"):
                st.code("""
                -- Create database
                CREATE DATABASE sla_monitoring_test;
                
                -- Create tables
                CREATE TABLE services (
                    service_id INT PRIMARY KEY AUTO_INCREMENT,
                    service_name VARCHAR(100) NOT NULL,
                    default_sla_hours INT DEFAULT 24
                );
                
                -- ... (full schema from earlier)
                """, language="sql")
        
        st.markdown("---")
        st.markdown("### Database Status")
        
        # Check if database exists
        status_query = """
        SELECT 
            (SELECT COUNT(*) FROM tickets) as ticket_count,
            (SELECT COUNT(*) FROM sla_delays) as delay_count,
            (SELECT COUNT(*) FROM escalations) as escalation_count
        """
        
        try:
            results = self.db.execute_query("SELECT 1")
            if results:
                st.success("✅ Database connection successful")
                
                # Get counts
                counts = self.db.execute_query(status_query)
                if counts:
                    count_data = counts[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tickets", count_data['ticket_count'] or 0)
                    with col2:
                        st.metric("Delayed Portions", count_data['delay_count'] or 0)
                    with col3:
                        st.metric("Escalations", count_data['escalation_count'] or 0)
                else:
                    st.warning("⚠️ Database is empty. Run quick setup to populate data.")
            else:
                st.error("❌ Database connection failed")
        except:
            st.error("❌ Cannot connect to database")
    
    def run_quick_setup(self):
        """Run quick database setup"""
        try:
            # First, try to install mysql-connector if not present
            try:
                import mysql.connector
            except ImportError:
                st.warning("Installing mysql-connector-python...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
            
            # Create database
            temp_config = self.config.copy()
            temp_config['database'] = None  # Connect without database
            
            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS sla_monitoring_test")
            cursor.execute("USE sla_monitoring_test")
            
            # Create tables
            tables_sql = self._get_table_schema()
            for sql in tables_sql:
                cursor.execute(sql)
            
            # Insert sample data
            self._insert_sample_data(cursor)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Setup failed: {str(e)}")
            return False
    
    def _get_table_schema(self):
        """Return table creation SQL"""
        return [
            """
            CREATE TABLE IF NOT EXISTS services (
                service_id INT PRIMARY KEY AUTO_INCREMENT,
                service_name VARCHAR(100) NOT NULL,
                default_sla_hours INT DEFAULT 24
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id VARCHAR(50) PRIMARY KEY,
                ticket_title VARCHAR(500) NOT NULL,
                service_id INT,
                priority VARCHAR(10),
                status VARCHAR(20),
                creation_time DATETIME NOT NULL,
                resolution_deadline DATETIME NOT NULL,
                actual_resolution_time DATETIME,
                assigned_team VARCHAR(100),
                sla_status VARCHAR(20),
                delay_minutes INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sla_delays (
                delay_id INT PRIMARY KEY AUTO_INCREMENT,
                ticket_id VARCHAR(50) NOT NULL,
                delay_type VARCHAR(30),
                delay_start DATETIME NOT NULL,
                delay_end DATETIME,
                delay_duration_minutes INT,
                delay_status VARCHAR(20),
                impact_score INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id INT PRIMARY KEY AUTO_INCREMENT,
                ticket_id VARCHAR(50) NOT NULL,
                escalation_level INT,
                escalation_reason TEXT,
                escalation_time DATETIME NOT NULL,
                escalation_status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    
    def _insert_sample_data(self, cursor):
        """Insert sample test data"""
        # Insert services
        services = [
            ('Database Support', 4),
            ('API Monitoring', 8),
            ('Frontend UI', 24),
            ('Security Incident', 2),
            ('Payment Gateway', 1)
        ]
        cursor.executemany(
            "INSERT INTO services (service_name, default_sla_hours) VALUES (%s, %s)",
            services
        )
        
        # Insert tickets with various statuses
        teams = ['Team_A', 'Team_B', 'Team_C']
        priorities = ['P1', 'P2', 'P3']
        statuses = ['new', 'in_progress', 'pending', 'resolved', 'failed']
        sla_statuses = ['within_sla', 'delayed', 'at_risk', 'breached']
        
        for i in range(50):  # Create 50 tickets
            creation_time = datetime.now() - timedelta(hours=random.randint(1, 168))
            sla_hours = random.choice([4, 8, 24, 48])
            resolution_deadline = creation_time + timedelta(hours=sla_hours)
            
            sla_status = random.choices(
                sla_statuses,
                weights=[40, 25, 20, 15]  # Weighted distribution
            )[0]
            
            # Generate ticket
            ticket_id = f"TKT-{creation_time.strftime('%Y%m%d')}-{1000+i}"
            
            cursor.execute("""
                INSERT INTO tickets 
                (ticket_id, ticket_title, service_id, priority, status, 
                 creation_time, resolution_deadline, actual_resolution_time,
                 assigned_team, sla_status, delay_minutes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_id,
                f"Test Issue {i+1} - {random.choice(['Performance', 'Error', 'Access'])}",
                random.randint(1, 5),
                random.choice(priorities),
                random.choice(statuses),
                creation_time,
                resolution_deadline,
                None if sla_status != 'within_sla' else creation_time + timedelta(hours=random.uniform(1, sla_hours*0.8)),
                random.choice(teams),
                sla_status,
                random.randint(0, 480) if sla_status != 'within_sla' else 0
            ))
            
            # Add delays for delayed/at-risk/breached tickets
            if sla_status in ['delayed', 'at_risk', 'breached'] and random.random() > 0.4:
                self._insert_sample_delays(cursor, ticket_id, creation_time, resolution_deadline)
                
            # Add escalations for some tickets
            if sla_status in ['breached', 'at_risk'] and random.random() > 0.6:
                self._insert_sample_escalations(cursor, ticket_id, creation_time)
    
    def _insert_sample_delays(self, cursor, ticket_id, creation_time, deadline):
        """Insert sample delays with various statuses"""
        delay_types = ['response', 'resolution', 'customer_waiting', 'internal']
        delay_statuses = ['pending', 'in_progress', 'resolved', 'failed']  # All status types
        
        num_delays = random.randint(1, 3)
        for _ in range(num_delays):
            delay_start = creation_time + timedelta(hours=random.randint(1, int((deadline - creation_time).total_seconds()/3600)-1))
            delay_duration = random.randint(30, 240)
            delay_end = delay_start + timedelta(minutes=delay_duration)
            
            # Randomly assign status
            delay_status = random.choice(delay_statuses)
            
            cursor.execute("""
                INSERT INTO sla_delays 
                (ticket_id, delay_type, delay_start, delay_end, 
                 delay_duration_minutes, delay_status, impact_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_id,
                random.choice(delay_types),
                delay_start,
                delay_end,
                delay_duration,
                delay_status,
                random.randint(1, 10)
            ))
    
    def _insert_sample_escalations(self, cursor, ticket_id, creation_time):
        """Insert sample escalations"""
        escalation_time = creation_time + timedelta(hours=random.randint(1, 12))
        
        cursor.execute("""
            INSERT INTO escalations 
            (ticket_id, escalation_level, escalation_reason, 
             escalation_time, escalation_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            ticket_id,
            random.randint(1, 4),
            random.choice(['SLA breach', 'Customer complaint', 'Technical blocker']),
            escalation_time,
            random.choice(['active', 'resolved', 'pending'])
        ))
    
    def show_data_analysis(self):
        """Display data analysis interface"""
        st.title("📊 Data Analysis")
        
        # Analysis options
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["SLA Performance", "Delayed Portions", "Escalation Patterns", "Team Performance"]
        )
        
        if analysis_type == "SLA Performance":
            self.show_sla_performance_analysis()
        elif analysis_type == "Delayed Portions":
            self.show_delayed_portions_analysis()
        elif analysis_type == "Escalation Patterns":
            self.show_escalation_analysis()
        elif analysis_type == "Team Performance":
            self.show_team_performance_analysis()
    
    def show_sla_performance_analysis(self):
        """Display SLA performance analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            # SLA compliance over time
            query = """
            SELECT 
                DATE(creation_time) as date,
                COUNT(*) as total,
                SUM(CASE WHEN sla_status = 'within_sla' THEN 1 ELSE 0 END) as within_sla,
                ROUND(SUM(CASE WHEN sla_status = 'within_sla' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as compliance_rate
            FROM tickets
            WHERE creation_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(creation_time)
            ORDER BY date
            """
            
            data = self.db.execute_query(query)
            if data:
                df = pd.DataFrame(data)
                fig = px.line(
                    df, 
                    x='date', 
                    y='compliance_rate',
                    title='SLA Compliance Rate (Last 7 Days)',
                    markers=True
                )
                fig.update_layout(yaxis_title="Compliance Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Breach reasons
            query = """
            SELECT 
                e.escalation_reason,
                COUNT(*) as count
            FROM escalations e
            JOIN tickets t ON e.ticket_id = t.ticket_id
            WHERE t.sla_status = 'breached'
            GROUP BY e.escalation_reason
            ORDER BY count DESC
            LIMIT 10
            """
            
            data = self.db.execute_query(query)
            if data:
                df = pd.DataFrame(data)
                fig = px.bar(
                    df,
                    x='escalation_reason',
                    y='count',
                    title='Top Breach Reasons',
                    color='count',
                    color_continuous_scale='reds'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed SLA metrics
        st.markdown("### 📈 Detailed SLA Metrics")
        
        metrics_query = """
        SELECT 
            sla_status,
            COUNT(*) as ticket_count,
            AVG(delay_minutes) as avg_delay_minutes,
            MIN(delay_minutes) as min_delay,
            MAX(delay_minutes) as max_delay,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tickets), 2) as percentage
        FROM tickets
        GROUP BY sla_status
        ORDER BY FIELD(sla_status, 'breached', 'at_risk', 'delayed', 'within_sla')
        """
        
        metrics = self.db.execute_query(metrics_query)
        if metrics:
            df_metrics = pd.DataFrame(metrics)
            st.dataframe(
                df_metrics.style.format({
                    'avg_delay_minutes': '{:.1f}',
                    'percentage': '{:.1f}%'
                }).apply(
                    lambda x: ['background-color: #ffe6e6' if x['sla_status'] == 'breached' else 
                              'background-color: #fff3cd' if x['sla_status'] == 'at_risk' else
                              'background-color: #fff8e6' if x['sla_status'] == 'delayed' else
                              'background-color: #e6f7f0' for _ in x],
                    axis=1
                ),
                use_container_width=True
            )
    
    def show_delayed_portions_analysis(self):
        """Display delayed portions analysis"""
        st.markdown("### ⏰ Delayed Portions Analysis")
        
        # Status distribution
        query = """
        SELECT 
            delay_status,
            COUNT(*) as count,
            AVG(delay_duration_minutes) as avg_duration,
            AVG(impact_score) as avg_impact,
            MIN(delay_duration_minutes) as min_duration,
            MAX(delay_duration_minutes) as max_duration
        FROM sla_delays
        GROUP BY delay_status
        ORDER BY count DESC
        """
        
        data = self.db.execute_query(query)
        if data:
            df = pd.DataFrame(data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    df,
                    values='count',
                    names='delay_status',
                    title='Delay Status Distribution',
                    color='delay_status',
                    color_discrete_map={
                        'pending': '#ffa500',
                        'in_progress': '#1f77b4',
                        'resolved': '#00cc96',
                        'failed': '#ff4b4b'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    df,
                    x='delay_status',
                    y='avg_duration',
                    title='Average Delay Duration by Status',
                    color='delay_status',
                    color_discrete_map={
                        'pending': '#ffa500',
                        'in_progress': '#1f77b4',
                        'resolved': '#00cc96',
                        'failed': '#ff4b4b'
                    }
                )
                fig.update_layout(yaxis_title="Average Duration (minutes)")
                st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed data
            st.markdown("### 📋 Delayed Portions Details")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                delay_status_filter = st.multiselect(
                    "Filter by Status",
                    options=df['delay_status'].unique().tolist(),
                    default=df['delay_status'].unique().tolist()
                )
            
            with col2:
                min_impact = st.slider("Minimum Impact Score", 1, 10, 1)
            
            with col3:
                min_duration = st.slider("Minimum Duration (min)", 0, 480, 0)
            
            # Query filtered data
            status_conditions = ", ".join([f"'{s}'" for s in delay_status_filter]) if delay_status_filter else "''"
            
            details_query = f"""
            SELECT 
                d.*,
                t.ticket_title,
                t.priority,
                t.sla_status as ticket_sla_status
            FROM sla_delays d
            JOIN tickets t ON d.ticket_id = t.ticket_id
            WHERE d.delay_status IN ({status_conditions})
                AND d.impact_score >= {min_impact}
                AND d.delay_duration_minutes >= {min_duration}
            ORDER BY d.impact_score DESC, d.delay_duration_minutes DESC
            LIMIT 100
            """
            
            details = self.db.execute_query(details_query)
            if details:
                df_details = pd.DataFrame(details)
                st.dataframe(
                    df_details[['ticket_id', 'ticket_title', 'delay_type', 'delay_status', 
                               'delay_duration_minutes', 'impact_score', 'priority']],
                    use_container_width=True
                )
    
    def show_escalation_analysis(self):
        """Display escalation analysis"""
        st.markdown("### 📤 Escalation Analysis")
        
        # Escalation levels
        query = """
        SELECT 
            escalation_level,
            escalation_status,
            COUNT(*) as count,
            AVG(TIMESTAMPDIFF(HOUR, escalation_time, COALESCE(resolved_time, NOW()))) as avg_hours_open
        FROM escalations
        GROUP BY escalation_level, escalation_status
        ORDER BY escalation_level, escalation_status
        """
        
        data = self.db.execute_query(query)
        if data:
            df = pd.DataFrame(data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.sunburst(
                    df,
                    path=['escalation_level', 'escalation_status'],
                    values='count',
                    title='Escalation Distribution by Level & Status',
                    color='escalation_level',
                    color_continuous_scale='reds'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                active_escalations = df[df['escalation_status'] == 'active']
                if not active_escalations.empty:
                    fig = px.bar(
                        active_escalations,
                        x='escalation_level',
                        y='avg_hours_open',
                        title='Average Hours Open for Active Escalations',
                        color='escalation_level',
                        color_continuous_scale='reds'
                    )
                    fig.update_layout(yaxis_title="Average Hours Open")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Active escalations details
            st.markdown("### 🚨 Active Escalations")
            
            active_query = """
            SELECT 
                e.*,
                t.ticket_title,
                t.priority,
                t.sla_status,
                t.assigned_team
            FROM escalations e
            JOIN tickets t ON e.ticket_id = t.ticket_id
            WHERE e.escalation_status = 'active'
            ORDER BY e.escalation_level DESC, e.escalation_time
            """
            
            active = self.db.execute_query(active_query)
            if active:
                df_active = pd.DataFrame(active)
                
                # Add action buttons
                for idx, escalation in enumerate(active[:5]):  # Show top 5
                    with st.expander(f"🚨 Level {escalation['escalation_level']}: {escalation['ticket_title']}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Ticket:** {escalation['ticket_id']}")
                            st.write(f"**Reason:** {escalation['escalation_reason']}")
                            st.write(f"**Team:** {escalation['assigned_team']}")
                            st.write(f"**Priority:** {escalation['priority']}")
                            st.write(f"**SLA Status:** {escalation['sla_status']}")
                        
                        with col2:
                            if st.button("Resolve", key=f"resolve_{idx}"):
                                self.resolve_escalation(escalation['escalation_id'])
                                st.success(f"Escalation {escalation['escalation_id']} marked as resolved")
                                st.rerun()
                            
                            if st.button("Escalate", key=f"escalate_{idx}"):
                                self.escalate_further(escalation['escalation_id'])
                                st.warning(f"Escalation {escalation['escalation_id']} escalated to next level")
                                st.rerun()
    
    def show_team_performance_analysis(self):
        """Display team performance analysis"""
        st.markdown("### 👥 Team Performance")
        
        query = """
        SELECT 
            assigned_team,
            COUNT(*) as total_tickets,
            SUM(CASE WHEN sla_status = 'breached' THEN 1 ELSE 0 END) as breached_count,
            SUM(CASE WHEN sla_status = 'within_sla' THEN 1 ELSE 0 END) as within_sla_count,
            ROUND(SUM(CASE WHEN sla_status = 'within_sla' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as sla_compliance_rate,
            AVG(delay_minutes) as avg_delay_minutes
        FROM tickets
        WHERE assigned_team IS NOT NULL
        GROUP BY assigned_team
        ORDER BY sla_compliance_rate DESC
        """
        
        data = self.db.execute_query(query)
        if data:
            df = pd.DataFrame(data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df,
                    x='assigned_team',
                    y='sla_compliance_rate',
                    title='SLA Compliance Rate by Team',
                    color='sla_compliance_rate',
                    color_continuous_scale='greens'
                )
                fig.update_layout(yaxis_title="Compliance Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(
                    df,
                    x='total_tickets',
                    y='avg_delay_minutes',
                    size='breached_count',
                    color='assigned_team',
                    title='Team Performance: Volume vs Delays',
                    hover_name='assigned_team',
                    size_max=50
                )
                fig.update_layout(
                    xaxis_title="Total Tickets",
                    yaxis_title="Average Delay (minutes)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Team comparison table
            st.markdown("### 📊 Team Performance Comparison")
            
            # Calculate additional metrics
            df['breach_rate'] = (df['breached_count'] / df['total_tickets'] * 100).round(2)
            
            # Display as styled dataframe
            st.dataframe(
                df.style.format({
                    'sla_compliance_rate': '{:.1f}%',
                    'avg_delay_minutes': '{:.1f}',
                    'breach_rate': '{:.1f}%'
                }).apply(
                    lambda x: ['background-color: #e6f7f0' if x['sla_compliance_rate'] >= 90 else
                              'background-color: #fff3cd' if x['sla_compliance_rate'] >= 70 else
                              'background-color: #ffe6e6' for _ in x],
                    axis=1
                ),
                use_container_width=True
            )
    
    def resolve_escalation(self, escalation_id):
        """Mark an escalation as resolved"""
        query = """
        UPDATE escalations 
        SET escalation_status = 'resolved', 
            resolved_time = NOW() 
        WHERE escalation_id = %s
        """
        return self.db.execute_update(query, (escalation_id,))
    
    def escalate_further(self, escalation_id):
        """Escalate to next level"""
        query = """
        UPDATE escalations 
        SET escalation_level = escalation_level + 1,
            escalation_time = NOW()
        WHERE escalation_id = %s
        """
        return self.db.execute_update(query, (escalation_id,))
    
    def show_ai_reasoning(self):
        """Display AI reasoning interface"""
        st.title("🤖 AI Reasoning Engine")
        
        st.info(
            "The AI agent analyzes tickets, builds context, reasons about delays, "
            "and determines appropriate escalation levels."
        )
        
        # Run AI analysis
        if st.button("🧠 Run AI Analysis on All Tickets", type="primary", use_container_width=True):
            with st.spinner("🤖 AI agent analyzing tickets..."):
                results = self.run_ai_analysis()
                st.session_state.analysis_results = results
                st.session_state.analysis_run = True
                st.success("✅ AI analysis completed!")
        
        if st.session_state.get('analysis_run', False) and st.session_state.get('analysis_results'):
            results = st.session_state.analysis_results
            
            # Display summary
            st.markdown("### 📊 Analysis Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_tickets = len(results['ticket_analyses'])
                st.metric("Tickets Analyzed", total_tickets)
            
            with col2:
                critical_count = sum(1 for t in results['ticket_analyses'] if t['severity'] >= 8)
                st.metric("Critical Tickets", critical_count)
            
            with col3:
                escalation_count = sum(1 for t in results['ticket_analyses'] if t['needs_escalation'])
                st.metric("Escalations Needed", escalation_count)
            
            # Severity distribution
            st.markdown("### 📈 Severity Distribution")
            
            severity_counts = {}
            for ticket in results['ticket_analyses']:
                severity = min(max(int(ticket['severity']), 1), 10)
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            severity_df = pd.DataFrame(list(severity_counts.items()), columns=['Severity', 'Count'])
            severity_df = severity_df.sort_values('Severity')
            
            fig = px.bar(
                severity_df,
                x='Severity',
                y='Count',
                title='Ticket Severity Distribution',
                color='Count',
                color_continuous_scale='reds'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed analysis
            st.markdown("### 🔍 Detailed Analysis")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                min_severity = st.slider("Minimum Severity", 1, 10, 5)
            
            with col2:
                show_escalations = st.checkbox("Show only tickets needing escalation", value=True)
            
            # Display tickets
            filtered_tickets = [
                t for t in results['ticket_analyses'] 
                if t['severity'] >= min_severity and (not show_escalations or t['needs_escalation'])
            ]
            
            for ticket in filtered_tickets[:10]:  # Show top 10
                with st.expander(f"🎯 {ticket['ticket_id']} - Severity: {ticket['severity']}/10"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Insights:**")
                        for insight in ticket['insights']:
                            st.write(f"• {insight}")
                    
                    with col2:
                        st.markdown("**Recommended Actions:**")
                        for action in ticket['actions']:
                            st.write(f"• {action}")
                    
                    if ticket['needs_escalation']:
                        st.warning(f"🚨 **Needs Escalation**: Severity {ticket['severity']}/10 requires Level {self._get_escalation_level(ticket['severity'])} escalation")
    
    def _get_escalation_level(self, severity):
        """Get escalation level based on severity"""
        if severity >= 9:
            return 3
        elif severity >= 7:
            return 2
        elif severity >= 5:
            return 1
        else:
            return 0
    
    def run_ai_analysis(self):
        """Run AI analysis on all tickets"""
        # Get tickets
        query = """
        SELECT 
            t.*,
            s.service_name
        FROM tickets t
        LEFT JOIN services s ON t.service_id = s.service_id
        WHERE t.resolution_deadline >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY t.priority DESC, t.resolution_deadline
        LIMIT 100
        """
        
        tickets = self.db.execute_query(query)
        
        # Get delays for all tickets
        ticket_ids = [t['ticket_id'] for t in tickets]
        delays_by_ticket = {}
        
        if ticket_ids:
            placeholders = ', '.join(['%s'] * len(ticket_ids))
            delays_query = f"""
            SELECT ticket_id, delay_type, delay_status, delay_duration_minutes, impact_score
            FROM sla_delays
            WHERE ticket_id IN ({placeholders})
            """
            delays = self.db.execute_query(delays_query, tuple(ticket_ids))
            
            for delay in delays:
                ticket_id = delay['ticket_id']
                if ticket_id not in delays_by_ticket:
                    delays_by_ticket[ticket_id] = []
                delays_by_ticket[ticket_id].append(delay)
        
        # Analyze each ticket
        ticket_analyses = []
        for ticket in tickets:
            delays = delays_by_ticket.get(ticket['ticket_id'], [])
            analysis = self.reasoning_engine.analyze_ticket(ticket, delays)
            analysis['ticket_id'] = ticket['ticket_id']
            analysis['ticket_title'] = ticket['ticket_title']
            analysis['priority'] = ticket['priority']
            analysis['sla_status'] = ticket['sla_status']
            ticket_analyses.append(analysis)
        
        return {
            'ticket_analyses': ticket_analyses,
            'total_tickets': len(tickets),
            'analysis_time': datetime.now().isoformat()
        }
    
    def show_reports(self):
        """Display reports interface"""
        st.title("📈 Reports")
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Daily Operations", "SLA Performance", "Escalation Summary", "Team Performance"]
        )
        
        date_range = st.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now()
        )
        
        if st.button("📊 Generate Report", type="primary"):
            with st.spinner(f"Generating {report_type} report..."):
                report = self.generate_report(report_type, date_range)
                
                # Display report
                st.markdown(f"### 📋 {report_type} Report")
                st.json(report)  # Simplified display
                
                # Download button
                report_json = json.dumps(report, indent=2, default=str)
                st.download_button(
                    label="📥 Download Report (JSON)",
                    data=report_json,
                    file_name=f"{report_type.lower().replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
    
    def generate_report(self, report_type, date_range):
        """Generate a report"""
        start_date, end_date = date_range
        
        if report_type == "Daily Operations":
            return self.generate_daily_operations_report(start_date, end_date)
        elif report_type == "SLA Performance":
            return self.generate_sla_performance_report(start_date, end_date)
        elif report_type == "Escalation Summary":
            return self.generate_escalation_report(start_date, end_date)
        elif report_type == "Team Performance":
            return self.generate_team_performance_report(start_date, end_date)
        
        return {}
    
    def generate_daily_operations_report(self, start_date, end_date):
        """Generate daily operations report"""
        # This is a simplified version - expand based on your needs
        report = {
            'report_type': 'Daily Operations',
            'period': f"{start_date} to {end_date}",
            'generated_at': datetime.now().isoformat(),
            'metrics': {},
            'summary': {},
            'recommendations': []
        }
        
        return report
    
    def show_settings(self):
        """Display settings interface"""
        st.title("⚙️ Settings")
        
        st.markdown("### Database Configuration")
        
        with st.form("db_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                host = st.text_input("Host", value="localhost")
                user = st.text_input("User", value="root")
            
            with col2:
                password = st.text_input("Password", type="password", value="")
                database = st.text_input("Database", value="sla_monitoring_test")
            
            if st.form_submit_button("Save Configuration"):
                # In a real app, you would save this to config file
                st.success("Configuration saved (note: this is demo-only)")
        
        st.markdown("---")
        st.markdown("### Agent Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_refresh = st.checkbox("Auto-refresh data", value=True)
            refresh_interval = st.selectbox("Refresh interval", ["5 minutes", "15 minutes", "30 minutes", "1 hour"])
        
        with col2:
            notifications = st.checkbox("Enable notifications", value=True)
            alert_threshold = st.slider("Alert threshold (severity)", 1, 10, 7)
        
        if st.button("Save Agent Settings"):
            st.success("Agent settings saved")
        
        st.markdown("---")
        st.markdown("### System Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Python Version", sys.version.split()[0])
        
        with col2:
            st.metric("Streamlit Version", st.__version__)
        
        with col3:
            try:
                import mysql.connector
                st.metric("MySQL Connector", mysql.connector.__version__)
            except:
                st.metric("MySQL Connector", "Not installed")
    
    # Helper methods for dashboard
    def get_total_tickets(self):
        query = "SELECT COUNT(*) as count FROM tickets"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_delayed_tickets(self):
        query = "SELECT COUNT(*) as count FROM tickets WHERE sla_status != 'within_sla'"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_breached_tickets(self):
        query = "SELECT COUNT(*) as count FROM tickets WHERE sla_status = 'breached'"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_active_escalations(self):
        query = "SELECT COUNT(*) as count FROM escalations WHERE escalation_status = 'active'"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_recent_tickets(self, limit=10):
        query = f"""
        SELECT ticket_id, ticket_title, priority, sla_status, assigned_team, creation_time
        FROM tickets 
        WHERE sla_status != 'within_sla'
        ORDER BY creation_time DESC 
        LIMIT {limit}
        """
        return self.db.execute_query(query)
    
    @property
    def config(self):
        return self.db.config

def main():
    """Main entry point"""
    app = StreamlitSLAApp()
    app.run()

if __name__ == "__main__":
    main()
