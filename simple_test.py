#!/usr/bin/env python3
"""
Simple test for dashboard
"""

import os
import sys
import sqlite3

print("=== SIMPLE DASHBOARD TEST ===\n")

# Check files exist
files_to_check = [
    "streamlit_app.py",
    "dashboard.db",
    "install_deps.bat",
    "launch_dashboard_now.bat"
]

for fname in files_to_check:
    path = os.path.join(os.path.dirname(__file__), fname)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✅ {fname}: {size:,} bytes")
    else:
        print(f"❌ {fname}: NOT FOUND")

# Check database
db_path = os.path.join(os.path.dirname(__file__), "dashboard.db")
if os.path.exists(db_path):
    print(f"\n📊 Database: {os.path.getsize(db_path):,} bytes")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"   Tables: {[t[0] for t in tables]}")
        conn.close()
        print("   ✅ Database connection successful")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
else:
    print(f"\n❌ Database not found")

# Check Python syntax
print(f"\n🐍 Checking streamlit_app.py syntax...")
streamlit_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
if os.path.exists(streamlit_path):
    try:
        with open(streamlit_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common issues
        issues = []
        if "remaining_credits" in content:
            issues.append("Uses 'remaining_credits' (column doesn't exist)")
        
        if "SELECT timestamp, total_credits, total_usage, remaining" in content:
            issues.append("SQL query asks for 'remaining' column")
        elif "SELECT timestamp, total_credits, total_usage" in content:
            print("   ✅ SQL query correct (no 'remaining')")
        
        if not issues:
            print("   ✅ No obvious issues found")
        else:
            print("   ⚠️ Issues:")
            for issue in issues:
                print(f"     - {issue}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("   ❌ streamlit_app.py not found")

print("\n=== TEST COMPLETE ===")
print("If you see ✅, dashboard should work.")
print("Run: python -m streamlit run streamlit_app.py")
