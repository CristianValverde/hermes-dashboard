#!/usr/bin/env python3
"""
Launch dashboard in background
"""
import subprocess
import sys
import os
import time

print("🚀 Starting Hermes Dashboard...")
print(f"Working directory: {os.getcwd()}")

# Start Streamlit
cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", 
       "--server.port", "8501", 
       "--server.headless", "true",
       "--browser.serverAddress", "localhost"]

print(f"Command: {' '.join(cmd)}")
print("Dashboard will be available at: http://localhost:8501")
print("Press Ctrl+C to stop")

process = subprocess.Popen(cmd, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         text=True,
                         encoding='utf-8')

# Wait a bit for startup, then check
time.sleep(5)

# Check if process is running
if process.poll() is None:
    print("✅ Streamlit process started successfully")
    print("PID:", process.pid)
    
    # Try to read some output
    import threading
    def read_output():
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                print(f"[Streamlit] {line.strip()}")
    
    thread = threading.Thread(target=read_output, daemon=True)
    thread.start()
    
    # Keep script running
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
        process.terminate()
        process.wait()
        print("Dashboard stopped")
else:
    print("❌ Streamlit process failed to start")
    stdout, stderr = process.communicate()
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    sys.exit(1)
