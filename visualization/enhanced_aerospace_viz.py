import plotly.graph_objects as go
import numpy as np
import time
import math

def create_enhanced_aerospace_visualization(
    chamber_pressure=2.0,  # MPa
    mixture_ratio=2.1,
    chamber_length=0.15,  # m
    chamber_diameter=0.08,  # m
    throat_diameter=0.03,  # m
    exit_diameter=0.09,  # m
    nozzle_length=0.12,  # m
    engine_status="Nominal Operation",
    num_points=100
):
    """
    Create a detailed aerospace visualization with enhanced features:
    - Realistic bell-shaped nozzle contour
    - Shock diamonds in exhaust plume based on pressure ratios
    - Dynamic combustion visualization with particle effects
    - Detailed engine components including cooling channels, propellant lines
    - Temperature-based color gradients
    - Different visualization effects based on engine state
    
    Args:
        chamber_pressure: Chamber pressure in MPa
        mixture_ratio: Propellant mixture ratio (O/F)
        chamber_length: Chamber length in meters
        chamber_diameter: Chamber diameter in meters
        throat_diameter: Throat diameter in meters
        exit_diameter: Exit diameter in meters
        nozzle_length: Nozzle length in meters
        engine_status: Current engine status ("Nominal Operation", "Startup", 
                      "Shutdown Sequence", "Ignition Sequence", "Standby")
        num_points: Number of points for resolution
        
    Returns:
        Plotly figure with enhanced 3D visualization
    """
    # Create figure
    fig = go.Figure()
    
    # Current time for animation
    t = time.time()
    
    # Generate performance data for visualization
    perf_data = generate_performance_data(
        chamber_pressure, 
        mixture_ratio, 
        engine_status,
        t
    )
    
    # Engine parameters
    chamber_radius = chamber_diameter / 2
    throat_radius = throat_diameter / 2
    exit_radius = exit_diameter / 2
    
    # Throat position
    throat_position = chamber_length + nozzle_length * 0.3
    
    # Create engine components
    add_combustion_chamber(fig, chamber_length, chamber_radius, perf_data, num_points)
    add_bell_nozzle(fig, chamber_length, nozzle_length, chamber_radius, throat_radius, exit_radius, throat_position, perf_data, num_points)
    add_injector_plate(fig, chamber_radius, perf_data)
    add_cooling_channels(fig, chamber_length, chamber_radius, perf_data)
    add_propellant_feed_lines(fig, chamber_diameter, chamber_radius)
    
    # Add dynamic components that depend on engine state
    if perf_data["combustion_efficiency"] > 0:
        add_combustion_visualization(fig, chamber_length, chamber_radius, perf_data)
    
    if perf_data["exit_velocity"] > 0:
        add_exhaust_plume(fig, chamber_length, nozzle_length, exit_radius, perf_data)
    
    # Set layout
    fig.update_layout(
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0.8),
                up=dict(x=0, y=0, z=1)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=600
    )
    
    return fig

