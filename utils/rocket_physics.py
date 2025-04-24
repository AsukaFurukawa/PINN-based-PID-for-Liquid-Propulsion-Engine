import numpy as np
import torch

# Constants
R_UNIVERSAL = 8.314  # Universal gas constant [J/(mol·K)]
G_0 = 9.81  # Standard gravity [m/s²]


def calculate_thrust(chamber_pressure, throat_area, exit_area, exit_pressure, ambient_pressure, exit_velocity, mass_flow_rate, gamma=1.4):
    """
    Calculate rocket thrust using the thrust equation.
    
    F = (ṁ * v_e) + (p_e - p_a) * A_e
    
    Args:
        chamber_pressure: Chamber pressure [Pa]
        throat_area: Throat cross-sectional area [m²]
        exit_area: Nozzle exit cross-sectional area [m²]
        exit_pressure: Pressure at nozzle exit [Pa]
        ambient_pressure: Ambient pressure [Pa]
        exit_velocity: Exit velocity of exhaust gases [m/s]
        mass_flow_rate: Propellant mass flow rate [kg/s]
        gamma: Specific heat ratio
        
    Returns:
        Thrust force [N]
    """
    momentum_thrust = mass_flow_rate * exit_velocity
    pressure_thrust = (exit_pressure - ambient_pressure) * exit_area
    
    return momentum_thrust + pressure_thrust


def calculate_isp(thrust, mass_flow_rate):
    """
    Calculate specific impulse.
    
    Args:
        thrust: Thrust force [N]
        mass_flow_rate: Propellant mass flow rate [kg/s]
        
    Returns:
        Specific impulse [s]
    """
    return thrust / (mass_flow_rate * G_0)


def calculate_exit_mach(expansion_ratio, gamma=1.4):
    """
    Calculate exit Mach number based on area expansion ratio.
    Uses iterative method to solve the area-Mach relation.
    
    Args:
        expansion_ratio: Ratio of exit area to throat area
        gamma: Specific heat ratio
        
    Returns:
        Exit Mach number
    """
    # Initial guess
    M = 2.0
    
    # Iterative solution to area-Mach relation
    for _ in range(100):
        # Area-Mach relation: A/A* = (1/M) * ((1 + (gamma-1)/2 * M^2) / ((gamma+1)/2))^((gamma+1)/(2*(gamma-1)))
        term1 = (1 / M)
        term2 = ((1 + (gamma - 1) / 2 * M**2) / ((gamma + 1) / 2))**((gamma + 1) / (2 * (gamma - 1)))
        A_ratio = term1 * term2
        
        if abs(A_ratio - expansion_ratio) < 1e-6:
            break
        
        # Update Mach number
        if A_ratio < expansion_ratio:
            M += 0.1
        else:
            M -= 0.05
            
    return M


def calculate_exit_velocity(chamber_temperature, exit_mach, gamma=1.4, molecular_weight=0.028):
    """
    Calculate exit velocity based on exit Mach number.
    
    Args:
        chamber_temperature: Chamber temperature [K]
        exit_mach: Exit Mach number
        gamma: Specific heat ratio
        molecular_weight: Molecular weight of combustion products [kg/mol]
        
    Returns:
        Exit velocity [m/s]
    """
    # Gas constant for this specific gas
    R = R_UNIVERSAL / molecular_weight
    
    # Speed of sound at chamber conditions
    c_chamber = np.sqrt(gamma * R * chamber_temperature)
    
    # Temperature ratio based on exit Mach number
    T_ratio = 1 / (1 + (gamma - 1) / 2 * exit_mach**2)
    
    # Speed of sound at exit
    c_exit = c_chamber * np.sqrt(T_ratio)
    
    # Exit velocity
    return exit_mach * c_exit


def calculate_mass_flow_rate(chamber_pressure, throat_area, chamber_temperature, gamma=1.4, molecular_weight=0.028):
    """
    Calculate mass flow rate through the throat.
    
    Args:
        chamber_pressure: Chamber pressure [Pa]
        throat_area: Throat cross-sectional area [m²]
        chamber_temperature: Chamber temperature [K]
        gamma: Specific heat ratio
        molecular_weight: Molecular weight of combustion products [kg/mol]
        
    Returns:
        Mass flow rate [kg/s]
    """
    # Gas constant for this specific gas
    R = R_UNIVERSAL / molecular_weight
    
    # Critical flow function
    term1 = gamma / R
    term2 = (2 / (gamma + 1))**((gamma + 1) / (gamma - 1))
    
    return chamber_pressure * throat_area * np.sqrt(term1 * term2 / chamber_temperature)


def calculate_pressure_ratio(exit_mach, gamma=1.4):
    """
    Calculate pressure ratio (p_exit/p_chamber) based on exit Mach number.
    
    Args:
        exit_mach: Exit Mach number
        gamma: Specific heat ratio
        
    Returns:
        Pressure ratio (p_exit/p_chamber)
    """
    return (1 + (gamma - 1) / 2 * exit_mach**2)**(-gamma / (gamma - 1))


def calculate_temperature_ratio(exit_mach, gamma=1.4):
    """
    Calculate temperature ratio (T_exit/T_chamber) based on exit Mach number.
    
    Args:
        exit_mach: Exit Mach number
        gamma: Specific heat ratio
        
    Returns:
        Temperature ratio (T_exit/T_chamber)
    """
    return (1 + (gamma - 1) / 2 * exit_mach**2)**(-1)


