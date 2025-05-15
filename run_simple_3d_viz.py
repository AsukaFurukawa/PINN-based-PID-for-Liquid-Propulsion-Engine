import streamlit as st
import numpy as np
import time
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from visualization.simple_engine_viz import create_simple_engine_viz, update_engine_params

# Set page configuration
st.set_page_config(
    page_title="Rocket Engine Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add navigation in sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["3D Visualization", "Performance Metrics", "Parameter Correlations", "Historical Data"]
)

# Title and description
st.title("Liquid Rocket Engine Visualization & Analysis")
st.markdown("""
This dashboard provides a simplified 3D visualization and analysis of a liquid rocket engine with physics-based effects.
Adjust the parameters to see how they affect the engine operation, appearance, and performance metrics.
""")

# Initialize session state variables
if 'animation_time' not in st.session_state:
    st.session_state.animation_time = time.time()
if 'startup_progress' not in st.session_state:
    st.session_state.startup_progress = 0.0
if 'shutdown_progress' not in st.session_state:
    st.session_state.shutdown_progress = 0.0
if 'ignition_progress' not in st.session_state:
    st.session_state.ignition_progress = 0.0
if 'previous_status' not in st.session_state:
    st.session_state.previous_status = "Standby"
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []
if 'show_grid' not in st.session_state:
    st.session_state.show_grid = True
    
# Initialize engine parameters
if "engine_params" not in st.session_state:
    st.session_state.engine_params = {
        "status": "Standby",
        "chamberPressure": 0.1,
        "mixtureRatio": 0.0,
        "chamberLength": 0.15,
        "chamberDiameter": 0.08,
        "throatDiameter": 0.03,
        "exitDiameter": 0.09,
        "nozzleLength": 0.12,
    }

