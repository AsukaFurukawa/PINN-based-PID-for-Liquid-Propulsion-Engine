#!/usr/bin/env python
"""
Advanced 3D Visualization for Liquid Propulsion Engine

This script runs the advanced 3D visualization with three.js integration, 
providing a more realistic and detailed visualization of the liquid propulsion
engine for educational and simulation purposes.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    """Run the advanced 3D visualization application"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run advanced 3D visualization for liquid propulsion engine")
    parser.add_argument("--port", type=int, default=8505, help="Port to run the Streamlit app on")
    parser.add_argument("--browser", action="store_true", help="Automatically open a browser window")
    parser.add_argument("--mode", choices=["educational", "simulation", "analysis"], default="simulation",
                      help="Visualization mode: educational, simulation, or analysis")
    args = parser.parse_args()
    
    # Determine which script to run based on mode
    if args.mode == "educational":
        dashboard_script = "threed_educational_dashboard.py"
    elif args.mode == "analysis":
        dashboard_script = "threed_analysis_dashboard.py"
    else:  # simulation mode (default)
        dashboard_script = "threed_simulation_dashboard.py"
    
    # Get the absolute path to the dashboard file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    viz_dir = os.path.join(script_dir, "visualization")
    dashboard_path = os.path.join(viz_dir, dashboard_script)
    
    # Ensure the file exists
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard file not found at {dashboard_path}")
        sys.exit(1)
    
    # Create command array
    cmd = [
        "streamlit", "run", dashboard_path,
        "--server.port", str(args.port),
    ]
    
    # Add browser flag if specified
    if not args.browser:
        cmd.extend(["--server.headless", "true"])
    
    # Print startup message
    print(f"Starting advanced 3D visualization in {args.mode} mode...")
    print(f"Server will be available at http://localhost:{args.port}")
    
    # Run the streamlit app
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("Visualization application stopped.")
    except Exception as e:
        print(f"Error running the visualization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 