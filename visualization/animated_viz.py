import plotly.graph_objects as go
import numpy as np
import os
from visualization.enhanced_aerospace_viz import create_enhanced_aerospace_visualization

def create_animated_visualization(
    parameter_name,
    parameter_values,
    base_config=None,
    duration=5000,
    transition_duration=100,
    fps=30
):
    """
    Create an animated visualization where a parameter varies over time.
    
    Args:
        parameter_name: Name of the parameter to animate (must be a valid parameter for
                       create_enhanced_aerospace_visualization)
        parameter_values: List of values for the parameter at each frame
        base_config: Dictionary with base configuration (default parameters will be used if None)
        duration: Total duration of the animation in milliseconds
        transition_duration: Duration of transition between frames in milliseconds
        fps: Frames per second (determines how many frames will be generated)
        
    Returns:
        Plotly figure with animation
    """
    if base_config is None:
        base_config = {}
    
    # Calculate number of frames
    num_frames = int(fps * duration / 1000)
    
    # Interpolate parameter values to match number of frames
    original_indices = np.linspace(0, num_frames - 1, len(parameter_values))
    frame_indices = np.arange(num_frames)
    interpolated_values = np.interp(frame_indices, original_indices, parameter_values)
    
    # Create base figure with initial configuration
    initial_config = base_config.copy()
    initial_config[parameter_name] = interpolated_values[0]
    fig = create_enhanced_aerospace_visualization(**initial_config)
    
    # Create frames list
    frames = []
    for i, value in enumerate(interpolated_values):
        frame_config = base_config.copy()
        frame_config[parameter_name] = value
        
        # Create a figure for this configuration
        frame_fig = create_enhanced_aerospace_visualization(**frame_config)
        
        # Add as a frame
        frames.append(go.Frame(
            data=frame_fig.data,
            name=f"frame_{i}",
            traces=list(range(len(frame_fig.data)))
        ))
    
    # Add frames to figure
    fig.frames = frames
    
    # Add animation buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None, 
                            dict(
                                frame=dict(duration=duration/num_frames, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=transition_duration),
                                mode="immediate"
                            )
                        ]
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=True),
                                mode="immediate",
                                transition=dict(duration=0)
                            )
                        ]
                    )
                ],
                direction="left",
                pad=dict(r=10, t=10),
                x=0.1,
                y=0,
                xanchor="right",
                yanchor="top"
            )
        ],
        sliders=[
            dict(
                active=0,
                steps=[
                    dict(
                        method="animate",
                        args=[
                            [f"frame_{i}"],
                            dict(
                                mode="immediate",
                                frame=dict(duration=0, redraw=True),
                                transition=dict(duration=transition_duration)
                            )
                        ],
                        label=f"{parameter_name}={interpolated_values[i]:.2f}"
                    )
                    for i in range(0, num_frames, max(1, num_frames // 10))
                ],
                pad=dict(b=10, t=60),
                len=0.9,
                x=0.1,
                y=0,
                xanchor="left",
                yanchor="top"
            )
        ]
    )
    
    # Add title with animated parameter
    fig.update_layout(
        title=dict(
            text=f"Animated {parameter_name} Visualization",
            x=0.5,
            y=0.95,
            font=dict(size=24)
        ),
        margin=dict(l=0, r=0, b=100, t=100),
    )
    
    return fig

def create_startup_shutdown_sequence(
    base_config=None,
    duration=10000,
    transition_duration=100,
    fps=30
):
    """
    Create an animated visualization of a complete engine startup to shutdown sequence.
    
    Args:
        base_config: Dictionary with base configuration (default parameters will be used if None)
        duration: Total duration of the animation in milliseconds
        transition_duration: Duration of transition between frames in milliseconds
        fps: Frames per second
        
    Returns:
        Plotly figure with animation
    """
    if base_config is None:
        base_config = {}
    
    # Calculate number of frames
    num_frames = int(fps * duration / 1000)
    
    # Define key sequence points (as fractions of total duration)
    sequence = [
        (0.0, "Standby", 0.1, 0.0),            # Start - Standby
        (0.1, "Ignition Sequence", 0.2, 0.0),  # Ignition start
        (0.2, "Ignition Sequence", 0.5, 1.0),  # Ignition progress
        (0.3, "Startup", 1.0, 1.5),            # Startup begin
        (0.4, "Startup", 1.5, 2.0),            # Startup progress
        (0.5, "Nominal Operation", 2.0, 2.1),  # Nominal operation begin
        (0.6, "Nominal Operation", 2.0, 2.1),  # Nominal operation
        (0.7, "Nominal Operation", 2.0, 2.1),  # Nominal operation continues
        (0.8, "Shutdown Sequence", 1.5, 2.0),  # Shutdown begin
        (0.9, "Shutdown Sequence", 0.8, 1.5),  # Shutdown progress
        (1.0, "Standby", 0.1, 0.0)             # Back to standby
    ]
    
    # Interpolate sequence to match number of frames
    frame_positions = np.linspace(0, 1, num_frames)
    sequence_positions = [s[0] for s in sequence]
    
    # Create arrays for each parameter
    statuses = [s[1] for s in sequence]
    pressure_values = [s[2] for s in sequence]
    mixture_values = [s[3] for s in sequence]
    
    # Interpolate numerical parameters
    interpolated_pressure = np.interp(frame_positions, sequence_positions, pressure_values)
    interpolated_mixture = np.interp(frame_positions, sequence_positions, mixture_values)
    
    # For status (categorical), use nearest neighbor interpolation
    interpolated_statuses = []
    for pos in frame_positions:
        # Find nearest status
        idx = np.argmin(np.abs(np.array(sequence_positions) - pos))
        interpolated_statuses.append(statuses[idx])
    
    # Create base figure with initial configuration
    initial_config = base_config.copy()
    initial_config["chamber_pressure"] = interpolated_pressure[0]
    initial_config["mixture_ratio"] = interpolated_mixture[0]
    initial_config["engine_status"] = interpolated_statuses[0]
    fig = create_enhanced_aerospace_visualization(**initial_config)
    
    # Create frames list
    frames = []
    for i in range(num_frames):
        frame_config = base_config.copy()
        frame_config["chamber_pressure"] = interpolated_pressure[i]
        frame_config["mixture_ratio"] = interpolated_mixture[i]
        frame_config["engine_status"] = interpolated_statuses[i]
        
        # Create a figure for this configuration
        frame_fig = create_enhanced_aerospace_visualization(**frame_config)
        
        # Add as a frame
        frames.append(go.Frame(
            data=frame_fig.data,
            name=f"frame_{i}",
            traces=list(range(len(frame_fig.data)))
        ))
    
    # Add frames to figure
    fig.frames = frames
    
    # Add animation buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None, 
                            dict(
                                frame=dict(duration=duration/num_frames, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=transition_duration),
                                mode="immediate"
                            )
                        ]
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=True),
                                mode="immediate",
                                transition=dict(duration=0)
                            )
                        ]
                    )
                ],
                direction="left",
                pad=dict(r=10, t=10),
                x=0.1,
                y=0,
                xanchor="right",
                yanchor="top"
            )
        ],
        sliders=[
            dict(
                active=0,
                steps=[
                    dict(
                        method="animate",
                        args=[
                            [f"frame_{i}"],
                            dict(
                                mode="immediate",
                                frame=dict(duration=0, redraw=True),
                                transition=dict(duration=transition_duration)
                            )
                        ],
                        label=f"Step {i}: {interpolated_statuses[i]}"
                    )
                    for i in range(0, num_frames, max(1, num_frames // 10))
                ],
                pad=dict(b=10, t=60),
                len=0.9,
                x=0.1,
                y=0,
                xanchor="left",
                yanchor="top"
            )
        ]
    )
    
    # Add title
    fig.update_layout(
        title=dict(
            text="Complete Engine Sequence: Startup to Shutdown",
            x=0.5,
            y=0.95,
            font=dict(size=24)
        ),
        margin=dict(l=0, r=0, b=100, t=100),
    )
    
    return fig

if __name__ == "__main__":
    # Example 1: Animate chamber pressure
    pressure_values = [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.1]
    
    fig = create_animated_visualization(
        "chamber_pressure",
        pressure_values,
        base_config={"engine_status": "Nominal Operation", "mixture_ratio": 2.1},
        duration=5000
    )
    
    output_file = "animated_pressure.html"
    fig.write_html(output_file)
    print(f"Animated pressure visualization saved to {output_file}")
    
    # Example 2: Create startup-shutdown sequence
    fig = create_startup_shutdown_sequence(duration=10000)
    
    output_file = "engine_sequence.html"
    fig.write_html(output_file)
    print(f"Engine sequence visualization saved to {output_file}") 