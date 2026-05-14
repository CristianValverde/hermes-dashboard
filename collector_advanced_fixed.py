#!/usr/bin/env python3
"""
Hermes Advanced Collector - Fixed Version
Procesa archivos de sesión para extraer tool usage.
"""

import sqlite3
import json
import os
from pathlib import Path
import time
import sys

# Configuración
HERMES_DATA_DIR = Path(os.getenv('LOCALAPPDATA', '')) / 'hermes'
SESSION_DUMP_DIR = HERMES_DATA_DIR / 'sessions'
DASHBOARD_DB = Path(__file__).parent / 'dashboard.db'

def main():
    print("🚀 Hermes Advanced Collector - Tool Usage Extraction")
    print("=" * 50)
    
    if not SESSION_DUMP_DIR.exists():
        print(f"❌ Directorio de sesiones no encontrado: {SESSION_DUMP_DIR}")
        return
    
    # Conectar a la base de datos
    conn = sqlite3.connect(str(DASHBOARD_DB))
    cursor = conn.cursor()
    
    # Encontrar archivos de sesión
    session_files = list(SESSION_DUMP_DIR.glob('session_*.json'))
    print(f"📁 Encontrados {len(session_files)} archivos de sesión")
    
    total_tool_calls = 0
    processed_files = 0
    
    for session_file in session_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session_id = session_file.stem.replace('session_', '')
            
            # Buscar tool_calls en los mensajes
            if 'messages' in data:
                for msg in data['messages']:
                    if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                        for tool_call in msg['tool_calls']:
                            if 'function' in tool_call:
                                tool_name = tool_call['function'].get('name', 'unknown')
                                timestamp = int(time.time())
                                
                                # Extraer timestamp del mensaje si existe
                                if 'timestamp' in msg:
                                    timestamp = msg['timestamp']
                                
                                # Extraer arguments
                                arguments = tool_call['function'].get('arguments', '{}')
                                
                                # Insertar en tool_usage (ignore duplicates)
                                cursor.execute("""
                                    INSERT OR IGNORE INTO tool_usage 
                                    (session_id, tool_name, timestamp, success, error_message,
                                     duration_ms, arguments, result_summary)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (session_id, tool_name, timestamp, 1, None, None, arguments, None))
                                
                                total_tool_calls += 1
                                
            processed_files += 1
            if processed_files % 10 == 0:
                print(f"  Procesados {processed_files}/{len(session_files)} archivos, {total_tool_calls} tool calls...")
                                    
        except Exception as e:
            print(f"⚠️  Error procesando {session_file.name}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print("=" * 50)
    print(f"✅ Procesados {processed_files} archivos de sesión")
    print(f"✅ Extraídos {total_tool_calls} tool calls")
    print(f"💾 Base de datos actualizada: {DASHBOARD_DB}")

if __name__ == "__main__":
    main()
