#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import numpy as np
from visualization.animated_viz import create_animated_visualization, create_startup_shutdown_sequence

def run_animated_visualization(
    parameter_name=None,
    parameter_values=None,
    output_file=None,
    sequence=False,
    duration=5000,
    fps=30
):
    """
    Run the animated visualization with specified parameters.
    
    Args:
        parameter_name: Name of the parameter to animate
        parameter_values: List of values for the parameter
        output_file: Path to save the HTML output
        sequence: Whether to run a complete engine sequence animation
        duration: Animation duration in milliseconds
        fps: Frames per second
    """
    print("Generating Animated Visualization...")
    
    if sequence:
        # Run complete engine sequence animation
        fig = create_startup_shutdown_sequence(
            duration=duration,
            fps=fps
        )
        
        if output_file is None:
            output_file = "engine_sequence.html"
            
    elif parameter_name and parameter_values:
        # Run single parameter animation
        base_config = {
            "chamber_pressure": 2.0,
            "mixture_ratio": 2.1,
            "engine_status": "Nominal Operation"
        }
        
        fig = create_animated_visualization(
            parameter_name,
            parameter_values,
            base_config=base_config,
            duration=duration,
            fps=fps
        )
        
        if output_file is None:
            output_file = f"animated_{parameter_name}.html"
    else:
        print("Error: Either specify a parameter to animate or use --sequence")
        sys.exit(1)
    
    # Save the visualization
    fig.write_html(output_file)
    print(f"Animated visualization saved to: {output_file}")
    
    return fig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate animated engine visualizations")
    
    # Main parameters
    parser.add_argument("--parameter", type=str, help="Parameter name to animate")
    parser.add_argument("--values", type=str, help="Comma-separated values for the parameter or range in format min:max:steps")
    parser.add_argument("--output", type=str, help="Output HTML file path")
    parser.add_argument("--duration", type=int, default=5000, help="Animation duration in milliseconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    
    # Predefined animations
    parser.add_argument("--sequence", action="store_true", 
                       help="Generate complete engine sequence animation")
    
    args = parser.parse_args()
    
    # Convert values string to list
    parameter_values = None
    if args.values:
        try:
            if ":" in args.values:
                # Range format: min:max:steps
                range_parts = args.values.split(":")
                if len(range_parts) == 3:
                    min_val = float(range_parts[0])
                    max_val = float(range_parts[1])
                    num_steps = int(range_parts[2])
                    parameter_values = np.linspace(min_val, max_val, num_steps).tolist()
                else:
                    print("Error: Range format should be min:max:steps")
                    sys.exit(1)
            else:
                # Comma-separated values
                values_str = args.values.split(",")
                parameter_values = [float(v.strip()) for v in values_str]
        except Exception as e:
            print(f"Error parsing parameter values: {e}")
            sys.exit(1)
    
    run_animated_visualization(
        parameter_name=args.parameter,
        parameter_values=parameter_values,
        output_file=args.output,
        sequence=args.sequence,
        duration=args.duration,
        fps=args.fps
    ) 