def generate_performance_data(chamber_pressure, mixture_ratio, engine_status, t):
    """Generate realistic performance data based on engine parameters and status"""
    # Base values determined by parameters
    chamber_pressure_pa = chamber_pressure * 1e6
    
    # Add some oscillation for realism
    pressure_oscillation = 0.05 * chamber_pressure_pa * np.sin(t * 2)
    
    # Calculate related parameters based on engine status
    if engine_status == "Nominal Operation":
        thrust = 500 + (chamber_pressure - 1.5) * 400 + 20 * np.sin(t)
        exit_velocity = 1500 + (chamber_pressure - 1.5) * 200 + 30 * np.sin(t * 1.5)
        chamber_temp = 2500 + (mixture_ratio - 2.0) * 200 + 40 * np.sin(t * 0.7)
        wall_temp = 500 + (chamber_temp - 2500) * 0.1 + 10 * np.sin(t * 0.3)
        throat_erosion = 0.01 + 0.003 * np.sin(t * 0.1)
        combustion_efficiency = 0.95 + 0.03 * np.sin(t * 0.2)
        exit_pressure = 0.1 * chamber_pressure_pa + 0.1e5 * np.sin(t * 0.5)
    elif engine_status == "Startup":
        # During startup, parameters are increasing
        startup_factor = min(1.0, (time.time() % 20) / 10)
        thrust = 500 * startup_factor + 10 * np.sin(t)
        exit_velocity = 1500 * startup_factor + 20 * np.sin(t * 1.2)
        chamber_temp = 2500 * startup_factor + 30 * np.sin(t * 0.5)
        wall_temp = 500 * startup_factor + 5 * np.sin(t * 0.2)
        throat_erosion = 0.005
        combustion_efficiency = 0.7 + 0.25 * startup_factor
        exit_pressure = (0.05 + 0.05 * startup_factor) * chamber_pressure_pa
    elif engine_status == "Ignition Sequence":
        ignition_factor = min(0.3, (time.time() % 5) / 5)
        thrust = 100 * ignition_factor
        exit_velocity = 300 * ignition_factor
        chamber_temp = 1000 * ignition_factor + 300
        wall_temp = 300 + 100 * ignition_factor
        throat_erosion = 0.001
        combustion_efficiency = 0.3 + 0.2 * ignition_factor
        exit_pressure = 0.02 * chamber_pressure_pa
    elif engine_status == "Shutdown Sequence":
        shutdown_factor = max(0.0, 1.0 - (time.time() % 20) / 10)
        thrust = 500 * shutdown_factor + 10 * np.sin(t)
        exit_velocity = 1500 * shutdown_factor + 20 * np.sin(t * 1.2)
        chamber_temp = 2500 * shutdown_factor + 300
        wall_temp = 500 * shutdown_factor + 300
        throat_erosion = 0.005
        combustion_efficiency = 0.6 + 0.3 * shutdown_factor
        exit_pressure = 0.1 * chamber_pressure_pa * shutdown_factor
    else:  # Standby or other states
        thrust = 0
        exit_velocity = 0
        chamber_temp = 300
        wall_temp = 300
        throat_erosion = 0.001
        combustion_efficiency = 0.0
        exit_pressure = 1e5  # 1 atm
    
    # Calculate fuel and oxidizer flow rates
    total_flow = thrust / (2000 * 9.81)  # Approximation based on a typical Isp
    fuel_flow = total_flow / (mixture_ratio + 1)
    oxidizer_flow = total_flow - fuel_flow
    
    # Return the dictionary with extended data
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
        "combustion_efficiency": combustion_efficiency,
        "exit_pressure": exit_pressure,
        "ambient_pressure": 1.01e5,  # Standard atmosphere
        "time": t  # Current time for animations
    }

def add_combustion_chamber(fig, chamber_length, chamber_radius, perf_data, num_points):
    """Add detailed combustion chamber to the visualization"""
    # Current time for animation
    t = perf_data["time"]
    
    # Vibration factor (more vibration at higher thrust)
    vibration_amp = 0.0001 * (perf_data["thrust"] / 1000) if perf_data["thrust"] > 0 else 0
    vibration = vibration_amp * np.sin(t * 20)
    
    # Generate points for chamber (cylinder)
    theta = np.linspace(0, 2*np.pi, num_points)
    z_chamber = np.linspace(0, chamber_length, num_points)
    
    # Create grid for surface
    theta_grid, z_grid = np.meshgrid(theta, z_chamber)
    
    # Add vibration effect to chamber
    x_chamber = (chamber_radius + vibration * np.sin(5*z_grid)) * np.cos(theta_grid)
    y_chamber = (chamber_radius + vibration * np.sin(5*z_grid)) * np.sin(theta_grid)
    
    # Chamber colorscale based on temperature
    temp_ratio = (perf_data["chamber_temperature"] - 300) / 3000  # Normalized 
    chamber_colorscale = [
        [0, "rgb(150, 150, 150)"],  # Cold
        [0.5, "rgb(200, 100, 50)"],  # Warm
        [1, "rgb(220, 50, 50)"]      # Hot
    ]
    
    # Add the chamber
    fig.add_trace(go.Surface(
        x=x_chamber, y=y_chamber, z=z_grid,
        colorscale=chamber_colorscale,
        surfacecolor=np.ones_like(z_grid) * temp_ratio,
        showscale=False, 
        opacity=0.85,
        name="Combustion Chamber"
    ))

