# PINN-based PID Controller for Liquid Propulsion Engine

This project implements a Physics-Informed Neural Network (PINN) to model and simulate a liquid rocket engine using methane and nitrous oxide propellants. The PINN is used to predict engine performance metrics and assist in PID controller tuning.

## Project Overview

The project combines hardware (a small-scale liquid rocket engine) with a software simulation system that uses deep learning, specifically Physics-Informed Neural Networks (PINNs), to model the internal dynamics of the engine.

### Key Components

1. **PINN Model**: Neural network that respects the physics of rocket engine operation
2. **Data Generation**: Synthetic data and physics-based calculations
3. **Visualization**: Interactive interface for parameter tuning and performance visualization
4. **PID Controller**: Control system for parameters like chamber pressure and thrust

## Project Structure

```
PINN-based-PID-for-Liquid-Propulsion-Engine/
├── data/                 # Datasets and data generation scripts
├── models/               # Neural network model definitions
├── utils/                # Utility functions and physics equations
├── visualization/        # Visualization tools and dashboard
├── notebooks/            # Jupyter notebooks for experimentation
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the simulation:
   ```
   python visualization/app.py
   ```

## Physics Components

The PINN model incorporates the following physical principles:
- Conservation of mass and momentum
- Energy conservation
- Thrust equation
- Flow dynamics through nozzles
- Thermodynamic state relations

## Visualization

The project includes an interactive dashboard built with Streamlit that allows you to:
- Adjust engine parameters (mixture ratio, chamber geometry, etc.)
- Visualize predicted performance metrics
- Compare different engine configurations
- View real-time simulation results

## Future Work

- Integration with actual engine hardware
- Real-time control and monitoring
- Enhanced physics models
- Optimization for different performance metrics 