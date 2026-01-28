#!/usr/bin/env python3
"""
Setup script for Streamlit SLA Monitoring App
Run this before starting the Streamlit app
"""

import subprocess
import sys
import os

def check_requirements():
    """Check and install requirements"""
    print("Checking requirements...")
    
    requirements = [
        "streamlit",
        "mysql-connector-python",
        "pandas",
        "plotly"
    ]
    
    for package in requirements:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\n✅ All requirements satisfied!")

def setup_database():
    """Setup test database"""
    print("\nSetting up test database...")
    
    # Create a simple database setup script
    setup_sql = """
    -- Create database if not exists
    CREATE DATABASE IF NOT EXISTS sla_monitoring_test;
    USE sla_monitoring_test;
    
    -- Create services table
    CREATE TABLE IF NOT EXISTS services (
        service_id INT PRIMARY KEY AUTO_INCREMENT,
        service_name VARCHAR(100) NOT NULL,
        default_sla_hours INT DEFAULT 24
    );
    
    -- Create tickets table
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
    );
    
    -- Create SLA delays table
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
    );
    
    -- Create escalations table
    CREATE TABLE IF NOT EXISTS escalations (
        escalation_id INT PRIMARY KEY AUTO_INCREMENT,
        ticket_id VARCHAR(50) NOT NULL,
        escalation_level INT,
        escalation_reason TEXT,
        escalation_time DATETIME NOT NULL,
        escalation_status VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Save SQL to file
    with open("setup_database.sql", "w") as f:
        f.write(setup_sql)
    
    print("✅ Database schema created in setup_database.sql")
    print("\nTo populate with test data, run the Streamlit app and use the Setup page.")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Streamlit SLA Monitoring App Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    # Check requirements
    check_requirements()
    
    # Setup database
    setup_database()
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\n🎉 Next steps:")
    print("1. Make sure MySQL is running")
    print("2. Update database credentials in the Streamlit app if needed")
    print("3. Run the app: streamlit run sla_streamlit_app.py")
    print("\n📁 Files created:")
    print("  - sla_streamlit_app.py : Main Streamlit application")
    print("  - requirements.txt     : Python dependencies")
    print("  - .streamlit/config.toml : Streamlit configuration")
    print("  - setup_database.sql   : Database schema")

if __name__ == "__main__":
    main()
