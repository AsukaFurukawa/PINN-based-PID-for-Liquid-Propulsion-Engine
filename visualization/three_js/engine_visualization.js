// Advanced Three.js Liquid Rocket Engine Visualization

// Main renderer class for rocket engine visualization
class RocketEngineVisualizer {
    constructor(containerId, options = {}) {
        // Store container reference
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with ID ${containerId} not found`);
            return;
        }
        
        // Configuration options with defaults
        this.options = Object.assign({
            width: this.container.clientWidth,
            height: this.container.clientHeight,
            antialias: true,
            background: 0x111122,
            cameraPosition: { x: 0.3, y: 0.3, z: 0.3 },
            engineParams: {
                chamberLength: 0.15,
                chamberDiameter: 0.08,
                throatDiameter: 0.03,
                exitDiameter: 0.09,
                nozzleLength: 0.12
            },
            autoRotate: true,
            showGrid: true,
            showAxes: true,
            showEffects: true,
            showStats: true
        }, options);
        
        // Initialize engine state
        this.engineState = {
            status: 'Standby',
            chamberPressure: 0.1, // MPa
            mixtureRatio: 0,
            thrust: 0,
            specificImpulse: 0,
            chamberTemperature: 300, // K
            performance: {}
        };
        
        // Initialize visualization
        this.init();
    }
    
    init() {
        // Initialize Three.js components
        this.initRenderer();
        this.initScene();
        this.initCamera();
        this.initLights();
        this.initControls();
        
        // Create engine model
        this.createEngineModel();
        
        // Add additional components
        if (this.options.showGrid) this.addGrid();
        if (this.options.showAxes) this.addAxes();
        if (this.options.showStats) this.addStats();
        
        // Start animation loop
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', this.onWindowResize.bind(this), false);
    }
    
    initRenderer() {
        // Create WebGL renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: this.options.antialias,
            alpha: true
        });
        
        this.renderer.setSize(this.options.width, this.options.height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        
        // Append to container
        this.container.appendChild(this.renderer.domElement);
    }
    
    initScene() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.background);
        
        // Add fog for depth
        this.scene.fog = new THREE.FogExp2(this.options.background, 0.05);
    }
    
    initCamera() {
        // Create perspective camera
        const aspect = this.options.width / this.options.height;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.01, 10);
        
        // Set initial position
        const { x, y, z } = this.options.cameraPosition;
        this.camera.position.set(x, y, z);
        this.camera.lookAt(0, 0, 0);
    }
    
    initLights() {
        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);
        
        // Add directional light (key light)
        const keyLight = new THREE.DirectionalLight(0xffffff, 1);
        keyLight.position.set(1, 2, 3);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        keyLight.shadow.camera.near = 0.1;
        keyLight.shadow.camera.far = 10;
        keyLight.shadow.camera.left = -1;
        keyLight.shadow.camera.right = 1;
        keyLight.shadow.camera.top = 1;
        keyLight.shadow.camera.bottom = -1;
        this.scene.add(keyLight);
        
        // Add fill light
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-1, 0.5, -1);
        this.scene.add(fillLight);
        
        // Add rim light for metallic highlights
        const rimLight = new THREE.DirectionalLight(0xaaddff, 0.8);
        rimLight.position.set(0, -1, -0.5);
        this.scene.add(rimLight);
    }
    
    initControls() {
        // Add orbit controls for camera manipulation
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.rotateSpeed = 0.5;
        this.controls.autoRotate = this.options.autoRotate;
        this.controls.autoRotateSpeed = 0.5;
        this.controls.minDistance = 0.1;
        this.controls.maxDistance = 5;
        this.controls.target.set(0, 0, 0.1); // Look slightly above the engine
        this.controls.update();
    }
    
    createEngineModel() {
        // Engine group to contain all components
        this.engineGroup = new THREE.Group();
        this.scene.add(this.engineGroup);
        
        // Create static engine components
        this.engineModel = createRocketEngineGeometry(this.options.engineParams);
        this.engineGroup.add(this.engineModel);
        
        // Add dynamic effects (will be updated in animation loop)
        this.updateEngineEffects();
    }
    
    updateEngineEffects() {
        // Remove previous effects
        if (this.engineEffects) {
            this.engineGroup.remove(this.engineEffects);
        }
        
        // Skip if effects are disabled
        if (!this.options.showEffects) {
            return;
        }
        
        // Create new effects based on current engine state
        const effectParams = {
            ...this.options.engineParams,
            chamberPressure: this.engineState.chamberPressure,
            mixtureRatio: this.engineState.mixtureRatio
        };
        
        this.engineEffects = createEngineEffects(effectParams, this.engineState.status);
        this.engineGroup.add(this.engineEffects);
    }
    
    addGrid() {
        // Add ground grid
        const gridHelper = new THREE.GridHelper(1, 10, 0x444444, 0x222222);
        gridHelper.position.y = -0.1;
        this.scene.add(gridHelper);
    }
    
    addAxes() {
        // Add coordinate axes
        const axesHelper = new THREE.AxesHelper(0.3);
        this.scene.add(axesHelper);
    }
    
    addStats() {
        // Add performance stats
        this.stats = new Stats();
        this.container.appendChild(this.stats.dom);
    }
    
    animate() {
        requestAnimationFrame(this.animate.bind(this));
        
        // Update controls
        this.controls.update();
        
        // Update engine effects if state changed
        this.updateEngineAnimations();
        
        // Update stats
        if (this.stats) this.stats.update();
        
        // Render scene
        this.renderer.render(this.scene, this.camera);
    }
    
    updateEngineAnimations() {
        // Apply dynamic animations based on engine state
        if (this.engineEffects) {
            // Animation time
            const time = performance.now() * 0.001;
            
            // Engine vibration effect
            if (this.engineState.status === 'Nominal Operation') {
                // Engine vibrates during nominal operation
                const vibrationAmplitude = 0.0005;
                this.engineGroup.position.x = Math.sin(time * 50) * vibrationAmplitude;
                this.engineGroup.position.y = Math.sin(time * 60) * vibrationAmplitude;
            } else if (this.engineState.status === 'Startup' || this.engineState.status === 'Shutdown Sequence') {
                // More irregular vibration during transients
                const startupAmplitude = 0.001;
                this.engineGroup.position.x = Math.sin(time * 30) * startupAmplitude;
                this.engineGroup.position.y = Math.sin(time * 40 + 1) * startupAmplitude;
            } else {
                // No vibration in standby
                this.engineGroup.position.x = 0;
                this.engineGroup.position.y = 0;
            }
            
            // Update effects that need time-based animation
            // (This would include flame flickering, plume dynamics, etc.)
        }
    }
    
    onWindowResize() {
        // Update dimensions
        this.options.width = this.container.clientWidth;
        this.options.height = this.container.clientHeight;
        
        // Update camera aspect ratio
        this.camera.aspect = this.options.width / this.options.height;
        this.camera.updateProjectionMatrix();
        
        // Update renderer size
        this.renderer.setSize(this.options.width, this.options.height);
    }
    
    // Public API methods
    
    /**
     * Update engine visualization state
     * @param {Object} state - New engine state
     */
    updateEngineState(state) {
        // Update state with new values
        this.engineState = {...this.engineState, ...state};
        
        // If engine status changed, update effects
        this.updateEngineEffects();
    }
    
    /**
     * Update engine geometry parameters
     * @param {Object} params - New geometry parameters
     */
    updateEngineGeometry(params) {
        // Update engine parameters
        this.options.engineParams = {...this.options.engineParams, ...params};
        
        // Recreate engine model with new parameters
        this.engineGroup.remove(this.engineModel);
        this.engineModel = createRocketEngineGeometry(this.options.engineParams);
        this.engineGroup.add(this.engineModel);
        
        // Update effects with new geometry
        this.updateEngineEffects();
    }
    
    /**
     * Set engine status (Standby, Startup, Nominal Operation, etc.)
     * @param {String} status - New engine status
     */
    setEngineStatus(status) {
        this.engineState.status = status;
        this.updateEngineEffects();
    }
    
    /**
     * Toggle auto-rotation
     * @param {Boolean} enabled - Whether auto-rotation should be enabled
     */
    setAutoRotate(enabled) {
        this.controls.autoRotate = enabled;
    }
    
    /**
     * Change camera position and target
     * @param {Object} position - New camera position {x, y, z}
     * @param {Object} target - New camera target {x, y, z}
     */
    setCameraView(position, target = {x: 0, y: 0, z: 0.1}) {
        // Set new camera position
        this.camera.position.set(position.x, position.y, position.z);
        
        // Set new orbit controls target
        this.controls.target.set(target.x, target.y, target.z);
        this.controls.update();
    }
    
    /**
     * Capture screenshot of the current view
     * @returns {String} - Data URL of the screenshot
     */
    captureScreenshot() {
        this.renderer.render(this.scene, this.camera);
        return this.renderer.domElement.toDataURL();
    }
}

// Make class available in global scope
if (typeof window !== 'undefined') {
    window.RocketEngineVisualizer = RocketEngineVisualizer;
}

// Export for module systems
if (typeof module !== 'undefined') {
    module.exports = RocketEngineVisualizer;
} 