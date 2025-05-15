import streamlit as st
import numpy as np
import time
import os
import sys
from visualization.simple_engine_viz import create_simple_engine_viz, update_engine_params

# Set page configuration
st.set_page_config(
    page_title="Simple 3D Rocket Engine Visualization",
    page_icon="🚀",
    layout="wide"
)

# Title and description
st.title("3D Liquid Rocket Engine Visualization")
st.markdown("""
This dashboard provides a simplified 3D visualization of a liquid rocket engine with physics-based effects.
Adjust the parameters to see how they affect the engine operation and appearance.
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

# Create two columns for layout
col1, col2 = st.columns([2, 1])

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
    
    # Refresh button
    if st.button("Refresh Visualization"):
        st.rerun()

# Main content area
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
    
    # Calculate performance metrics
    if engine_status == "Nominal Operation":
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
        
    elif engine_status == "Startup":
        # During startup
        progress = st.session_state.startup_progress
        base_thrust = 5000 * chamber_pressure
        thrust = base_thrust * (0.5 + 0.5 * progress)
        isp = 300 * (0.5 + 0.5 * progress)
        temp = 300 + 3000 * progress
        mass_flow = thrust / (isp * 9.81) if isp > 0 else 0
        
    elif engine_status == "Ignition Sequence":
        # Small values during ignition
        t = time.time()
        thrust = 500 * (0.2 + 0.1 * np.sin(t * 20))
        isp = 100
        temp = 500 + 500 * np.sin(t * 0.5)
        mass_flow = thrust / (isp * 9.81) if isp > 0 else 0
        
    elif engine_status == "Shutdown Sequence":
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
    
    # Display metrics
    metrics_cols = st.columns(2)
    
    with metrics_cols[0]:
        st.metric("Thrust (N)", f"{thrust:.1f}")
        st.metric("Chamber Pressure (MPa)", f"{chamber_pressure:.2f}")
        
    with metrics_cols[1]:
        st.metric("Specific Impulse (s)", f"{isp:.1f}")
        st.metric("Chamber Temperature (K)", f"{temp:.0f}")
    
    # Mass flow breakdown
    if mass_flow > 0:
        st.subheader("Propellant Flow")
        fuel_flow = mass_flow / (mixture_ratio + 1)
        oxidizer_flow = mass_flow * mixture_ratio / (mixture_ratio + 1)
        
        flow_cols = st.columns(2)
        with flow_cols[0]:
            st.metric("Fuel Flow (kg/s)", f"{fuel_flow:.3f}")
        with flow_cols[1]:
            st.metric("Oxidizer Flow (kg/s)", f"{oxidizer_flow:.3f}")
    
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

if __name__ == "__main__":
    # The app is already running at this point
    pass 