import numpy as np
import pandas as pd
import json
import time
import plotly.graph_objects as go
from engine_3d_viz import create_simplified_engine_3d, visualize_temperature_distribution, visualize_flow_velocity

def create_real_time_engine_visualization(
    engine_parameters=None,
    performance_data=None,
    mode="3d_model"  # Options: "3d_model", "temperature", "flow_velocity"
):
    """
    Create a real-time visualization of the engine with live performance data.
    
    Args:
        engine_parameters: Dictionary with engine geometry parameters
        performance_data: Dictionary with live performance data
        mode: Visualization mode
        
    Returns:
        Plotly figure with selected visualization
    """
    # Set default engine parameters if not provided
    if engine_parameters is None:
        engine_parameters = {
            "chamber_length": 0.15,  # m
            "chamber_diameter": 0.08,  # m
            "throat_diameter": 0.03,  # m
            "exit_diameter": 0.09,  # m
            "nozzle_length": 0.12,  # m
            "injector_plate_thickness": 0.02,  # m
        }
    
    # Get current animation frame (for effects)
    animation_frame = time.time() * 5  # Scaling factor for animation speed
    
    # Select visualization mode
    if mode == "temperature":
        # Temperature visualization with live data
        max_temp = 3000  # Default max temperature
        if performance_data and 'chamber_temperature' in performance_data:
            max_temp = performance_data['chamber_temperature']
            
        return visualize_temperature_distribution(
            chamber_length=engine_parameters["chamber_length"],
            chamber_diameter=engine_parameters["chamber_diameter"],
            throat_diameter=engine_parameters["throat_diameter"],
            exit_diameter=engine_parameters["exit_diameter"],
            nozzle_length=engine_parameters["nozzle_length"],
            max_temp=max_temp,
            performance_data=performance_data  # Pass performance data for enhanced visualization
        )
    
    elif mode == "flow_velocity":
        # Flow velocity visualization with live data
        max_velocity = 2000  # Default max velocity
        if performance_data and 'exit_velocity' in performance_data:
            max_velocity = performance_data['exit_velocity'] * 1.1  # Slight margin
            
        return visualize_flow_velocity(
            chamber_length=engine_parameters["chamber_length"],
            chamber_diameter=engine_parameters["chamber_diameter"],
            throat_diameter=engine_parameters["throat_diameter"],
            exit_diameter=engine_parameters["exit_diameter"],
            nozzle_length=engine_parameters["nozzle_length"],
            max_velocity=max_velocity,
            performance_data=performance_data  # Pass performance data for enhanced visualization
        )
    
    else:  # Default to 3D model
        return create_simplified_engine_3d(
            chamber_length=engine_parameters["chamber_length"],
            chamber_diameter=engine_parameters["chamber_diameter"],
            throat_diameter=engine_parameters["throat_diameter"],
            exit_diameter=engine_parameters["exit_diameter"],
            nozzle_length=engine_parameters["nozzle_length"],
            injector_plate_thickness=engine_parameters["injector_plate_thickness"],
            animation_frame=animation_frame,
            performance_data=performance_data,
            enhanced_visuals=True  # Enable enhanced visuals for more detailed rendering
        )


def generate_optimization_recommendations(performance_data):
    """
    Generate optimization recommendations based on current performance data.
    
    Args:
        performance_data: Dictionary with performance metrics
        
    Returns:
        Dictionary with recommendations
    """
    recommendations = {}
    
    # Check chamber pressure
    if 'chamber_pressure' in performance_data:
        pressure_mpa = performance_data['chamber_pressure'] / 1e6
        if pressure_mpa < 1.5:
            recommendations['Chamber Pressure'] = "Increase for better performance"
        elif pressure_mpa > 3.0:
            recommendations['Chamber Pressure'] = "Consider structural limits"
    
    # Check thrust efficiency
    if 'thrust' in performance_data and 'fuel_flow_rate' in performance_data and 'oxidizer_flow_rate' in performance_data:
        total_flow = performance_data['fuel_flow_rate'] + performance_data['oxidizer_flow_rate']
        if total_flow > 0:
            specific_impulse = performance_data['thrust'] / (total_flow * 9.81)  # Isp in seconds
            if specific_impulse < 200:
                recommendations['Efficiency'] = f"Low Isp ({specific_impulse:.1f}s). Check mixture ratio."
    
    # Check mixture ratio
    if 'mixture_ratio' in performance_data:
        o_f = performance_data['mixture_ratio']
        if o_f < 2.0:
            recommendations['Mixture Ratio'] = f"Current: {o_f:.2f}. Increase oxidizer."
        elif o_f > 3.0:
            recommendations['Mixture Ratio'] = f"Current: {o_f:.2f}. Reduce oxidizer."
    
    # Check throat erosion (simulated)
    if 'throat_erosion' in performance_data:
        if performance_data['throat_erosion'] > 0.05:  # 5% erosion
            recommendations['Throat'] = f"Erosion detected: {performance_data['throat_erosion']*100:.1f}%"
    
    # Check thermal management
    if 'wall_temperature' in performance_data:
        if performance_data['wall_temperature'] > 700:  # Kelvin
            recommendations['Cooling'] = f"Wall temp high: {performance_data['wall_temperature']:.0f}K"
    
    return recommendations


def save_visualization_data(performance_data, filename="visualization_data.json"):
    """
    Save performance data for visualization purposes.
    
    Args:
        performance_data: Dictionary with performance metrics
        filename: Output JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(performance_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving visualization data: {e}")
        return False


def load_visualization_data(filename="visualization_data.json"):
    """
    Load performance data for visualization purposes.
    
    Args:
        filename: Input JSON file
        
    Returns:
        Dictionary with performance data
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading visualization data: {e}")
        return None


if __name__ == "__main__":
    # Example usage with simulated real-time data
    example_performance_data = {
        "thrust": 750.0,  # N
        "chamber_pressure": 2.5e6,  # Pa
        "exit_velocity": 1800.0,  # m/s
        "mixture_ratio": 2.4,
        "fuel_flow_rate": 0.25,  # kg/s
        "oxidizer_flow_rate": 0.6,  # kg/s
        "chamber_temperature": 2800,  # K
        "wall_temperature": 650,  # K
        "throat_erosion": 0.02,  # 2% erosion
        "status": "Nominal Operation"
    }
    
    # Generate recommendations
    example_performance_data["recommendations"] = generate_optimization_recommendations(example_performance_data)
    
    # Create visualization with real-time data
    fig_engine = create_real_time_engine_visualization(
        performance_data=example_performance_data,
        mode="3d_model"
    )
    fig_engine.write_html("rocket_engine_3d_realtime.html")
    
    fig_temp = create_real_time_engine_visualization(
        performance_data=example_performance_data,
        mode="temperature"
    )
    fig_temp.write_html("temperature_distribution_realtime.html")
    
    fig_flow = create_real_time_engine_visualization(
        performance_data=example_performance_data,
        mode="flow_velocity"
    )
    fig_flow.write_html("flow_velocity_realtime.html") 