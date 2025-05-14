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

# Create a session state for animation
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

# Sidebar for controls
with st.sidebar:
    st.header("Engine Parameters")
    
    # Engine status selection with a more prominent display
    st.subheader("Engine Status")
    
    # Different control modes
    control_mode = st.radio(
        "Control Mode",
        ["Manual Status Control", "Simulate Engine Sequence"]
    )
    
    if control_mode == "Manual Status Control":
        engine_status = st.selectbox(
            "Current Status",
            ["Standby", "Ignition Sequence", "Startup", "Nominal Operation", "Shutdown Sequence"]
        )
    else:
        # Sequence simulation controls
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
    
    # Chamber pressure - dynamically set based on engine status
    st.subheader("Propulsion Parameters")
    
    if engine_status == "Nominal Operation":
        pressure_min = 1.0
        pressure_max = 5.0
        pressure_default = 2.0
    elif engine_status == "Startup":
        # Calculate progress-based pressure for startup
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
        # Calculate progress-based pressure for shutdown
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
    
    # Geometry parameters
    st.subheader("Engine Geometry")
    with st.expander("Engine Dimensions"):
        chamber_length = st.slider("Chamber Length (m)", 0.05, 0.3, 0.15, 0.01)
        chamber_diameter = st.slider("Chamber Diameter (m)", 0.04, 0.15, 0.08, 0.01)
        throat_diameter = st.slider("Throat Diameter (m)", 0.01, 0.05, 0.03, 0.005)
        
        # Calculate expansion ratio
        expansion_ratio = st.slider("Expansion Ratio", 1.5, 10.0, 3.0, 0.5)
        exit_diameter = throat_diameter * np.sqrt(expansion_ratio)
        st.info(f"Exit Diameter: {exit_diameter:.3f} m")
        
        nozzle_length = st.slider("Nozzle Length (m)", 0.05, 0.3, 0.12, 0.01)
    
    # Animation settings
    st.subheader("Visualization Settings")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    animation_speed = st.slider("Animation Speed", 0.1, 2.0, 1.0, 0.1)
    
    # Manual refresh button
    if st.button("Refresh Visualization"):
        st.experimental_rerun()
    
    # Telemetry view
    if st.checkbox("Show Telemetry Panel", value=True):
        st.session_state.show_telemetry = True
    else:
        st.session_state.show_telemetry = False

