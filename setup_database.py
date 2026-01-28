#!/usr/bin/env python3
"""
Setup database for SLA Monitoring Agent
Run this script to initialize the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 SLA Monitoring Database Setup")
    print("=" * 60)
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Test connection
    print("\n1️⃣ Testing database connection...")
    if not db.test_connection():
        print("❌ Cannot connect to database. Please check:")
        print("   - MySQL is running")
        print("   - Database credentials are correct")
        print("   - Network connectivity")
        return
    
    print("✅ Database connection successful")
    
    # Create database schema
    print("\n2️⃣ Creating database schema...")
    if db.create_test_database():
        print("✅ Database schema created")
    else:
        print("❌ Failed to create database schema")
        return
    
    # Populate with test data
    print("\n3️⃣ Populating with test data...")
    num_tickets = 50
    if db.populate_test_data(num_tickets):
        print(f"✅ {num_tickets} test tickets created")
        print("   - Services: Database, API, Frontend, Security, Payment")
        print("   - Customers: TechCorp, StartUp Ventures, Global Bank, EduTech")
        print("   - Tickets with various SLA statuses")
        print("   - Delayed portions with success/failure/pending statuses")
        print("   - Sample escalations")
    else:
        print("❌ Failed to populate test data")
        return
    
    # Verify data
    print("\n4️⃣ Verifying data...")
    metrics = db.get_sla_metrics(days_back=7)
    if metrics:
        print(f"✅ Data verification complete:")
        print(f"   Total tickets: {metrics.get('total_tickets', 0)}")
        print(f"   SLA compliance: {metrics.get('compliance_rate', 0)}%")
        print(f"   Average delay: {metrics.get('avg_delay_minutes', 0):.1f} minutes")
    else:
        print("⚠️ Could not retrieve metrics")
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run the Streamlit app: streamlit run streamlit_app.py")
    print("2. Access the dashboard at http://localhost:8501")
    print("3. Use the Setup page in the app for additional configuration")
    print("\n📊 Sample queries:")
    print("   SELECT * FROM tickets WHERE sla_status != 'within_sla' LIMIT 5;")
    print("   SELECT delay_status, COUNT(*) FROM sla_delays GROUP BY delay_status;")
    print("   SELECT escalation_level, COUNT(*) FROM escalations GROUP BY escalation_level;")

if __name__ == "__main__":
    main()
