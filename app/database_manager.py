"""
Database Manager for SLA Monitoring Agent
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'host': 'localhost',
            'user': 'root',
            'password': 'test123',
            'database': 'sla_monitoring',
            'port': 3306
        }
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("✅ Database connection established")
            return True
        except Error as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            results = self.cursor.fetchall()
            return results
        except Error as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> bool:
        """Execute an UPDATE/INSERT/DELETE query"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Update execution failed: {e}")
            return False
    
    def get_tickets(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Get tickets with optional filters"""
        query = """
        SELECT 
            t.ticket_id,
            t.ticket_title,
            t.priority,
            t.status,
            t.creation_time,
            t.resolution_deadline,
            t.actual_resolution_time,
            t.assigned_team,
            t.sla_status,
            t.delay_minutes,
            s.service_name,
            c.customer_name,
            c.customer_tier
        FROM tickets t
        LEFT JOIN services s ON t.service_id = s.service_id
        LEFT JOIN customers c ON t.customer_id = c.customer_id
        WHERE 1=1
        """
        
        params = []
        
        if filters:
            if 'sla_status' in filters:
                query += " AND t.sla_status = %s"
                params.append(filters['sla_status'])
            
            if 'priority' in filters:
                query += " AND t.priority = %s"
                params.append(filters['priority'])
            
            if 'start_date' in filters:
                query += " AND t.creation_time >= %s"
                params.append(filters['start_date'])
            
            if 'end_date' in filters:
                query += " AND t.creation_time <= %s"
                params.append(filters['end_date'])
            
            if 'assigned_team' in filters:
                query += " AND t.assigned_team = %s"
                params.append(filters['assigned_team'])
        
        query += " ORDER BY t.priority DESC, t.creation_time DESC LIMIT %s"
        params.append(limit)
        
        return self.execute_query(query, tuple(params))
    
    def get_delayed_portions(self, ticket_id: Optional[str] = None) -> List[Dict]:
        """Get delayed portions for tickets"""
        query = """
        SELECT 
            d.delay_id,
            d.ticket_id,
            d.delay_type,
            d.delay_start,
            d.delay_end,
            d.delay_duration_minutes,
            d.delay_status,
            d.impact_score,
            d.resolution_notes,
            t.ticket_title,
            t.priority
        FROM sla_delays d
        LEFT JOIN tickets t ON d.ticket_id = t.ticket_id
        WHERE 1=1
        """
        
        params = []
        
        if ticket_id:
            query += " AND d.ticket_id = %s"
            params.append(ticket_id)
        
        query += " ORDER BY d.delay_start DESC"
        
        return self.execute_query(query, tuple(params) if params else None)
    
    def get_escalations(self, status: Optional[str] = None) -> List[Dict]:
        """Get escalations with optional status filter"""
        query = """
        SELECT 
            e.escalation_id,
            e.ticket_id,
            e.escalation_level,
            e.escalation_reason,
            e.escalation_time,
            e.escalation_status,
            e.resolved_time,
            t.ticket_title,
            t.priority,
            t.sla_status
        FROM escalations e
        LEFT JOIN tickets t ON e.ticket_id = t.ticket_id
        WHERE 1=1
        """
        
        params = []
        
        if status:
            query += " AND e.escalation_status = %s"
            params.append(status)
        
        query += " ORDER BY e.escalation_level DESC, e.escalation_time DESC"
        
        return self.execute_query(query, tuple(params) if params else None)
    
    def get_sla_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get SLA performance metrics"""
        query = f"""
        SELECT 
            COUNT(*) as total_tickets,
            SUM(CASE WHEN sla_status = 'within_sla' THEN 1 ELSE 0 END) as within_sla,
            SUM(CASE WHEN sla_status = 'breached' THEN 1 ELSE 0 END) as breached,
            SUM(CASE WHEN sla_status = 'at_risk' THEN 1 ELSE 0 END) as at_risk,
            SUM(CASE WHEN sla_status = 'delayed' THEN 1 ELSE 0 END) as delayed,
            AVG(delay_minutes) as avg_delay_minutes,
            ROUND(SUM(CASE WHEN sla_status = 'within_sla' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as compliance_rate
        FROM tickets
        WHERE creation_time >= DATE_SUB(NOW(), INTERVAL {days_back} DAY)
        """
        
        results = self.execute_query(query)
        
        if results:
            return results[0]
        return {}
    
    def create_ticket(self, ticket_data: Dict) -> bool:
        """Create a new ticket"""
        query = """
        INSERT INTO tickets 
        (ticket_id, ticket_title, service_id, priority, status, 
         creation_time, resolution_deadline, assigned_team, sla_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            ticket_data.get('ticket_id'),
            ticket_data.get('ticket_title'),
            ticket_data.get('service_id', 1),
            ticket_data.get('priority', 'P3'),
            ticket_data.get('status', 'new'),
            ticket_data.get('creation_time', datetime.now()),
            ticket_data.get('resolution_deadline'),
            ticket_data.get('assigned_team', 'Unassigned'),
            ticket_data.get('sla_status', 'within_sla')
        )
        
        return self.execute_update(query, params)
    
    def update_ticket_status(self, ticket_id: str, status: str, sla_status: Optional[str] = None) -> bool:
        """Update ticket status"""
        query = "UPDATE tickets SET status = %s"
        params = [status]
        
        if sla_status:
            query += ", sla_status = %s"
            params.append(sla_status)
        
        query += " WHERE ticket_id = %s"
        params.append(ticket_id)
        
        return self.execute_update(query, tuple(params))
    
    def add_delay(self, delay_data: Dict) -> bool:
        """Add a delayed portion record"""
        query = """
        INSERT INTO sla_delays 
        (ticket_id, delay_type, delay_start, delay_end, 
         delay_duration_minutes, delay_status, impact_score, resolution_notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            delay_data.get('ticket_id'),
            delay_data.get('delay_type'),
            delay_data.get('delay_start'),
            delay_data.get('delay_end'),
            delay_data.get('delay_duration_minutes', 0),
            delay_data.get('delay_status', 'pending'),
            delay_data.get('impact_score', 5),
            delay_data.get('resolution_notes', '')
        )
        
        return self.execute_update(query, params)
    
    def escalate_ticket(self, escalation_data: Dict) -> bool:
        """Create an escalation record"""
        query = """
        INSERT INTO escalations 
        (ticket_id, escalation_level, escalation_reason, 
         escalation_time, escalation_status)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        params = (
            escalation_data.get('ticket_id'),
            escalation_data.get('escalation_level', 1),
            escalation_data.get('escalation_reason', ''),
            escalation_data.get('escalation_time', datetime.now()),
            escalation_data.get('escalation_status', 'active')
        )
        
        return self.execute_update(query, params)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.connect()
            if self.connection and self.connection.is_connected():
                self.execute_query("SELECT 1")
                return True
        except Exception:
            pass
        return False
    
    def create_test_database(self) -> bool:
        """Create test database schema"""
        try:
            # Connect without database
            temp_config = self.config.copy()
            temp_config.pop('database', None)
            
            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            cursor.execute(f"USE {self.config['database']}")
            
            # Create tables
            tables = self._get_table_schema()
            for table_sql in tables:
                cursor.execute(table_sql)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ Test database created successfully")
            return True
            
        except Error as e:
            logger.error(f"Failed to create test database: {e}")
            return False
    
    def _get_table_schema(self) -> List[str]:
        """Return table creation SQL"""
        return [
            """
            CREATE TABLE IF NOT EXISTS services (
                service_id INT PRIMARY KEY AUTO_INCREMENT,
                service_name VARCHAR(100) NOT NULL,
                service_category VARCHAR(50),
                default_sla_hours INT DEFAULT 24,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INT PRIMARY KEY AUTO_INCREMENT,
                customer_name VARCHAR(200) NOT NULL,
                customer_tier VARCHAR(20),
                account_manager VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id VARCHAR(50) PRIMARY KEY,
                ticket_title VARCHAR(500) NOT NULL,
                service_id INT,
                customer_id INT,
                priority VARCHAR(10),
                status VARCHAR(20),
                creation_time DATETIME NOT NULL,
                resolution_deadline DATETIME NOT NULL,
                actual_resolution_time DATETIME,
                assigned_team VARCHAR(100),
                sla_status VARCHAR(20),
                delay_minutes INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES services(service_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
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
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
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
                resolved_time DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
            )
            """
        ]
    
    def populate_test_data(self, num_tickets: int = 50) -> bool:
        """Populate database with test data"""
        try:
            # Insert sample services
            services = [
                ('Database Support', 'Infrastructure', 4),
                ('API Monitoring', 'Application', 8),
                ('Frontend UI', 'Application', 24),
                ('Security Incident', 'Security', 2),
                ('Payment Gateway', 'Finance', 1)
            ]
            
            for service in services:
                self.execute_update(
                    "INSERT INTO services (service_name, service_category, default_sla_hours) VALUES (%s, %s, %s)",
                    service
                )
            
            # Insert sample customers
            customers = [
                ('TechCorp Inc', 'Enterprise', 'John Smith'),
                ('StartUp Ventures', 'Premium', 'Sarah Johnson'),
                ('Global Bank', 'Platinum', 'Mike Chen'),
                ('EduTech Solutions', 'Premium', 'Emma Wilson')
            ]
            
            for customer in customers:
                self.execute_update(
                    "INSERT INTO customers (customer_name, customer_tier, account_manager) VALUES (%s, %s, %s)",
                    customer
                )
            
            # Generate sample tickets
            import random
            from datetime import datetime, timedelta
            
            teams = ['Team A', 'Team B', 'Team C', 'Team D']
            priorities = ['P1', 'P2', 'P3', 'P4']
            statuses = ['new', 'in_progress', 'pending', 'resolved', 'closed']
            sla_statuses = ['within_sla', 'delayed', 'at_risk', 'breached']
            
            for i in range(num_tickets):
                creation_time = datetime.now() - timedelta(hours=random.randint(1, 168))
                sla_hours = random.choice([4, 8, 24, 48])
                resolution_deadline = creation_time + timedelta(hours=sla_hours)
                
                sla_status = random.choices(
                    sla_statuses,
                    weights=[40, 25, 20, 15]  # Weighted distribution
                )[0]
                
                ticket_id = f"TKT-{creation_time.strftime('%Y%m%d')}-{1000+i}"
                
                self.execute_update(
                    """
                    INSERT INTO tickets 
                    (ticket_id, ticket_title, service_id, customer_id, priority, status,
                     creation_time, resolution_deadline, assigned_team, sla_status, delay_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ticket_id,
                        f"Test Issue {i+1} - {random.choice(['Performance', 'Error', 'Access'])}",
                        random.randint(1, 5),
                        random.randint(1, 4),
                        random.choice(priorities),
                        random.choice(statuses),
                        creation_time,
                        resolution_deadline,
                        random.choice(teams),
                        sla_status,
                        random.randint(0, 480) if sla_status != 'within_sla' else 0
                    )
                )
                
                # Add delays for some tickets
                if sla_status in ['delayed', 'at_risk', 'breached'] and random.random() > 0.4:
                    self._add_sample_delays(ticket_id, creation_time, resolution_deadline)
                
                # Add escalations for some tickets
                if sla_status in ['breached', 'at_risk'] and random.random() > 0.6:
                    self._add_sample_escalation(ticket_id, creation_time)
            
            logger.info(f"✅ Test data populated: {num_tickets} tickets created")
            return True
            
        except Error as e:
            logger.error(f"Failed to populate test data: {e}")
            return False
    
    def _add_sample_delays(self, ticket_id: str, creation_time: datetime, deadline: datetime):
        """Add sample delays for a ticket"""
        import random
        
        delay_types = ['response', 'resolution', 'customer_waiting', 'internal']
        delay_statuses = ['pending', 'in_progress', 'resolved', 'failed']
        
        num_delays = random.randint(1, 3)
        for _ in range(num_delays):
            delay_start = creation_time + timedelta(
                hours=random.randint(1, int((deadline - creation_time).total_seconds()/3600)-1)
            )
            delay_duration = random.randint(30, 240)
            delay_end = delay_start + timedelta(minutes=delay_duration)
            
            self.execute_update(
                """
                INSERT INTO sla_delays 
                (ticket_id, delay_type, delay_start, delay_end, 
                 delay_duration_minutes, delay_status, impact_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ticket_id,
                    random.choice(delay_types),
                    delay_start,
                    delay_end,
                    delay_duration,
                    random.choice(delay_statuses),
                    random.randint(1, 10)
                )
            )
    
    def _add_sample_escalation(self, ticket_id: str, creation_time: datetime):
        """Add sample escalation for a ticket"""
        import random
        
        escalation_time = creation_time + timedelta(hours=random.randint(1, 12))
        
        self.execute_update(
            """
            INSERT INTO escalations 
            (ticket_id, escalation_level, escalation_reason, 
             escalation_time, escalation_status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                ticket_id,
                random.randint(1, 4),
                random.choice(['SLA breach', 'Customer complaint', 'Technical blocker']),
                escalation_time,
                random.choice(['active', 'resolved', 'pending'])
            )
        )
