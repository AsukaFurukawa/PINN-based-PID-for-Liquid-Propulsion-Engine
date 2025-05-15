#!/usr/bin/env python3
"""
PINN-based PID Controller for Liquid Rocket Engine - Integration Demo

This script demonstrates the integration of all major components:
1. Physics-Informed Neural Network (PINN) model
2. PID controller with PINN guidance
3. Virtual hardware interface
4. Real-time visualization

This serves as a proof-of-concept for the full control system before
connecting to actual hardware.
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import torch
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from models.pinn_model import RocketEnginePINN
from utils.pid_controller import PIDController, PINNGuidedPIDController
from utils.hardware_interface import get_hardware_interface
from utils.rocket_physics import (
    calculate_thrust,
    calculate_exit_velocity,
    calculate_mass_flow_rate
)


def load_pinn_model(model_path="models/rocket_engine_pinn.pt"):
    """
    Load the trained PINN model.
    
    Args:
        model_path: Path to the saved model
        
    Returns:
        Loaded PINN model or None if loading fails
    """
    try:
        model = RocketEnginePINN()
        
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path))
            model.eval()
            print(f"Loaded model from {model_path}")
        else:
            print(f"Model file not found at {model_path}")
            print("Using untrained model (not recommended)")
            
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def setup_controllers(pinn_model, target_thrust=500.0):
    """
    Set up PID controllers with and without PINN guidance.
    
    Args:
        pinn_model: Trained PINN model
        target_thrust: Target thrust in Newtons
        
    Returns:
        Dictionary with controllers
    """
    # Basic PID controller for thrust
    basic_pid = PIDController(
        kp=0.005,    # Increase proportional gain
        ki=0.0005,   # Increase integral gain
        kd=0.0002,   # Slightly increase derivative gain
        setpoint=target_thrust,
        output_limits=(0.05, 0.5)  # Limit fuel flow rate
    )
    
    # PINN-guided PID controller
    pinn_pid = PINNGuidedPIDController(
        pinn_model=pinn_model,
        kp=0.005,    # Match the basic controller for fair comparison
        ki=0.0005,
        kd=0.0002,
        setpoint=target_thrust,
        output_limits=(0.05, 0.5)
    )
    
    return {
        'basic': basic_pid,
        'pinn': pinn_pid
    }


def run_control_loop(hardware, controller, duration=30.0, update_rate=10.0,
                    target_mixture_ratio=2.5, ignition_delay=2.0,
                    use_pinn_predictions=False):
    """
    Run the control loop for a specified duration.
    
    Args:
        hardware: Hardware interface (virtual or real)
        controller: PID controller
        duration: Total duration to run (seconds)
        update_rate: Control loop update rate (Hz)
        target_mixture_ratio: Target O/F ratio
        ignition_delay: Delay before ignition (seconds)
        use_pinn_predictions: Whether to use PINN for predictions
        
    Returns:
        DataFrame with time history data
    """
    # Start hardware simulation
    hardware.start()
    
    # Initialize data storage
    update_interval = 1.0 / update_rate
    num_samples = int(duration * update_rate)
    
    time_points = np.zeros(num_samples)
    thrust_data = np.zeros(num_samples)
    pressure_data = np.zeros(num_samples)
    fuel_flow_data = np.zeros(num_samples)
    oxidizer_flow_data = np.zeros(num_samples)
    setpoint_data = np.zeros(num_samples)
    control_output_data = np.zeros(num_samples)
    
    # Set initial mixture ratio by setting oxidizer valve
    initial_fuel_flow = 0.1  # Initial fuel flow [kg/s]
    hardware.set_actuator('fuel_valve', initial_fuel_flow / 0.3)  # Scale to valve position
    hardware.set_actuator('oxidizer_valve', (initial_fuel_flow * target_mixture_ratio) / 0.7)
    
    # Create state array for PINN input
    if use_pinn_predictions and isinstance(controller, PINNGuidedPIDController):
        # Default engine parameters for PINN input
        current_state = np.zeros(8)
        current_state[0] = target_mixture_ratio  # mixture_ratio
        current_state[1] = 1.0e6  # chamber_pressure
        current_state[2] = 3000.0  # chamber_temperature
        current_state[3] = 0.001  # chamber_volume
        current_state[4] = 0.03  # throat_diameter
        current_state[5] = 0.09  # exit_diameter
        current_state[6] = 0.0  # time_step
        current_state[7] = initial_fuel_flow  # fuel_flow_rate
    
    print("Starting control loop...")
    print(f"Target thrust: {controller.setpoint} N")
    
    # Record start time
    start_time = time.time()
    
    # Run control loop
    for i in range(num_samples):
        loop_start = time.time()
        current_time = loop_start - start_time
        
        # Ignite engine after delay
        if current_time >= ignition_delay and not hardware.is_ignited():
            print(f"Igniting engine at t={current_time:.1f}s...")
            hardware.set_actuator('igniter', 1.0)
        
        # Read current sensor values
        thrust = hardware.read_sensor('thrust')
        chamber_pressure = hardware.read_sensor('chamber_pressure')
        fuel_flow = hardware.read_sensor('fuel_flow_rate')
        oxidizer_flow = hardware.read_sensor('oxidizer_flow_rate')
        
        # Update state array for PINN
        if use_pinn_predictions and isinstance(controller, PINNGuidedPIDController):
            # Update with current readings
            if hardware.is_ignited():
                # Use measured values after ignition
                current_state[0] = oxidizer_flow / max(fuel_flow, 1e-6)  # mixture_ratio
                current_state[1] = chamber_pressure  # chamber_pressure
            
            current_state[6] = current_time  # Update time
            current_state[7] = fuel_flow  # fuel_flow_rate
            
            # Update controller with PINN predictions
            control_output = controller.update_with_predictions(thrust, current_state, current_time)
        else:
            # Basic PID update
            control_output = controller.update(thrust, current_time)
        
        # Apply control output to fuel valve
        hardware.set_actuator('fuel_valve', control_output / 0.3)  # Scale to valve position
        
        # Adjust oxidizer to maintain mixture ratio
        oxidizer_target = control_output * target_mixture_ratio
        hardware.set_actuator('oxidizer_valve', oxidizer_target / 0.7)  # Scale to valve position
        
        # Store data
        time_points[i] = current_time
        thrust_data[i] = thrust
        pressure_data[i] = chamber_pressure
        fuel_flow_data[i] = fuel_flow
        oxidizer_flow_data[i] = oxidizer_flow
        setpoint_data[i] = controller.setpoint
        control_output_data[i] = control_output
        
        # Print status every second
        if i % int(update_rate) == 0:
            print(f"t={current_time:.1f}s | Thrust={thrust:.1f}N | Pressure={chamber_pressure/1e6:.2f}MPa | "
                 f"Fuel Flow={fuel_flow*1000:.1f}g/s | O/F Ratio={oxidizer_flow/max(fuel_flow, 1e-6):.2f}")
        
        # Wait for next update
        elapsed = time.time() - loop_start
        if elapsed < update_interval:
            time.sleep(update_interval - elapsed)
    
    # Turn off the engine
    print("Shutting down engine...")
    hardware.set_actuator('igniter', 0.0)
    hardware.set_actuator('fuel_valve', 0.0)
    hardware.set_actuator('oxidizer_valve', 0.0)
    
    # Stop hardware
    time.sleep(1.0)
    hardware.stop()
    
    # Create DataFrame with time history
    results = pd.DataFrame({
        'Time': time_points,
        'Thrust': thrust_data,
        'Chamber Pressure': pressure_data,
        'Fuel Flow Rate': fuel_flow_data,
        'Oxidizer Flow Rate': oxidizer_flow_data,
        'Mixture Ratio': oxidizer_flow_data / np.clip(fuel_flow_data, 1e-6, None),
        'Setpoint': setpoint_data,
        'Control Output': control_output_data
    })
    
    return results


def plot_results(results, controller_name, save_plot=True, show_plot=True):
    """
    Plot the control system performance.
    
    Args:
        results: DataFrame with time history data
        controller_name: Name of the controller used
        save_plot: Whether to save the plot to a file
        show_plot: Whether to show the plot
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # Plot 1: Thrust vs Time
    axes[0].plot(results['Time'], results['Thrust'], 'b-', label='Actual')
    axes[0].plot(results['Time'], results['Setpoint'], 'r--', label='Setpoint')
    axes[0].set_ylabel('Thrust [N]')
    axes[0].set_title(f'Rocket Engine Control with {controller_name}')
    axes[0].grid(True)
    axes[0].legend()
    
    # Plot 2: Control Output and Chamber Pressure vs Time
    ax2a = axes[1]
    ax2b = ax2a.twinx()
    
    ax2a.plot(results['Time'], results['Control Output'] * 1000, 'g-', label='Fuel Flow Command')
    ax2a.set_ylabel('Fuel Flow Command [g/s]')
    ax2a.grid(True)
    
    ax2b.plot(results['Time'], results['Chamber Pressure'] / 1e6, 'c-', label='Chamber Pressure')
    ax2b.set_ylabel('Chamber Pressure [MPa]')
    
    lines1, labels1 = ax2a.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2a.legend(lines1 + lines2, labels1 + labels2)
    
    # Plot 3: Mixture Ratio vs Time
    axes[2].plot(results['Time'], results['Mixture Ratio'], 'm-')
    axes[2].axhline(y=2.5, color='k', linestyle='--', label='Target Ratio')
    axes[2].set_xlabel('Time [s]')
    axes[2].set_ylabel('Mixture Ratio (O/F)')
    axes[2].grid(True)
    axes[2].legend()
    
    plt.tight_layout()
    
    # Save plot if requested
    if save_plot:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results_{controller_name}_{timestamp}.png"
        plt.savefig(filename, dpi=150)
        print(f"Plot saved to {filename}")
    
    # Show plot if requested
    if show_plot:
        plt.show()


