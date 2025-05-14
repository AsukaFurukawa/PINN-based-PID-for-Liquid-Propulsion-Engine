import plotly.graph_objects as go
import numpy as np
import pandas as pd
import json
import time


def create_simplified_engine_3d(
    chamber_length=0.15,  # m
    chamber_diameter=0.08,  # m
    throat_diameter=0.03,  # m
    exit_diameter=0.09,  # m
    nozzle_length=0.12,  # m
    injector_plate_thickness=0.02,  # m
    cooling_channels=True,
    num_points=100,
    animation_frame=None,
    performance_data=None,
    enhanced_visuals=False
):
    """
    Create a 3D visualization of a simplified rocket engine with optional performance data overlay.
    
    Args:
        chamber_length: Chamber length [m]
        chamber_diameter: Chamber diameter [m]
        throat_diameter: Throat diameter [m]
        exit_diameter: Exit diameter [m]
        nozzle_length: Nozzle length [m]
        injector_plate_thickness: Injector plate thickness [m]
        cooling_channels: Whether to show cooling channels
        num_points: Number of points for resolution
        animation_frame: Current animation frame (if animating)
        performance_data: Dictionary with performance data to display
        enhanced_visuals: Enable enhanced visual effects for more detailed rendering
        
    Returns:
        Plotly figure with 3D visualization
    """
    # Create figure
    fig = go.Figure()
    
    # Generate points for chamber (cylinder)
    theta = np.linspace(0, 2*np.pi, num_points)
    z_chamber = np.linspace(0, chamber_length, num_points)
    r_chamber = chamber_diameter / 2
    
    theta_grid, z_grid = np.meshgrid(theta, z_chamber)
    x_chamber = r_chamber * np.cos(theta_grid)
    y_chamber = r_chamber * np.sin(theta_grid)
    
    # Add combustion chamber
    fig.add_trace(go.Surface(
        x=x_chamber,
        y=y_chamber,
        z=z_grid,
        colorscale='Reds',
        showscale=False,
        opacity=0.7,
        name="Combustion Chamber"
    ))
    
    # Generate points for nozzle (converging-diverging)
    z_nozzle = np.linspace(chamber_length, chamber_length + nozzle_length, num_points)
    
    # Define radius profile for converging-diverging nozzle
    # Linear approximation with three sections
    r_throat = throat_diameter / 2
    r_exit = exit_diameter / 2
    
    # Transition point from chamber to throat
    throat_position = chamber_length + nozzle_length * 0.3
    
    # Create radius profile along z-axis
    r_nozzle = np.zeros_like(z_nozzle)
    
    for i, z in enumerate(z_nozzle):
        if z < throat_position:
            # Converging section (linear)
            ratio = (z - chamber_length) / (throat_position - chamber_length)
            r_nozzle[i] = r_chamber - ratio * (r_chamber - r_throat)
        else:
            # Diverging section (linear)
            ratio = (z - throat_position) / (chamber_length + nozzle_length - throat_position)
            r_nozzle[i] = r_throat + ratio * (r_exit - r_throat)
    
    theta_grid, z_grid = np.meshgrid(theta, z_nozzle)
    r_grid, _ = np.meshgrid(r_nozzle, theta)
    r_grid = r_grid.T
    
    x_nozzle = r_grid * np.cos(theta_grid)
    y_nozzle = r_grid * np.sin(theta_grid)
    
    # Add nozzle
    fig.add_trace(go.Surface(
        x=x_nozzle,
        y=y_nozzle,
        z=z_grid,
        colorscale='Blues',
        showscale=False,
        opacity=0.7,
        name="Nozzle"
    ))
    
    # Add injector plate
    z_injector = np.linspace(-injector_plate_thickness, 0, 10)
    r_injector = np.linspace(0, r_chamber, 10)
    
    r_grid, z_grid = np.meshgrid(r_injector, z_injector)
    
    # Create theta grid with same shape as r_grid
    theta_temp = np.linspace(0, 2*np.pi, 10)
    theta_grid, _ = np.meshgrid(theta_temp, z_injector)
    
    x_injector = r_grid * np.cos(theta_grid)
    y_injector = r_grid * np.sin(theta_grid)
    
    fig.add_trace(go.Surface(
        x=x_injector,
        y=y_injector,
        z=z_grid,
        colorscale='Greys',
        showscale=False,
        opacity=0.9,
        name="Injector Plate"
    ))
    
    # Add cooling channels if requested
    if cooling_channels:
        # Create helical cooling channels around the chamber
        t = np.linspace(0, 6*np.pi, 200)  # 3 turns
        r_channel = r_chamber + 0.005  # Slightly outside chamber
        channel_width = 0.003
        
        # First cooling channel
        x_channel = r_channel * np.cos(t)
        y_channel = r_channel * np.sin(t)
        z_channel = np.linspace(0, chamber_length, 200)
        
        fig.add_trace(go.Scatter3d(
            x=x_channel,
            y=y_channel,
            z=z_channel,
            mode='lines',
            line=dict(width=5, color='cyan'),
            name="Cooling Channel 1"
        ))
        
        # Second cooling channel (offset by 180 degrees)
        x_channel2 = r_channel * np.cos(t + np.pi)
        y_channel2 = r_channel * np.sin(t + np.pi)
        
        fig.add_trace(go.Scatter3d(
            x=x_channel2,
            y=y_channel2,
            z=z_channel,
            mode='lines',
            line=dict(width=5, color='cyan'),
            name="Cooling Channel 2"
        ))
    
    # Add injector elements
    num_elements = 8  # Number of injector elements
    element_radius = 0.004  # Radius of injector element
    
    for i in range(num_elements):
        angle = i * (2*np.pi / num_elements)
        r_element = r_chamber * 0.7  # Position elements at 70% of chamber radius
        
        x_element = r_element * np.cos(angle)
        y_element = r_element * np.sin(angle)
        
        # Create mini cylinder for each injector element
        theta_element = np.linspace(0, 2*np.pi, 20)
        z_element = np.linspace(-injector_plate_thickness, 0.01, 10)  # Slight protrusion
        
        theta_grid, z_grid = np.meshgrid(theta_element, z_element)
        x_element_surface = x_element + element_radius * np.cos(theta_grid)
        y_element_surface = y_element + element_radius * np.sin(theta_grid)
        
        fig.add_trace(go.Surface(
            x=x_element_surface,
            y=y_element_surface,
            z=z_grid,
            colorscale='Greens',
            showscale=False,
            opacity=0.9,
            name=f"Injector Element {i+1}"
        ))
    
    # Add a visualization of the combustion
    # Create a cone-like shape inside the chamber
    z_combustion = np.linspace(0.01, chamber_length * 0.9, 50)
    r_combustion = np.linspace(r_chamber * 0.4, r_chamber * 0.8, 50)
    
    r_grid, z_grid = np.meshgrid(r_combustion, z_combustion)
    
    # Create a compatible theta grid
    theta_comb = np.linspace(0, 2*np.pi, 50)
    theta_grid, _ = np.meshgrid(theta_comb, z_combustion)
    
    x_combustion = r_grid * np.cos(theta_grid)
    y_combustion = r_grid * np.sin(theta_grid)
    
    fig.add_trace(go.Volume(
        x=x_combustion.flatten(),
        y=y_combustion.flatten(),
        z=z_grid.flatten(),
        opacity=0.2,
        surface_count=20,
        colorscale='YlOrRd',
        name="Combustion Zone"
    ))
    
    # Add exhaust plume
    z_exhaust = np.linspace(chamber_length + nozzle_length, chamber_length + nozzle_length + 0.2, 50)
    r_exhaust = np.linspace(r_exit, r_exit * 1.5, 50)
    
    r_grid, z_grid = np.meshgrid(r_exhaust, z_exhaust)
    
    # Create a compatible theta grid
    theta_exhaust = np.linspace(0, 2*np.pi, 50)
    theta_grid, _ = np.meshgrid(theta_exhaust, z_exhaust)
    
    x_exhaust = r_grid * np.cos(theta_grid)
    y_exhaust = r_grid * np.sin(theta_grid)
    
    fig.add_trace(go.Volume(
        x=x_exhaust.flatten(),
        y=y_exhaust.flatten(),
        z=z_grid.flatten(),
        opacity=0.1,
        surface_count=20,
        colorscale='Blues',
        name="Exhaust Plume"
    ))
    
    # Set layout
    fig.update_layout(
        title="3D Rocket Engine Model",
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode='data'
        ),
        width=900,
        height=700,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    return fig