def add_bell_nozzle(fig, chamber_length, nozzle_length, chamber_radius, throat_radius, exit_radius, throat_position, perf_data, num_points):
    """Add a realistic bell-shaped nozzle to the visualization"""
    # Current time for animation
    t = perf_data["time"]
    
    # Calculate nozzle profile
    nozzle_z = np.linspace(chamber_length, chamber_length + nozzle_length, num_points)
    
    # Create a realistic bell-shaped nozzle profile
    r_profile = np.zeros_like(nozzle_z)
    for i, z in enumerate(nozzle_z):
        if z < throat_position:
            # Converging section (quadratic profile)
            ratio = (z - chamber_length) / (throat_position - chamber_length)
            r_profile[i] = chamber_radius - (chamber_radius - throat_radius) * ratio**1.5
        else:
            # Diverging section (bell-shaped)
            ratio = (z - throat_position) / (chamber_length + nozzle_length - throat_position)
            # Bell curve rather than linear
            r_profile[i] = throat_radius + (exit_radius - throat_radius) * (1 - np.exp(-2.5 * ratio))
    
    # Create grid for nozzle surface
    theta = np.linspace(0, 2*np.pi, num_points)
    theta_grid, z_grid = np.meshgrid(theta, nozzle_z)
    
    # Create cylindrical coordinates for nozzle surface
    r_grid = np.zeros_like(theta_grid)
    for i in range(len(nozzle_z)):
        r_grid[i,:] = r_profile[i]
    
    # Convert to Cartesian
    x_nozzle = r_grid * np.cos(theta_grid)
    y_nozzle = r_grid * np.sin(theta_grid)
    
    # Nozzle colorscale based on temperature gradient
    # Higher at chamber end, lower at exit
    temp_gradient = np.zeros_like(z_grid)
    temp_ratio = (perf_data["chamber_temperature"] - 300) / 3000
    
    for i, z in enumerate(nozzle_z):
        # Temperature drops along nozzle
        ratio = 1 - (z - chamber_length) / nozzle_length
        temp_gradient[i,:] = temp_ratio * ratio**0.5
    
    nozzle_colorscale = [
        [0, "rgb(50, 50, 150)"],     # Cool
        [0.5, "rgb(100, 100, 200)"],  # Medium
        [1, "rgb(200, 50, 50)"]      # Hot (throat)
    ]
    
    # Add the nozzle
    fig.add_trace(go.Surface(
        x=x_nozzle, y=y_nozzle, z=z_grid,
        surfacecolor=temp_gradient,
        colorscale=nozzle_colorscale,
        showscale=False, 
        opacity=0.8,
        name="Nozzle"
    ))

def add_injector_plate(fig, chamber_radius, perf_data):
    """Add detailed injector plate with injector elements"""
    # Injector plate
    z_injector = np.linspace(-0.02, 0, 10)
    r_injector = np.linspace(0, chamber_radius, 20)
    theta = np.linspace(0, 2*np.pi, 20)  # Changed from 40 to 20 to match r_injector
    
    r_grid, z_grid = np.meshgrid(r_injector, z_injector)
    theta_grid, _ = np.meshgrid(theta, z_injector)
    
    x_injector = r_grid * np.cos(theta_grid)
    y_injector = r_grid * np.sin(theta_grid)
    
    fig.add_trace(go.Surface(
        x=x_injector, y=y_injector, z=z_grid,
        colorscale="Greys",
        showscale=False, 
        opacity=0.9,
        name="Injector Plate"
    ))
    
    # Add injector elements
    num_elements = 8
    element_radius = 0.005
    element_z = np.linspace(-0.025, 0.01, 10)  # Slight protrusion into chamber
    element_theta = np.linspace(0, 2*np.pi, 15)
    
    # Create meshgrid for injector elements
    element_theta_grid, element_z_grid = np.meshgrid(element_theta, element_z)
    
    for i in range(num_elements):
        angle = i * (2*np.pi / num_elements)
        r_element = chamber_radius * 0.7  # Position at 70% of chamber radius
        
        x_center = r_element * np.cos(angle)
        y_center = r_element * np.sin(angle)
        
        # Create cylindrical surface for injector element
        x_element = x_center + element_radius * np.cos(element_theta_grid)
        y_element = y_center + element_radius * np.sin(element_theta_grid)
        
        fig.add_trace(go.Surface(
            x=x_element, y=y_element, z=element_z_grid,
            colorscale='Greens',
            showscale=False,
            opacity=0.9,
            name=f"Injector Element {i+1}"
        ))

