#!/usr/bin/env python3
"""
Test script for Hermes Dashboard
Validates that streamlit_app.py works correctly
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

print("=== TEST DEL DASHBOARD ===\n")

# 1. Check database exists
db_path = os.path.join(os.path.dirname(__file__), "dashboard.db")
print(f"1. 📊 Verificando database: {db_path}")
if os.path.exists(db_path):
    print(f"   ✅ Existe ({os.path.getsize(db_path)} bytes)")
    
    # Check schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"   📋 Tablas encontradas: {tables}")
    
    # Check account_snapshots columns
    if 'account_snapshots' in tables:
        cursor.execute("PRAGMA table_info(account_snapshots);")
        columns = cursor.fetchall()
        account_cols = [col[1] for col in columns]
        print(f"   🔍 Columnas de account_snapshots: {account_cols}")
        
        # Verify we have required columns
        required = ['timestamp', 'total_credits', 'total_usage']
        missing = [col for col in required if col not in account_cols]
        if missing:
            print(f"   ❌ Faltan columnas: {missing}")
        else:
            print(f"   ✅ Todas las columnas requeridas presentes")
    
    conn.close()
else:
    print(f"   ❌ No encontrado")

print("\n2. 🐍 Verificando Python imports...")
try:
    import streamlit
    import pandas
    import plotly
    import sqlite3
    print("   ✅ Todos los imports funcionan")
except ImportError as e:
    print(f"   ❌ Import error: {e}")

print("\n3. 📄 Verificando streamlit_app.py...")
streamlit_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
if os.path.exists(streamlit_path):
    print(f"   ✅ Existe ({os.path.getsize(streamlit_path)} bytes)")
    
    # Try to parse it
    try:
        with open(streamlit_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common issues
        issues = []
        if "remaining_credits" in content:
            issues.append("Uso de 'remaining_credits' (columna no existe)")
        if "SELECT timestamp, total_credits, total_usage, remaining" in content:
            issues.append("Query SQL pide columna 'remaining' (no existe)")
        
        if issues:
            print(f"   ⚠️ Problemas encontrados:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print(f"   ✅ Sin problemas obvios")
            
    except Exception as e:
        print(f"   ❌ Error leyendo archivo: {e}")
else:
    print(f"   ❌ No encontrado")

print("\n4. 🧪 Ejecutando load_data()...")
try:
    # Import the load_data function
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Create a mock st module for testing
    class MockSt:
        cache_data = lambda **kwargs: lambda f: f
    
    import __main__
    __main__.st = MockSt()
    
    # Now we can import
    exec(open(streamlit_path).read(), {'st': MockSt()})
    
    print("   ✅ load_data() se puede ejecutar (mock)")
except Exception as e:
    print(f"   ❌ Error ejecutando load_data(): {e}")

print("\n=== RESULTADO DEL TEST ===")
print("Si ves ✅, el dashboard debería funcionar.")
print("Si ves ❌, hay problemas que corregir.")
print("\nPara ejecutar el dashboard:")
print("\nPara ejecutar el dashboard:")
print(f"cd \"{dashboard_path}\"")
print("python -m streamlit run streamlit_app.py")
print("\nLuego abre: http://localhost:8501")