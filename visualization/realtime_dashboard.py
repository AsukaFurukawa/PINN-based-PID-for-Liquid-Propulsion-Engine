import streamlit as st
import numpy as np
import pandas as pd
import time
import json
import os
import plotly.graph_objects as go
from real_time_engine_viz import (
    create_real_time_engine_visualization,
    generate_optimization_recommendations,
    save_visualization_data,
    load_visualization_data
)

# Set page configuration
st.set_page_config(
    page_title="PINN Rocket Engine Real-Time Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .title-text {
        color: #FF9500;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .highlight {
        background-color: rgba(76, 175, 80, 0.1);
        border-radius: 5px;
        padding: 10px;
    }
    .metric-container {
        background-color: #1E2130;
        border-radius: 5px;
        padding: 15px;
        margin: 5px;
    }
    .warning {
        color: #FF5733;
    }
    .normal {
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='title-text'>🚀 PINN-Based Rocket Engine Visualization Dashboard</h1>", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.markdown("## Engine Controls")
    
    # Engine Status
    engine_status = st.selectbox(
        "Engine Status",
        options=["Standby", "Ignition Sequence", "Startup", "Nominal Operation", "Shutdown Sequence", "Emergency Shutdown"]
    )
    
    # Visualization mode
    viz_mode = st.radio(
        "Visualization Mode", 
        options=["3D Model", "Temperature", "Flow Velocity"]
    )
    
    # Engine parameters
    st.markdown("## Engine Parameters")
    
    chamber_pressure = st.slider("Chamber Pressure (MPa)", 1.0, 5.0, 2.5, 0.1)
    mixture_ratio = st.slider("Mixture Ratio (O/F)", 1.5, 3.5, 2.4, 0.1)
    
    # Advanced parameters 
    with st.expander("Advanced Parameters"):
        chamber_length = st.slider("Chamber Length (m)", 0.08, 0.25, 0.15, 0.01)
        chamber_diameter = st.slider("Chamber Diameter (m)", 0.05, 0.15, 0.08, 0.01)
        throat_diameter = st.slider("Throat Diameter (m)", 0.02, 0.06, 0.03, 0.005)
        exit_diameter = st.slider("Exit Diameter (m)", 0.06, 0.18, 0.09, 0.01)
        nozzle_length = st.slider("Nozzle Length (m)", 0.08, 0.20, 0.12, 0.01)
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("Start Simulation")
    with col2:
        stop_button = st.button("Stop Simulation")

# Main content area
col1, col2 = st.columns([2, 1])

# Generate simulated performance data
def generate_performance_data():
    # Current time for dynamic effects
    t = time.time()
    
    # Base values determined by slider settings
    chamber_pressure_pa = chamber_pressure * 1e6
    
    # Add some oscillation for realism
    pressure_oscillation = 0.05 * chamber_pressure_pa * np.sin(t * 2)
    
    # Calculate related parameters
    if engine_status == "Nominal Operation":
        thrust = 500 + (chamber_pressure - 1.5) * 400 + 20 * np.sin(t)
        exit_velocity = 1500 + (chamber_pressure - 1.5) * 200 + 30 * np.sin(t * 1.5)
        chamber_temp = 2500 + (mixture_ratio - 2.0) * 200 + 40 * np.sin(t * 0.7)
        wall_temp = 500 + (chamber_temp - 2500) * 0.1 + 10 * np.sin(t * 0.3)
        throat_erosion = 0.01 + 0.003 * np.sin(t * 0.1)
    elif engine_status == "Startup":
        # During startup, parameters are increasing
        startup_factor = min(1.0, (time.time() % 20) / 10)
        thrust = 500 * startup_factor + 10 * np.sin(t)
        exit_velocity = 1500 * startup_factor + 20 * np.sin(t * 1.2)
        chamber_temp = 2500 * startup_factor + 30 * np.sin(t * 0.5)
        wall_temp = 500 * startup_factor + 5 * np.sin(t * 0.2)
        throat_erosion = 0.005
    elif engine_status == "Ignition Sequence":
        # Just starting up
        ignition_factor = min(0.2, (time.time() % 5) / 5)
        thrust = 100 * ignition_factor
        exit_velocity = 300 * ignition_factor
        chamber_temp = 1000 * ignition_factor
        wall_temp = 300 * ignition_factor
        throat_erosion = 0.001
    elif engine_status == "Shutdown Sequence":
        # Decreasing parameters
        shutdown_factor = max(0.0, 1.0 - (time.time() % 20) / 10)
        thrust = 500 * shutdown_factor + 10 * np.sin(t)
        exit_velocity = 1500 * shutdown_factor + 20 * np.sin(t * 1.2)
        chamber_temp = 2500 * shutdown_factor + 30 * np.sin(t * 0.5)
        wall_temp = 500 * shutdown_factor + 5 * np.sin(t * 0.2)
        throat_erosion = 0.005
    else:  # Standby or Emergency
        thrust = 0
        exit_velocity = 0
        chamber_temp = 300
        wall_temp = 300
        throat_erosion = 0
    
    # Calculate fuel and oxidizer flow rates
    total_flow = thrust / (2000 * 9.81)  # Approximation based on a typical Isp
    fuel_flow = total_flow / (mixture_ratio + 1)
    oxidizer_flow = total_flow - fuel_flow
    
    # Create the performance data dictionary
    performance_data = {
        "thrust": thrust,
        "chamber_pressure": chamber_pressure_pa + pressure_oscillation,
        "exit_velocity": exit_velocity,
        "mixture_ratio": mixture_ratio,
        "fuel_flow_rate": fuel_flow,
        "oxidizer_flow_rate": oxidizer_flow,
        "chamber_temperature": chamber_temp,
        "wall_temperature": wall_temp,
        "throat_erosion": throat_erosion,
        "status": engine_status
    }
    
    # Generate recommendations
    performance_data["recommendations"] = generate_optimization_recommendations(performance_data)
    
    return performance_data

# First column: 3D visualization
with col1:
    # Get the selected visualization mode
    mode_mapping = {
        "3D Model": "3d_model",
        "Temperature": "temperature",
        "Flow Velocity": "flow_velocity"
    }
    selected_mode = mode_mapping[viz_mode]
    
    # Engine parameters dictionary
    engine_params = {
        "chamber_length": chamber_length,
        "chamber_diameter": chamber_diameter,
        "throat_diameter": throat_diameter,
        "exit_diameter": exit_diameter,
        "nozzle_length": nozzle_length,
        "injector_plate_thickness": 0.02,
    }
    
    # Generate performance data
    perf_data = generate_performance_data()
    
    # Create the visualization
    fig = create_real_time_engine_visualization(
        engine_parameters=engine_params,
        performance_data=perf_data,
        mode=selected_mode
    )
    
    # Display the visualization
    st.plotly_chart(fig, use_container_width=True)

# Second column: Performance metrics and controls
with col2:
    # Performance metrics
    st.markdown("## Engine Performance")
    
    # Create three columns for metrics
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric(
            "Thrust",
            f"{perf_data['thrust']:.1f} N",
            delta=f"{(perf_data['thrust'] - 700):.1f} N"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_b:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        pressure_mpa = perf_data['chamber_pressure'] / 1e6
        st.metric(
            "Chamber P",
            f"{pressure_mpa:.2f} MPa",
            delta=f"{(pressure_mpa - chamber_pressure):.2f} MPa"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_c:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric(
            "Exit Velocity",
            f"{perf_data['exit_velocity']:.0f} m/s",
            delta=f"{(perf_data['exit_velocity'] - 1800):.0f} m/s"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    col_d, col_e, col_f = st.columns(3)
    
    with col_d:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric(
            "Mixture Ratio",
            f"{perf_data['mixture_ratio']:.2f}",
            delta=f"{(perf_data['mixture_ratio'] - 2.4):.2f}"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_e:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric(
            "Chamber Temp",
            f"{perf_data['chamber_temperature']:.0f} K",
            delta=f"{(perf_data['chamber_temperature'] - 2800):.0f} K"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_f:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        erosion_percent = perf_data['throat_erosion'] * 100
        st.metric(
            "Throat Erosion",
            f"{erosion_percent:.2f}%",
            delta=f"{(erosion_percent - 2):.2f}%",
            delta_color="inverse"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recommendations section
    st.markdown("## Optimization Recommendations")
    
    recs = perf_data.get("recommendations", {})
    if recs:
        for key, value in recs.items():
            st.markdown(f"<div class='highlight'><b>{key}:</b> {value}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='highlight normal'>No recommendations needed. Engine operating within optimal parameters.</div>", unsafe_allow_html=True)
    
    # Historical data plot
    st.markdown("## Performance Trend")
    
    # Normally we would load historical data here, but for this example we'll generate some
    # In a real app, you would maintain a historical data structure and update it each iteration
    
    # Create a simulated time series
    times = np.arange(0, 100, 1)
    baseline_thrust = 700 + 50 * np.sin(times / 10)
    noise = np.random.normal(0, 10, size=len(times))
    thrust_history = baseline_thrust + noise
    
    # Create a simple line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, 
        y=thrust_history,
        mode='lines',
        name='Thrust History',
        line=dict(color='#4CAF50', width=2)
    ))
    
    fig.update_layout(
        title="Thrust History",
        xaxis_title="Time (s)",
        yaxis_title="Thrust (N)",
        template="plotly_dark",
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Status indicator
    status_color = {
        "Standby": "blue",
        "Ignition Sequence": "orange",
        "Startup": "yellow",
        "Nominal Operation": "green",
        "Shutdown Sequence": "orange",
        "Emergency Shutdown": "red"
    }
    
    st.markdown(f"""
    <div style='background-color: {status_color[engine_status]}; 
                padding: 10px; 
                border-radius: 5px;
                color: white;
                text-align: center;
                margin-top: 20px;'>
        <h3>{engine_status}</h3>
    </div>
    """, unsafe_allow_html=True)

# Auto-refresh the dashboard (in a real app)
if st.button("Auto-refresh (5s)"):
    st.rerun() 