# Data for metrics
def get_performance_metrics(chamber_pressure, mixture_ratio, engine_status, animation_time, sequence_progress=0.0):
    """Calculate realistic performance metrics based on engine parameters and status"""
    # Add time-based variation
    t = animation_time
    
    # Base values from parameters
    chamber_pressure_pa = chamber_pressure * 1e6
    
    # Calculate metrics based on engine status
    if engine_status == "Nominal Operation":
        # More realistic parameters for nominal operation
        # Theoretical sea-level ISP for different propellants
        if mixture_ratio < 2.5:  # LOX/LH2
            base_isp = 360 + (mixture_ratio - 1.5) * 20
        elif mixture_ratio < 3.5:  # LOX/CH4
            base_isp = 300 + (mixture_ratio - 2.5) * 10
        else:  # LOX/RP-1
            base_isp = 280 + (mixture_ratio - 3.5) * 5
        
        # Calculate chamber temperature based on propellant type and mixture ratio
        if mixture_ratio < 2.5:  # LOX/LH2 (~3500K at optimal mixture ratio)
            base_temp = 2800 + (mixture_ratio - 1.5) * 400
        elif mixture_ratio < 3.5:  # LOX/CH4 (~3400K at optimal mixture ratio)
            base_temp = 2700 + (mixture_ratio - 2.5) * 300
        else:  # LOX/RP-1 (~3300K at optimal mixture ratio)
            base_temp = 2600 + (mixture_ratio - 3.5) * 200
        
        # Calculate thrust based on chamber pressure and throat area
        throat_area = np.pi * (throat_diameter/2)**2
        c_f = 1.4  # Thrust coefficient (simplified)
        thrust = c_f * chamber_pressure_pa * throat_area
        
        # Add oscillations for realism
        thrust_oscillation = 0.03 * thrust * np.sin(t * 10)
        temp_oscillation = 40 * np.sin(t * 0.7)
        isp_oscillation = 10 * np.sin(t * 0.5)
        
        # Final values
        thrust = thrust + thrust_oscillation
        isp = base_isp + isp_oscillation
        chamber_temp = base_temp + temp_oscillation
        exit_velocity = isp * 9.81  # Simplified from Isp definition
        
    elif engine_status == "Startup":
        # During startup, parameters are increasing
        progress = sequence_progress if sequence_progress > 0 else 0.5
        # More smooth oscillation during startup
        startup_factor = progress + 0.02 * np.sin(t * 5)
        startup_factor = max(0, min(1, startup_factor))
        
        # Base values for fully operational state
        base_thrust = 5000 * chamber_pressure
        base_isp = 300 
        base_temp = 3000
        
        # Apply startup factor
        thrust = base_thrust * startup_factor * (0.5 + 0.5 * np.sin(t * 2))
        isp = base_isp * (0.5 + 0.5 * startup_factor)
        chamber_temp = 300 + base_temp * startup_factor
        exit_velocity = isp * 9.81 * startup_factor
        
    elif engine_status == "Ignition Sequence":
        # During ignition, small values with rapid fluctuations
        progress = sequence_progress if sequence_progress > 0 else 0.5
        ignition_factor = progress * (0.8 + 0.2 * np.sin(t * 20))
        
        # Ignition is characterized by rapid spikes
        thrust = 500 * ignition_factor * (0.5 + 0.5 * np.sin(t * 30))
        isp = 100 * ignition_factor
        chamber_temp = 300 + 1500 * ignition_factor
        exit_velocity = isp * 9.81 * ignition_factor
        
    elif engine_status == "Shutdown Sequence":
        # During shutdown, parameters are decreasing
        progress = sequence_progress if sequence_progress > 0 else 0.5
        shutdown_factor = max(0, 1.0 - progress) + 0.05 * np.sin(t * 3)
        
        # Base values for fully operational state
        base_thrust = 5000 * chamber_pressure
        base_isp = 300
        base_temp = 3000
        
        # Apply shutdown factor with some oscillation during cooldown
        thrust = base_thrust * shutdown_factor * (0.8 + 0.2 * np.sin(t * 5))
        isp = base_isp * shutdown_factor
        chamber_temp = 300 + base_temp * shutdown_factor
        exit_velocity = isp * 9.81 * shutdown_factor
        
    else:  # Standby
        # Minimal values with slight environmental variations
        thrust = 0 + 2 * np.sin(t * 0.2)  # Minimal sensor noise
        isp = 0
        chamber_temp = 290 + 10 * np.sin(t * 0.1)  # Ambient temperature variation
        exit_velocity = 0
    
    # Return comprehensive metrics dictionary
    return {
        "Thrust (N)": thrust,
        "Specific Impulse (s)": isp,
        "Chamber Pressure (MPa)": chamber_pressure,
        "Chamber Temperature (K)": chamber_temp,
        "Exit Velocity (m/s)": exit_velocity,
        "Mixture Ratio": mixture_ratio,
        "Expansion Ratio": (exit_diameter / throat_diameter)**2,
        "Mass Flow (kg/s)": thrust / (isp * 9.81) if isp > 0 else 0
    }

