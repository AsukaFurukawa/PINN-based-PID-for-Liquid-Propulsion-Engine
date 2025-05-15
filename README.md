# PINN-based PID Controller for Liquid Propulsion Engine

This project implements a Physics-Informed Neural Network (PINN) to model and simulate a liquid rocket engine using methane and nitrous oxide propellants. The PINN is used to predict engine performance metrics and assist in PID controller tuning.

## Project Overview

The project combines hardware (a small-scale liquid rocket engine) with a software simulation system that uses deep learning, specifically Physics-Informed Neural Networks (PINNs), to model the internal dynamics of the engine.

### Key Components

1. **PINN Model**: Neural network that respects the physics of rocket engine operation
2. **Data Generation**: Synthetic data and physics-based calculations
3. **Visualization**: Interactive interface for parameter tuning and performance visualization
4. **PID Controller**: Control system for parameters like chamber pressure and thrust

## Advanced 3D Visualization

The visualization branch contains advanced 3D visualization capabilities using three.js to provide realistic and detailed rocket engine models with physics-based simulations. This visualization system is designed for educational purposes, engineering analysis, and real-time monitoring.

### Visualization Features

- **Realistic 3D Engine Models**: Detailed liquid rocket engine components with physically accurate proportions
- **Dynamic Effects**: Real-time visualization of combustion, exhaust plumes with shock diamonds, and transient behaviors
- **Physics-Based Simulation**: Performance metrics calculated from real rocket engine principles
- **Interactive Controls**: Adjust engine parameters and observe real-time effects
- **Educational Capabilities**: Learn about rocket engine design, performance, and operation

### Running the Visualization

To run the advanced 3D visualization:

```bash
python run_threed_visualization.py --mode simulation
```

Available modes:
- `simulation` - For interactive engine simulation
- `educational` - For educational/learning purposes
- `analysis` - For detailed performance analysis

See the [visualization documentation](visualization/three_js/README.md) for more details.

## Project Structure

```
PINN-based-PID-for-Liquid-Propulsion-Engine/
├── data/                    # Datasets and data generation scripts
├── models/                  # Neural network model definitions
├── utils/                   # Utility functions and physics equations
├── visualization/           # Visualization tools and dashboard
│   ├── enhanced_aerospace_viz.py  # Enhanced 3D engine visualization
│   ├── enhanced_dashboard.py      # Interactive dashboard for enhanced viz
│   ├── comparison_viz.py          # Side-by-side comparison visualization
│   ├── animated_viz.py            # Time-varying animated visualizations
│   └── ...                  # Other visualization modules
├── notebooks/               # Jupyter notebooks for experimentation
├── run_app.py               # Script to run the basic dashboard
├── run_enhanced_viz.py      # Script to run the enhanced aerospace visualization
├── run_standalone_viz.py    # Generate standalone visualization HTML
├── run_comparison_viz.py    # Generate side-by-side comparisons
├── run_animated_viz.py      # Generate animated visualizations
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the simulation:
   ```
   python run_app.py
   ```
4. Run the enhanced visualization:
   ```
   python run_enhanced_viz.py
   ```

## Physics Components

The PINN model incorporates the following physical principles:
- Conservation of mass and momentum
- Energy conservation
- Thrust equation
- Flow dynamics through nozzles
- Thermodynamic state relations

## Visualization

The project includes multiple visualization options:

### Basic Dashboard
The standard dashboard allows you to:
- Adjust engine parameters (mixture ratio, chamber geometry, etc.)
- Visualize predicted performance metrics
- Compare different engine configurations
- View real-time simulation results

### Enhanced Aerospace Visualization
For more detailed and realistic visualizations, the enhanced dashboard provides:

- **Realistic Engine Components**:
  - Bell-shaped nozzle with proper contour
  - Detailed injector face with multiple elements
  - Cooling channels with temperature-dependent effects
  - Propellant feed lines

- **Dynamic Visual Effects**:
  - Shock diamonds in exhaust plume based on pressure ratios
  - Particle-based combustion visualization
  - Temperature-based color gradients
  - Engine state visualization (startup, nominal, shutdown)

To use the enhanced visualization:
```
python run_enhanced_viz.py
```

### Standalone Visualizations

Generate static HTML visualizations with configurable parameters:
```
python run_standalone_viz.py --pressure 2.5 --mixture 2.1 --status "Nominal Operation"
```

### Comparison Visualizations

Compare multiple engine configurations side by side:
```
# Compare different engine statuses
python run_comparison_viz.py --status-comparison

# Compare different mixture ratios
python run_comparison_viz.py --parameter mixture_ratio --values 1.8,2.5,5.0
```

### Animated Visualizations

Create animated visualizations showing parameter changes over time:
```
# Animate chamber pressure changes
python run_animated_viz.py --parameter chamber_pressure --values 0.5:3.0:10

# Show complete engine sequence from startup to shutdown
python run_animated_viz.py --sequence
```

## Command-Line Options

### Enhanced Visualization Options
```
python run_enhanced_viz.py
```

### Standalone Visualization Options
```
python run_standalone_viz.py [--pressure PRESSURE] [--mixture MIXTURE] 
                             [--status STATUS] [--output OUTPUT_FILE]
```

### Comparison Visualization Options
```
python run_comparison_viz.py [--parameter PARAMETER] [--values VALUES]
                             [--output OUTPUT_FILE] [--status-comparison]
```

### Animated Visualization Options
```
python run_animated_viz.py [--parameter PARAMETER] [--values VALUES] 
                           [--output OUTPUT_FILE] [--duration MILLISECONDS]
                           [--fps FPS] [--sequence]
```

## Future Work

- Integration with actual engine hardware
- Real-time control and monitoring
- Enhanced physics models

## License

MIT License
 