# Sidebar for controls
with st.sidebar:
    st.header("Engine Controls")
    
    # Control mode selection
    control_mode = st.radio(
        "Control Mode",
        ["Manual Status Control", "Simulate Engine Sequence"]
    )
    
    if control_mode == "Manual Status Control":
        engine_status = st.selectbox(
            "Engine Status",
            ["Standby", "Ignition Sequence", "Startup", "Nominal Operation", "Shutdown Sequence"]
        )
    else:
        # Engine sequence simulation
        if 'sequence_state' not in st.session_state:
            st.session_state.sequence_state = "Standby"
            
        # Sequence control buttons
        sequence_cols = st.columns(2)
        with sequence_cols[0]:
            if st.button("Start Engine", use_container_width=True, 
                        disabled=st.session_state.sequence_state != "Standby"):
                st.session_state.sequence_state = "Ignition"
                st.session_state.ignition_progress = 0.0
                
            if st.button("Emergency Shutdown", use_container_width=True,
                        disabled=st.session_state.sequence_state in ["Standby", "Shutdown"]):
                st.session_state.sequence_state = "Shutdown"
                st.session_state.shutdown_progress = 0.0
                
        with sequence_cols[1]:
            if st.button("Reset", use_container_width=True):
                st.session_state.sequence_state = "Standby"
                st.session_state.startup_progress = 0.0
                st.session_state.shutdown_progress = 0.0
                st.session_state.ignition_progress = 0.0
        
        # Update sequence state based on progress
        if st.session_state.sequence_state == "Ignition":
            st.session_state.ignition_progress += 0.01
            if st.session_state.ignition_progress >= 1.0:
                st.session_state.sequence_state = "Startup"
                st.session_state.startup_progress = 0.0
            engine_status = "Ignition Sequence"
            
        elif st.session_state.sequence_state == "Startup":
            st.session_state.startup_progress += 0.005
            if st.session_state.startup_progress >= 1.0:
                st.session_state.sequence_state = "Nominal"
            engine_status = "Startup"
            
        elif st.session_state.sequence_state == "Nominal":
            engine_status = "Nominal Operation"
            
        elif st.session_state.sequence_state == "Shutdown":
            st.session_state.shutdown_progress += 0.005
            if st.session_state.shutdown_progress >= 1.0:
                st.session_state.sequence_state = "Standby"
            engine_status = "Shutdown Sequence"
            
        else:  # Standby
            engine_status = "Standby"
        
        # Display current sequence status
        st.info(f"Current Status: {engine_status}")
        
        # Display progress bars
        if st.session_state.sequence_state == "Ignition":
            st.progress(st.session_state.ignition_progress, "Ignition in progress...")
        elif st.session_state.sequence_state == "Startup":
            st.progress(st.session_state.startup_progress, "Engine startup in progress...")
        elif st.session_state.sequence_state == "Shutdown":
            st.progress(st.session_state.shutdown_progress, "Engine shutdown in progress...")
    
    # Chamber pressure - dynamic range based on engine status
    st.subheader("Propulsion Parameters")
    
    if engine_status == "Nominal Operation":
        pressure_min = 1.0
        pressure_max = 5.0
        pressure_default = 2.0
    elif engine_status == "Startup":
        max_pressure = 2.0
        progress = st.session_state.startup_progress if 'startup_progress' in st.session_state else 0.5
        pressure_min = 0.1
        pressure_max = max(max_pressure * progress + 0.1, 0.5)
        pressure_default = max(max_pressure * progress, 0.5)
    elif engine_status == "Ignition Sequence":
        pressure_min = 0.1
        pressure_max = 1.0
        pressure_default = 0.3
    elif engine_status == "Shutdown Sequence":
        progress = st.session_state.shutdown_progress if 'shutdown_progress' in st.session_state else 0.5
        pressure_min = 0.1
        pressure_max = 2.0
        pressure_default = max(2.0 * (1.0 - progress), 0.1)
    else:  # Standby
        pressure_min = 0.1
        pressure_max = 0.5
        pressure_default = 0.1
    
    chamber_pressure = st.slider(
        "Chamber Pressure (MPa)",
        min_value=pressure_min,
        max_value=pressure_max,
        value=pressure_default,
        step=0.1
    )
    
    # Mixture ratio - constrained based on engine status
    if engine_status == "Nominal Operation":
        mr_min = 1.5
        mr_max = 7.0
        mr_default = 2.1
    elif engine_status == "Standby":
        mr_min = 0.0
        mr_max = 1.0
        mr_default = 0.0
    else:
        mr_min = 1.5
        mr_max = 3.0
        mr_default = 2.1
    
    mixture_ratio = st.slider(
        "Mixture Ratio (O/F)",
        min_value=mr_min,
        max_value=mr_max,
        value=mr_default,
        step=0.1
    )
    
    # Engine Geometry section
    st.subheader("Engine Geometry")
    with st.expander("Engine Dimensions", expanded=False):
        chamber_length = st.slider("Chamber Length (m)", 0.05, 0.3, 0.15, 0.01)
        chamber_diameter = st.slider("Chamber Diameter (m)", 0.04, 0.15, 0.08, 0.01)
        throat_diameter = st.slider("Throat Diameter (m)", 0.01, 0.05, 0.03, 0.005)
        
        # Calculate expansion ratio
        expansion_ratio = st.slider("Expansion Ratio", 1.5, 10.0, 3.0, 0.5)
        exit_diameter = throat_diameter * np.sqrt(expansion_ratio)
        st.info(f"Exit Diameter: {exit_diameter:.3f} m")
        
        nozzle_length = st.slider("Nozzle Length (m)", 0.05, 0.3, 0.12, 0.01)
    
    # Visualization options
    st.subheader("Visualization Options")
    st.session_state.show_grid = st.checkbox("Show Grid", value=True)
    animation_speed = st.slider("Animation Speed", 0.5, 2.0, 1.0, 0.1)
    
    # Refresh button
    if st.button("Refresh Visualization"):
        st.rerun()

