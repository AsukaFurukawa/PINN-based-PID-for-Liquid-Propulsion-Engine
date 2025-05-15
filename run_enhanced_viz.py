import os
import subprocess
import sys

def run_enhanced_dashboard():
    """
    Run the enhanced aerospace visualization dashboard using Streamlit.
    This dashboard provides detailed 3D visualization of rocket engine components
    with realistic effects like shock diamonds, combustion visualization, etc.
    """
    print("Starting Enhanced Aerospace Visualization Dashboard...")
    
    # Get the absolute path to the dashboard file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(script_dir, "visualization", "enhanced_dashboard.py")
    
    # Ensure the file exists
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard file not found at {dashboard_path}")
        sys.exit(1)
    
    # Execute the Streamlit app
    try:
        subprocess.run([
            "streamlit", "run", 
            dashboard_path,
            "--server.port", "8504",
            "--server.headless", "true"
        ])
    except Exception as e:
        print(f"Error running the dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_enhanced_dashboard()
