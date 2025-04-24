"""
Hardware Interface for Rocket Engine Control

This module provides a virtual hardware interface for the rocket engine control system.
It can be extended to interface with real hardware in the future.

The interface simulates:
1. Sensor readings (pressure, temperature, flow rates)
2. Control outputs (valve positions, ignition)
3. Communication with embedded systems (STM32)
"""

import time
import numpy as np
import threading
import queue
import serial
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HardwareInterface")


class VirtualSensor:
    """
    Base class for a virtual sensor.
    """
    
    def __init__(self, name, units, noise_level=0.02, update_rate_hz=10):
        """
        Initialize a virtual sensor.
        
        Args:
            name: Sensor name
            units: Units of measurement
            noise_level: Noise level as a fraction of reading
            update_rate_hz: Update rate in Hz
        """
        self.name = name
        self.units = units
        self.noise_level = noise_level
        self.update_interval = 1.0 / update_rate_hz
        self.value = 0.0
        self.last_update = time.time()
        
    def read(self):
        """
        Read the current sensor value.
        
        Returns:
            Current sensor value with added noise
        """
        current_time = time.time()
        
        # Initialize noise
        noise = 0.0
        
        # If it's time to update, add some noise to the value
        if current_time - self.last_update >= self.update_interval:
            noise = np.random.normal(0, self.noise_level * abs(self.value) + 1e-6)
            self.last_update = current_time
            
        # Return value with noise
        return self.value * (1 + noise)
    
    def set_value(self, value):
        """
        Set the underlying true sensor value.
        
        Args:
            value: New sensor value
        """
        self.value = value


class VirtualActuator:
    """
    Base class for a virtual actuator.
    """
    
    def __init__(self, name, min_value=0.0, max_value=1.0, response_time=0.1):
        """
        Initialize a virtual actuator.
        
        Args:
            name: Actuator name
            min_value: Minimum actuator value
            max_value: Maximum actuator value
            response_time: Time to reach target value (in seconds)
        """
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.response_time = response_time
        
        self.current_value = 0.0
        self.target_value = 0.0
        self.last_update = time.time()
        
    def set(self, value):
        """
        Set the target actuator value.
        
        Args:
            value: Target value (will be clipped to min/max range)
        """
        self.target_value = np.clip(value, self.min_value, self.max_value)
        
    def read(self):
        """
        Read the current actuator value.
        
        The actuator gradually approaches the target value based on response time.
        
        Returns:
            Current actuator value
        """
        current_time = time.time()
        dt = current_time - self.last_update
        
        # Calculate how much the value should change based on response time
        if self.response_time > 0:
            max_change = dt / self.response_time * (self.max_value - self.min_value)
            
            # Move toward target value
            if self.current_value < self.target_value:
                self.current_value = min(
                    self.current_value + max_change, 
                    self.target_value
                )
            elif self.current_value > self.target_value:
                self.current_value = max(
                    self.current_value - max_change, 
                    self.target_value
                )
        else:
            # Instant response
            self.current_value = self.target_value
            
        self.last_update = current_time
        return self.current_value


