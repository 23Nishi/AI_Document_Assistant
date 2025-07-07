"""
Combined GenAI Document Assistant Application
Run both FastAPI backend and Streamlit frontend with one command
"""

import subprocess
import threading
import time
import sys
import os

def run_backend():
    """Start FastAPI backend server"""
    print("🚀 Starting FastAPI backend on http://localhost:8000")
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])

def run_frontend():
    """Start Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

def main():
    """Main function to run both backend and frontend"""
    print("🚀 Starting GenAI Document Assistant...")
    
    # Start FastAPI backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(5)
    
    print("✅ Backend started successfully!")
    print("🌐 Starting Streamlit frontend...")
    
    # Start Streamlit frontend in main thread
    run_frontend()

if __name__ == "__main__":
    main()
