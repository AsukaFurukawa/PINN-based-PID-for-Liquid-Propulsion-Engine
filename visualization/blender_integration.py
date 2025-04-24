"""
Blender Integration for Rocket Engine Simulation

This script provides instructions and helper functions for importing PINN
simulation data into Blender for advanced 3D visualization.

It requires Blender 2.90+ with Python 3.7+ and the following packages:
- numpy
- pandas
- mathutils (comes with Blender)

Usage:
1. Export simulation data using the export_for_blender() function
2. In Blender, use the Text Editor to run this script
3. Use the import_simulation_data() function to load the data
4. Create visualizations using the provided helper functions
"""

import os
import json
import numpy as np
import pandas as pd
import math

# Import mathutils conditionally (only available in Blender)
try:
    import bpy
    import mathutils
    from mathutils import Vector
    RUNNING_IN_BLENDER = True
except ImportError:
    RUNNING_IN_BLENDER = False


def export_for_blender(simulation_results, output_file="simulation_data.json"):
    """
    Export simulation data to JSON for import into Blender.
    
    Args:
        simulation_results: DataFrame with simulation results
        output_file: Output JSON file path
    """
    if isinstance(simulation_results, pd.DataFrame):
        # Convert DataFrame to dict for JSON serialization
        data_dict = {
            'time': simulation_results['Time'].tolist(),
            'chamber_pressure': simulation_results['Chamber Pressure'].tolist(),
            'exit_velocity': simulation_results['Exit Velocity'].tolist(),
            'thrust': simulation_results['Thrust'].tolist()
        }
        
        # Additional columns if present
        if 'Fuel Flow Rate' in simulation_results:
            data_dict['fuel_flow_rate'] = simulation_results['Fuel Flow Rate'].tolist()
            
        # Add metadata
        data_dict['metadata'] = {
            'num_frames': len(simulation_results),
            'time_start': simulation_results['Time'].min(),
            'time_end': simulation_results['Time'].max(),
            'max_thrust': simulation_results['Thrust'].max(),
            'max_pressure': simulation_results['Chamber Pressure'].max(),
            'max_velocity': simulation_results['Exit Velocity'].max()
        }
        
        # Save to JSON
        with open(output_file, 'w') as f:
            json.dump(data_dict, f)
            
        print(f"Data exported to {output_file}")
        return True
    else:
        print("Error: simulation_results must be a pandas DataFrame")
        return False


# ==== Blender-specific functions ====

def import_simulation_data(json_file):
    """
    Import simulation data from JSON file in Blender.
    
    Args:
        json_file: Path to JSON file with simulation data
        
    Returns:
        Dictionary with imported data
    """
    if not RUNNING_IN_BLENDER:
        print("This function can only be run in Blender")
        return None
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        print(f"Successfully imported data from {json_file}")
        print(f"Contains {data['metadata']['num_frames']} frames of simulation data")
        return data
    except Exception as e:
        print(f"Error importing data: {e}")
        return None


def setup_blender_scene(clear_scene=True):
    """
    Set up the Blender scene for rocket engine visualization.
    
    Args:
        clear_scene: Whether to clear existing objects
    """
    if not RUNNING_IN_BLENDER:
        print("This function can only be run in Blender")
        return
    
    # Clear existing objects if requested
    if clear_scene:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
    
    # Set up world properties
    bpy.context.scene.world.use_nodes = True
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.01, 0.02, 1.0)
    
    # Add lighting
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 5))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    
    # Add camera
    bpy.ops.object.camera_add(location=(0.3, -0.4, 0.2), rotation=(math.radians(70), 0, math.radians(60)))
    camera = bpy.context.active_object
    bpy.context.scene.camera = camera
    
    # Set render properties
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    
    # Set up animation properties
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250
    
    print("Blender scene set up for rocket engine visualization")


