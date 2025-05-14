import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Rocket Engine Visualization",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .title-text { color: #FF9500; }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .metric-container {
        background-color: #1E2130;
        border-radius: 5px;
        padding: 15px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='title-text'>🚀 Enhanced Rocket Engine Visualization</h1>", unsafe_allow_html=True)

# Create sidebar controls
with st.sidebar:
    st.markdown("## Engine Controls")
    
    # Engine Status
    engine_status = st.selectbox(
        "Engine Status",
        options=["Standby", "Ignition Sequence", "Startup", "Nominal Operation", "Shutdown Sequence", "Emergency Shutdown"]
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

# Function to generate performance data
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
    else:  # Standby or other states
        thrust = 100 + 10 * np.sin(t)
        exit_velocity = 300 + 20 * np.sin(t * 1.2)
        chamber_temp = 1000 + 30 * np.sin(t * 0.5)
        wall_temp = 300 + 5 * np.sin(t * 0.2)
        throat_erosion = 0.001
    
    # Calculate fuel and oxidizer flow rates
    total_flow = thrust / (2000 * 9.81)  # Approximation based on a typical Isp
    fuel_flow = total_flow / (mixture_ratio + 1)
    oxidizer_flow = total_flow - fuel_flow
    
    # Return the dictionary
    return {
        "thrust": thrust,
        "chamber_pressure": chamber_pressure_pa + pressure_oscillation,
        "exit_velocity": exit_velocity,
        "mixture_ratio": mixture_ratio,
        "fuel_flow_rate": fuel_flow,
        "oxidizer_flow_rate": oxidizer_flow,
        "chamber_temperature": chamber_temp,
        "wall_temperature": wall_temp,
        "throat_erosion": throat_erosion,
    }

# Function to create a simple rocket engine visualization
def create_simple_engine_viz():
    # Create a new figure
    fig = go.Figure()
    
    # Generate a simple engine shape
    # Chamber
    chamber_z = np.linspace(0, chamber_length, 20)
    chamber_radius = chamber_diameter / 2
    theta = np.linspace(0, 2*np.pi, 20)
    
    theta_grid, z_grid = np.meshgrid(theta, chamber_z)
    x_chamber = chamber_radius * np.cos(theta_grid)
    y_chamber = chamber_radius * np.sin(theta_grid)
    
    # Add the chamber
    fig.add_trace(go.Surface(
        x=x_chamber, y=y_chamber, z=z_grid,
        colorscale='Reds', showscale=False, opacity=0.7
    ))
    
    # Add the nozzle
    nozzle_z = np.linspace(chamber_length, chamber_length + nozzle_length, 20)
    throat_radius = throat_diameter / 2
    exit_radius = exit_diameter / 2
    throat_pos = chamber_length + nozzle_length * 0.3
    
    # Calculate nozzle profile
    nozzle_radius = []
    for z in nozzle_z:
        if z < throat_pos:
            # Converging section
            ratio = (z - chamber_length) / (throat_pos - chamber_length)
            radius = chamber_radius - ratio * (chamber_radius - throat_radius)
        else:
            # Diverging section
            ratio = (z - throat_pos) / (chamber_length + nozzle_length - throat_pos)
            radius = throat_radius + ratio * (exit_radius - throat_radius)
        nozzle_radius.append(radius)
    
    nozzle_radius = np.array(nozzle_radius)
    
    theta_grid, z_grid = np.meshgrid(theta, nozzle_z)
    r_grid, _ = np.meshgrid(nozzle_radius, theta)
    r_grid = r_grid.T
    
    x_nozzle = r_grid * np.cos(theta_grid)
    y_nozzle = r_grid * np.sin(theta_grid)
    
    # Add the nozzle
    fig.add_trace(go.Surface(
        x=x_nozzle, y=y_nozzle, z=z_grid,
        colorscale='Blues', showscale=False, opacity=0.7
    ))
    
    # Add a simple exhaust plume if the engine is running
    if engine_status in ["Nominal Operation", "Startup"]:
        plume_z = np.linspace(
            chamber_length + nozzle_length, 
            chamber_length + nozzle_length + 0.2, 
            10
        )
        plume_radius = np.linspace(exit_radius, exit_radius * 2, 10)
        
        r_grid, z_grid = np.meshgrid(plume_radius, plume_z)
        theta_grid, _ = np.meshgrid(theta, plume_z)
        
        x_plume = r_grid * np.cos(theta_grid)
        y_plume = r_grid * np.sin(theta_grid)
        
        # Add the plume
        fig.add_trace(go.Surface(
            x=x_plume, y=y_plume, z=z_grid,
            colorscale='Oranges', showscale=False, opacity=0.4
        ))
    
    # Set layout
    fig.update_layout(
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=600
    )
    
    return fig

# First column: visualization 
with col1:
    # Generate performance data
    perf_data = generate_performance_data()
    
    # Create visualization
    fig = create_simple_engine_viz()
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a note explaining the simplified visualization
    st.info("Note: This is a simplified visualization. The full enhanced aerospace visualization requires additional setup.")

# Second column: performance metrics
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
    <div style='background-color: {status_color.get(engine_status, "gray")}; 
                padding: 10px; 
                border-radius: 5px;
                color: white;
                text-align: center;
                margin-top: 20px;'>
        <h3>{engine_status}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a simple trend line
    st.markdown("## Performance Trend")
    
    # Generate some fake data for the trend
    times = np.arange(0, 100, 1)
    baseline_thrust = 700 + 50 * np.sin(times / 10)
    noise = np.random.normal(0, 10, size=len(times))
    thrust_history = baseline_thrust + noise
    
    # Create a line chart
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=times, 
        y=thrust_history,
        mode='lines',
        name='Thrust History',
        line=dict(color='#4CAF50', width=2)
    ))
    
    trend_fig.update_layout(
        title="Thrust History",
        xaxis_title="Time (s)", 
        yaxis_title="Thrust (N)",
        template="plotly_dark",
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    
    st.plotly_chart(trend_fig, use_container_width=True)

# Add auto-refresh button
if st.button("Auto-refresh (5s)"):
    st.rerun() 