def compare_controllers(basic_results, pinn_results):
    """
    Compare performance of basic PID and PINN-guided PID.
    
    Args:
        basic_results: DataFrame with results from basic PID
        pinn_results: DataFrame with results from PINN-guided PID
    """
    # Calculate performance metrics
    def calculate_metrics(results):
        # Skip initial ignition phase
        start_idx = results[results['Thrust'] > 50].index[0]
        operating_data = results.iloc[start_idx:]
        
        # Mean absolute error
        mae = np.mean(np.abs(operating_data['Thrust'] - operating_data['Setpoint']))
        
        # Root mean square error
        rmse = np.sqrt(np.mean((operating_data['Thrust'] - operating_data['Setpoint'])**2))
        
        # Maximum overshoot
        max_overshoot = np.max(operating_data['Thrust'] - operating_data['Setpoint'])
        if max_overshoot > 0:
            percent_overshoot = max_overshoot / operating_data['Setpoint'].iloc[0] * 100
        else:
            percent_overshoot = 0
            
        # Settling time (within 5% of setpoint)
        target = operating_data['Setpoint'].iloc[0]
        tolerance = 0.05 * target
        
        settled_idx = None
        for i in range(len(operating_data) - 20):  # Need at least 20 consecutive samples
            if all(abs(operating_data['Thrust'].iloc[i:i+20] - target) < tolerance):
                settled_idx = i
                break
                
        if settled_idx is not None:
            settling_time = operating_data['Time'].iloc[settled_idx] - operating_data['Time'].iloc[0]
        else:
            settling_time = float('inf')
            
        return {
            'MAE': mae,
            'RMSE': rmse,
            'Overshoot (%)': percent_overshoot,
            'Settling Time (s)': settling_time
        }
    
    basic_metrics = calculate_metrics(basic_results)
    pinn_metrics = calculate_metrics(pinn_results)
    
    # Display comparison
    print("\nPerformance Comparison:")
    print(f"{'Metric':<20} {'Basic PID':<15} {'PINN-guided PID':<15} {'Improvement':<15}")
    print("-" * 70)
    
    for metric in basic_metrics:
        basic_val = basic_metrics[metric]
        pinn_val = pinn_metrics[metric]
        
        if basic_val > 0:
            improvement = (1 - pinn_val / basic_val) * 100
        else:
            improvement = 0
            
        print(f"{metric:<20} {basic_val:<15.2f} {pinn_val:<15.2f} {improvement:>+15.2f}%")
    
    # Plot comparison
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Plot 1: Thrust comparison
    axes[0].plot(basic_results['Time'], basic_results['Thrust'], 'b-', label='Basic PID')
    axes[0].plot(pinn_results['Time'], pinn_results['Thrust'], 'g-', label='PINN-guided PID')
    axes[0].plot(basic_results['Time'], basic_results['Setpoint'], 'r--', label='Setpoint')
    axes[0].set_ylabel('Thrust [N]')
    axes[0].set_title('Controller Performance Comparison')
    axes[0].grid(True)
    axes[0].legend()
    
    # Plot 2: Error comparison
    basic_error = basic_results['Thrust'] - basic_results['Setpoint']
    pinn_error = pinn_results['Thrust'] - pinn_results['Setpoint']
    
    axes[1].plot(basic_results['Time'], basic_error, 'b-', label='Basic PID Error')
    axes[1].plot(pinn_results['Time'], pinn_error, 'g-', label='PINN-guided PID Error')
    axes[1].axhline(y=0, color='k', linestyle='--')
    axes[1].set_xlabel('Time [s]')
    axes[1].set_ylabel('Error [N]')
    axes[1].grid(True)
    axes[1].legend()
    
    plt.tight_layout()
    
    # Save comparison plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"controller_comparison_{timestamp}.png"
    plt.savefig(filename, dpi=150)
    print(f"Comparison plot saved to {filename}")
    
    plt.show()


