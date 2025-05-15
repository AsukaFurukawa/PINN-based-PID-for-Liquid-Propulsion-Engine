#!/usr/bin/env python3
"""
Entry point script to run the PINN-based Rocket Engine Simulator.

This script launches the Streamlit application that provides an interactive
interface for the Physics-Informed Neural Network (PINN) based simulation
of a liquid rocket engine.

Usage:
    python run_app.py
    
Requirements:
    - See requirements.txt for dependencies
"""

import os
import sys
import subprocess

def run_dashboard():
    """
    Run the standard rocket engine visualization dashboard using Streamlit.
    This dashboard provides visualization of rocket engine parameters and performance.
    """
    print("Starting Rocket Engine Visualization Dashboard...")
    
    # Get the absolute path to the dashboard file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(script_dir, "visualization", "app.py")
    
    # Ensure the file exists
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard file not found at {dashboard_path}")
        sys.exit(1)
    
    # Execute the Streamlit app
    try:
        subprocess.run([
            "streamlit", "run", 
            dashboard_path,
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except Exception as e:
        print(f"Error running the dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_dashboard() 