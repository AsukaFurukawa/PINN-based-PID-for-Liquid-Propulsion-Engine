import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.graph_objects as go
from advanced_threed_visualization import (
    AdvancedThreeDVisualization, 
    get_predefined_camera_views, 
    generate_performance_data,
    generate_optimization_recommendations
)

# Set page configuration
st.set_page_config(
    page_title="Advanced 3D Liquid Rocket Engine Simulation",
    page_icon="🚀",
    layout="wide"
)

# Title and description
st.title("Advanced 3D Liquid Rocket Engine Simulation")
st.markdown("""
This advanced simulation provides a detailed 3D visualization of a liquid rocket engine with physics-based modeling.
Use the controls to adjust engine parameters and observe how they affect performance and behavior.
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
if 'show_telemetry' not in st.session_state:
    st.session_state.show_telemetry = True
if 'telemetry_data' not in st.session_state:
    st.session_state.telemetry_data = {
        'time': [],
        'thrust': [],
        'temperature': [],
        'pressure': []
    }

# Create layout with columns
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
    
    # Propulsion Parameters section
    st.subheader("Propulsion Parameters")
    
    # Chamber pressure - dynamic range based on engine status
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
    
    # Propellant selection
    propellant_type = st.selectbox(
        "Propellant Combination",
        ["LOX/LH2", "LOX/CH4", "LOX/RP-1"],
        index=1  # Default to LOX/CH4
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
    
    # Visualization settings
    st.subheader("Visualization Settings")
    
    # Camera controls
    camera_views = get_predefined_camera_views()
    selected_view = st.selectbox("Camera View", list(camera_views.keys()))
    
    # Auto-rotation
    auto_rotate = st.checkbox("Auto-rotate Camera", value=True)
    
    # Display options
    show_grid = st.checkbox("Show Grid", value=True)
    show_axes = st.checkbox("Show Coordinate Axes", value=True)
    
    # Telemetry panel
    show_telemetry = st.checkbox("Show Telemetry Panel", value=True)
    st.session_state.show_telemetry = show_telemetry
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    
    # Manual refresh button
    if st.button("Refresh Visualization"):
        st.rerun()

# Main content area
with col1:
    # Create and display the 3D visualization
    threed_viz = AdvancedThreeDVisualization(height=600)
    
    # Update visualization with current parameters
    threed_viz.update_engine_state(
        status=engine_status,
        chamber_pressure=chamber_pressure,
        mixture_ratio=mixture_ratio
    )
    
    threed_viz.update_engine_geometry(
        chamber_length=chamber_length,
        chamber_diameter=chamber_diameter,
        throat_diameter=throat_diameter,
        exit_diameter=exit_diameter,
        nozzle_length=nozzle_length
    )
    
    # Set camera position
    if selected_view in camera_views:
        threed_viz.set_camera_view(
            camera_views[selected_view]["position"],
            camera_views[selected_view]["target"]
        )
    
    # Toggle auto-rotation
    threed_viz.toggle_auto_rotate(auto_rotate)
    
    # Render the visualization
    threed_viz.render()
    
    # Add auto-refresh logic
    if auto_refresh:
        st.empty()
        time.sleep(0.1)
        st.rerun()

# Performance metrics and telemetry
with col2:
    st.header("Engine Performance")
    
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
    
    # Generate performance data
    metrics = generate_performance_data(
        chamber_pressure, 
        mixture_ratio, 
        engine_status, 
        st.session_state.animation_time + progress
    )
    
    # Display metrics in a dynamic way
    metrics_cols = st.columns(2)
    
    # First column of metrics
    with metrics_cols[0]:
        st.metric("Thrust (N)", f"{metrics['thrust']:.1f}")
        st.metric("Chamber Pressure (MPa)", f"{metrics['chamber_pressure']:.2f}")
        st.metric("Chamber Temperature (K)", f"{metrics['chamber_temperature']:.0f}")
        st.metric("Fuel Flow (kg/s)", f"{metrics['fuel_flow_rate']:.3f}")
        
    # Second column of metrics
    with metrics_cols[1]:
        st.metric("Specific Impulse (s)", f"{metrics['specific_impulse']:.1f}")
        st.metric("C* (m/s)", f"{metrics['c_star']:.1f}")
        st.metric("Expansion Ratio", f"{metrics['expansion_ratio']:.2f}")
        st.metric("Oxidizer Flow (kg/s)", f"{metrics['oxidizer_flow_rate']:.3f}")
    
    # Optimization recommendations
    st.subheader("Optimization Recommendations")
    
    recommendations = generate_optimization_recommendations(metrics)
    if recommendations:
        for rec in recommendations:
            st.info(f"ℹ️ {rec}")
    else:
        st.success("✓ Engine parameters appear to be well optimized.")
    
    # Add engine status specific messages
    if engine_status == "Startup":
        st.info("📈 Engine startup in progress. Monitoring parameters...")
    elif engine_status == "Shutdown Sequence":
        st.info("📉 Engine shutdown in progress. Monitoring cooldown...")
    elif engine_status == "Ignition Sequence":
        st.info("🔥 Ignition sequence in progress. Monitoring ignition stability...")
    elif engine_status == "Standby":
        st.info("⏸️ Engine in standby mode. Ready for operation.")
    
    # Add telemetry panel if enabled
    if st.session_state.show_telemetry:
        st.subheader("Live Telemetry")
        
        # Update telemetry data (limit to 100 points)
        max_points = 100
        current_time = time.time()
        st.session_state.telemetry_data['time'].append(current_time)
        st.session_state.telemetry_data['thrust'].append(metrics["thrust"])
        st.session_state.telemetry_data['temperature'].append(metrics["chamber_temperature"])
        st.session_state.telemetry_data['pressure'].append(metrics["chamber_pressure"])
        
        # Trim data if too long
        if len(st.session_state.telemetry_data['time']) > max_points:
            for key in st.session_state.telemetry_data:
                st.session_state.telemetry_data[key] = st.session_state.telemetry_data[key][-max_points:]
        
        # Create time array relative to start
        time_relative = [t - st.session_state.telemetry_data['time'][0] for t in st.session_state.telemetry_data['time']]
        
        # Create plots
        # Thrust plot
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
        
        # Temperature & Pressure plot
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
    
    # Advanced Analysis section
    st.subheader("Advanced Analysis")
    with st.expander("Performance Analysis", expanded=False):
        st.write("Analyze engine performance metrics in detail:")
        
        # Calculate theoretical performance metrics
        if metrics["specific_impulse"] > 0:
            st.write(f"**Theoretical Exit Velocity**: {metrics['exit_velocity']:.1f} m/s")
            
            # Calculate thrust coefficient
            if metrics["chamber_pressure"] > 0 and throat_diameter > 0:
                throat_area = np.pi * (throat_diameter/2)**2
                chamber_pressure_pa = metrics["chamber_pressure"] * 1e6
                thrust_coef = metrics["thrust"] / (chamber_pressure_pa * throat_area)
                st.write(f"**Thrust Coefficient**: {thrust_coef:.3f}")
            
            # Calculate characteristic velocity efficiency
            if metrics["c_star"] > 0:
                ideal_c_star = 2000  # Approximate ideal value
                c_star_efficiency = metrics["c_star"] / ideal_c_star
                st.write(f"**C* Efficiency**: {c_star_efficiency:.2%}")
            
            # Calculate energy release efficiency
            energy_efficiency = metrics["combustion_efficiency"]
            st.write(f"**Combustion Efficiency**: {energy_efficiency:.2%}")
        
        # Display propellant properties
        st.write("#### Propellant Properties")
        if propellant_type == "LOX/LH2":
            st.write("**LOX/LH2 Properties:**")
            st.write("- Theoretical max Isp (vac): 450-470 s")
            st.write("- Optimal mixture ratio: 4.8-6.0")
            st.write("- Bulk density: Low")
            st.write("- Chamber temperature: 2700-3300 K")
        elif propellant_type == "LOX/CH4":
            st.write("**LOX/CH4 Properties:**")
            st.write("- Theoretical max Isp (vac): 360-380 s")
            st.write("- Optimal mixture ratio: 2.7-3.5")
            st.write("- Bulk density: Medium")
            st.write("- Chamber temperature: 3200-3500 K")
        elif propellant_type == "LOX/RP-1":
            st.write("**LOX/RP-1 Properties:**")
            st.write("- Theoretical max Isp (vac): 320-340 s")
            st.write("- Optimal mixture ratio: 2.1-2.5")
            st.write("- Bulk density: High")
            st.write("- Chamber temperature: 3400-3700 K")

# Update animation time for next iteration
st.session_state.animation_time += 0.1

# Footer
st.markdown("---")
st.markdown("Advanced 3D Rocket Engine Simulation - Visualization Branch")
st.markdown("Created with three.js integration for realistic engine modeling") 