def add_cooling_channels(fig, chamber_length, chamber_radius, perf_data):
    """Add realistic cooling channels around the chamber"""
    # Add cooling channels
    num_channels = 12
    channel_radius = 0.003
    
    for i in range(num_channels):
        angle = i * (2*np.pi / num_channels)
        
        # Create helical path for cooling channel
        t_channel = np.linspace(0, 6*np.pi, 100)
        z_channel = np.linspace(0, chamber_length, 100)
        
        # Radial position slightly outside chamber
        r_channel = chamber_radius + 0.005
        
        # Helical path
        x_channel = r_channel * np.cos(t_channel + angle)
        y_channel = r_channel * np.sin(t_channel + angle)
        
        # Color based on temperature
        temp_ratio = perf_data["wall_temperature"] / 1500
        color = f'rgba({50 + int(150*temp_ratio)}, {150 + int(100*(1-temp_ratio))}, 255, 0.8)'
        
        fig.add_trace(go.Scatter3d(
            x=x_channel, y=y_channel, z=z_channel,
            mode='lines',
            line=dict(width=5, color=color),
            name=f"Cooling Channel {i+1}"
        ))

def add_propellant_feed_lines(fig, chamber_diameter, chamber_radius):
    """Add propellant feed lines to the visualization"""
    # Fuel line
    fuel_line_start = [-chamber_diameter*0.8, -chamber_diameter*0.3, -0.03]
    fuel_line_end = [-chamber_radius*0.5, -chamber_radius*0.5, -0.02]
    
    fuel_line_x = [fuel_line_start[0], fuel_line_end[0]]
    fuel_line_y = [fuel_line_start[1], fuel_line_end[1]]
    fuel_line_z = [fuel_line_start[2], fuel_line_end[2]]
    
    fig.add_trace(go.Scatter3d(
        x=fuel_line_x, y=fuel_line_y, z=fuel_line_z,
        mode='lines',
        line=dict(width=10, color='blue'),
        name="Fuel Line"
    ))
    
    # Oxidizer line
    ox_line_start = [chamber_diameter*0.8, -chamber_diameter*0.3, -0.03]
    ox_line_end = [chamber_radius*0.5, -chamber_radius*0.5, -0.02]
    
    ox_line_x = [ox_line_start[0], ox_line_end[0]]
    ox_line_y = [ox_line_start[1], ox_line_end[1]]
    ox_line_z = [ox_line_start[2], ox_line_end[2]]
    
    fig.add_trace(go.Scatter3d(
        x=ox_line_x, y=ox_line_y, z=ox_line_z,
        mode='lines',
        line=dict(width=10, color='green'),
        name="Oxidizer Line"
    ))