# Update animation time
st.session_state.animation_time += 0.1 * animation_speed

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
    if control_mode == "Simulate Engine Sequence":
        # Use sequence progress for more accurate simulation
        if engine_status == "Startup":
            progress = st.session_state.startup_progress
        elif engine_status == "Shutdown Sequence":
            progress = st.session_state.shutdown_progress
        elif engine_status == "Ignition Sequence":
            progress = st.session_state.ignition_progress
        else:
            progress = 0.0
    else:
        progress = 0.0
    
    metrics = get_performance_metrics(
        chamber_pressure, 
        mixture_ratio, 
        engine_status, 
        st.session_state.animation_time,
        progress
    )
    
    # Display metrics in a dynamic way
    for metric, value in metrics.items():
        # Format the value based on its size
        if abs(value) < 0.01:
            formatted_value = f"{value:.5f}"
        elif abs(value) < 1:
            formatted_value = f"{value:.3f}"
        elif abs(value) < 1000:
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = f"{value:.1f}"
        
        # Add delta if engine is in transient state
        if engine_status in ["Startup", "Shutdown Sequence"]:
            if st.session_state.previous_status == engine_status:
                if engine_status == "Startup":
                    delta = "↑"
                else:
                    delta = "↓"
            else:
                delta = None
            st.metric(metric, formatted_value, delta=delta)
        else:
            st.metric(metric, formatted_value)
    
    # Save current status for delta comparison
    st.session_state.previous_status = engine_status
    
    # Optimization recommendations
    st.subheader("Optimization Recommendations")
    
    if engine_status == "Nominal Operation":
        if metrics["Chamber Temperature (K)"] > 3000:
            st.warning("⚠️ Chamber temperature is high. Consider decreasing mixture ratio or increasing cooling.")
        elif metrics["Chamber Temperature (K)"] < 2200:
            st.info("ℹ️ Chamber temperature is low. Consider increasing mixture ratio for better performance.")
            
        # Optimal mixture ratio guidance based on propellant type
        if mixture_ratio < 2.5:  # LOX/LH2
            optimal_mr = 5.0
            propellant = "LOX/LH2"
        elif mixture_ratio < 3.5:  # LOX/CH4
            optimal_mr = 3.0
            propellant = "LOX/CH4"
        else:  # LOX/RP-1
            optimal_mr = 2.3
            propellant = "LOX/RP-1"
            
        mr_diff = abs(mixture_ratio - optimal_mr)
        if mr_diff > 0.5:
            st.info(f"ℹ️ For {propellant}, the optimal mixture ratio is around {optimal_mr}.")
            
        # Expansion ratio guidance
        p_ambient = 0.101  # MPa, sea level
        optimal_expansion = (chamber_pressure / p_ambient) ** (1/4)
        actual_expansion = metrics["Expansion Ratio"]
        
        if abs(optimal_expansion - actual_expansion) / optimal_expansion > 0.2:
            st.info(f"ℹ️ For this chamber pressure, an expansion ratio closer to {optimal_expansion:.1f} might improve performance.")
            
    elif engine_status == "Startup":
        st.info("📈 Engine startup in progress. Monitoring parameters...")
    elif engine_status == "Shutdown Sequence":
        st.info("📉 Engine shutdown in progress. Monitoring cooldown...")
    elif engine_status == "Ignition Sequence":
        st.info("🔥 Ignition sequence in progress. Monitoring ignition stability...")
    else:  # Standby
        st.info("⏸️ Engine in standby mode. Ready for operation.")
    
    # Add telemetry panel if enabled
    if st.session_state.get('show_telemetry', False):
        st.subheader("Live Telemetry")
        
        # Create plots for time-series data
        if 'telemetry_data' not in st.session_state:
            st.session_state.telemetry_data = {
                'time': [],
                'thrust': [],
                'temperature': [],
                'pressure': []
            }
        
        # Update telemetry data (limit to 100 points)
        max_points = 100
        st.session_state.telemetry_data['time'].append(time.time())
        st.session_state.telemetry_data['thrust'].append(metrics["Thrust (N)"])
        st.session_state.telemetry_data['temperature'].append(metrics["Chamber Temperature (K)"])
        st.session_state.telemetry_data['pressure'].append(metrics["Chamber Pressure (MPa)"])
        
        # Trim data if too long
        if len(st.session_state.telemetry_data['time']) > max_points:
            for key in st.session_state.telemetry_data:
                st.session_state.telemetry_data[key] = st.session_state.telemetry_data[key][-max_points:]
        
        # Create thrust plot
        time_relative = [t - st.session_state.telemetry_data['time'][0] for t in st.session_state.telemetry_data['time']]
        
        thrust_fig = go.Figure()
        thrust_fig.add_trace(go.Scatter(
            x=time_relative, 
            y=st.session_state.telemetry_data['thrust'],
            mode='lines',
            name='Thrust',
            line=dict(color='red', width=2)
        ))
        thrust_fig.update_layout(
            height=200, 
            margin=dict(l=0, r=0, t=30, b=0),
            title="Thrust (N)",
            xaxis_title="Time (s)",
            yaxis_title="Thrust (N)"
        )
        st.plotly_chart(thrust_fig, use_container_width=True)
        
        # Create temp/pressure plot
        temp_pressure_fig = go.Figure()
        temp_pressure_fig.add_trace(go.Scatter(
            x=time_relative, 
            y=st.session_state.telemetry_data['temperature'],
            mode='lines',
            name='Temperature',
            line=dict(color='orange', width=2),
            yaxis="y"
        ))
        temp_pressure_fig.add_trace(go.Scatter(
            x=time_relative, 
            y=[p * 500 for p in st.session_state.telemetry_data['pressure']],  # Scale for visualization
            mode='lines',
            name='Pressure',
            line=dict(color='blue', width=2),
            yaxis="y2"
        ))
        temp_pressure_fig.update_layout(
            height=200, 
            margin=dict(l=0, r=0, t=30, b=0),
            title="Temperature & Pressure",
            xaxis_title="Time (s)",
            yaxis=dict(
                title="Temperature (K)",
                titlefont=dict(color="orange"),
                tickfont=dict(color="orange")
            ),
            yaxis2=dict(
                title="Pressure (MPa)",
                titlefont=dict(color="blue"),
                tickfont=dict(color="blue"),
                anchor="x",
                overlaying="y",
                side="right",
                range=[0, max(st.session_state.telemetry_data['pressure']) * 1000]  # Adjusted for scaling
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(temp_pressure_fig, use_container_width=True)

# Run the app with: streamlit run enhanced_dashboard.py 