def calculate_chamber_pressure(mass_flow_rate, chamber_volume, chamber_temperature, 
                              molecular_weight=0.028, time_step=0.01, outflow_coefficient=0.5):
    """
    Calculate change in chamber pressure over time based on mass flow.
    
    Args:
        mass_flow_rate: Mass flow rate into the chamber [kg/s]
        chamber_volume: Chamber volume [m³]
        chamber_temperature: Chamber temperature [K]
        molecular_weight: Molecular weight of gases [kg/mol]
        time_step: Time step for calculation [s]
        outflow_coefficient: Coefficient for outflow rate (0-1)
        
    Returns:
        Pressure change rate [Pa/s]
    """
    # Gas constant for this specific gas
    R = R_UNIVERSAL / molecular_weight
    
    # Estimate outflow rate as a fraction of inflow rate
    outflow_rate = mass_flow_rate * outflow_coefficient
    
    # Net mass flow rate
    net_flow_rate = mass_flow_rate - outflow_rate
    
    # Pressure change (from ideal gas law: P = nRT/V)
    pressure_change_rate = (net_flow_rate * R * chamber_temperature) / (molecular_weight * chamber_volume)
    
    return pressure_change_rate


def create_combustion_products_properties(mixture_ratio, fuel_type="methane", oxidizer_type="nitrous_oxide"):
    """
    Estimate combustion products properties based on mixture ratio and propellants.
    
    Args:
        mixture_ratio: Oxidizer to fuel ratio (O/F)
        fuel_type: Type of fuel
        oxidizer_type: Type of oxidizer
        
    Returns:
        Dictionary with combustion properties:
        - gamma: Specific heat ratio
        - molecular_weight: Molecular weight [kg/mol]
        - combustion_temperature: Combustion temperature [K]
    """
    # Default properties for methane + nitrous oxide
    if fuel_type.lower() == "methane" and oxidizer_type.lower() == "nitrous_oxide":
        # These are approximate values and would vary based on exact mixture ratio
        if mixture_ratio < 2.0:
            # Fuel-rich mixture
            gamma = 1.22
            molecular_weight = 0.024
            combustion_temp = 2700
        elif mixture_ratio <= 3.5:
            # Near stoichiometric
            gamma = 1.25
            molecular_weight = 0.026
            combustion_temp = 3100
        else:
            # Oxidizer-rich
            gamma = 1.30
            molecular_weight = 0.028
            combustion_temp = 2800
    else:
        # Default values if specific propellant combination is not defined
        gamma = 1.25
        molecular_weight = 0.026
        combustion_temp = 3000
    
    return {
        "gamma": gamma,
        "molecular_weight": molecular_weight,
        "combustion_temperature": combustion_temp
    }


def calculate_characteristic_velocity(chamber_temperature, gamma=1.4, molecular_weight=0.028):
    """
    Calculate characteristic velocity (c*).
    
    Args:
        chamber_temperature: Chamber temperature [K]
        gamma: Specific heat ratio
        molecular_weight: Molecular weight of combustion products [kg/mol]
        
    Returns:
        Characteristic velocity [m/s]
    """
    # Gas constant for this specific gas
    R = R_UNIVERSAL / molecular_weight
    
    term1 = np.sqrt(gamma * R * chamber_temperature)
    term2 = gamma * ((2 / (gamma + 1))**((gamma + 1) / (gamma - 1)))
    
    return term1 / np.sqrt(term2)


def calculate_optimal_expansion_ratio(ambient_pressure, chamber_pressure, gamma=1.4):
    """
    Calculate optimal expansion ratio for a given ambient pressure.
    
    Args:
        ambient_pressure: Ambient pressure [Pa]
        chamber_pressure: Chamber pressure [Pa]
        gamma: Specific heat ratio
        
    Returns:
        Optimal expansion ratio
    """
    pressure_ratio = ambient_pressure / chamber_pressure
    term1 = (gamma + 1) / 2
    term2 = pressure_ratio**(1 / gamma)
    term3 = (gamma - 1) / gamma
    
    mach = np.sqrt((term1 * (1 - term2)) / term3)
    
    # Area ratio from Mach number
    term4 = 1 + ((gamma - 1) / 2) * mach**2
    term5 = (gamma + 1) / (2 * (gamma - 1))
    
    return (1 / mach) * (term4**term5)


# Physics loss functions for PINNs
def thrust_equation_loss(mass_flow_rate, exit_velocity, thrust):
    """
    Compute loss based on the thrust equation (momentum conservation).
    
    Args:
        mass_flow_rate: Mass flow rate [kg/s]
        exit_velocity: Exit velocity [m/s]
        thrust: Thrust [N]
        
    Returns:
        Loss value
    """
    computed_thrust = mass_flow_rate * exit_velocity
    return torch.mean((thrust - computed_thrust)**2)


def isentropic_flow_loss(chamber_pressure, exit_pressure, chamber_temperature, exit_temperature, gamma):
    """
    Compute loss based on isentropic flow relations.
    
    Args:
        chamber_pressure: Chamber pressure [Pa]
        exit_pressure: Exit pressure [Pa]
        chamber_temperature: Chamber temperature [K]
        exit_temperature: Exit temperature [K]
        gamma: Specific heat ratio
        
    Returns:
        Loss value
    """
    # In isentropic flow: (p1/p2) = (T1/T2)^(gamma/(gamma-1))
    left_side = (chamber_pressure / exit_pressure)
    right_side = (chamber_temperature / exit_temperature)**(gamma / (gamma - 1))
    
    return torch.mean((left_side - right_side)**2)


def mass_conservation_loss(mass_in, mass_out):
    """
    Compute loss based on mass conservation.
    
    Args:
        mass_in: Mass flow rate in [kg/s]
        mass_out: Mass flow rate out [kg/s]
        
    Returns:
        Loss value
    """
    return torch.mean((mass_in - mass_out)**2) 