def add_combustion_visualization(fig, chamber_length, chamber_radius, perf_data):
    """Add dynamic combustion visualization with particle effects"""
    # Parameters for combustion visualization
    num_points = 1000
    combustion_factor = perf_data["combustion_efficiency"]
    t = perf_data["time"]
    
    # Random points within chamber volume
    r_points = np.random.rand(num_points) * (chamber_radius * 0.9)
    theta_points = np.random.rand(num_points) * 2 * np.pi
    z_points = np.random.rand(num_points) * chamber_length
    
    # Convert to Cartesian
    x_comb = r_points * np.cos(theta_points)
    y_comb = r_points * np.sin(theta_points)
    z_comb = z_points
    
    # Colors based on temperature and time
    # Dynamic color effect
    colors = []
    sizes = []
    
    for i in range(num_points):
        # Position-based color (hotter near injector)
        z_ratio = 1 - z_points[i] / chamber_length
        
        # Time-based fluctuation
        flicker = 0.2 * np.sin(t * 10 + z_points[i] * 20 + r_points[i] * 15)
        
        # Color intensity based on combustion and position
        intensity = combustion_factor * (z_ratio + flicker)
        intensity = max(0, min(1, intensity))
        
        if z_ratio > 0.7:  # Near injector
            # Yellow/white hot
            colors.append(f'rgba(255, {180 + int(75*intensity)}, {50 + int(200*intensity)}, {0.7*intensity})')
        else:  # Further down chamber
            # Orange/red
            colors.append(f'rgba(255, {100 + int(155*intensity)}, {20 + int(80*intensity)}, {0.5*intensity})')
        
        # Vary particle size
        sizes.append(3 + 2 * np.random.rand())
    
    # Add combustion particles
    fig.add_trace(go.Scatter3d(
        x=x_comb, y=y_comb, z=z_comb,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=0)
        ),
        opacity=0.8,
        name="Combustion"
    ))