def main():
    """Main function for the integration demo."""
    print("PINN-based PID Controller for Liquid Rocket Engine - Integration Demo")
    print("-------------------------------------------------------------------")
    
    # Load the PINN model
    pinn_model = load_pinn_model()
    if pinn_model is None:
        print("Failed to load PINN model. Exiting.")
        return
    
    # Set up controllers
    target_thrust = 500.0  # Target thrust in Newtons
    controllers = setup_controllers(pinn_model, target_thrust)
    
    # Get virtual hardware interface
    hardware = get_hardware_interface(use_virtual=True)
    
    # Run basic PID controller
    print("\nRunning test with basic PID controller...")
    basic_results = run_control_loop(
        hardware, 
        controllers['basic'], 
        duration=20.0, 
        update_rate=10.0,
        use_pinn_predictions=False
    )
    
    # Plot results
    plot_results(basic_results, "Basic PID", save_plot=True, show_plot=False)
    
    # Run PINN-guided PID controller
    print("\nRunning test with PINN-guided PID controller...")
    pinn_results = run_control_loop(
        hardware, 
        controllers['pinn'], 
        duration=20.0, 
        update_rate=10.0,
        use_pinn_predictions=True
    )
    
    # Plot results
    plot_results(pinn_results, "PINN-guided PID", save_plot=True, show_plot=False)
    
    # Compare controllers
    compare_controllers(basic_results, pinn_results)
    
    # Save results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    basic_results.to_csv(f"basic_pid_results_{timestamp}.csv", index=False)
    pinn_results.to_csv(f"pinn_pid_results_{timestamp}.csv", index=False)
    
    print("Demo completed successfully.")


if __name__ == "__main__":
    main() 