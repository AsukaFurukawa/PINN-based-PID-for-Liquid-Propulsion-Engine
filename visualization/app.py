import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import sys
import os
import torch

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.pinn_model import RocketEnginePINN, train_pinn
from utils.rocket_physics import (
    calculate_thrust,
    calculate_exit_velocity,
    calculate_mass_flow_rate,
    calculate_exit_mach,
    calculate_pressure_ratio,
    create_combustion_products_properties
)
from utils.pid_controller import PIDController, PINNGuidedPIDController
from data.data_generator import RocketEngineDataGenerator


def load_or_create_model(load_existing=False, model_path='models/rocket_engine_pinn.pt'):
    """
    Load existing model or create a new one if not available.
    
    Args:
        load_existing: Whether to try loading an existing model
        model_path: Path to saved model
        
    Returns:
        Trained PINN model
    """
    model = RocketEnginePINN()
    
    if load_existing and os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        model.eval()
        return model
    
    # Generate training data
    generator = RocketEngineDataGenerator()
    inputs, outputs = generator.generate_dataset(num_samples=2000)
    
    # Convert to PyTorch tensors
    inputs_tensor = torch.tensor(inputs, dtype=torch.float32)
    outputs_tensor = torch.tensor(outputs, dtype=torch.float32)
    
    # Train the PINN model
    losses = train_pinn(
        model, 
        inputs_tensor, 
        outputs_tensor, 
        num_epochs=1000, 
        learning_rate=0.001,
        physics_weight=0.5
    )
    
    # Save the model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save(model.state_dict(), model_path)
    
    model.eval()
    return model


def create_engine_simulator(model, time_span=10.0, time_step=0.1):
    """
    Create a simulator function based on the trained PINN model.
    
    Args:
        model: Trained PINN model
        time_span: Total simulation time
        time_step: Time step for simulation
        
    Returns:
        Simulator function
    """
    time_points = np.arange(0, time_span, time_step)
    num_steps = len(time_points)
    
    def simulator(mixture_ratio, chamber_pressure, chamber_temperature, 
                 chamber_volume, throat_diameter, exit_diameter, fuel_flow_rate):
        """
        Simulate rocket engine behavior over time.
        
        Args:
            mixture_ratio: Mixture ratio (O/F)
            chamber_pressure: Initial chamber pressure [Pa]
            chamber_temperature: Chamber temperature [K]
            chamber_volume: Chamber volume [m³]
            throat_diameter: Throat diameter [m]
            exit_diameter: Exit diameter [m]
            fuel_flow_rate: Fuel flow rate [kg/s]
            
        Returns:
            DataFrame with simulation results
        """
        # Create input array
        inputs = np.zeros((num_steps, 8))
        
        # Fill constant parameters
        inputs[:, 0] = mixture_ratio  # Mixture ratio
        inputs[:, 1] = chamber_pressure  # Initial chamber pressure
        inputs[:, 2] = chamber_temperature  # Chamber temperature
        inputs[:, 3] = chamber_volume  # Chamber volume
        inputs[:, 4] = throat_diameter  # Throat diameter
        inputs[:, 5] = exit_diameter  # Exit diameter
        inputs[:, 7] = fuel_flow_rate  # Fuel flow rate
        
        # Fill time points
        inputs[:, 6] = time_points
        
        # Convert to tensor
        inputs_tensor = torch.tensor(inputs, dtype=torch.float32)
        
        # Get predictions
        with torch.no_grad():
            outputs = model(inputs_tensor).cpu().numpy()
            
        # Extract outputs
        chamber_pressure_out = outputs[:, 0]
        exit_velocity = outputs[:, 1]
        thrust = outputs[:, 2]
        
        # Create DataFrame
        results = pd.DataFrame({
            'Time': time_points,
            'Chamber Pressure': chamber_pressure_out,
            'Exit Velocity': exit_velocity,
            'Thrust': thrust
        })
        
        return results
    
    return simulator


