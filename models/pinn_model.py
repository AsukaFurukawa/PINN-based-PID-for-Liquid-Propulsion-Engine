import torch
import torch.nn as nn
import numpy as np

class RocketEnginePINN(nn.Module):
    """
    Physics-Informed Neural Network (PINN) for liquid rocket engine simulation.
    
    This model predicts key metrics like chamber pressure, exit velocity, and thrust
    while incorporating physics constraints in the loss function.
    """
    
    def __init__(self, input_dim=8, hidden_dim=50, output_dim=3, num_layers=5):
        """
        Initialize the PINN model.
        
        Args:
            input_dim (int): Number of input parameters (default: 8)
                - mixture ratio
                - chamber pressure initial
                - chamber temperature initial
                - chamber volume
                - throat diameter
                - exit diameter
                - time step
                - fuel flow rate
            hidden_dim (int): Number of neurons in hidden layers
            output_dim (int): Number of output parameters (default: 3)
                - chamber pressure
                - exit velocity
                - thrust
            num_layers (int): Number of hidden layers
        """
        super(RocketEnginePINN, self).__init__()
        
        # Input normalization parameters (to be set during training)
        self.input_mean = None
        self.input_std = None
        
        # Build neural network architecture
        layers = [nn.Linear(input_dim, hidden_dim), nn.Tanh()]
        
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
            
        layers.append(nn.Linear(hidden_dim, output_dim))
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x (torch.Tensor): Input tensor with shape [batch_size, input_dim]
                Contains engine parameters and time points.
                
        Returns:
            torch.Tensor: Output tensor with shape [batch_size, output_dim]
                Contains predicted chamber pressure, exit velocity, and thrust.
        """
        # Normalize inputs if normalization parameters are available
        if self.input_mean is not None and self.input_std is not None:
            x = (x - self.input_mean) / self.input_std
            
        return self.network(x)
    
    def set_normalization_params(self, input_data):
        """
        Set input normalization parameters based on the training data.
        
        Args:
            input_data (torch.Tensor): Training input data
        """
        self.input_mean = torch.mean(input_data, dim=0)
        self.input_std = torch.std(input_data, dim=0)
        
    def physics_loss(self, inputs, outputs):
        """
        Compute physics-informed loss based on the governing equations.
        
        Args:
            inputs (torch.Tensor): Input tensor
            outputs (torch.Tensor): Output predictions from the network
            
        Returns:
            torch.Tensor: Physics-based loss
        """
        # Extract inputs
        mixture_ratio = inputs[:, 0:1]
        chamber_pressure_init = inputs[:, 1:2]
        chamber_temp_init = inputs[:, 2:3]
        chamber_volume = inputs[:, 3:4]
        throat_diameter = inputs[:, 4:5]
        exit_diameter = inputs[:, 5:6]
        time_step = inputs[:, 6:7]
        fuel_flow_rate = inputs[:, 7:8]
        
        # Extract outputs
        chamber_pressure = outputs[:, 0:1]
        exit_velocity = outputs[:, 1:2]
        thrust = outputs[:, 2:3]
        
        # Constants (these would be more precise in a real implementation)
        R = 8.314  # Universal gas constant [J/(mol·K)]
        gamma = 1.4  # Specific heat ratio (approximation)
        M = 0.028  # Molar mass [kg/mol] (approximation for combustion products)
        
        # Compute throat area and exit area
        A_t = np.pi * (throat_diameter/2)**2
        A_e = np.pi * (exit_diameter/2)**2
        
        # Physics constraint 1: Thrust equation
        # F = ṁ * v_e + (p_e - p_a) * A_e
        # For simplicity, assuming p_e = p_a (perfectly expanded)
        total_flow_rate = fuel_flow_rate * (1 + mixture_ratio)
        thrust_computed = total_flow_rate * exit_velocity
        thrust_loss = torch.mean((thrust - thrust_computed)**2)
        
        # Physics constraint 2: Pressure-velocity relationship from Bernoulli
        # Use simplified isentropic flow relations
        pressure_ratio = (2/(gamma+1))**((gamma)/(gamma-1))
        exit_velocity_computed = torch.sqrt(2 * gamma * R * chamber_temp_init / M * (1 - pressure_ratio))
        velocity_loss = torch.mean((exit_velocity - exit_velocity_computed)**2)
        
        # Physics constraint 3: Mass conservation
        # Rate of pressure change based on mass flow and chamber volume
        # dp/dt = (R*T/V)*(ṁ_in - ṁ_out)
        # For steady state: chamber_pressure ≈ chamber_pressure_init
        pressure_loss = torch.mean((chamber_pressure - chamber_pressure_init)**2)
        
        # Combine all physics-based losses
        return thrust_loss + velocity_loss + pressure_loss
    
    def data_loss(self, outputs, targets):
        """
        Compute loss between predictions and target data.
        
        Args:
            outputs (torch.Tensor): Model predictions
            targets (torch.Tensor): Target values
            
        Returns:
            torch.Tensor: Mean squared error loss
        """
        return torch.mean((outputs - targets)**2)
    
    def combined_loss(self, inputs, outputs, targets=None, physics_weight=0.5):
        """
        Combine data loss and physics loss.
        
        Args:
            inputs (torch.Tensor): Input tensor
            outputs (torch.Tensor): Output predictions
            targets (torch.Tensor, optional): Target values for supervised learning
            physics_weight (float): Weight of physics loss term
            
        Returns:
            torch.Tensor: Combined loss
        """
        physics_loss = self.physics_loss(inputs, outputs)
        
        if targets is not None:
            data_loss = self.data_loss(outputs, targets)
            return (1 - physics_weight) * data_loss + physics_weight * physics_loss
        else:
            return physics_loss


def train_pinn(model, inputs, targets=None, num_epochs=1000, learning_rate=0.001, physics_weight=0.5):
    """
    Train the PINN model.
    
    Args:
        model (RocketEnginePINN): The PINN model
        inputs (torch.Tensor): Input data
        targets (torch.Tensor, optional): Target data for supervised learning
        num_epochs (int): Number of training epochs
        learning_rate (float): Learning rate for optimizer
        physics_weight (float): Weight of physics loss in combined loss
        
    Returns:
        list: Training losses
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Set normalization parameters
    model.set_normalization_params(inputs)
    
    losses = []
    
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(inputs)
        
        # Compute loss
        loss = model.combined_loss(inputs, outputs, targets, physics_weight)
        
        # Backward pass and optimization
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
        
        if epoch % 100 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.6f}")
    
    return losses 