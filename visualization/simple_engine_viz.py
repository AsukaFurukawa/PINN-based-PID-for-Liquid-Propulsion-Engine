import streamlit as st
import streamlit_elements as elements
import time
import json
import numpy as np

def create_simple_engine_viz(height=600):
    """Create a simple but effective 3D engine visualization using Streamlit Elements"""
    
    # Initialize session state for engine parameters
    if "engine_params" not in st.session_state:
        st.session_state.engine_params = {
            "status": "Standby",
            "chamberPressure": 0.1,
            "mixtureRatio": 0.0,
            "chamberLength": 0.15,
            "chamberDiameter": 0.08,
            "throatDiameter": 0.03,
            "exitDiameter": 0.09,
            "nozzleLength": 0.12,
        }
    
    # Create container for three.js visualization
    with elements.media:
        # Dashboard container with dashboard ID
        with elements.dashboard:
            # Create a card for the 3D visualization
            with elements.card(key="engine_viz", height=height):
                # Three.js visualization
                elements.three.canvas(
                    key="rocket_engine_canvas",
                    script="""
                    // Initialize Three.js scene
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0x111133);
                    
                    // Add ambient light
                    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
                    scene.add(ambientLight);
                    
                    // Add directional light
                    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
                    directionalLight.position.set(1, 2, 3);
                    scene.add(directionalLight);
                    
                    // Add grid for reference
                    const grid = new THREE.GridHelper(1, 10, 0x444444, 0x222222);
                    scene.add(grid);
                    
                    // Add coordinate axes
                    const axesHelper = new THREE.AxesHelper(0.3);
                    scene.add(axesHelper);
                    
                    // Function to create the rocket engine
                    function createRocketEngine(params) {
                        const engineGroup = new THREE.Group();
                        
                        // Create combustion chamber
                        const chamberMaterial = new THREE.MeshStandardMaterial({
                            color: 0x888888,
                            metalness: 0.8,
                            roughness: 0.2
                        });
                        
                        const chamberGeometry = new THREE.CylinderGeometry(
                            params.chamberDiameter/2, 
                            params.chamberDiameter/2, 
                            params.chamberLength, 
                            32
                        );
                        const chamber = new THREE.Mesh(chamberGeometry, chamberMaterial);
                        chamber.rotation.x = Math.PI / 2;
                        chamber.position.z = params.chamberLength / 2;
                        engineGroup.add(chamber);
                        
                        // Create nozzle
                        const nozzleGeometry = new THREE.CylinderGeometry(
                            params.throatDiameter/2,
                            params.exitDiameter/2,
                            params.nozzleLength,
                            32
                        );
                        const nozzle = new THREE.Mesh(nozzleGeometry, chamberMaterial);
                        nozzle.rotation.x = Math.PI / 2;
                        nozzle.position.z = params.chamberLength + params.nozzleLength/2;
                        engineGroup.add(nozzle);
                        
                        // Create injector face
                        const injectorGeometry = new THREE.CylinderGeometry(
                            params.chamberDiameter/2,
                            params.chamberDiameter/2,
                            0.01,
                            32
                        );
                        const injectorMaterial = new THREE.MeshStandardMaterial({
                            color: 0x444444,
                            metalness: 0.7,
                            roughness: 0.4
                        });
                        const injector = new THREE.Mesh(injectorGeometry, injectorMaterial);
                        injector.rotation.x = Math.PI / 2;
                        injector.position.z = 0.005;
                        engineGroup.add(injector);
                        
                        // Add effects based on engine status
                        if (params.status !== "Standby") {
                            // Combustion chamber glow
                            let flameColor = 0xddffff; // Default color
                            let flameOpacity = 0.5;
                            
                            if (params.status === "Nominal Operation") {
                                flameOpacity = 0.8;
                                // Adjust color based on mixture ratio
                                if (params.mixtureRatio < 2.0) {
                                    flameColor = 0x88aaff; // Fuel rich - more blue
                                } else if (params.mixtureRatio > 3.0) {
                                    flameColor = 0xff8800; // Oxidizer rich - more orange
                                }
                            } else if (params.status === "Startup") {
                                flameOpacity = 0.6;
                                flameColor = 0xffaa44;
                            } else if (params.status === "Ignition Sequence") {
                                flameOpacity = 0.4;
                                flameColor = 0xff6600;
                            }
                            
                            // Create combustion effect
                            const combustionMaterial = new THREE.MeshBasicMaterial({
                                color: flameColor,
                                transparent: true,
                                opacity: flameOpacity
                            });
                            
                            const combustionGeometry = new THREE.CylinderGeometry(
                                params.chamberDiameter/2 * 0.9, 
                                params.throatDiameter/2 * 1.1, 
                                params.chamberLength, 
                                32
                            );
                            
                            const combustion = new THREE.Mesh(combustionGeometry, combustionMaterial);
                            combustion.rotation.x = Math.PI / 2;
                            combustion.position.z = params.chamberLength / 2;
                            engineGroup.add(combustion);
                            
                            // Add exhaust plume for operating states
                            if (params.status === "Nominal Operation" || params.status === "Startup") {
                                // Calculate plume length based on parameters
                                const plumeLength = params.exitDiameter * 5 * 
                                    (0.5 + params.chamberPressure/2) * 
                                    (params.status === "Startup" ? 0.6 : 1.0);
                                
                                // Create exhaust plume
                                const plumeGeometry = new THREE.ConeGeometry(
                                    params.exitDiameter * 1.2,
                                    plumeLength,
                                    32, 1, true
                                );
                                
                                const plumeColor = params.mixtureRatio < 2.0 ? 0xffdd66 : 
                                                  params.mixtureRatio > 3.0 ? 0xaaddff : 0xeeeeff;
                                
                                const plumeMaterial = new THREE.MeshBasicMaterial({
                                    color: plumeColor,
                                    transparent: true,
                                    opacity: 0.7 * (params.status === "Startup" ? 0.7 : 1.0)
                                });
                                
                                const plume = new THREE.Mesh(plumeGeometry, plumeMaterial);
                                plume.rotation.x = -Math.PI / 2;
                                plume.position.z = params.chamberLength + params.nozzleLength + plumeLength/2;
                                engineGroup.add(plume);
                                
                                // Add shock diamonds for nominal operation
                                if (params.status === "Nominal Operation" && params.chamberPressure > 1.0) {
                                    const shockCount = Math.floor(3 + params.chamberPressure * 1.5);
                                    const shockSpacing = plumeLength / (shockCount + 1);
                                    
                                    for (let i = 1; i <= shockCount; i++) {
                                        const position = i * shockSpacing;
                                        const shockSize = params.exitDiameter * (0.7 - 0.4 * (i / shockCount));
                                        
                                        const shockGeometry = new THREE.SphereGeometry(shockSize, 16, 16);
                                        const shockMaterial = new THREE.MeshBasicMaterial({
                                            color: 0xffaa44,
                                            transparent: true,
                                            opacity: 0.9 * (1 - 0.7 * (i / shockCount))
                                        });
                                        
                                        const shock = new THREE.Mesh(shockGeometry, shockMaterial);
                                        shock.position.z = params.chamberLength + params.nozzleLength + position;
                                        engineGroup.add(shock);
                                    }
                                }
                            }
                        }
                        
                        return engineGroup;
                    }
                    
                    // Handle engine creation
                    let engine = createRocketEngine(streamlit_data.engine_params);
                    scene.add(engine);
                    
                    // Set up camera
                    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
                    camera.position.set(0.3, 0.3, 0.3);
                    camera.lookAt(0, 0, 0.1);
                    
                    // Set up controls
                    const controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    controls.dampingFactor = 0.05;
                    controls.autoRotate = true;
                    controls.autoRotateSpeed = 0.5;
                    
                    // Animation loop
                    function animate() {
                        controls.update();
                        
                        // Add a subtle vibration when engine is running
                        if (streamlit_data.engine_params.status === "Nominal Operation") {
                            engine.position.x = Math.sin(Date.now() * 0.05) * 0.0005;
                            engine.position.y = Math.sin(Date.now() * 0.06) * 0.0005;
                        } else if (streamlit_data.engine_params.status === "Startup" || 
                                 streamlit_data.engine_params.status === "Shutdown Sequence") {
                            engine.position.x = Math.sin(Date.now() * 0.03) * 0.001;
                            engine.position.y = Math.sin(Date.now() * 0.04) * 0.001;
                        } else {
                            engine.position.x = 0;
                            engine.position.y = 0;
                        }
                        
                        renderer.render(scene, camera);
                    }
                    
                    // Handle parameter updates
                    function onDataChanged() {
                        // Remove existing engine
                        scene.remove(engine);
                        
                        // Create new engine with updated parameters
                        engine = createRocketEngine(streamlit_data.engine_params);
                        scene.add(engine);
                    }
                    
                    // Register data changed callback
                    streamlit.setFrameHeight(height);
                    return {
                        update: onDataChanged
                    };
                    """,
                    data={"engine_params": st.session_state.engine_params},
                )

    return st.session_state.engine_params

def update_engine_params(**kwargs):
    """Update engine parameters in session state"""
    # Initialize engine_params if it doesn't exist
    if "engine_params" not in st.session_state:
        st.session_state.engine_params = {
            "status": "Standby",
            "chamberPressure": 0.1,
            "mixtureRatio": 0.0,
            "chamberLength": 0.15,
            "chamberDiameter": 0.08,
            "throatDiameter": 0.03,
            "exitDiameter": 0.09,
            "nozzleLength": 0.12,
        }
    
    # Update parameters
    for key, value in kwargs.items():
        if key in st.session_state.engine_params:
            st.session_state.engine_params[key] = value 