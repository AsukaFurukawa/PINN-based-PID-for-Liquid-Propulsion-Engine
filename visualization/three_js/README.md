# Advanced 3D Liquid Rocket Engine Visualization

This module provides advanced 3D visualization capabilities for liquid rocket engines using three.js. It offers highly detailed real-time visualization with physics-based simulations for educational and engineering purposes.

## Features

- Realistic 3D rendering of liquid rocket engine components
- Real-time dynamic effects (combustion, exhaust plume, shock diamonds)
- Physics-based simulation of engine performance
- Interactive controls for adjusting engine parameters
- Multiple visualization modes (educational, simulation, analysis)
- Streamlit integration for interactive dashboards
- Standalone HTML version for web deployment

## Usage

### Streamlit Dashboard

The main way to use this visualization is through the Streamlit dashboard:

```bash
python run_threed_visualization.py --mode simulation
```

Available modes:
- `simulation` - For interactive engine simulation
- `educational` - For educational/learning purposes
- `analysis` - For detailed performance analysis

### Standalone HTML Version

For a lightweight standalone version, open the `index.html` file in a web browser:

```bash
cd visualization/three_js
# Then open index.html in your browser
```

### Python API

You can also use the visualization module directly in your own Python code:

```python
from visualization.advanced_threed_visualization import AdvancedThreeDVisualization

# Create a visualization instance
viz = AdvancedThreeDVisualization(height=600)

# Update engine state
viz.update_engine_state(
    status="Nominal Operation",
    chamber_pressure=2.0,
    mixture_ratio=2.1
)

# Update engine geometry
viz.update_engine_geometry(
    chamber_length=0.15,
    chamber_diameter=0.08,
    throat_diameter=0.03,
    exit_diameter=0.09,
    nozzle_length=0.12
)

# Render the visualization in a Streamlit app
viz.render()
```

## Components

### JavaScript Files

- `engine_visualization.js` - Main three.js visualization class
- `utils.js` - Utility functions for engine geometry and effects

### Python Files

- `advanced_threed_visualization.py` - Python bridge for three.js integration
- `threed_simulation_dashboard.py` - Streamlit dashboard for simulation mode
- `threed_educational_dashboard.py` - Streamlit dashboard for educational mode
- `threed_analysis_dashboard.py` - Streamlit dashboard for analysis mode

## Engine Parameters

The visualization supports the following engine parameters:

- **Chamber Pressure (MPa)** - Affects thrust, temperature, and efficiency
- **Mixture Ratio (O/F)** - Ratio of oxidizer to fuel mass flow
- **Chamber Length (m)** - Length of the combustion chamber
- **Chamber Diameter (m)** - Diameter of the combustion chamber
- **Throat Diameter (m)** - Diameter of the nozzle throat
- **Exit Diameter (m)** - Diameter of the nozzle exit
- **Nozzle Length (m)** - Length of the nozzle
- **Engine Status** - Current operating mode:
  - Standby
  - Ignition Sequence
  - Startup
  - Nominal Operation
  - Shutdown Sequence

## Dependencies

- three.js
- Streamlit (for dashboard)
- NumPy
- Plotly (for telemetry plots)
- streamlit-elements (for Streamlit-three.js integration)

## License

MIT License 