# Calculate performance metrics
def calculate_metrics(status, chamber_pressure, mixture_ratio):
    metrics = {}
    
    if status == "Nominal Operation":
        # Calculate thrust (simplified)
        chamber_pressure_pa = chamber_pressure * 1e6
        throat_area = np.pi * (throat_diameter/2)**2
        c_f = 1.4  # Thrust coefficient
        thrust = c_f * chamber_pressure_pa * throat_area
        
        # Add oscillations for realism
        t = time.time()
        thrust_oscillation = 0.03 * thrust * np.sin(t * 10)
        thrust = thrust + thrust_oscillation
        
        # Calculate ISP based on mixture ratio
        if mixture_ratio < 2.5:  # LOX/LH2
            isp = 360 + (mixture_ratio - 1.5) * 20
        elif mixture_ratio < 3.5:  # LOX/CH4
            isp = 300 + (mixture_ratio - 2.5) * 10
        else:  # LOX/RP-1
            isp = 280 + (mixture_ratio - 3.5) * 5
        
        # Calculate temperature
        if mixture_ratio < 2.5:
            temp = 2800 + (mixture_ratio - 1.5) * 400
        elif mixture_ratio < 3.5:
            temp = 2700 + (mixture_ratio - 2.5) * 300
        else:
            temp = 2600 + (mixture_ratio - 3.5) * 200
        
        # Calculate mass flow
        mass_flow = thrust / (isp * 9.81)
        
    elif status == "Startup":
        # During startup
        progress = st.session_state.startup_progress
        base_thrust = 5000 * chamber_pressure
        thrust = base_thrust * (0.5 + 0.5 * progress)
        isp = 300 * (0.5 + 0.5 * progress)
        temp = 300 + 3000 * progress
        mass_flow = thrust / (isp * 9.81) if isp > 0 else 0
        
    elif status == "Ignition Sequence":
        # Small values during ignition
        t = time.time()
        thrust = 500 * (0.2 + 0.1 * np.sin(t * 20))
        isp = 100
        temp = 500 + 500 * np.sin(t * 0.5)
        mass_flow = thrust / (isp * 9.81) if isp > 0 else 0
        
    elif status == "Shutdown Sequence":
        # Decreasing during shutdown
        progress = st.session_state.shutdown_progress
        shutdown_factor = max(0, 1.0 - progress)
        base_thrust = 5000 * chamber_pressure
        thrust = base_thrust * shutdown_factor
        isp = 300 * shutdown_factor
        temp = 300 + 3000 * shutdown_factor
        mass_flow = thrust / (isp * 9.81) if isp > 0 else 0
        
    else:  # Standby
        thrust = 0
        isp = 0
        temp = 300
        mass_flow = 0
    
    metrics["thrust"] = thrust
    metrics["isp"] = isp
    metrics["temperature"] = temp
    metrics["mass_flow"] = mass_flow
    
    if mass_flow > 0:
        metrics["fuel_flow"] = mass_flow / (mixture_ratio + 1)
        metrics["oxidizer_flow"] = mass_flow * mixture_ratio / (mixture_ratio + 1)
    else:
        metrics["fuel_flow"] = 0
        metrics["oxidizer_flow"] = 0
        
    # Calculate additional performance metrics
    metrics["c_star"] = isp * 9.81 / 1.4 if isp > 0 else 0  # Characteristic velocity
    metrics["expansion_ratio"] = (exit_diameter / throat_diameter)**2  # Nozzle expansion ratio
    metrics["area_ratio"] = metrics["expansion_ratio"]  # Same as expansion ratio
    metrics["chamber_mach"] = 0.1 + 0.1 * chamber_pressure if chamber_pressure > 0 else 0
    
    # Record data for historical tracking
    current_time = time.time()
    if len(st.session_state.historical_data) == 0 or current_time - st.session_state.historical_data[-1]["timestamp"] >= 0.5:
        metrics["timestamp"] = current_time
        st.session_state.historical_data.append(metrics)
        # Keep only last 100 data points
        if len(st.session_state.historical_data) > 100:
            st.session_state.historical_data = st.session_state.historical_data[-100:]
    
    return metrics

# Main content based on selected page
if page == "3D Visualization":
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Update engine parameter values
        update_engine_params(
            status=engine_status,
            chamberPressure=chamber_pressure,
            mixtureRatio=mixture_ratio,
            chamberLength=chamber_length,
            chamberDiameter=chamber_diameter,
            throatDiameter=throat_diameter,
            exitDiameter=exit_diameter,
            nozzleLength=nozzle_length
        )
        
        # Create the 3D visualization
        engine_params = create_simple_engine_viz(height=600)
    
    # Performance metrics and telemetry in the right column
    with col2:
        st.header("Engine Performance")
        
        metrics = calculate_metrics(engine_status, chamber_pressure, mixture_ratio)
        
        # Display metrics
        metrics_cols = st.columns(2)
        
        with metrics_cols[0]:
            st.metric("Thrust (N)", f"{metrics['thrust']:.1f}")
            st.metric("Chamber Pressure (MPa)", f"{chamber_pressure:.2f}")
            
        with metrics_cols[1]:
            st.metric("Specific Impulse (s)", f"{metrics['isp']:.1f}")
            st.metric("Chamber Temperature (K)", f"{metrics['temperature']:.0f}")
        
        # Mass flow breakdown
        if metrics['mass_flow'] > 0:
            st.subheader("Propellant Flow")
            flow_cols = st.columns(2)
            with flow_cols[0]:
                st.metric("Fuel Flow (kg/s)", f"{metrics['fuel_flow']:.3f}")
            with flow_cols[1]:
                st.metric("Oxidizer Flow (kg/s)", f"{metrics['oxidizer_flow']:.3f}")
        
        # Add engine status specific messages
        if engine_status == "Startup":
            st.info("📈 Engine startup in progress. Monitoring parameters...")
        elif engine_status == "Shutdown Sequence":
            st.info("📉 Engine shutdown in progress. Monitoring cooldown...")
        elif engine_status == "Ignition Sequence":
            st.info("🔥 Ignition sequence in progress. Monitoring ignition stability...")
        elif engine_status == "Standby":
            st.info("⏸️ Engine in standby mode. Ready for operation.")
        elif engine_status == "Nominal Operation":
            if chamber_pressure > 3.0:
                st.warning("⚠️ High chamber pressure. Monitor cooling systems.")
            else:
                st.success("✓ Engine running at nominal parameters.")

