#!/usr/bin/env python3
"""
Entry point script to run the enhanced real-time visualization dashboard.

This script launches the Streamlit application that provides an interactive
3D visualization dashboard for the liquid rocket engine with enhanced 
aerospace visualization features.

Usage:
    python run_real_time_viz.py
    
Requirements:
    - See requirements.txt for dependencies
"""

import os
import sys
import subprocess

def main():
    """
    Run the Streamlit application for the enhanced real-time visualization dashboard.
    """
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Streamlit dashboard app
    app_path = os.path.join(script_dir, 'visualization', 'realtime_dashboard.py')
    
    # Check if the app file exists
    if not os.path.exists(app_path):
        print(f"Error: Dashboard file not found at {app_path}")
        sys.exit(1)
    
    # Print information
    print("Starting Enhanced Aerospace Visualization Dashboard...")
    print("Press Ctrl+C to stop the application.")
    
    # Run the Streamlit application using subprocess
    try:
        # Use subprocess.Popen to handle the process more robustly
        process = subprocess.Popen([
            'streamlit', 'run', 
            app_path,
            '--server.headless', 'true',
            '--browser.serverAddress', 'localhost',
            '--server.port', '8502'  # Use different port than main app
        ])
        
        # Keep the main process running while the subprocess is active
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down the visualization dashboard...")
        process.terminate()
    except Exception as e:
        print(f"Error running the dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 