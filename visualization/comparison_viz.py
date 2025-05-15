import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from visualization.enhanced_aerospace_viz import create_enhanced_aerospace_visualization

def create_comparison_visualization(
    configurations,
    titles=None,
    layout_title="Engine Configuration Comparison"
):
    """
    Create a side-by-side comparison of multiple engine configurations.
    
    Args:
        configurations: List of dictionaries, each containing parameters for 
                       create_enhanced_aerospace_visualization
        titles: List of strings, titles for each configuration
        layout_title: Overall title for the comparison
        
    Returns:
        Plotly figure with multiple engine visualizations
    """
    num_configs = len(configurations)
    
    if titles is None:
        titles = [f"Configuration {i+1}" for i in range(num_configs)]
    
    # Create a subplot figure with appropriate dimensions
    rows = 1
    cols = num_configs
    
    if num_configs > 2:
        rows = 2
        cols = (num_configs + 1) // 2
    
    subplot_titles = titles
    fig = make_subplots(
        rows=rows, 
        cols=cols,
        specs=[[{"type": "scene"}] * cols] * rows,
        subplot_titles=subplot_titles,
    )
    
    # Create and add each configuration
    for i, config in enumerate(configurations):
        # Calculate row and column position
        row = (i // cols) + 1
        col = (i % cols) + 1
        
        # Create the visualization for this configuration
        config_fig = create_enhanced_aerospace_visualization(**config)
        
        # Add all traces from the configuration figure to the subplot
        for trace in config_fig.data:
            fig.add_trace(trace, row=row, col=col)
        
        # Update the scene for this subplot
        camera = dict(
            eye=dict(x=1.5, y=1.5, z=0.8),
            up=dict(x=0, y=0, z=1)
        )
        
        scene_key = f"scene{i+1}" if i > 0 else "scene"
        fig.update_layout(**{scene_key: dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode='data',
            camera=camera
        )})
    
    # Update overall layout
    fig.update_layout(
        title=dict(
            text=layout_title,
            x=0.5,
            y=0.95,
            font=dict(size=24)
        ),
        height=800 if rows > 1 else 600,
        margin=dict(l=0, r=0, b=0, t=100),
    )
    
    return fig

def generate_parametric_comparison(parameter_name, parameter_values, base_config=None):
    """
    Generate a comparison visualization with one parameter varied across configurations.
    
    Args:
        parameter_name: Name of the parameter to vary (must be a valid parameter for 
                       create_enhanced_aerospace_visualization)
        parameter_values: List of values to use for the parameter
        base_config: Dictionary with base configuration (default parameters will be used if None)
        
    Returns:
        Plotly figure with parametric comparison
    """
    if base_config is None:
        base_config = {}
    
    configurations = []
    titles = []
    
    for value in parameter_values:
        # Create a new configuration with the parameter value
        config = base_config.copy()
        config[parameter_name] = value
        
        # Add to configurations and titles
        configurations.append(config)
        titles.append(f"{parameter_name} = {value}")
    
    return create_comparison_visualization(
        configurations, 
        titles, 
        f"Parametric Comparison: Effect of {parameter_name}"
    )

if __name__ == "__main__":
    # Example: Compare different engine statuses
    engine_statuses = ["Startup", "Nominal Operation", "Shutdown Sequence"]
    
    configurations = [
        {"engine_status": status, "chamber_pressure": 2.0, "mixture_ratio": 2.1}
        for status in engine_statuses
    ]
    
    fig = create_comparison_visualization(
        configurations,
        titles=engine_statuses,
        layout_title="Engine Status Comparison"
    )
    
    fig.write_html("engine_status_comparison.html")
    print("Comparison visualization saved to engine_status_comparison.html")
    
    # Example: Parametric study of mixture ratio
    mixture_ratios = [1.8, 3.0, 5.0]
    base_config = {
        "chamber_pressure": 2.5,
        "engine_status": "Nominal Operation"
    }
    
    fig = generate_parametric_comparison(
        "mixture_ratio", 
        mixture_ratios, 
        base_config
    )
    
    fig.write_html("mixture_ratio_comparison.html")
    print("Parametric comparison saved to mixture_ratio_comparison.html") 