elif page == "Performance Metrics":
    st.header("Detailed Performance Analysis")
    
    metrics = calculate_metrics(engine_status, chamber_pressure, mixture_ratio)
    
    # Create more detailed metrics display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Thrust (N)", f"{metrics['thrust']:.1f}")
        st.metric("Specific Impulse (s)", f"{metrics['isp']:.1f}")
        st.metric("Chamber Pressure (MPa)", f"{chamber_pressure:.2f}")
        st.metric("Chamber Temperature (K)", f"{metrics['temperature']:.0f}")
    
    with col2:
        st.metric("Characteristic Velocity (m/s)", f"{metrics['c_star']:.1f}")
        st.metric("Chamber Mach Number", f"{metrics['chamber_mach']:.3f}")
        st.metric("Expansion Ratio", f"{metrics['expansion_ratio']:.2f}")
        st.metric("Throat Diameter (m)", f"{throat_diameter:.3f}")
    
    with col3:
        st.metric("Total Mass Flow (kg/s)", f"{metrics['mass_flow']:.3f}")
        st.metric("Mixture Ratio (O/F)", f"{mixture_ratio:.2f}")
        st.metric("Fuel Flow (kg/s)", f"{metrics['fuel_flow']:.3f}")
        st.metric("Oxidizer Flow (kg/s)", f"{metrics['oxidizer_flow']:.3f}")
    
    # Create time-series plot of thrust
    if len(st.session_state.historical_data) > 1:
        st.subheader("Thrust History")
        
        # Extract data for plotting
        times = [(d["timestamp"] - st.session_state.historical_data[0]["timestamp"]) for d in st.session_state.historical_data]
        thrusts = [d["thrust"] for d in st.session_state.historical_data]
        
        # Create Plotly figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=thrusts, mode='lines', name='Thrust (N)'))
        fig.update_layout(
            title="Thrust Over Time",
            xaxis_title="Time (s)",
            yaxis_title="Thrust (N)",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Small 3D visualization on this page as well
    st.subheader("Engine Visualization")
    create_simple_engine_viz(height=400)

elif page == "Parameter Correlations":
    st.header("Parameter Correlation Analysis")
    
    # Create data for parameter correlation plots
    st.subheader("Chamber Pressure vs. Thrust")
    
    # Generate data points for correlation
    pressures = np.linspace(0.1, 5.0, 20)
    thrusts = []
    isps = []
    temps = []
    
    for p in pressures:
        # Calculate metrics for this pressure with current mixture ratio
        metrics = calculate_metrics("Nominal Operation", p, mixture_ratio)
        thrusts.append(metrics["thrust"])
        isps.append(metrics["isp"])
        temps.append(metrics["temperature"])
    
    # Create correlation dataframe
    corr_data = pd.DataFrame({
        "Chamber Pressure (MPa)": pressures,
        "Thrust (N)": thrusts,
        "ISP (s)": isps,
        "Temperature (K)": temps
    })
    
    # Pressure vs Thrust plot
    fig1 = px.scatter(corr_data, x="Chamber Pressure (MPa)", y="Thrust (N)", 
                     trendline="ols", template="plotly_dark")
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Mixture ratio correlations
    st.subheader("Mixture Ratio Effects")
    
    # Generate data for different mixture ratios
    mixture_ratios = np.linspace(1.5, 7.0, 20)
    isp_values = []
    temp_values = []
    
    for mr in mixture_ratios:
        metrics = calculate_metrics("Nominal Operation", chamber_pressure, mr)
        isp_values.append(metrics["isp"])
        temp_values.append(metrics["temperature"])
    
    # Create dataframe
    mr_data = pd.DataFrame({
        "Mixture Ratio (O/F)": mixture_ratios,
        "ISP (s)": isp_values,
        "Temperature (K)": temp_values
    })
    
    # Create two-column layout for mixture ratio plots
    mr_col1, mr_col2 = st.columns(2)
    
    with mr_col1:
        fig2 = px.line(mr_data, x="Mixture Ratio (O/F)", y="ISP (s)", 
                      template="plotly_dark")
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)
    
    with mr_col2:
        fig3 = px.line(mr_data, x="Mixture Ratio (O/F)", y="Temperature (K)", 
                      template="plotly_dark")
        fig3.update_layout(height=350)
        st.plotly_chart(fig3, use_container_width=True)
    
    # Throat-to-Exit Area Ratio Effect
    st.subheader("Nozzle Expansion Effects")
    
    # Generate data for different expansion ratios
    exp_ratios = np.linspace(1.5, 10.0, 15)
    exp_cf_values = []  # Thrust coefficient
    exp_isp_values = []  # ISP
    
    for er in exp_ratios:
        # Simplified calculations
        cf = 1.2 + 0.15 * np.log(er)  # Approximation of thrust coefficient
        isp_factor = 0.8 + 0.2 * np.log(er) / np.log(10)  # Effect on ISP
        
        exp_cf_values.append(cf)
        exp_isp_values.append(300 * isp_factor)  # Base ISP of 300s
    
    # Create dataframe
    exp_data = pd.DataFrame({
        "Expansion Ratio": exp_ratios,
        "Thrust Coefficient": exp_cf_values,
        "Relative ISP": exp_isp_values
    })
    
    # Plot expansion ratio effects
    fig4 = px.line(exp_data, x="Expansion Ratio", y=["Thrust Coefficient", "Relative ISP"], 
                  template="plotly_dark")
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, use_container_width=True)

