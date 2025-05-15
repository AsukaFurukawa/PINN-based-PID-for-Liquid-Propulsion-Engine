import streamlit as st
import streamlit.components.v1 as components
import os
import json
import numpy as np
import time
from pathlib import Path
import base64
import tempfile

class AdvancedThreeDVisualization:
    """
    Advanced 3D visualization class that integrates three.js with Streamlit
    for realistic rocket engine simulation and visualization.
    """
    
    def __init__(self, height=600, key=None):
        """
        Initialize the 3D visualization component
        
        Args:
            height (int): Height of the visualization in pixels
            key (str): Unique key for the component instance
        """
        self.height = height
        self.key = key or f"threed_viz_{int(time.time() * 1000)}"
        self.viz_key = f"{self.key}_viz"
        self.state_key = f"{self.key}_state"
        
        # Initialize state in session if not exists
        if self.state_key not in st.session_state:
            st.session_state[self.state_key] = {
                "engine_status": "Standby",
                "chamber_pressure": 0.1,
                "mixture_ratio": 0.0,
                "chamber_length": 0.15,
                "chamber_diameter": 0.08,
                "throat_diameter": 0.03,
                "exit_diameter": 0.09,
                "nozzle_length": 0.12,
                "auto_rotate": True,
                "last_update": time.time()
            }
        
        # Load three.js dependencies
        three_js_path = self._get_js_path('three.min.js')
        orbit_controls_path = self._get_js_path('OrbitControls.js')
        stats_js_path = self._get_js_path('stats.min.js')
        utils_js_path = self._get_js_path('utils.js')
        engine_viz_path = self._get_js_path('engine_visualization.js')
        
        # Set up component resources
        self.js_resources = [
            three_js_path,
            orbit_controls_path,
            stats_js_path,
            utils_js_path,
            engine_viz_path
        ]
    
    def _get_js_path(self, js_file):
        """Get path to JavaScript file, handling both development and bundled modes"""
        # Check if file exists in three_js directory
        three_js_dir = Path(__file__).parent / "three_js"
        if (three_js_dir / js_file).exists():
            return str(three_js_dir / js_file)
        
        # Fallback to CDN resources for standard libraries
        if js_file == 'three.min.js':
            return "https://cdn.jsdelivr.net/npm/three@0.137.0/build/three.min.js"
        elif js_file == 'OrbitControls.js':
            return "https://cdn.jsdelivr.net/npm/three@0.137.0/examples/js/controls/OrbitControls.js"
        elif js_file == 'stats.min.js':
            return "https://cdn.jsdelivr.net/npm/stats.js@0.17.0/build/stats.min.js"
        
        # Could not find file
        st.error(f"Could not locate JavaScript file: {js_file}")
        return None
    
    def _read_js_file(self, file_path):
        """Read a JavaScript file and return its contents"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            # For CDN URLs, return a script tag to load from URL
            if file_path.startswith('http'):
                return f'<script src="{file_path}"></script>'
            
            st.error(f"Error reading JavaScript file: {e}")
            return ""
    
    def render(self, engine_params=None, engine_status=None):
        """
        Render the 3D visualization component
        
        Args:
            engine_params (dict): Dictionary of engine parameters to update
            engine_status (str): Engine status to update
        """
        # Update state with provided parameters
        if engine_params:
            for key, value in engine_params.items():
                if key in st.session_state[self.state_key]:
                    st.session_state[self.state_key][key] = value
        
        if engine_status:
            st.session_state[self.state_key]["engine_status"] = engine_status
        
        st.session_state[self.state_key]["last_update"] = time.time()
        
        # Create the component HTML
        html_content = self._create_html_component()
        
        # Render component
        components.html(
            html_content,
            height=self.height
        )
    
    def _create_html_component(self):
        """Create the HTML component with embedded JavaScript"""
        state = st.session_state[self.state_key]
        
        # Format engine parameters for JavaScript
        engine_params_json = json.dumps({
            "chamberLength": state["chamber_length"],
            "chamberDiameter": state["chamber_diameter"],
            "throatDiameter": state["throat_diameter"],
            "exitDiameter": state["exit_diameter"],
            "nozzleLength": state["nozzle_length"]
        })

        # Create HTML with direct script tags for proper loading order
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; }}
                #engine-container {{ width: 100%; height: {self.height}px; }}
            </style>
            <!-- Load Three.js first -->
            <script src="https://cdn.jsdelivr.net/npm/three@0.137.0/build/three.min.js"></script>
            <!-- Load Three.js dependencies -->
            <script src="https://cdn.jsdelivr.net/npm/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/stats.js@0.17.0/build/stats.min.js"></script>
        </head>
        <body>
            <div id="engine-container"></div>
            
            <!-- Load custom scripts -->
            <script>
                {self._read_js_file(self._get_js_path('utils.js'))}
            </script>
            <script>
                {self._read_js_file(self._get_js_path('engine_visualization.js'))}
            </script>
            
            <script>
                // Initialize visualizer when DOM is loaded
                document.addEventListener('DOMContentLoaded', function() {{
                    // Create engine visualizer
                    const container = document.getElementById('engine-container');
                    const visualizer = new RocketEngineVisualizer('engine-container', {{
                        autoRotate: {str(state['auto_rotate']).lower()},
                        showGrid: true,
                        showAxes: true,
                        engineParams: {engine_params_json}
                    }});
                    
                    // Set initial state
                    visualizer.updateEngineState({{
                        status: '{state["engine_status"]}',
                        chamberPressure: {state["chamber_pressure"]},
                        mixtureRatio: {state["mixture_ratio"]}
                    }});
                    
                    // Expose visualizer to window for debugging
                    window.engineVisualizer = visualizer;
                    
                    // Function to handle messages from Streamlit
                    window.addEventListener('message', function(event) {{
                        const data = event.data;
                        
                        // Check if the message is for our component
                        if (data.type === 'streamlit:render' && data.key === '{self.viz_key}') {{
                            if (data.args.engineState) {{
                                visualizer.updateEngineState(data.args.engineState);
                            }}
                            
                            if (data.args.engineParams) {{
                                visualizer.updateEngineGeometry(data.args.engineParams);
                            }}
                            
                            if (data.args.cameraView) {{
                                visualizer.setCameraView(
                                    data.args.cameraView.position,
                                    data.args.cameraView.target
                                );
                            }}
                            
                            if (data.args.autoRotate !== undefined) {{
                                visualizer.setAutoRotate(data.args.autoRotate);
                            }}
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    
    def update_engine_state(self, status=None, chamber_pressure=None, mixture_ratio=None):
        """
        Update the engine state (non-geometry parameters)
        
        Args:
            status (str): Engine status ("Standby", "Startup", "Nominal Operation", etc.)
            chamber_pressure (float): Chamber pressure in MPa
            mixture_ratio (float): Propellant mixture ratio (O/F)
        """
        # Update state values
        state = st.session_state[self.state_key]
        if status is not None:
            state["engine_status"] = status
        if chamber_pressure is not None:
            state["chamber_pressure"] = chamber_pressure
        if mixture_ratio is not None:
            state["mixture_ratio"] = mixture_ratio
        
        state["last_update"] = time.time()
        
        # Re-render component
        self.render()
    
    def update_engine_geometry(self, chamber_length=None, chamber_diameter=None, 
                             throat_diameter=None, exit_diameter=None, nozzle_length=None):
        """
        Update the engine geometry parameters
        
        Args:
            chamber_length (float): Chamber length in meters
            chamber_diameter (float): Chamber diameter in meters
            throat_diameter (float): Throat diameter in meters
            exit_diameter (float): Exit diameter in meters
            nozzle_length (float): Nozzle length in meters
        """
        # Update state values
        state = st.session_state[self.state_key]
        if chamber_length is not None:
            state["chamber_length"] = chamber_length
        if chamber_diameter is not None:
            state["chamber_diameter"] = chamber_diameter
        if throat_diameter is not None:
            state["throat_diameter"] = throat_diameter
        if exit_diameter is not None:
            state["exit_diameter"] = exit_diameter
        if nozzle_length is not None:
            state["nozzle_length"] = nozzle_length
        
        state["last_update"] = time.time()
        
        # Re-render component
        self.render()
    
    def set_camera_view(self, position, target=None):
        """
        Set the camera position and target
        
        Args:
            position (dict): Camera position {x, y, z}
            target (dict): Camera target {x, y, z}, defaults to center of engine
        """
        if target is None:
            target = {"x": 0, "y": 0, "z": 0.1}
        
        # Re-render with updated camera
        self.render()  # This will implicitly use the updated state
    
    def toggle_auto_rotate(self, enabled=None):
        """
        Toggle auto-rotation of the camera
        
        Args:
            enabled (bool): Whether auto-rotation should be enabled
        """
        if enabled is not None:
            st.session_state[self.state_key]["auto_rotate"] = enabled
        else:
            st.session_state[self.state_key]["auto_rotate"] = not st.session_state[self.state_key]["auto_rotate"]
        
        # Re-render component
        self.render()


def get_predefined_camera_views():
    """Return a dictionary of predefined camera views for the engine visualization"""
    return {
        "Default": {
            "position": {"x": 0.3, "y": 0.3, "z": 0.3},
            "target": {"x": 0, "y": 0, "z": 0.1}
        },
        "Side View": {
            "position": {"x": 0.4, "y": 0, "z": 0.1},
            "target": {"x": 0, "y": 0, "z": 0.1}
        },
        "Top View": {
            "position": {"x": 0, "y": 0, "z": 0.4},
            "target": {"x": 0, "y": 0, "z": 0.1}
        },
        "Injector End": {
            "position": {"x": 0, "y": 0, "z": -0.2},
            "target": {"x": 0, "y": 0, "z": 0.05}
        },
        "Exit View": {
            "position": {"x": 0, "y": 0, "z": 0.5},
            "target": {"x": 0, "y": 0, "z": 0.3}
        },
        "Chamber Detail": {
            "position": {"x": 0.15, "y": 0.15, "z": 0.1},
            "target": {"x": 0, "y": 0, "z": 0.1}
        }
    }


def generate_performance_data(chamber_pressure, mixture_ratio, engine_status, animation_time=None):
    """
    Generate realistic performance data for a liquid rocket engine based on input parameters
    
    Args:
        chamber_pressure (float): Chamber pressure in MPa
        mixture_ratio (float): Mixture ratio (O/F)
        engine_status (str): Current engine status
        animation_time (float): Current animation time, used for adding realistic variations
        
    Returns:
        dict: Dictionary containing performance metrics
    """
    if animation_time is None:
        animation_time = time.time()
    
    t = animation_time
    
    # Convert to proper units
    chamber_pressure_pa = chamber_pressure * 1e6
    
    # Calculate base values based on engine status
    if engine_status == "Nominal Operation":
        # Theoretical values based on propellant types
        if mixture_ratio < 2.5:  # LOX/LH2
            base_isp = 360 + (mixture_ratio - 1.5) * 20
            base_c_star = 2200 + (mixture_ratio - 1.5) * 200
            base_temp = 2800 + (mixture_ratio - 1.5) * 400
            propellant = "LOX/LH2"
        elif mixture_ratio < 3.5:  # LOX/CH4
            base_isp = 300 + (mixture_ratio - 2.5) * 10
            base_c_star = 1800 + (mixture_ratio - 2.5) * 100
            base_temp = 2700 + (mixture_ratio - 2.5) * 300
            propellant = "LOX/CH4"
        else:  # LOX/RP-1
            base_isp = 280 + (mixture_ratio - 3.5) * 5
            base_c_star = 1750 + (mixture_ratio - 3.5) * 50
            base_temp = 2600 + (mixture_ratio - 3.5) * 200
            propellant = "LOX/RP-1"
        
        # Calculate thrust from chamber pressure and throat area (simplified)
        throat_area = np.pi * (0.03/2)**2  # Using default throat diameter
        c_f = 1.4  # Thrust coefficient (simplified)
        thrust = c_f * chamber_pressure_pa * throat_area
        
        # Add oscillations for realism
        thrust_oscillation = 0.02 * thrust * np.sin(t * 10)
        temp_oscillation = 30 * np.sin(t * 0.5)
        isp_oscillation = 3 * np.sin(t * 0.3)
        
        # Set final values
        thrust = thrust + thrust_oscillation
        isp = base_isp + isp_oscillation
        chamber_temp = base_temp + temp_oscillation
        c_star = base_c_star + 20 * np.sin(t * 0.2)
        exit_velocity = isp * 9.81
        combustion_efficiency = 0.96 + 0.02 * np.sin(t * 0.1)
        
    elif engine_status == "Startup":
        # During startup, parameters are increasing
        startup_factor = 0.5 + 0.5 * np.sin(np.pi * min(t % 10 / 10, 1))
        
        # Base values for fully operational state
        base_thrust = 5000 * chamber_pressure
        base_isp = 300 
        base_temp = 3000
        base_c_star = 1800
        
        # Apply startup factor
        thrust = base_thrust * startup_factor
        isp = base_isp * (0.5 + 0.5 * startup_factor)
        chamber_temp = 300 + base_temp * startup_factor
        c_star = base_c_star * startup_factor
        exit_velocity = isp * 9.81 * startup_factor
        propellant = "Mixed"
        combustion_efficiency = 0.7 + 0.25 * startup_factor
        
    elif engine_status == "Ignition Sequence":
        # During ignition, small values with rapid fluctuations
        ignition_factor = 0.2 + 0.1 * np.sin(t * 20)
        
        # Ignition is characterized by rapid spikes
        thrust = 500 * ignition_factor * (0.5 + 0.5 * np.sin(t * 30))
        isp = 100 * ignition_factor
        chamber_temp = 500 + 1000 * ignition_factor
        c_star = 500 + 500 * ignition_factor
        exit_velocity = isp * 9.81 * ignition_factor
        propellant = "Mixed"
        combustion_efficiency = 0.4 + 0.1 * np.sin(t * 15)
        
    elif engine_status == "Shutdown Sequence":
        # During shutdown, parameters are decreasing
        shutdown_factor = max(0, 1.0 - (t % 10) / 10)
        
        # Base values for fully operational state
        base_thrust = 5000 * chamber_pressure
        base_isp = 300
        base_temp = 3000
        base_c_star = 1800
        
        # Apply shutdown factor with some oscillation during cooldown
        thrust = base_thrust * shutdown_factor * (0.8 + 0.2 * np.sin(t * 5))
        isp = base_isp * shutdown_factor
        chamber_temp = 300 + base_temp * shutdown_factor
        c_star = base_c_star * shutdown_factor
        exit_velocity = isp * 9.81 * shutdown_factor
        propellant = "Mixed"
        combustion_efficiency = 0.8 * shutdown_factor
        
    else:  # Standby
        # Minimal values with slight environmental variations
        thrust = 0 + 2 * np.sin(t * 0.2)  # Minimal sensor noise
        isp = 0
        chamber_temp = 290 + 10 * np.sin(t * 0.1)  # Ambient temperature variation
        c_star = 0
        exit_velocity = 0
        propellant = "None"
        combustion_efficiency = 0
    
    # Calculate additional parameters
    if thrust > 0:
        mass_flow = thrust / (isp * 9.81) if isp > 0 else 0
        fuel_flow = mass_flow / (mixture_ratio + 1)
        oxidizer_flow = mass_flow * mixture_ratio / (mixture_ratio + 1)
    else:
        mass_flow = 0
        fuel_flow = 0
        oxidizer_flow = 0
    
    # Calculate pressure ratio (chamber to ambient)
    ambient_pressure = 0.101  # MPa (sea level)
    pressure_ratio = chamber_pressure / ambient_pressure
    
    # Calculate expansion ratio from ideal gas law and isentropic relations
    gamma = 1.2  # Specific heat ratio (simplification)
    if chamber_pressure > ambient_pressure:
        expansion_ratio = (pressure_ratio) ** (1/gamma)
    else:
        expansion_ratio = 1.0
    
    # Return comprehensive data dictionary
    return {
        "thrust": thrust,
        "specific_impulse": isp,
        "chamber_pressure": chamber_pressure,
        "chamber_temperature": chamber_temp,
        "c_star": c_star,
        "exit_velocity": exit_velocity,
        "mixture_ratio": mixture_ratio,
        "mass_flow_rate": mass_flow,
        "fuel_flow_rate": fuel_flow,
        "oxidizer_flow_rate": oxidizer_flow,
        "expansion_ratio": expansion_ratio,
        "pressure_ratio": pressure_ratio,
        "propellant_type": propellant,
        "combustion_efficiency": combustion_efficiency
    }


def generate_optimization_recommendations(metrics):
    """
    Generate optimization recommendations based on engine metrics
    
    Args:
        metrics (dict): Engine performance metrics
        
    Returns:
        list: List of recommendation strings
    """
    recommendations = []
    
    # Optimum mixture ratio recommendations
    if metrics["propellant_type"] == "LOX/LH2":
        optimum_mr = 5.0
    elif metrics["propellant_type"] == "LOX/CH4":
        optimum_mr = 3.0
    elif metrics["propellant_type"] == "LOX/RP-1":
        optimum_mr = 2.3
    else:
        optimum_mr = 2.5
    
    mr_diff = abs(metrics["mixture_ratio"] - optimum_mr)
    if mr_diff > 0.5 and metrics["mixture_ratio"] > 0:
        if metrics["mixture_ratio"] < optimum_mr:
            recommendations.append(f"Consider increasing mixture ratio toward optimal value of {optimum_mr:.1f} for {metrics['propellant_type']}")
        else:
            recommendations.append(f"Consider decreasing mixture ratio toward optimal value of {optimum_mr:.1f} for {metrics['propellant_type']}")
    
    # Temperature recommendations
    if metrics["chamber_temperature"] > 3200:
        recommendations.append("Chamber temperature is high. Consider reducing chamber pressure or increasing cooling.")
    elif metrics["chamber_temperature"] < 2000 and metrics["chamber_temperature"] > 0:
        recommendations.append("Chamber temperature is low. Performance could be improved with higher temperature.")
    
    # Expansion ratio recommendations
    p_ambient = 0.101  # MPa, sea level
    optimal_expansion = (metrics["chamber_pressure"] / p_ambient) ** (1/5)
    current_expansion = metrics["expansion_ratio"]
    
    if abs(optimal_expansion - current_expansion) / optimal_expansion > 0.2 and metrics["chamber_pressure"] > 0.2:
        recommendations.append(f"Current expansion ratio is {current_expansion:.1f}. Optimal for this chamber pressure would be {optimal_expansion:.1f}")
    
    # Combustion efficiency recommendations
    if metrics["combustion_efficiency"] < 0.9 and metrics["combustion_efficiency"] > 0:
        recommendations.append("Combustion efficiency could be improved. Check injector design and propellant conditioning.")
    
    return recommendations 