def visualize_temperature_distribution(
    chamber_length=0.15,  # m
    chamber_diameter=0.08,  # m
    throat_diameter=0.03,  # m
    exit_diameter=0.09,  # m
    nozzle_length=0.12,  # m
    max_temp=3000,  # K
    ambient_temp=300,  # K
    num_points=50,
    performance_data=None
):
    """
    Create a 3D visualization of temperature distribution in a rocket engine.
    
    Args:
        chamber_length: Chamber length [m]
        chamber_diameter: Chamber diameter [m]
        throat_diameter: Throat diameter [m]
        exit_diameter: Exit diameter [m]
        nozzle_length: Nozzle length [m]
        max_temp: Maximum temperature [K]
        ambient_temp: Ambient temperature [K]
        num_points: Number of points for resolution
        performance_data: Dictionary with live performance data
        
    Returns:
        Plotly figure with 3D visualization
    """
    # Create figure
    fig = go.Figure()
    
    # Create a grid for the entire engine (chamber + nozzle)
    z_total = np.linspace(0, chamber_length + nozzle_length, num_points)
    r_chamber = chamber_diameter / 2
    r_throat = throat_diameter / 2
    r_exit = exit_diameter / 2
    
    # Throat position
    throat_position = chamber_length + nozzle_length * 0.3
    
    # Create radius profile for the engine
    r_profile = np.zeros_like(z_total)
    
    for i, z in enumerate(z_total):
        if z <= chamber_length:
            # Chamber (constant radius)
            r_profile[i] = r_chamber
        elif z < throat_position:
            # Converging section
            ratio = (z - chamber_length) / (throat_position - chamber_length)
            r_profile[i] = r_chamber - ratio * (r_chamber - r_throat)
        else:
            # Diverging section
            ratio = (z - throat_position) / (chamber_length + nozzle_length - throat_position)
            r_profile[i] = r_throat + ratio * (r_exit - r_throat)
    
    # Create a temperature distribution model
    # Peak temperature near the injector, then gradual decrease
    temp_distribution = np.zeros((num_points, num_points))
    
    # Radial positions
    r_positions = np.linspace(0, 1, num_points)  # Normalized radius
    
    for i, z in enumerate(z_total):
        for j, r_norm in enumerate(r_positions):
            # Actual radius at this position
            r_actual = r_norm * r_profile[i]
            
            # Base temperature profile along axis
            if z < chamber_length * 0.3:
                # Temperature rises in the first third of the chamber
                z_factor = z / (chamber_length * 0.3)
                base_temp = ambient_temp + z_factor * (max_temp - ambient_temp)
            elif z < throat_position:
                # Temperature is high in the chamber, then starts dropping toward throat
                z_factor = (z - chamber_length * 0.3) / (throat_position - chamber_length * 0.3)
                base_temp = max_temp - z_factor * (max_temp - max_temp * 0.7)
            else:
                # Temperature drops more rapidly in the diverging section
                z_factor = (z - throat_position) / (chamber_length + nozzle_length - throat_position)
                base_temp = max_temp * 0.7 - z_factor * (max_temp * 0.7 - ambient_temp)
            
            # Radial temperature variation (hotter in the core, cooler near walls)
            # Use quadratic profile: T = T_base * (1 - r_norm^2)
            radial_factor = 1 - 0.5 * r_norm**2
            
            # Combine factors
            temp_distribution[i, j] = base_temp * radial_factor
    
    # Create cylindrical grid
    theta = np.linspace(0, 2*np.pi, 36)
    z_grid, r_norm_grid = np.meshgrid(z_total, r_positions)
    r_grid = r_norm_grid * np.reshape(r_profile, (1, -1))
    
    # Convert to Cartesian coordinates
    x = np.zeros((num_points, num_points, len(theta)))
    y = np.zeros((num_points, num_points, len(theta)))
    z = np.zeros((num_points, num_points, len(theta)))
    
    for k, angle in enumerate(theta):
        x[:, :, k] = r_grid * np.cos(angle)
        y[:, :, k] = r_grid * np.sin(angle)
        z[:, :, k] = z_grid
    
    # Create temperature array matching the 3D coordinates
    temp_3d = np.zeros((num_points, num_points, len(theta)))
    for k in range(len(theta)):
        temp_3d[:, :, k] = temp_distribution.T
    
    # Create 3D volume plot
    fig.add_trace(go.Volume(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        value=temp_3d.flatten(),
        opacity=0.3,
        surface_count=20,
        colorscale='Jet',
        colorbar=dict(
            title=dict(
                text="Temperature [K]",
                side="right"
            )
        ),
        caps=dict(
            x_show=False,
            y_show=False,
            z_show=False
        ),
        name="Temperature Distribution"
    ))
    
    # Add engine outline
    theta_outline = np.linspace(0, 2*np.pi, 100)
    z_outline = np.concatenate([z_total, z_total[::-1]])
    r_outline = np.concatenate([r_profile, np.zeros_like(r_profile)])
    
    x_outline = r_outline * np.cos(theta_outline[0])
    y_outline = r_outline * np.sin(theta_outline[0])
    
    fig.add_trace(go.Scatter3d(
        x=x_outline,
        y=y_outline,
        z=z_outline,
        mode='lines',
        line=dict(width=4, color='black'),
        name="Engine Outline"
    ))
    
    # Set layout
    fig.update_layout(
        title="Temperature Distribution in Rocket Engine",
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode='data'
        ),
        width=900,
        height=700,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    return fig