def create_simple_engine_model(
    chamber_length=0.15,
    chamber_diameter=0.08,
    throat_diameter=0.03,
    exit_diameter=0.09,
    nozzle_length=0.12
):
    """
    Create a simple 3D model of a rocket engine in Blender.
    
    Args:
        chamber_length: Length of combustion chamber [m]
        chamber_diameter: Diameter of combustion chamber [m]
        throat_diameter: Diameter of nozzle throat [m]
        exit_diameter: Diameter of nozzle exit [m]
        nozzle_length: Length of nozzle [m]
        
    Returns:
        Dictionary with created objects
    """
    if not RUNNING_IN_BLENDER:
        print("This function can only be run in Blender")
        return None
    
    engine_objects = {}
    
    # Create combustion chamber (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=chamber_diameter/2,
        depth=chamber_length,
        location=(0, 0, chamber_length/2)
    )
    chamber = bpy.context.active_object
    chamber.name = "CombustionChamber"
    
    # Create material for chamber
    chamber_mat = bpy.data.materials.new(name="ChamberMaterial")
    chamber_mat.use_nodes = True
    chamber_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.2, 0.2, 1.0)
    chamber_mat.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.9
    chamber_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.2
    chamber.data.materials.append(chamber_mat)
    
    engine_objects['chamber'] = chamber
    
    # Create nozzle using a mesh
    throat_position = chamber_length + nozzle_length * 0.3
    
    vertices = []
    faces = []
    
    # Create vertices for cross-sections
    num_sections = 10
    num_points = 16  # Points around circumference
    
    for i in range(num_sections):
        z_pos = chamber_length + (i / (num_sections - 1)) * nozzle_length
        
        # Determine radius at this position
        if z_pos < throat_position:
            # Converging section
            ratio = (z_pos - chamber_length) / (throat_position - chamber_length)
            radius = chamber_diameter/2 - ratio * (chamber_diameter/2 - throat_diameter/2)
        else:
            # Diverging section
            ratio = (z_pos - throat_position) / (chamber_length + nozzle_length - throat_position)
            radius = throat_diameter/2 + ratio * (exit_diameter/2 - throat_diameter/2)
        
        # Create vertices around the circumference
        for j in range(num_points):
            angle = 2 * math.pi * j / num_points
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y, z_pos))
    
    # Create faces
    for i in range(num_sections - 1):
        for j in range(num_points):
            j_next = (j + 1) % num_points
            idx1 = i * num_points + j
            idx2 = i * num_points + j_next
            idx3 = (i + 1) * num_points + j_next
            idx4 = (i + 1) * num_points + j
            faces.append((idx1, idx2, idx3, idx4))
    
    # Create nozzle mesh
    nozzle_mesh = bpy.data.meshes.new("NozzleMesh")
    nozzle_mesh.from_pydata(vertices, [], faces)
    nozzle_mesh.update()
    
    nozzle_obj = bpy.data.objects.new("Nozzle", nozzle_mesh)
    bpy.context.collection.objects.link(nozzle_obj)
    
    # Create material for nozzle
    nozzle_mat = bpy.data.materials.new(name="NozzleMaterial")
    nozzle_mat.use_nodes = True
    nozzle_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.4, 0.8, 1.0)
    nozzle_mat.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.9
    nozzle_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.1
    nozzle_obj.data.materials.append(nozzle_mat)
    
    engine_objects['nozzle'] = nozzle_obj
    
    # Create injector face
    bpy.ops.mesh.primitive_cylinder_add(
        radius=chamber_diameter/2,
        depth=0.01,
        location=(0, 0, 0.005)
    )
    injector = bpy.context.active_object
    injector.name = "InjectorFace"
    
    # Create material for injector
    injector_mat = bpy.data.materials.new(name="InjectorMaterial")
    injector_mat.use_nodes = True
    injector_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1.0)
    injector_mat.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
    injector_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
    injector.data.materials.append(injector_mat)
    
    engine_objects['injector'] = injector
    
    print("Simple rocket engine model created")
    return engine_objects


def create_particle_system(exhaust_object, simulation_data):
    """
    Set up a particle system for the exhaust plume.
    
    Args:
        exhaust_object: Blender object to use for the particle emitter
        simulation_data: Simulation data dictionary
        
    Returns:
        Particle system
    """
    if not RUNNING_IN_BLENDER:
        print("This function can only be run in Blender")
        return None
    
    # Add particle system to object
    bpy.context.view_layer.objects.active = exhaust_object
    bpy.ops.object.particle_system_add()
    
    # Get particle system
    psys = exhaust_object.particle_systems[0]
    pset = psys.settings
    
    # Set particle system properties
    pset.name = "ExhaustParticles"
    pset.count = 5000
    pset.lifetime = 50
    pset.emission_on_frame = 1
    pset.normal_factor = 0.5
    pset.factor_random = 0.2
    pset.render_type = 'NONE'
    pset.physics_type = 'NEWTON'
    pset.mass = 0.01
    
    # Create force field for controlling particles
    bpy.ops.object.effector_add(type='FORCE', location=(0, 0, chamber_length + nozzle_length))
    force = bpy.context.active_object
    force.name = "ExhaustForce"
    force.field.strength = 5.0
    force.field.flow = 1.0
    
    # Animate force field strength based on thrust
    max_thrust = simulation_data['metadata']['max_thrust']
    times = simulation_data['time']
    thrusts = simulation_data['thrust']
    
    for frame, (time, thrust) in enumerate(zip(times, thrusts), start=1):
        # Map frame number to time
        frame_time = (frame - 1) / (len(times) - 1) * (times[-1] - times[0]) + times[0]
        
        # Find closest time in data
        time_idx = np.argmin(np.abs(np.array(times) - frame_time))
        
        # Set force strength based on thrust
        force.field.strength = 2.0 + 8.0 * (thrusts[time_idx] / max_thrust)
        
        # Add keyframe
        force.keyframe_insert(data_path="field.strength", frame=frame)
    
    print("Particle system set up for exhaust plume")
    return psys