elif page == "Historical Data":
    st.header("Historical Performance Data")
    
    if len(st.session_state.historical_data) > 1:
        # Extract data for plotting
        times = [(d["timestamp"] - st.session_state.historical_data[0]["timestamp"]) for d in st.session_state.historical_data]
        thrusts = [d["thrust"] for d in st.session_state.historical_data]
        isps = [d["isp"] for d in st.session_state.historical_data]
        temps = [d["temperature"] for d in st.session_state.historical_data]
        mass_flows = [d["mass_flow"] for d in st.session_state.historical_data]
        
        # Create dataframe
        hist_data = pd.DataFrame({
            "Time (s)": times,
            "Thrust (N)": thrusts,
            "ISP (s)": isps,
            "Temperature (K)": temps,
            "Mass Flow (kg/s)": mass_flows
        })
        
        # Display as table
        st.dataframe(hist_data, use_container_width=True)
        
        # Create multi-line plot
        st.subheader("Performance Metrics Over Time")
        
        # Normalize data for plotting multiple metrics on the same scale
        hist_data["Thrust (N) [Normalized]"] = hist_data["Thrust (N)"] / max(thrusts) if max(thrusts) > 0 else 0
        hist_data["ISP (s) [Normalized]"] = hist_data["ISP (s)"] / max(isps) if max(isps) > 0 else 0
        hist_data["Temperature (K) [Normalized]"] = hist_data["Temperature (K)"] / max(temps) if max(temps) > 0 else 0
        hist_data["Mass Flow (kg/s) [Normalized]"] = hist_data["Mass Flow (kg/s)"] / max(mass_flows) if max(mass_flows) > 0 else 0
        
        # Create plotly figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_data["Time (s)"], y=hist_data["Thrust (N) [Normalized]"], mode='lines', name='Thrust'))
        fig.add_trace(go.Scatter(x=hist_data["Time (s)"], y=hist_data["ISP (s) [Normalized]"], mode='lines', name='ISP'))
        fig.add_trace(go.Scatter(x=hist_data["Time (s)"], y=hist_data["Temperature (K) [Normalized]"], mode='lines', name='Temperature'))
        fig.add_trace(go.Scatter(x=hist_data["Time (s)"], y=hist_data["Mass Flow (kg/s) [Normalized]"], mode='lines', name='Mass Flow'))
        
        fig.update_layout(
            title="Normalized Performance Metrics Over Time",
            xaxis_title="Time (s)",
            yaxis_title="Normalized Value",
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Add download button for the data
        csv = hist_data.to_csv(index=False)
        st.download_button(
            "Download Historical Data as CSV",
            csv,
            "engine_performance_data.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.info("No historical data available yet. Operate the engine to generate data.")

if __name__ == "__main__":
    # The app is already running at this point
    pass 