def visualize_flow_velocity(
    chamber_length=0.15,  # m
    chamber_diameter=0.08,  # m
    throat_diameter=0.03,  # m
    exit_diameter=0.09,  # m
    nozzle_length=0.12,  # m
    max_velocity=2000,  # m/s
    num_points=20,
    performance_data=None
):
    """
    Create a 3D visualization of flow velocity in a rocket engine.
    
    Args:
        chamber_length: Chamber length [m]
        chamber_diameter: Chamber diameter [m]
        throat_diameter: Throat diameter [m]
        exit_diameter: Exit diameter [m]
        nozzle_length: Nozzle length [m]
        max_velocity: Maximum flow velocity [m/s]
        num_points: Number of points for resolution
        performance_data: Dictionary with live performance data
        
    Returns:
        Plotly figure with 3D visualization
    """
    # Create figure
    fig = go.Figure()
    
    # Create a grid for the entire engine (chamber + nozzle)
    z_total = np.linspace(0, chamber_length + nozzle_length, num_points)
    r_chamber = chamber_diameter / 2
    r_throat = throat_diameter / 2
    r_exit = exit_diameter / 2
    
    # Throat position
    throat_position = chamber_length + nozzle_length * 0.3
    
    # Create radius profile for the engine
    r_profile = np.zeros_like(z_total)
    
    for i, z in enumerate(z_total):
        if z <= chamber_length:
            # Chamber (constant radius)
            r_profile[i] = r_chamber
        elif z < throat_position:
            # Converging section
            ratio = (z - chamber_length) / (throat_position - chamber_length)
            r_profile[i] = r_chamber - ratio * (r_chamber - r_throat)
        else:
            # Diverging section
            ratio = (z - throat_position) / (chamber_length + nozzle_length - throat_position)
            r_profile[i] = r_throat + ratio * (r_exit - r_throat)
    
    # Calculate areas at each position
    areas = np.pi * r_profile**2
    
    # Model velocity based on continuity equation
    # For constant mass flow, v ∝ 1/A
    # Normalize by the throat area (maximum velocity at throat)
    normalized_velocity = areas[0] / areas
    
    # Adjust velocity profile to be physical:
    # Low at injector, increases toward throat, then slightly decreases in diverging section
    axial_velocity = np.zeros_like(normalized_velocity)
    
    for i, z in enumerate(z_total):
        if z < chamber_length * 0.1:
            # Near injector face, velocity is low but increasing
            factor = z / (chamber_length * 0.1)
            axial_velocity[i] = 0.1 * max_velocity * factor
        elif z < chamber_length:
            # In the chamber, velocity increases gradually
            factor = (z - chamber_length * 0.1) / (chamber_length - chamber_length * 0.1)
            axial_velocity[i] = 0.1 * max_velocity + factor * (0.3 * max_velocity - 0.1 * max_velocity)
        elif z < throat_position:
            # In the converging section, velocity increases rapidly
            factor = (z - chamber_length) / (throat_position - chamber_length)
            axial_velocity[i] = 0.3 * max_velocity + factor * (max_velocity - 0.3 * max_velocity)
        else:
            # In the diverging section, velocity increases but less rapidly
            factor = (z - throat_position) / (chamber_length + nozzle_length - throat_position)
            # Use a more realistic expansion model
            axial_velocity[i] = max_velocity * (1 + 0.5 * factor)
    
    # Create velocity vectors for visualization
    # We'll create a grid of points and vectors
    
    # Radial positions (normalized)
    r_positions = np.linspace(0, 0.9, 4)  # 4 radial positions (avoid edge)
    
    # Angular positions
    theta_positions = np.linspace(0, 2*np.pi, 8, endpoint=False)  # 8 angular positions
    
    # Create lists to store vector positions and components
    x, y, z = [], [], []
    u, v, w = [], [], []
    
    # Create vectors at various positions
    for i, z_pos in enumerate(z_total):
        # Area at this position
        area = areas[i]
        
        # Velocity at this position
        vel = axial_velocity[i]
        
        # Current radius in profile
        r_current = r_profile[i]
        
        for r_norm in r_positions:
            r_actual = r_norm * r_current
            
            for theta in theta_positions:
                # Vector start position (Cartesian)
                x_pos = r_actual * np.cos(theta)
                y_pos = r_actual * np.sin(theta)
                
                # Add to position lists
                x.append(x_pos)
                y.append(y_pos)
                z.append(z_pos)
                
                # Vector components (mainly axial with small radial component)
                # Add a small radial component in the converging/diverging sections
                u_component, v_component, w_component = 0, 0, vel
                
                if z_pos > chamber_length and z_pos < throat_position:
                    # Converging section - add inward radial component
                    radial_component = -0.2 * vel
                    u_component = radial_component * np.cos(theta)
                    v_component = radial_component * np.sin(theta)
                elif z_pos > throat_position:
                    # Diverging section - add outward radial component
                    radial_component = 0.1 * vel
                    u_component = radial_component * np.cos(theta)
                    v_component = radial_component * np.sin(theta)
                
                # Add to vector component lists
                u.append(u_component)
                v.append(v_component)
                w.append(w_component)
    
    # Normalize vectors for visualization
    vectors = np.array([u, v, w]).T
    vector_lengths = np.linalg.norm(vectors, axis=1)
    max_length = np.max(vector_lengths)
    
    # Scale factors for visualization
    scale_factor = chamber_length / (10 * max_length)
    
    # Scale vectors for visualization
    u = np.array(u) * scale_factor
    v = np.array(v) * scale_factor
    w = np.array(w) * scale_factor
    
    # Add vectors to plot
    fig.add_trace(go.Cone(
        x=x,
        y=y,
        z=z,
        u=u,
        v=v,
        w=w,
        colorscale='Blues',
        colorbar=dict(
            title="Flow Velocity [m/s]"
        ),
        sizemode="absolute",
        sizeref=0.05,
        anchor="tail",
        name="Flow Vectors"
    ))
    
    # Add engine outline
    theta_outline = np.linspace(0, 2*np.pi, 36)
    z_grid, theta_grid = np.meshgrid(z_total, theta_outline)
    r_grid, _ = np.meshgrid(r_profile, theta_outline)
    
    x_outline = r_grid * np.cos(theta_grid)
    y_outline = r_grid * np.sin(theta_grid)
    
    fig.add_trace(go.Surface(
        x=x_outline,
        y=y_outline,
        z=z_grid,
        opacity=0.2,
        colorscale='Greys',
        showscale=False,
        name="Engine Outline"
    ))
    
    # Set layout
    fig.update_layout(
        title="Flow Velocity Visualization in Rocket Engine",
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode='data'
        ),
        width=900,
        height=700,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    return fig


if __name__ == "__main__":
    # Example usage
    fig_engine = create_simplified_engine_3d()
    fig_engine.write_html("rocket_engine_3d.html")
    
    fig_temp = visualize_temperature_distribution()
    fig_temp.write_html("temperature_distribution.html")
    
    fig_flow = visualize_flow_velocity()
    fig_flow.write_html("flow_velocity.html") 