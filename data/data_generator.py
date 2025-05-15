import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.rocket_physics import (
    calculate_thrust,
    calculate_exit_velocity,
    calculate_mass_flow_rate,
    calculate_exit_mach,
    calculate_pressure_ratio,
    create_combustion_products_properties
)


class RocketEngineDataGenerator:
    """
    Generate synthetic data for rocket engine simulation.
    
    This class creates datasets that combine physics-based calculations
    with controlled random variations to simulate real engine behavior.
    """
    
    def __init__(self, seed=42):
        """
        Initialize the data generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)
        
        # Default parameter ranges
        self.parameter_ranges = {
            'mixture_ratio': (1.5, 4.0),  # Oxidizer to fuel ratio
            'chamber_pressure': (1.0e6, 5.0e6),  # Pa (1-5 MPa)
            'chamber_temperature': (2700, 3200),  # K
            'chamber_volume': (0.0005, 0.002),  # m³
            'throat_diameter': (0.01, 0.05),  # m
            'exit_diameter': (0.03, 0.15),  # m
            'fuel_flow_rate': (0.05, 0.5),  # kg/s
            'ambient_pressure': (101325, 101325)  # Pa (sea level)
        }
        
    def set_parameter_ranges(self, param_dict):
        """
        Set custom parameter ranges.
        
        Args:
            param_dict: Dictionary of parameter ranges {param_name: (min_val, max_val)}
        """
        for param, range_vals in param_dict.items():
            if param in self.parameter_ranges:
                self.parameter_ranges[param] = range_vals
                
    def _sample_parameters(self, num_samples):
        """
        Sample random parameters within defined ranges.
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            Dictionary of parameter arrays
        """
        params = {}
        
        for param, (min_val, max_val) in self.parameter_ranges.items():
            params[param] = np.random.uniform(min_val, max_val, num_samples)
            
        # Calculate time steps (0 to 5 seconds)
        params['time_step'] = np.linspace(0, 5, num_samples)
        
        return params
    
    def generate_dataset(self, num_samples=1000, add_noise=True, noise_level=0.02):
        """
        Generate a synthetic dataset for rocket engine simulation.
        
        Args:
            num_samples: Number of samples to generate
            add_noise: Whether to add noise to the output data
            noise_level: Level of noise to add (fraction of value)
            
        Returns:
            tuple: (input_data, output_data) as numpy arrays
        """
        # Sample input parameters
        params = self._sample_parameters(num_samples)
        
        # Create empty arrays for outputs
        chamber_pressure = np.zeros(num_samples)
        exit_velocity = np.zeros(num_samples)
        thrust = np.zeros(num_samples)
        
        # Calculate outputs based on physics
        for i in range(num_samples):
            # Get parameters for this sample
            mixture_ratio = params['mixture_ratio'][i]
            chamber_pressure_init = params['chamber_pressure'][i]
            chamber_temp = params['chamber_temperature'][i]
            chamber_vol = params['chamber_volume'][i]
            throat_diam = params['throat_diameter'][i]
            exit_diam = params['exit_diameter'][i]
            fuel_flow = params['fuel_flow_rate'][i]
            ambient_p = params['ambient_pressure'][i]
            
            # Calculate areas
            throat_area = np.pi * (throat_diam/2)**2
            exit_area = np.pi * (exit_diam/2)**2
            expansion_ratio = exit_area / throat_area
            
            # Get combustion properties
            comb_props = create_combustion_products_properties(mixture_ratio)
            gamma = comb_props['gamma']
            mol_weight = comb_props['molecular_weight']
            
            # Calculate mass flow rate
            total_flow = fuel_flow * (1 + mixture_ratio)  # Total propellant flow
            
            # Calculate exit Mach number and velocity
            exit_mach = calculate_exit_mach(expansion_ratio, gamma)
            v_exit = calculate_exit_velocity(chamber_temp, exit_mach, gamma, mol_weight)
            
            # Calculate exit pressure
            p_ratio = calculate_pressure_ratio(exit_mach, gamma)
            exit_p = chamber_pressure_init * p_ratio
            
            # Calculate thrust
            F = calculate_thrust(
                chamber_pressure_init, 
                throat_area, 
                exit_area, 
                exit_p, 
                ambient_p, 
                v_exit, 
                total_flow,
                gamma
            )
            
            # For simplicity, assume steady state for chamber pressure
            # In a more complex model, we'd model the pressure rise
            chamber_pressure[i] = chamber_pressure_init
            exit_velocity[i] = v_exit
            thrust[i] = F
        
        # Add noise if requested
        if add_noise:
            chamber_pressure += np.random.normal(0, noise_level * np.mean(chamber_pressure), num_samples)
            exit_velocity += np.random.normal(0, noise_level * np.mean(exit_velocity), num_samples)
            thrust += np.random.normal(0, noise_level * np.mean(thrust), num_samples)
        
        # Create input array
        inputs = np.column_stack([
            params['mixture_ratio'],
            params['chamber_pressure'],
            params['chamber_temperature'],
            params['chamber_volume'],
            params['throat_diameter'],
            params['exit_diameter'],
            params['time_step'],
            params['fuel_flow_rate']
        ])
        
        # Create output array
        outputs = np.column_stack([
            chamber_pressure,
            exit_velocity,
            thrust
        ])
        
        return inputs, outputs
    
    def save_dataset(self, filename, num_samples=1000, add_noise=True, noise_level=0.02):
        """
        Generate and save dataset to CSV file.
        
        Args:
            filename: Output filename
            num_samples: Number of samples to generate
            add_noise: Whether to add noise to output data
            noise_level: Level of noise to add
        """
        inputs, outputs = self.generate_dataset(num_samples, add_noise, noise_level)
        
        # Combine into a single DataFrame
        columns = [
            'mixture_ratio',
            'chamber_pressure_initial',
            'chamber_temperature',
            'chamber_volume',
            'throat_diameter',
            'exit_diameter',
            'time_step',
            'fuel_flow_rate',
            'chamber_pressure_output',
            'exit_velocity',
            'thrust'
        ]
        
        data = np.hstack([inputs, outputs])
        df = pd.DataFrame(data, columns=columns)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
        print(f"Dataset saved to {filename}")
        
        return df


# Example usage
if __name__ == "__main__":
    generator = RocketEngineDataGenerator()
    df = generator.save_dataset("rocket_engine_data.csv", num_samples=1000)
    
    # Print some statistics
    print("\nDataset Statistics:")
    print(df.describe()) 