#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from visualization.enhanced_aerospace_viz import create_enhanced_aerospace_visualization

def run_standalone_visualization(
    chamber_pressure=2.0,
    mixture_ratio=2.1,
    chamber_length=0.15,
    chamber_diameter=0.08,
    throat_diameter=0.03,
    exit_diameter=0.09,
    nozzle_length=0.12,
    engine_status="Nominal Operation",
    output_file=None
):
    """
    Generate a standalone HTML file with the enhanced aerospace visualization.
    
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
        output_file: Path to save the HTML output (default: enhanced_aerospace_viz.html)
    """
    print("Generating Enhanced Aerospace Visualization...")
    
    # Create visualization figure
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
    
    # Save as HTML file
    if output_file is None:
        output_file = "enhanced_aerospace_viz.html"
    
    fig.write_html(output_file)
    print(f"Visualization saved to: {output_file}")
    
    return fig

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a standalone enhanced aerospace visualization")
    parser.add_argument("--pressure", type=float, default=2.0, help="Chamber pressure in MPa")
    parser.add_argument("--mixture", type=float, default=2.1, help="Mixture ratio (O/F)")
    parser.add_argument("--status", type=str, default="Nominal Operation", 
                        choices=["Nominal Operation", "Startup", "Shutdown Sequence", "Ignition Sequence", "Standby"],
                        help="Engine status")
    parser.add_argument("--output", type=str, help="Output HTML file path")
    
    args = parser.parse_args()
    
    run_standalone_visualization(
        chamber_pressure=args.pressure,
        mixture_ratio=args.mixture,
        engine_status=args.status,
        output_file=args.output
    ) 