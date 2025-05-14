#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from visualization.comparison_viz import create_comparison_visualization, generate_parametric_comparison

def run_comparison_visualization(
    parameter_name=None,
    parameter_values=None,
    output_file=None,
    status_comparison=False
):
    """
    Run the comparison visualization with specified parameters.
    
    Args:
        parameter_name: Name of the parameter to vary
        parameter_values: List of values for the parameter
        output_file: Path to save the HTML output
        status_comparison: Whether to run a predefined status comparison
    """
    print("Generating Comparison Visualization...")
    
    if status_comparison:
        # Run engine status comparison
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
        
        if output_file is None:
            output_file = "engine_status_comparison.html"
            
    elif parameter_name and parameter_values:
        # Run parametric comparison
        base_config = {
            "chamber_pressure": 2.0,
            "mixture_ratio": 2.1,
            "engine_status": "Nominal Operation"
        }
        
        fig = generate_parametric_comparison(
            parameter_name,
            parameter_values,
            base_config
        )
        
        if output_file is None:
            output_file = f"{parameter_name}_comparison.html"
    else:
        print("Error: Either specify a parameter to vary or use --status-comparison")
        sys.exit(1)
    
    # Save the visualization
    fig.write_html(output_file)
    print(f"Comparison visualization saved to: {output_file}")
    
    return fig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate engine comparison visualizations")
    
    # Main parameters
    parser.add_argument("--parameter", type=str, help="Parameter name to vary in comparison")
    parser.add_argument("--values", type=str, help="Comma-separated values for the parameter")
    parser.add_argument("--output", type=str, help="Output HTML file path")
    
    # Predefined comparisons
    parser.add_argument("--status-comparison", action="store_true", 
                       help="Generate engine status comparison")
    
    args = parser.parse_args()
    
    # Convert values string to list
    parameter_values = None
    if args.values:
        try:
            # Try to convert to appropriate type (float or string)
            values_str = args.values.split(",")
            
            # Check if values are numeric
            try:
                parameter_values = [float(v.strip()) for v in values_str]
            except ValueError:
                # If not numeric, keep as strings
                parameter_values = [v.strip() for v in values_str]
        except Exception as e:
            print(f"Error parsing parameter values: {e}")
            sys.exit(1)
    
    run_comparison_visualization(
        parameter_name=args.parameter,
        parameter_values=parameter_values,
        output_file=args.output,
        status_comparison=args.status_comparison
    ) 