def animate_engine_properties(engine_objects, simulation_data):
    """
    Animate engine properties based on simulation data.
    
    Args:
        engine_objects: Dictionary of engine objects
        simulation_data: Simulation data dictionary
    """
    if not RUNNING_IN_BLENDER:
        print("This function can only be run in Blender")
        return
    
    # Create material for exhaust
    exhaust_mat = bpy.data.materials.new(name="ExhaustMaterial")
    exhaust_mat.use_nodes = True
    nodes = exhaust_mat.node_tree.nodes
    links = exhaust_mat.node_tree.links
    
    # Clear existing nodes
    for node in nodes:
        nodes.remove(node)
    
    # Create nodes for volume shader
    output = nodes.new(type='ShaderNodeOutputMaterial')
    volume = nodes.new(type='ShaderNodeVolumePrincipled')
    colorramp = nodes.new(type='ShaderNodeValToRGB')
    
    # Set up color ramp
    colorramp.color_ramp.elements[0].position = 0.0
    colorramp.color_ramp.elements[0].color = (1.0, 0.5, 0.1, 1.0)
    colorramp.color_ramp.elements[1].position = 1.0
    colorramp.color_ramp.elements[1].color = (0.1, 0.2, 0.8, 0.0)
    
    # Connect nodes
    links.new(colorramp.outputs[0], volume.inputs['Color'])
    links.new(volume.outputs[0], output.inputs[1])  # Connect to Volume input
    
    # Create cone for exhaust plume
    bpy.ops.mesh.primitive_cone_add(
        radius1=engine_objects['nozzle'].dimensions.x/2,
        radius2=engine_objects['nozzle'].dimensions.x,
        depth=0.2,
        location=(0, 0, engine_objects['chamber'].location.z + 
                 engine_objects['chamber'].dimensions.z/2 + 0.1)
    )
    exhaust = bpy.context.active_object
    exhaust.name = "ExhaustPlume"
    exhaust.data.materials.append(exhaust_mat)
    
    # Animate exhaust properties based on simulation data
    max_thrust = simulation_data['metadata']['max_thrust']
    times = simulation_data['time']
    thrusts = simulation_data['thrust']
    
    for frame, (time, thrust) in enumerate(zip(times, thrusts), start=1):
        # Scale exhaust based on thrust
        scale_factor = 0.5 + 1.5 * (thrust / max_thrust)
        exhaust.scale = (scale_factor, scale_factor, 1.0 + scale_factor)
        
        # Set exhaust density based on thrust
        volume.inputs['Density'].default_value = 0.2 * (thrust / max_thrust)
        volume.keyframe_insert(data_path="inputs[1].default_value", frame=frame)
        
        # Insert keyframes
        exhaust.keyframe_insert(data_path="scale", frame=frame)
    
    print("Engine properties animated based on simulation data")


# Instructions for using this script in Blender
INSTRUCTIONS = """
## Instructions for Using This Script in Blender

1. First, export your simulation data using the `export_for_blender()` function from Python:
   ```python
   from visualization.blender_integration import export_for_blender
   export_for_blender(simulation_results, "simulation_data.json")
   ```

2. Open Blender and create a new scene or open your existing .blend file

3. Open the Text Editor in Blender and open this script file

4. Run the script to make the functions available

5. In the Blender Python Console, run the following commands:
   ```python
   import bpy
   data = import_simulation_data("/path/to/simulation_data.json")
   setup_blender_scene()
   engine_objects = create_simple_engine_model()
   animate_engine_properties(engine_objects, data)
   ```

6. For more advanced visualizations, you can create particle systems:
   ```python
   # Create an emitter object at nozzle exit
   bpy.ops.mesh.primitive_plane_add(
       size=engine_objects['nozzle'].dimensions.x/2,
       location=(0, 0, chamber_length + nozzle_length)
   )
   emitter = bpy.context.active_object
   create_particle_system(emitter, data)
   ```

7. Render the animation using Cycles renderer for best results
"""

if __name__ == "__main__":
    if RUNNING_IN_BLENDER:
        print(INSTRUCTIONS)
    else:
        print("This script provides functions for Blender integration.")
        print("Some functions can only be run within Blender itself.")
        print("Use export_for_blender() to prepare your data for Blender.") 