def add_exhaust_plume(fig, chamber_length, nozzle_length, exit_radius, perf_data):
    """Add exhaust plume with shock diamonds based on pressure ratio"""
    # Plume length depends on thrust
    plume_length = 0.2 + 0.0005 * perf_data["thrust"]
    
    # Parameters for shock diamonds
    exit_pressure = perf_data["exit_pressure"]
    ambient_pressure = perf_data["ambient_pressure"]
    t = perf_data["time"]
    
    # Mach diamonds appear when flow is under-expanded or over-expanded
    expansion_ratio = exit_pressure / ambient_pressure
    has_shock_diamonds = abs(1 - expansion_ratio) > 0.1 and perf_data["exit_velocity"] > 800
    
    # Calculate basic plume shape
    plume_z = np.linspace(
        chamber_length + nozzle_length, 
        chamber_length + nozzle_length + plume_length, 
        50
    )
    
    # Plume expansion based on pressure ratio
    if expansion_ratio > 1.1:  # Under-expanded
        # Plume expands more rapidly after exiting
        max_plume_radius = exit_radius * (1 + 0.5 * (expansion_ratio - 1))
        expansion_rate = 1.2
    elif expansion_ratio < 0.9:  # Over-expanded
        # Plume contracts initially then expands
        max_plume_radius = exit_radius * 0.9
        expansion_rate = 0.8
    else:  # Optimally expanded
        max_plume_radius = exit_radius * 1.1
        expansion_rate = 1.0
    
    # Base plume profile (without shock diamonds)
    plume_radius = np.zeros_like(plume_z)
    for i, z in enumerate(plume_z):
        # Distance from nozzle exit
        dist = z - (chamber_length + nozzle_length)
        
        # Normalize distance
        dist_norm = dist / plume_length
        
        # Calculate radius at this position
        if expansion_ratio < 0.9:  # Over-expanded
            # Initial contraction followed by expansion
            if dist_norm < 0.1:
                # Initial contraction
                plume_radius[i] = exit_radius * (1 - 0.2 * dist_norm / 0.1)
            else:
                # Subsequent expansion
                plume_radius[i] = exit_radius * 0.8 + max_plume_radius * (dist_norm - 0.1) / 0.9
        else:
            # Continuous expansion
            plume_radius[i] = exit_radius + (max_plume_radius - exit_radius) * dist_norm**expansion_rate
    
    # Add shock diamonds if present
    if has_shock_diamonds:
        # Number of diamonds depends on pressure mismatch
        num_diamonds = int(3 + 2 * abs(1 - expansion_ratio))
        
        # Modify plume profile to create shock diamond pattern
        for i, z in enumerate(plume_z):
            # Distance from nozzle exit
            dist = z - (chamber_length + nozzle_length)
            
            # Calculate shock diamond effect
            diamond_effect = 0
            
            for diamond in range(num_diamonds):
                # Diamond positions (closer together as we move downstream)
                diamond_pos = 0.05 * (1 + 0.8 * diamond) * plume_length
                
                # Diamond amplitude decreases downstream
                diamond_amp = 0.2 * (1 - 0.7 * diamond / num_diamonds)
                
                # Add sinusoidal perturbation for diamond
                if dist < diamond_pos + 0.05 and dist > diamond_pos - 0.05:
                    # Distance from diamond center
                    dist_from_center = abs(dist - diamond_pos)
                    
                    # Diamond shape effect (larger in middle)
                    shape_effect = 1 - (dist_from_center / 0.05)**2
                    
                    # Add effect
                    diamond_effect += diamond_amp * shape_effect
            
            # Apply diamond effect to radius
            plume_radius[i] = plume_radius[i] * (1 - diamond_effect)
    
    # Create plume surface
    theta = np.linspace(0, 2*np.pi, 40)
    r_grid, z_grid = np.meshgrid(np.linspace(0, 1, 20), plume_z)
    theta_grid, _ = np.meshgrid(theta, plume_z)
    
    # Adjust radius based on grid
    r_grid_scaled = np.zeros_like(r_grid)
    for i in range(r_grid.shape[0]):
        r_grid_scaled[i, :] = plume_radius[i] * r_grid[i, :]
    
    # Convert to Cartesian
    x_plume = r_grid_scaled * np.cos(theta_grid)
    y_plume = r_grid_scaled * np.sin(theta_grid)
    
    # Create color data for plume
    plume_colors = np.zeros_like(z_grid)
    
    for i, z in enumerate(plume_z):
        # Distance from nozzle exit
        dist = z - (chamber_length + nozzle_length)
        
        # Normalize distance
        dist_norm = dist / plume_length
        
        # Color varies based on distance and shock diamonds
        base_color = 1 - dist_norm**0.5  # Fades with distance
        
        # Add shock diamond effect to color
        if has_shock_diamonds:
            for diamond in range(num_diamonds):
                diamond_pos = 0.05 * (1 + 0.8 * diamond) * plume_length
                
                if dist < diamond_pos + 0.05 and dist > diamond_pos - 0.05:
                    # Distance from diamond center
                    dist_from_center = abs(dist - diamond_pos) / 0.05
                    
                    # Diamond creates intense color
                    diamond_color = 0.7 * (1 - dist_from_center**2)
                    
                    # Add effect (but don't exceed 1.0)
                    base_color = min(1.0, base_color + diamond_color)
        
        # Set color for this row
        plume_colors[i, :] = base_color
    
    # Choose colorscale based on propellants (mixture ratio)
    if perf_data["mixture_ratio"] > 3.0:  # Likely LOX/RP-1
        plume_colorscale = [
            [0, "rgba(255, 130, 20, 0)"],
            [0.2, "rgba(255, 160, 30, 0.2)"],
            [0.4, "rgba(255, 180, 50, 0.4)"],
            [0.6, "rgba(255, 220, 80, 0.6)"],
            [0.8, "rgba(255, 250, 170, 0.7)"],
            [1.0, "rgba(255, 255, 240, 0.9)"]
        ]
    else:  # LOX/LH2
        plume_colorscale = [
            [0, "rgba(30, 100, 255, 0)"],
            [0.2, "rgba(50, 150, 255, 0.2)"],
            [0.4, "rgba(100, 180, 255, 0.4)"],
            [0.6, "rgba(150, 210, 255, 0.6)"],
            [0.8, "rgba(200, 230, 255, 0.7)"],
            [1.0, "rgba(240, 250, 255, 0.9)"]
        ]
    
    # Add volume visualization for the plume
    fig.add_trace(go.Volume(
        x=x_plume.flatten(),
        y=y_plume.flatten(),
        z=z_grid.flatten(),
        value=plume_colors.flatten(),
        opacity=0.3,
        surface_count=20,
        colorscale=plume_colorscale,
        showscale=False,
        name="Exhaust Plume"
    ))

# Example usage if this module is run directly
if __name__ == "__main__":
    fig = create_enhanced_aerospace_visualization()
    fig.write_html("enhanced_aerospace_viz.html")
    print("Visualization saved to enhanced_aerospace_viz.html") 