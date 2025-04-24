import numpy as np
import time


class PIDController:
    """
    PID controller for rocket engine control.
    
    This class implements a PID controller that can be used to control
    various parameters of a rocket engine, such as chamber pressure or thrust.
    """
    
    def __init__(self, kp=1.0, ki=0.1, kd=0.05, setpoint=0.0, output_limits=None,
                 integral_limits=None, differential_on_measurement=False, sample_time=0.01):
        """
        Initialize the PID controller.
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            setpoint: Controller setpoint
            output_limits: Tuple (min, max) for output limits
            integral_limits: Tuple (min, max) for integral term limits
            differential_on_measurement: Whether to compute derivative on measurement
                rather than error (reduces "derivative kick")
            sample_time: Sample time in seconds
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.integral_limits = integral_limits
        self.differential_on_measurement = differential_on_measurement
        self.sample_time = sample_time
        
        # Initialize internal state
        self.last_time = None
        self.last_error = 0.0
        self.last_measurement = 0.0
        self.proportional = 0.0
        self.integral = 0.0
        self.derivative = 0.0
        
        # Initialize output and last time
        self.output = 0.0
        self.last_time = time.time()
        
    def reset(self):
        """Reset the controller's internal state."""
        self.last_error = 0.0
        self.last_measurement = 0.0
        self.proportional = 0.0
        self.integral = 0.0
        self.derivative = 0.0
        self.output = 0.0
        self.last_time = time.time()
        
    def set_tunings(self, kp, ki, kd):
        """
        Set PID controller tuning parameters.
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
    def set_setpoint(self, setpoint):
        """
        Set controller setpoint.
        
        Args:
            setpoint: Desired setpoint
        """
        self.setpoint = setpoint
        
    def update(self, measurement, current_time=None):
        """
        Update the PID controller.
        
        Args:
            measurement: Current process value
            current_time: Current time (defaults to time.time())
            
        Returns:
            Control output
        """
        if current_time is None:
            current_time = time.time()
            
        # Calculate time delta
        dt = current_time - self.last_time
        
        # If sample time hasn't elapsed, return last output
        if dt < self.sample_time:
            return self.output
            
        # Calculate error
        error = self.setpoint - measurement
        
        # Proportional term
        self.proportional = self.kp * error
        
        # Integral term
        self.integral += self.ki * error * dt
        
        # Apply integral limits if specified
        if self.integral_limits is not None:
            self.integral = np.clip(self.integral, *self.integral_limits)
            
        # Derivative term (on measurement or error)
        if self.differential_on_measurement:
            self.derivative = -self.kd * (measurement - self.last_measurement) / dt
        else:
            self.derivative = self.kd * (error - self.last_error) / dt
            
        # Calculate output
        self.output = self.proportional + self.integral + self.derivative
        
        # Apply output limits if specified
        if self.output_limits is not None:
            self.output = np.clip(self.output, *self.output_limits)
            
        # Update internal state
        self.last_error = error
        self.last_measurement = measurement
        self.last_time = current_time
        
        return self.output
        
    def compute_auto_tunings(self, process_gain, process_time_constant, process_dead_time,
                            tuning_rule='ziegler-nichols'):
        """
        Compute PID tunings using various tuning rules.
        
        Args:
            process_gain: Process gain (steady state gain)
            process_time_constant: Process time constant
            process_dead_time: Process dead time
            tuning_rule: Tuning rule to use (options: 'ziegler-nichols', 'cohen-coon', 'chien-hrones-reswick')
            
        Returns:
            Tuple of (kp, ki, kd)
        """
        if tuning_rule == 'ziegler-nichols':
            # Ziegler-Nichols tuning rule
            kp = 1.2 / (process_gain * process_dead_time / process_time_constant)
            ki = kp / (2.0 * process_dead_time)
            kd = kp * 0.5 * process_dead_time
            
        elif tuning_rule == 'cohen-coon':
            # Cohen-Coon tuning rule
            a = process_dead_time / (process_dead_time + process_time_constant)
            kp = (1.35 / process_gain) * (1 + 0.18 * a / (1 - a))
            ki = kp / (process_dead_time * (1.17 + 0.53 * a / (1 - a)))
            kd = kp * process_dead_time * 0.37 * (1 - a) / (1 + 0.18 * a / (1 - a))
            
        elif tuning_rule == 'chien-hrones-reswick':
            # Chien-Hrones-Reswick tuning rule (0% overshoot)
            kp = 0.6 / (process_gain * process_dead_time / process_time_constant)
            ki = kp / (4.0 * process_dead_time)
            kd = kp * 0.5 * process_dead_time
            
        else:
            raise ValueError(f"Unknown tuning rule: {tuning_rule}")
            
        return kp, ki, kd
        
    def auto_tune(self, process_gain, process_time_constant, process_dead_time,
                 tuning_rule='ziegler-nichols'):
        """
        Automatically tune the PID controller.
        
        Args:
            process_gain: Process gain (steady state gain)
            process_time_constant: Process time constant
            process_dead_time: Process dead time
            tuning_rule: Tuning rule to use
        """
        kp, ki, kd = self.compute_auto_tunings(
            process_gain, process_time_constant, process_dead_time, tuning_rule
        )
        
        self.set_tunings(kp, ki, kd)
        self.reset()
        
        return kp, ki, kd


class PINNGuidedPIDController(PIDController):
    """
    PID controller guided by PINN model predictions.
    
    This controller extends the base PID controller by incorporating 
    predictions from a Physics-Informed Neural Network to improve control.
    """
    
    def __init__(self, pinn_model=None, **kwargs):
        """
        Initialize the PINN-guided PID controller.
        
        Args:
            pinn_model: PINN model for predictions
            **kwargs: Arguments to pass to PIDController
        """
        super().__init__(**kwargs)
        self.pinn_model = pinn_model
        self.prediction_horizon = 5  # Number of time steps to predict ahead
        self.prediction_dt = 0.1  # Time step for predictions
        
    def set_pinn_model(self, pinn_model):
        """
        Set the PINN model for predictions.
        
        Args:
            pinn_model: PINN model
        """
        self.pinn_model = pinn_model
        
    def _predict_future_state(self, current_state):
        """
        Use PINN model to predict future states.
        
        Args:
            current_state: Current state parameters
            
        Returns:
            Predicted future states
        """
        if self.pinn_model is None:
            return None
            
        # Create input array for predictions
        predictions = []
        
        # Create batch of future time steps
        input_batch = np.tile(current_state, (self.prediction_horizon, 1))
        
        # Set time steps for prediction
        current_time = current_state[6]  # Assuming time is at index 6
        for i in range(self.prediction_horizon):
            input_batch[i, 6] = current_time + (i + 1) * self.prediction_dt
            
        # Convert to torch tensor (assuming PyTorch model)
        import torch
        input_tensor = torch.tensor(input_batch, dtype=torch.float32)
        
        # Get predictions
        with torch.no_grad():
            predicted_outputs = self.pinn_model(input_tensor).cpu().numpy()
            
        return predicted_outputs
        
    def update_with_predictions(self, measurement, current_state, current_time=None):
        """
        Update controller using both current measurement and PINN predictions.
        
        Args:
            measurement: Current process value
            current_state: Current state parameters for PINN input
            current_time: Current time
            
        Returns:
            Control output
        """
        # Get normal PID output
        pid_output = self.update(measurement, current_time)
        
        # If no PINN model is available, return standard PID output
        if self.pinn_model is None:
            return pid_output
            
        # Get PINN predictions
        future_predictions = self._predict_future_state(current_state)
        
        if future_predictions is None:
            return pid_output
            
        # Use the first prediction for feedback (assuming we're controlling the first output)
        predicted_next_value = future_predictions[0, 0]  # First future point, first output variable
        
        # Calculate predicted error
        predicted_error = self.setpoint - predicted_next_value
        
        # Adjust output based on predicted error
        # Simple weighted blend between current PID and predicted correction
        prediction_weight = 0.3  # How much we trust predictions vs. current
        prediction_correction = self.kp * predicted_error * prediction_weight
        
        # Blend outputs
        blended_output = pid_output * (1 - prediction_weight) + prediction_correction
        
        # Apply output limits if specified
        if self.output_limits is not None:
            blended_output = np.clip(blended_output, *self.output_limits)
            
        self.output = blended_output
        
        return blended_output 