class RocketEngineVirtualHardware:
    """
    Virtual hardware interface for a liquid rocket engine.
    """
    
    def __init__(self):
        """Initialize the virtual hardware."""
        # Create virtual sensors
        self.sensors = {
            'chamber_pressure': VirtualSensor('Chamber Pressure', 'Pa', noise_level=0.03),
            'chamber_temperature': VirtualSensor('Chamber Temperature', 'K', noise_level=0.02),
            'fuel_flow_rate': VirtualSensor('Fuel Flow Rate', 'kg/s', noise_level=0.04),
            'oxidizer_flow_rate': VirtualSensor('Oxidizer Flow Rate', 'kg/s', noise_level=0.04),
            'thrust': VirtualSensor('Thrust', 'N', noise_level=0.05)
        }
        
        # Create virtual actuators
        self.actuators = {
            'fuel_valve': VirtualActuator('Fuel Valve', response_time=0.2),
            'oxidizer_valve': VirtualActuator('Oxidizer Valve', response_time=0.2),
            'igniter': VirtualActuator('Igniter', min_value=0.0, max_value=1.0, response_time=0.05)
        }
        
        # Initialize internal state
        self.running = False
        self.ignited = False
        self.simulation_thread = None
        self.stop_event = threading.Event()
        
        # Create data queue for communication between threads
        self.data_queue = queue.Queue(maxsize=100)
        
        # Initialize internal simulation parameters
        self._init_simulation_params()
        
    def _init_simulation_params(self):
        """Initialize internal simulation parameters."""
        self.sim_params = {
            'chamber_volume': 0.001,  # m³
            'throat_diameter': 0.03,  # m
            'exit_diameter': 0.09,  # m
            'fuel_density': 420,  # kg/m³ (methane)
            'oxidizer_density': 1230,  # kg/m³ (nitrous oxide)
            'mixture_ratio_target': 2.5,  # O/F ratio
            'chamber_pressure_max': 5e6,  # Pa
            'ambient_pressure': 101325,  # Pa
            'temperature_ambient': 290,  # K
            'temperature_combustion': 3000,  # K
            'simulation_rate': 20,  # Hz
            'ignition_delay': 0.5,  # seconds delay after igniter signal
            'pressure_factor': 5e6  # Pa/(kg/s) - more realistic value
        }
        
    def start(self):
        """Start the virtual hardware simulation."""
        if self.running:
            logger.warning("Hardware simulation already running")
            return False
            
        self.stop_event.clear()
        self.running = True
        
        # Reset sensors and actuators
        for sensor in self.sensors.values():
            sensor.set_value(0.0)
            
        for actuator in self.actuators.values():
            actuator.set(0.0)
            
        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(
            target=self._simulation_loop, 
            daemon=True
        )
        self.simulation_thread.start()
        
        logger.info("Virtual hardware simulation started")
        return True
        
    def stop(self):
        """Stop the virtual hardware simulation."""
        if not self.running:
            logger.warning("Hardware simulation not running")
            return False
            
        self.stop_event.set()
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2.0)
            
        self.running = False
        self.ignited = False
        
        # Reset ignition timer
        if hasattr(self, 'ignition_start_time'):
            delattr(self, 'ignition_start_time')
        
        # Reset sensors and actuators
        for sensor in self.sensors.values():
            sensor.set_value(0.0)
            
        for actuator in self.actuators.values():
            actuator.set(0.0)
            
        logger.info("Virtual hardware simulation stopped")
        return True
        
    def _simulation_loop(self):
        """Main simulation loop that runs in a separate thread."""
        update_interval = 1.0 / self.sim_params['simulation_rate']
        
        while not self.stop_event.is_set():
            loop_start = time.time()
            
            # Read current actuator values
            fuel_valve = self.actuators['fuel_valve'].read()
            oxidizer_valve = self.actuators['oxidizer_valve'].read()
            igniter = self.actuators['igniter'].read()
            
            # Calculate flow rates based on valve positions
            fuel_flow = fuel_valve * 0.3  # kg/s at max opening
            oxidizer_flow = oxidizer_valve * 0.7  # kg/s at max opening
            
            # Check ignition state
            if igniter > 0.7 and not self.ignited and fuel_flow > 0.05 and oxidizer_flow > 0.05:
                # Start ignition sequence with delay
                if not hasattr(self, 'ignition_start_time'):
                    self.ignition_start_time = time.time()
                
                # Check if ignition delay has passed
                if time.time() - self.ignition_start_time >= self.sim_params['ignition_delay']:
                    self.ignited = True
                    logger.info("Engine ignited")
            
            # If ignition has occurred, simulate engine running
            if self.ignited:
                # Calculate mixture ratio
                if fuel_flow > 1e-6:  # Avoid division by zero
                    mixture_ratio = oxidizer_flow / fuel_flow
                else:
                    mixture_ratio = 0.0
                    
                # Calculate chamber pressure (simplified model)
                total_flow = fuel_flow + oxidizer_flow
                chamber_pressure = total_flow * self.sim_params['pressure_factor']
                
                # Ensure pressure is within realistic bounds
                chamber_pressure = max(self.sim_params['ambient_pressure'], min(chamber_pressure, self.sim_params['chamber_pressure_max']))
                
                # Calculate chamber temperature (simplification)
                if 1.5 < mixture_ratio < 4.0:
                    # Good mixture ratio range
                    temperature_factor = 0.9
                else:
                    # Suboptimal combustion
                    temperature_factor = 0.7
                    
                chamber_temperature = self.sim_params['temperature_combustion'] * temperature_factor
                
                # Calculate thrust (simplified)
                # F = m_dot * v_e + (p_e - p_a) * A_e
                # Simplified to: F = CF * A_t * p_c
                throat_area = np.pi * (self.sim_params['throat_diameter'] / 2)**2
                thrust_coefficient = 1.4  # Typical value for a decent nozzle
                thrust = thrust_coefficient * throat_area * chamber_pressure
                
                # Update sensor values
                self.sensors['chamber_pressure'].set_value(chamber_pressure)
                self.sensors['chamber_temperature'].set_value(chamber_temperature)
                self.sensors['fuel_flow_rate'].set_value(fuel_flow)
                self.sensors['oxidizer_flow_rate'].set_value(oxidizer_flow)
                self.sensors['thrust'].set_value(thrust)
            else:
                # Engine not ignited, set low/zero values for sensors
                self.sensors['chamber_pressure'].set_value(self.sim_params['ambient_pressure'])
                self.sensors['chamber_temperature'].set_value(self.sim_params['temperature_ambient'])
                self.sensors['fuel_flow_rate'].set_value(fuel_flow)
                self.sensors['oxidizer_flow_rate'].set_value(oxidizer_flow)
                self.sensors['thrust'].set_value(0.0)
                
            # Push data to queue for other threads to use
            sensor_data = {name: sensor.read() for name, sensor in self.sensors.items()}
            actuator_data = {name: actuator.read() for name, actuator in self.actuators.items()}
            
            data_packet = {
                'timestamp': time.time(),
                'sensors': sensor_data,
                'actuators': actuator_data,
                'ignited': self.ignited
            }
            
            try:
                self.data_queue.put(data_packet, block=False)
            except queue.Full:
                # Queue is full, just drop this packet
                pass
                
            # Sleep to maintain update rate
            elapsed = time.time() - loop_start
            if elapsed < update_interval:
                time.sleep(update_interval - elapsed)
                
    def get_latest_data(self):
        """
        Get the latest data packet from the simulation.
        
        Returns:
            Latest data packet or None if no data is available
        """
        try:
            return self.data_queue.get(block=False)
        except queue.Empty:
            return None
            
    def read_sensor(self, sensor_name):
        """
        Read a specific sensor value.
        
        Args:
            sensor_name: Name of the sensor to read
            
        Returns:
            Sensor value or None if sensor doesn't exist
        """
        if sensor_name in self.sensors:
            return self.sensors[sensor_name].read()
        return None
        
    def set_actuator(self, actuator_name, value):
        """
        Set a specific actuator value.
        
        Args:
            actuator_name: Name of the actuator to set
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        if actuator_name in self.actuators:
            self.actuators[actuator_name].set(value)
            return True
        return False
        
    def is_running(self):
        """
        Check if the simulation is running.
        
        Returns:
            True if running, False otherwise
        """
        return self.running
        
    def is_ignited(self):
        """
        Check if the engine is ignited.
        
        Returns:
            True if ignited, False otherwise
        """
        return self.ignited


class SerialHardwareInterface:
    """
    Real hardware interface using serial communication with the STM32 controller.
    This is a placeholder class for future implementation.
    """
    
    def __init__(self, port, baudrate=115200):
        """
        Initialize the serial hardware interface.
        
        Args:
            port: Serial port to use
            baudrate: Baud rate for serial communication
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = False
        self.read_thread = None
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue(maxsize=100)
        
    def connect(self):
        """
        Connect to the hardware.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1.0)
            self.running = True
            
            # Start read thread
            self.stop_event.clear()
            self.read_thread = threading.Thread(
                target=self._read_loop,
                daemon=True
            )
            self.read_thread.start()
            
            logger.info(f"Connected to hardware on {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to hardware: {e}")
            return False
            
    def disconnect(self):
        """
        Disconnect from the hardware.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.running:
            return True
            
        self.running = False
        self.stop_event.set()
        
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
            
        if self.serial:
            try:
                self.serial.close()
                logger.info("Disconnected from hardware")
                return True
            except Exception as e:
                logger.error(f"Failed to disconnect from hardware: {e}")
                return False
                
    def _read_loop(self):
        """Read data from the serial port in a separate thread."""
        while not self.stop_event.is_set() and self.serial:
            try:
                line = self.serial.readline().decode('utf-8').strip()
                if line:
                    # Parse the data format from STM32
                    # Example format: "SENSOR:chamber_pressure:1234567"
                    parts = line.split(':')
                    if len(parts) >= 3:
                        data_type = parts[0]
                        name = parts[1]
                        value = parts[2]
                        
                        try:
                            value = float(value)
                            
                            data_packet = {
                                'timestamp': time.time(),
                                'type': data_type,
                                'name': name,
                                'value': value
                            }
                            
                            try:
                                self.data_queue.put(data_packet, block=False)
                            except queue.Full:
                                pass
                        except ValueError:
                            logger.warning(f"Invalid value received: {line}")
            except Exception as e:
                logger.error(f"Error reading from serial: {e}")
                time.sleep(1.0)
                
    def send_command(self, command, value=None):
        """
        Send a command to the hardware.
        
        Args:
            command: Command to send
            value: Value to send with the command
            
        Returns:
            True if successful, False otherwise
        """
        if not self.running or not self.serial:
            logger.error("Not connected to hardware")
            return False
            
        try:
            if value is not None:
                cmd_str = f"CMD:{command}:{value}\n"
            else:
                cmd_str = f"CMD:{command}\n"
                
            self.serial.write(cmd_str.encode('utf-8'))
            logger.debug(f"Sent command: {cmd_str.strip()}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
            
    def get_latest_data(self):
        """
        Get the latest data packet from the hardware.
        
        Returns:
            Latest data packet or None if no data is available
        """
        try:
            return self.data_queue.get(block=False)
        except queue.Empty:
            return None


def get_hardware_interface(use_virtual=True, port=None):
    """
    Factory function to get a hardware interface.
    
    Args:
        use_virtual: Whether to use the virtual hardware interface
        port: Serial port to use for real hardware
        
    Returns:
        Hardware interface instance
    """
    if use_virtual:
        return RocketEngineVirtualHardware()
    else:
        if port is None:
            # Try to detect the port automatically
            # This is platform-dependent and might not work in all cases
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            
            if ports:
                # Just use the first port found
                port = ports[0].device
                logger.info(f"Auto-detected serial port: {port}")
            else:
                logger.error("No serial ports found")
                return None
                
        return SerialHardwareInterface(port)


if __name__ == "__main__":
    # Example usage
    print("Testing virtual hardware interface...")
    hw = get_hardware_interface(use_virtual=True)
    
    # Start the simulation
    hw.start()
    
    # Set actuator values
    hw.set_actuator('fuel_valve', 0.3)
    hw.set_actuator('oxidizer_valve', 0.6)
    
    # Wait for valves to open
    time.sleep(1.0)
    
    # Ignite the engine
    hw.set_actuator('igniter', 1.0)
    
    # Run for a few seconds
    for i in range(10):
        # Read sensor values
        chamber_pressure = hw.read_sensor('chamber_pressure')
        chamber_temperature = hw.read_sensor('chamber_temperature')
        thrust = hw.read_sensor('thrust')
        
        print(f"Time: {i}s")
        print(f"  Chamber Pressure: {chamber_pressure/1e6:.2f} MPa")
        print(f"  Chamber Temperature: {chamber_temperature:.2f} K")
        print(f"  Thrust: {thrust:.2f} N")
        
        time.sleep(1.0)
        
    # Shut down
    hw.set_actuator('igniter', 0.0)
    hw.set_actuator('fuel_valve', 0.0)
    hw.set_actuator('oxidizer_valve', 0.0)
    
    time.sleep(1.0)
    hw.stop()
    
    print("Test completed.") 