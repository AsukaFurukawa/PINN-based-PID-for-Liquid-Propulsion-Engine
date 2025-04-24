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

def main():
    """
    Run the Streamlit application for the PINN-based rocket engine simulator.
    """
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Streamlit app
    app_path = os.path.join(script_dir, 'visualization', 'app.py')
    
    # Check if the app file exists
    if not os.path.exists(app_path):
        print(f"Error: Application file not found at {app_path}")
        sys.exit(1)
    
    # Print information
    print("Starting PINN-based Rocket Engine Simulator...")
    print("Press Ctrl+C to stop the application.")
    
    # Run the Streamlit application
    subprocess.run([
        'streamlit', 'run', 
        app_path,
        '--server.headless', 'true',
        '--browser.serverAddress', 'localhost',
        '--server.port', '8501'
    ])

if __name__ == "__main__":
    main() 