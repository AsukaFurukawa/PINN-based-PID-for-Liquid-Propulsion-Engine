import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.graph_objects as go
from enhanced_aerospace_viz import create_enhanced_aerospace_visualization

# Set page configuration
st.set_page_config(
    page_title="Enhanced Aerospace Visualization",
    page_icon="🚀",
    layout="wide"
)

# Title and description
st.title("Enhanced Rocket Engine Visualization Dashboard")
st.markdown("""
This dashboard provides an interactive 3D visualization of a liquid rocket engine with physics-based simulations.
Adjust the parameters to see how they affect the engine performance and visualization.
""")

# Create two columns for layout
col1, col2 = st.columns([3, 1])

# Sidebar for controls
with st.sidebar:
    st.header("Engine Parameters")
    
    # Engine status selection
    engine_status = st.selectbox(
        "Engine Status",
        ["Standby", "Ignition Sequence", "Startup", "Nominal Operation", "Shutdown Sequence"]
    )
    
    # Chamber pressure
    chamber_pressure = st.slider(
        "Chamber Pressure (MPa)",
        min_value=0.5,
        max_value=5.0,
        value=2.0,
        step=0.1
    )
    
    # Mixture ratio
    mixture_ratio = st.slider(
        "Mixture Ratio (O/F)",
        min_value=1.5,
        max_value=7.0,
        value=2.1,
        step=0.1
    )
    
    # Geometry parameters
    st.subheader("Engine Geometry")
    chamber_length = st.slider("Chamber Length (m)", 0.05, 0.3, 0.15, 0.01)
    chamber_diameter = st.slider("Chamber Diameter (m)", 0.04, 0.15, 0.08, 0.01)
    throat_diameter = st.slider("Throat Diameter (m)", 0.01, 0.05, 0.03, 0.005)
    exit_diameter = st.slider("Exit Diameter (m)", 0.05, 0.2, 0.09, 0.01)
    nozzle_length = st.slider("Nozzle Length (m)", 0.05, 0.3, 0.12, 0.01)
    
    # Auto-refresh button
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    
    # Manual refresh button
    if st.button("Refresh Visualization"):
        st.experimental_rerun()

# Data for metrics
def get_performance_metrics(chamber_pressure, mixture_ratio, engine_status):
    # Current time for adding variation
    t = time.time()
    
    # Base values from parameters
    chamber_pressure_pa = chamber_pressure * 1e6
    
    # Calculate metrics based on engine status
    if engine_status == "Nominal Operation":
        thrust = 500 + (chamber_pressure - 1.5) * 400 + 20 * np.sin(t)
        isp = 240 + 10 * np.sin(t * 0.5)
        exit_velocity = 1500 + (chamber_pressure - 1.5) * 200 + 30 * np.sin(t * 1.5)
        chamber_temp = 2500 + (mixture_ratio - 2.0) * 200 + 40 * np.sin(t * 0.7)
    elif engine_status == "Startup":
        startup_factor = min(1.0, (time.time() % 20) / 10)
        thrust = 500 * startup_factor + 10 * np.sin(t)
        isp = 220 * startup_factor + 5 * np.sin(t * 0.5)
        exit_velocity = 1500 * startup_factor + 20 * np.sin(t * 1.2)
        chamber_temp = 2500 * startup_factor + 30 * np.sin(t * 0.5)
    elif engine_status == "Ignition Sequence":
        ignition_factor = min(0.3, (time.time() % 5) / 5)
        thrust = 100 * ignition_factor
        isp = 100 * ignition_factor
        exit_velocity = 300 * ignition_factor
        chamber_temp = 1000 * ignition_factor + 300
    elif engine_status == "Shutdown Sequence":
        shutdown_factor = max(0.0, 1.0 - (time.time() % 20) / 10)
        thrust = 500 * shutdown_factor + 10 * np.sin(t)
        isp = 240 * shutdown_factor + 5 * np.sin(t * 0.5)
        exit_velocity = 1500 * shutdown_factor + 20 * np.sin(t * 1.2)
        chamber_temp = 2500 * shutdown_factor + 300
    else:  # Standby
        thrust = 0
        isp = 0
        exit_velocity = 0
        chamber_temp = 300
    
    return {
        "Thrust (N)": thrust,
        "Specific Impulse (s)": isp,
        "Chamber Pressure (MPa)": chamber_pressure,
        "Chamber Temperature (K)": chamber_temp,
        "Exit Velocity (m/s)": exit_velocity,
        "Mixture Ratio": mixture_ratio
    }

# First column: visualization 
with col1:
    # Create enhanced visualization
    fig = create_enhanced_aerospace_visualization(
        chamber_pressure=chamber_pressure,
        mixture_ratio=mixture_ratio,
        chamber_length=chamber_length,
        chamber_diameter=chamber_diameter,
        throat_diameter=throat_diameter,
        exit_diameter=exit_diameter,
        nozzle_length=nozzle_length,
        engine_status=engine_status
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Add auto-refresh logic
    if auto_refresh:
        st.empty()
        time.sleep(0.1)  # Small delay
        st.experimental_rerun()

# Second column: performance metrics
with col2:
    st.header("Performance Metrics")
    
    # Get current performance metrics
    metrics = get_performance_metrics(chamber_pressure, mixture_ratio, engine_status)
    
    # Display metrics
    for metric, value in metrics.items():
        st.metric(metric, f"{value:.2f}")
    
    # Optimization recommendations
    st.subheader("Optimization Recommendations")
    
    if engine_status == "Nominal Operation":
        if metrics["Chamber Temperature (K)"] > 3000:
            st.warning("⚠️ Chamber temperature is too high. Consider decreasing mixture ratio.")
        elif metrics["Chamber Temperature (K)"] < 2200:
            st.info("ℹ️ Chamber temperature is low. Consider increasing mixture ratio.")
    elif engine_status == "Standby":
        st.info("ℹ️ Engine is in standby mode. Change status to begin operation.")

# Run the app with: streamlit run enhanced_dashboard.py 