def run_pid_simulation(simulator, pid_controller, setpoint, control_variable='Thrust',
                       simulation_time=10.0, time_step=0.1):
    """
    Run a simulation with PID control.
    
    Args:
        simulator: Engine simulator function
        pid_controller: PID controller
        setpoint: Controller setpoint
        control_variable: Variable to control ('Thrust' or 'Chamber Pressure')
        simulation_time: Total simulation time
        time_step: Time step for simulation
        
    Returns:
        DataFrame with simulation results
    """
    # Set controller setpoint
    pid_controller.set_setpoint(setpoint)
    
    # Initialize parameters
    mixture_ratio = 2.5
    chamber_pressure = 2.0e6  # Pa
    chamber_temperature = 3000  # K
    chamber_volume = 0.001  # m³
    throat_diameter = 0.03  # m
    exit_diameter = 0.09  # m
    fuel_flow_rate = 0.2  # kg/s
    
    # Number of time steps
    time_points = np.arange(0, simulation_time, time_step)
    num_steps = len(time_points)
    
    # Arrays to store results
    chamber_pressure_arr = np.zeros(num_steps)
    exit_velocity_arr = np.zeros(num_steps)
    thrust_arr = np.zeros(num_steps)
    control_output_arr = np.zeros(num_steps)
    fuel_flow_arr = np.zeros(num_steps)
    
    # Run simulation
    for i, t in enumerate(time_points):
        # Run simulator with current parameters
        results = simulator(
            mixture_ratio, 
            chamber_pressure, 
            chamber_temperature, 
            chamber_volume, 
            throat_diameter, 
            exit_diameter, 
            fuel_flow_rate
        )
        
        # Get values at current time step
        current_pressure = results['Chamber Pressure'].iloc[0]
        current_velocity = results['Exit Velocity'].iloc[0]
        current_thrust = results['Thrust'].iloc[0]
        
        # Store results
        chamber_pressure_arr[i] = current_pressure
        exit_velocity_arr[i] = current_velocity
        thrust_arr[i] = current_thrust
        fuel_flow_arr[i] = fuel_flow_rate
        
        # Update PID controller
        if control_variable == 'Thrust':
            control_output = pid_controller.update(current_thrust, t)
        else:  # Chamber Pressure
            control_output = pid_controller.update(current_pressure, t)
            
        control_output_arr[i] = control_output
        
        # Update fuel flow rate based on controller output
        # Assuming flow rate is directly controlled
        fuel_flow_rate = control_output
    
    # Create DataFrame with results
    results_df = pd.DataFrame({
        'Time': time_points,
        'Chamber Pressure': chamber_pressure_arr,
        'Exit Velocity': exit_velocity_arr,
        'Thrust': thrust_arr,
        'Control Output': control_output_arr,
        'Fuel Flow Rate': fuel_flow_arr
    })
    
    return results_df


def main():
    st.set_page_config(
        page_title="Rocket Engine PINN Simulator",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Liquid Rocket Engine Simulator with PINN-based PID Controller")
    st.subheader("Physics-Informed Neural Network for Engine Performance Prediction")
    
    # Sidebar for engine parameters
    st.sidebar.header("Engine Parameters")
    
    mixture_ratio = st.sidebar.slider(
        "Mixture Ratio (O/F)", 
        min_value=1.0, 
        max_value=5.0, 
        value=2.5,
        step=0.1,
        help="Ratio of oxidizer to fuel by mass"
    )
    
    chamber_pressure = st.sidebar.slider(
        "Chamber Pressure [MPa]", 
        min_value=1.0, 
        max_value=10.0, 
        value=2.0,
        step=0.1
    ) * 1e6  # Convert to Pa
    
    chamber_temperature = st.sidebar.slider(
        "Chamber Temperature [K]", 
        min_value=2000, 
        max_value=3500, 
        value=3000,
        step=100
    )
    
    chamber_volume = st.sidebar.slider(
        "Chamber Volume [cm³]", 
        min_value=100, 
        max_value=2000, 
        value=1000,
        step=100
    ) * 1e-6  # Convert to m³
    
    throat_diameter = st.sidebar.slider(
        "Throat Diameter [mm]", 
        min_value=10, 
        max_value=100, 
        value=30,
        step=5
    ) * 1e-3  # Convert to m
    
    exit_diameter = st.sidebar.slider(
        "Exit Diameter [mm]", 
        min_value=30, 
        max_value=300, 
        value=90,
        step=10
    ) * 1e-3  # Convert to m
    
    fuel_flow_rate = st.sidebar.slider(
        "Fuel Flow Rate [g/s]", 
        min_value=50, 
        max_value=500, 
        value=200,
        step=10
    ) * 1e-3  # Convert to kg/s
    
    # Controller settings
    st.sidebar.header("Controller Settings")
    
    control_variable = st.sidebar.selectbox(
        "Control Variable",
        options=["Thrust", "Chamber Pressure"],
        index=0
    )
    
    if control_variable == "Thrust":
        setpoint = st.sidebar.slider(
            "Thrust Setpoint [N]", 
            min_value=100, 
            max_value=5000, 
            value=1000,
            step=100
        )
    else:
        setpoint = st.sidebar.slider(
            "Chamber Pressure Setpoint [MPa]", 
            min_value=1.0, 
            max_value=10.0, 
            value=2.0,
            step=0.1
        ) * 1e6  # Convert to Pa
    
    kp = st.sidebar.slider("P Gain", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
    ki = st.sidebar.slider("I Gain", min_value=0.0, max_value=1.0, value=0.1, step=0.01)
    kd = st.sidebar.slider("D Gain", min_value=0.0, max_value=1.0, value=0.05, step=0.01)
    
    use_pinn_controller = st.sidebar.checkbox("Use PINN-guided PID", value=True)
    
    simulation_time = st.sidebar.slider(
        "Simulation Time [s]", 
        min_value=1.0, 
        max_value=30.0, 
        value=10.0,
        step=1.0
    )
    
    # Load model and create simulator
    with st.spinner("Loading PINN model..."):
        model = load_or_create_model(load_existing=True)
        simulator = create_engine_simulator(model, time_span=simulation_time)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Engine Simulation", "PID Control", "PINN Internals"])
    
    with tab1:
        st.header("Engine Simulation")
        
        col1, col2 = st.columns(2)
        
        if col1.button("Run Engine Simulation", use_container_width=True):
            # Run simulator
            results = simulator(
                mixture_ratio, 
                chamber_pressure, 
                chamber_temperature, 
                chamber_volume, 
                throat_diameter, 
                exit_diameter, 
                fuel_flow_rate
            )
            
            # Create plots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
            
            # Chamber pressure
            ax1.plot(results['Time'], results['Chamber Pressure']/1e6, 'b-')
            ax1.set_ylabel('Chamber Pressure [MPa]')
            ax1.set_xlabel('Time [s]')
            ax1.grid(True)
            
            # Exit velocity
            ax2.plot(results['Time'], results['Exit Velocity'], 'g-')
            ax2.set_ylabel('Exit Velocity [m/s]')
            ax2.set_xlabel('Time [s]')
            ax2.grid(True)
            
            # Thrust
            ax3.plot(results['Time'], results['Thrust'], 'r-')
            ax3.set_ylabel('Thrust [N]')
            ax3.set_xlabel('Time [s]')
            ax3.grid(True)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Display numerical results
            col2.subheader("Steady-State Results")
            
            # Calculate average of last few points for steady state
            steady_state = results.iloc[-10:].mean()
            
            col2.metric("Chamber Pressure", f"{steady_state['Chamber Pressure']/1e6:.2f} MPa")
            col2.metric("Exit Velocity", f"{steady_state['Exit Velocity']:.2f} m/s")
            col2.metric("Thrust", f"{steady_state['Thrust']:.2f} N")
            
            # Calculate expansion ratio and ISP
            throat_area = np.pi * (throat_diameter/2)**2
            exit_area = np.pi * (exit_diameter/2)**2
            expansion_ratio = exit_area / throat_area
            
            total_flow = fuel_flow_rate * (1 + mixture_ratio)
            isp = steady_state['Thrust'] / (total_flow * 9.81)
            
            col2.metric("Expansion Ratio", f"{expansion_ratio:.2f}")
            col2.metric("Specific Impulse", f"{isp:.2f} s")
            
    with tab2:
        st.header("PID Control Simulation")
        
        if st.button("Run PID Simulation", use_container_width=True):
            # Create controller
            if use_pinn_controller:
                controller = PINNGuidedPIDController(
                    pinn_model=model,
                    kp=kp,
                    ki=ki,
                    kd=kd,
                    setpoint=setpoint,
                    output_limits=(0.05, 0.5)  # Fuel flow rate limits
                )
            else:
                controller = PIDController(
                    kp=kp,
                    ki=ki,
                    kd=kd,
                    setpoint=setpoint,
                    output_limits=(0.05, 0.5)  # Fuel flow rate limits
                )
            
            # Run PID simulation
            results = run_pid_simulation(
                simulator,
                controller,
                setpoint,
                control_variable,
                simulation_time
            )
            
            # Create plots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
            
            # Control variable (Thrust or Chamber Pressure)
            if control_variable == "Thrust":
                ax1.plot(results['Time'], results['Thrust'], 'b-', label='Actual')
                ax1.axhline(y=setpoint, color='r', linestyle='--', label='Setpoint')
                ax1.set_ylabel('Thrust [N]')
            else:
                ax1.plot(results['Time'], results['Chamber Pressure']/1e6, 'b-', label='Actual')
                ax1.axhline(y=setpoint/1e6, color='r', linestyle='--', label='Setpoint')
                ax1.set_ylabel('Chamber Pressure [MPa]')
                
            ax1.set_xlabel('Time [s]')
            ax1.grid(True)
            ax1.legend()
            
            # Control output (fuel flow rate)
            ax2.plot(results['Time'], results['Fuel Flow Rate']*1000, 'g-')
            ax2.set_ylabel('Fuel Flow Rate [g/s]')
            ax2.set_xlabel('Time [s]')
            ax2.grid(True)
            
            # Error
            if control_variable == "Thrust":
                error = setpoint - results['Thrust']
            else:
                error = setpoint - results['Chamber Pressure']
                
            ax3.plot(results['Time'], error, 'r-')
            ax3.set_ylabel('Error')
            ax3.set_xlabel('Time [s]')
            ax3.grid(True)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Calculate performance metrics
            settling_time = None
            for i, err in enumerate(error):
                if abs(err) < 0.05 * setpoint:
                    settling_time = results['Time'][i]
                    break
                    
            if settling_time:
                st.metric("Settling Time", f"{settling_time:.2f} s")
                
            overshoot = 0
            if control_variable == "Thrust":
                max_val = np.max(results['Thrust'])
                if max_val > setpoint:
                    overshoot = (max_val - setpoint) / setpoint * 100
            else:
                max_val = np.max(results['Chamber Pressure'])
                if max_val > setpoint:
                    overshoot = (max_val - setpoint) / setpoint * 100
                    
            st.metric("Overshoot", f"{overshoot:.2f}%")
            
            # Steady-state error
            if control_variable == "Thrust":
                ss_error = np.mean(setpoint - results['Thrust'].iloc[-20:]) / setpoint * 100
            else:
                ss_error = np.mean(setpoint - results['Chamber Pressure'].iloc[-20:]) / setpoint * 100
                
            st.metric("Steady-State Error", f"{abs(ss_error):.2f}%")
    
    with tab3:
        st.header("PINN Model Details")
        
        # Model architecture
        st.subheader("Model Architecture")
        
        st.text("""
        Physics-Informed Neural Network (PINN) for Rocket Engine Simulation
        
        Input Parameters:
        - Mixture Ratio (O/F)
        - Chamber Pressure Initial [Pa]
        - Chamber Temperature [K]
        - Chamber Volume [m³]
        - Throat Diameter [m]
        - Exit Diameter [m]
        - Time Step [s]
        - Fuel Flow Rate [kg/s]
        
        Output Parameters:
        - Chamber Pressure [Pa]
        - Exit Velocity [m/s]
        - Thrust [N]
        
        Model Structure:
        - 5 hidden layers with 50 neurons each
        - Tanh activation function
        - Physics constraints in loss function
        """)
        
        # Physics constraints
        st.subheader("Physics Constraints")
        
        st.markdown("""
        The PINN model incorporates the following physics-based constraints:
        
        1. **Thrust Equation**: $F = \dot{m} v_e + (p_e - p_a)A_e$
        2. **Mass Conservation**: Ensuring mass flow is conserved
        3. **Isentropic Flow Relations**: Relating pressures and temperatures
        
        These constraints are added to the loss function during training:
        
        $L_{total} = \alpha L_{data} + (1-\alpha) L_{physics}$
        
        where $\alpha$ is a weighting parameter.
        """)
        
        # Visualization of model prediction
        st.subheader("Parameter Sensitivity")
        
        param_to_vary = st.selectbox(
            "Parameter to Vary",
            options=["Mixture Ratio", "Chamber Pressure", "Throat Diameter", "Exit Diameter", "Fuel Flow Rate"],
            index=0
        )
        
        # Create parameter variations
        if param_to_vary == "Mixture Ratio":
            values = np.linspace(1.5, 4.0, 6)
            param_index = 0
            param_name = "Mixture Ratio"
            param_unit = ""
        elif param_to_vary == "Chamber Pressure":
            values = np.linspace(1.0e6, 5.0e6, 6)
            param_index = 1
            param_name = "Chamber Pressure"
            param_unit = "MPa"
            values_plot = values / 1e6  # Convert to MPa for plotting
        elif param_to_vary == "Throat Diameter":
            values = np.linspace(0.01, 0.05, 6)
            param_index = 4
            param_name = "Throat Diameter"
            param_unit = "mm"
            values_plot = values * 1000  # Convert to mm for plotting
        elif param_to_vary == "Exit Diameter":
            values = np.linspace(0.03, 0.15, 6)
            param_index = 5
            param_name = "Exit Diameter"
            param_unit = "mm"
            values_plot = values * 1000  # Convert to mm for plotting
        else:  # Fuel Flow Rate
            values = np.linspace(0.05, 0.5, 6)
            param_index = 7
            param_name = "Fuel Flow Rate"
            param_unit = "g/s"
            values_plot = values * 1000  # Convert to g/s for plotting
            
        # Run simulations with parameter variations
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        for i, val in enumerate(values):
            # Create input array
            inputs = np.zeros((1, 8))
            inputs[0, 0] = mixture_ratio
            inputs[0, 1] = chamber_pressure
            inputs[0, 2] = chamber_temperature
            inputs[0, 3] = chamber_volume
            inputs[0, 4] = throat_diameter
            inputs[0, 5] = exit_diameter
            inputs[0, 6] = 0.0  # Time
            inputs[0, 7] = fuel_flow_rate
            
            # Set varied parameter
            inputs[0, param_index] = val
            
            # Convert to tensor
            inputs_tensor = torch.tensor(inputs, dtype=torch.float32)
            
            # Get predictions
            with torch.no_grad():
                outputs = model(inputs_tensor).cpu().numpy()
                
            # Plot
            if param_index == 0:
                label_val = val
            elif param_index == 1:
                label_val = val / 1e6
            elif param_index in (4, 5):
                label_val = val * 1000
            else:
                label_val = val * 1000
                
            ax1.scatter(label_val, outputs[0, 2], label=f"{label_val:.2f}")  # Thrust
            ax2.scatter(label_val, outputs[0, 1], label=f"{label_val:.2f}")  # Exit Velocity
        
        # Add axis labels
        ax1.set_xlabel(f"{param_name} [{param_unit}]")
        ax1.set_ylabel("Thrust [N]")
        ax1.grid(True)
        
        ax2.set_xlabel(f"{param_name} [{param_unit}]")
        ax2.set_ylabel("Exit Velocity [m/s]")
        ax2.grid(True)
        
        plt.tight_layout()
        st.pyplot(fig)


if __name__ == "__main__":
    main() 