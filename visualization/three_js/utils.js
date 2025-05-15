// Three.js utility functions for advanced rocket engine visualization

/**
 * Creates a rocket engine geometry with detailed components
 * 
 * @param {Object} params - Engine parameters
 * @returns {THREE.Group} - A group containing all engine components
 */
function createRocketEngineGeometry(params) {
    const {
        chamberLength = 0.15,
        chamberDiameter = 0.08,
        throatDiameter = 0.03,
        exitDiameter = 0.09,
        nozzleLength = 0.12,
        cooling = true,
        feedLines = true,
        detailLevel = 'high'
    } = params;

    const engineGroup = new THREE.Group();
    
    // Add combustion chamber
    const chamberMaterial = new THREE.MeshStandardMaterial({
        color: 0x888888,
        metalness: 0.8,
        roughness: 0.2,
        emissive: 0x000000
    });
    
    // Create combustion chamber
    const chamberGeometry = new THREE.CylinderGeometry(
        chamberDiameter/2, chamberDiameter/2, chamberLength, 32, 1, false
    );
    const chamber = new THREE.Mesh(chamberGeometry, chamberMaterial);
    chamber.rotation.x = Math.PI / 2;
    chamber.position.z = chamberLength / 2;
    engineGroup.add(chamber);
    
    // Create nozzle using custom bell shape
    const nozzle = createBellNozzle({
        throatDiameter,
        exitDiameter,
        nozzleLength,
        chamberDiameter,
        chamberLength
    });
    nozzle.position.z = chamberLength;
    engineGroup.add(nozzle);
    
    // Add injector plate
    const injector = createInjectorPlate(chamberDiameter, detailLevel);
    injector.position.z = 0.001;
    engineGroup.add(injector);
    
    // Add cooling channels if requested
    if (cooling) {
        const coolingChannels = createCoolingChannels(chamberLength, chamberDiameter);
        engineGroup.add(coolingChannels);
    }
    
    // Add propellant feed lines if requested
    if (feedLines) {
        const feedLinesGroup = createFeedLines(chamberDiameter);
        engineGroup.add(feedLinesGroup);
    }
    
    return engineGroup;
}

/**
 * Creates a bell-shaped nozzle with proper contour
 */
function createBellNozzle(params) {
    const {
        throatDiameter,
        exitDiameter,
        nozzleLength,
        chamberDiameter,
        chamberLength
    } = params;
    
    // Create points for nozzle profile
    const segments = 40;
    const throatPosition = nozzleLength * 0.2;
    
    // Create bell shape using proper aerospace contour
    const points = [];
    
    // Start with chamber diameter
    points.push(new THREE.Vector2(chamberDiameter/2, 0));
    
    // Converging section (chamber to throat)
    for (let i = 1; i <= segments/4; i++) {
        const ratio = i / (segments/4);
        const z = ratio * throatPosition;
        
        // Quadratic convergence
        const r = chamberDiameter/2 - (chamberDiameter/2 - throatDiameter/2) * Math.pow(ratio, 1.5);
        points.push(new THREE.Vector2(r, z));
    }
    
    // Throat point
    points.push(new THREE.Vector2(throatDiameter/2, throatPosition));
    
    // Diverging section (throat to exit)
    for (let i = 1; i <= segments/4 * 3; i++) {
        const ratio = i / (segments/4 * 3);
        const z = throatPosition + ratio * (nozzleLength - throatPosition);
        
        // Bell curve - using Rao approximate contour for bell nozzles
        const expansionRatio = exitDiameter / throatDiameter;
        const x = ratio * Math.PI / 2;
        const bellFactor = 0.8 - 0.2 * Math.cos(x);
        const r = throatDiameter/2 + (exitDiameter/2 - throatDiameter/2) * bellFactor * ratio;
        
        points.push(new THREE.Vector2(r, z));
    }
    
    // Make sure last point is at exit diameter
    points.push(new THREE.Vector2(exitDiameter/2, nozzleLength));
    
    // Create geometry by rotating points around z-axis
    const nozzleGeometry = new THREE.LatheGeometry(points, 32);
    const nozzleMaterial = new THREE.MeshStandardMaterial({
        color: 0x666666,
        metalness: 0.8,
        roughness: 0.3
    });
    
    const nozzle = new THREE.Mesh(nozzleGeometry, nozzleMaterial);
    nozzle.rotation.x = Math.PI / 2;
    
    return nozzle;
}

/**
 * Creates an injector plate with detailed injector elements
 */
function createInjectorPlate(chamberDiameter, detailLevel) {
    const plateGroup = new THREE.Group();
    
    // Injector plate
    const plateGeometry = new THREE.CylinderGeometry(
        chamberDiameter/2, chamberDiameter/2, 0.01, 32
    );
    const plateMaterial = new THREE.MeshStandardMaterial({
        color: 0x444444,
        metalness: 0.7,
        roughness: 0.4
    });
    
    const plate = new THREE.Mesh(plateGeometry, plateMaterial);
    plate.rotation.x = Math.PI / 2;
    plateGroup.add(plate);
    
    // Add injector elements if high detail
    if (detailLevel === 'high') {
        // Create injector pattern
        const injectorRadius = chamberDiameter * 0.4;
        const numInjectors = 24;
        
        for (let i = 0; i < numInjectors; i++) {
            // Create alternating fuel and oxidizer injectors
            const angle = (i / numInjectors) * Math.PI * 2;
            const radius = injectorRadius;
            
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            // Injector geometry
            const injectorGeometry = new THREE.CylinderGeometry(0.003, 0.003, 0.02, 8);
            
            // Alternate colors for fuel and oxidizer
            const color = i % 2 === 0 ? 0x66aaff : 0xff8866;
            const injectorMaterial = new THREE.MeshStandardMaterial({
                color: color,
                metalness: 0.6,
                roughness: 0.4
            });
            
            const injector = new THREE.Mesh(injectorGeometry, injectorMaterial);
            injector.position.set(x, y, 0.01);
            injector.rotation.x = Math.PI / 2;
            plateGroup.add(injector);
        }
    }
    
    return plateGroup;
}

/**
 * Creates cooling channels visualization
 */
function createCoolingChannels(chamberLength, chamberDiameter) {
    const coolingGroup = new THREE.Group();
    
    // Number of visible cooling channels
    const numChannels = 16;
    const radius = chamberDiameter/2 + 0.003;
    const channelWidth = 0.003;
    
    // Create cooling channels around the chamber
    for (let i = 0; i < numChannels; i++) {
        const angle = (i / numChannels) * Math.PI * 2;
        
        // Cooling channel shape
        const channelShape = new THREE.Shape();
        channelShape.moveTo(0, 0);
        channelShape.lineTo(channelWidth, 0);
        channelShape.lineTo(channelWidth, chamberLength);
        channelShape.lineTo(0, chamberLength);
        channelShape.lineTo(0, 0);
        
        const channelGeometry = new THREE.ShapeGeometry(channelShape);
        const channelMaterial = new THREE.MeshStandardMaterial({
            color: 0x3388ff,
            metalness: 0.6,
            roughness: 0.3,
            transparent: true,
            opacity: 0.7
        });
        
        const channel = new THREE.Mesh(channelGeometry, channelMaterial);
        channel.position.set(0, 0, 0);
        
        // Position around the chamber
        channel.rotation.y = angle;
        channel.position.x = Math.cos(angle) * radius;
        channel.position.y = Math.sin(angle) * radius;
        
        coolingGroup.add(channel);
    }
    
    return coolingGroup;
}

/**
 * Creates propellant feed lines
 */
function createFeedLines(chamberDiameter) {
    const feedGroup = new THREE.Group();
    
    // Parameters for feed lines
    const lineRadius = 0.01;
    const bendRadius = 0.04;
    
    // Materials for fuel and oxidizer
    const fuelMaterial = new THREE.MeshStandardMaterial({
        color: 0x22aa22,
        metalness: 0.7,
        roughness: 0.3
    });
    
    const oxMaterial = new THREE.MeshStandardMaterial({
        color: 0xaa5522,
        metalness: 0.7,
        roughness: 0.3
    });
    
    // Fuel line
    const fuelPath = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-chamberDiameter/2 - 0.05, -chamberDiameter/2, -0.05),
        new THREE.Vector3(-chamberDiameter/2 - 0.02, -chamberDiameter/2, 0),
        new THREE.Vector3(-chamberDiameter/2, -chamberDiameter/2, 0)
    ]);
    
    const fuelGeometry = new THREE.TubeGeometry(fuelPath, 16, lineRadius, 8, false);
    const fuelLine = new THREE.Mesh(fuelGeometry, fuelMaterial);
    feedGroup.add(fuelLine);
    
    // Oxidizer line
    const oxPath = new THREE.CatmullRomCurve3([
        new THREE.Vector3(chamberDiameter/2 + 0.05, -chamberDiameter/2, -0.05),
        new THREE.Vector3(chamberDiameter/2 + 0.02, -chamberDiameter/2, 0),
        new THREE.Vector3(chamberDiameter/2, -chamberDiameter/2, 0)
    ]);
    
    const oxGeometry = new THREE.TubeGeometry(oxPath, 16, lineRadius, 8, false);
    const oxLine = new THREE.Mesh(oxGeometry, oxMaterial);
    feedGroup.add(oxLine);
    
    // Add valves (simplified as spheres)
    const fuelValve = new THREE.Mesh(
        new THREE.SphereGeometry(lineRadius * 1.5, 16, 16),
        fuelMaterial
    );
    fuelValve.position.set(-chamberDiameter/2 - 0.05, -chamberDiameter/2, -0.05);
    feedGroup.add(fuelValve);
    
    const oxValve = new THREE.Mesh(
        new THREE.SphereGeometry(lineRadius * 1.5, 16, 16),
        oxMaterial
    );
    oxValve.position.set(chamberDiameter/2 + 0.05, -chamberDiameter/2, -0.05);
    feedGroup.add(oxValve);
    
    return feedGroup;
}

/**
 * Creates dynamic combustion/exhaust effects
 * 
 * @param {Object} params - Effect parameters
 * @param {String} engineStatus - Current engine status
 * @returns {THREE.Group} - Group containing combustion and exhaust effects
 */
function createEngineEffects(params, engineStatus) {
    const {
        chamberLength = 0.15,
        chamberDiameter = 0.08,
        throatDiameter = 0.03,
        exitDiameter = 0.09,
        nozzleLength = 0.12,
        chamberPressure = 2.0,
        mixtureRatio = 2.1
    } = params;
    
    const effectsGroup = new THREE.Group();
    
    // Skip effects if engine is in standby
    if (engineStatus === 'Standby') {
        return effectsGroup;
    }
    
    // Combustion chamber effects
    if (['Nominal Operation', 'Startup', 'Ignition Sequence'].includes(engineStatus)) {
        // Add combustion glow inside chamber
        const combustionMaterial = new THREE.MeshBasicMaterial({
            color: getFlameColor(engineStatus, mixtureRatio),
            transparent: true,
            opacity: getCombustionOpacity(engineStatus)
        });
        
        const combustionGeometry = new THREE.CylinderGeometry(
            chamberDiameter/2 * 0.9, 
            throatDiameter/2 * 1.1, 
            chamberLength, 
            32, 1, false
        );
        
        const combustion = new THREE.Mesh(combustionGeometry, combustionMaterial);
        combustion.rotation.x = Math.PI / 2;
        combustion.position.z = chamberLength / 2;
        effectsGroup.add(combustion);
    }
    
    // Exhaust plume
    if (['Nominal Operation', 'Startup'].includes(engineStatus)) {
        const plumeLength = getPlumeLength(engineStatus, chamberPressure, exitDiameter);
        
        // Create main exhaust plume
        const plumeGeometry = new THREE.ConeGeometry(
            exitDiameter * 1.2,
            plumeLength,
            32, 1, true
        );
        
        const plumeMaterial = new THREE.MeshBasicMaterial({
            color: getExhaustColor(engineStatus, mixtureRatio),
            transparent: true,
            opacity: 0.7 * getEffectIntensity(engineStatus)
        });
        
        const plume = new THREE.Mesh(plumeGeometry, plumeMaterial);
        plume.rotation.x = -Math.PI / 2;
        plume.position.z = chamberLength + nozzleLength + plumeLength/2;
        effectsGroup.add(plume);
        
        // Add shock diamonds for nominal operation
        if (engineStatus === 'Nominal Operation') {
            // Calculate shock spacing based on over/under-expansion
            const shockCount = Math.floor(3 + chamberPressure * 1.5);
            const shockSpacing = plumeLength / (shockCount + 1);
            
            for (let i = 1; i <= shockCount; i++) {
                const position = i * shockSpacing;
                const shockSize = exitDiameter * (0.7 - 0.4 * (i / shockCount));
                
                // Create shock diamond
                const shockGeometry = new THREE.SphereGeometry(shockSize, 16, 16);
                const shockMaterial = new THREE.MeshBasicMaterial({
                    color: 0xffaa44,
                    transparent: true,
                    opacity: 0.9 * (1 - 0.7 * (i / shockCount))
                });
                
                const shock = new THREE.Mesh(shockGeometry, shockMaterial);
                shock.position.z = chamberLength + nozzleLength + position;
                effectsGroup.add(shock);
            }
        }
    }
    
    return effectsGroup;
}

/**
 * Utility function to get flame color based on engine status and mixture ratio
 */
function getFlameColor(engineStatus, mixtureRatio) {
    // Adjust color based on mixture ratio (Fuel rich -> blue, Oxidizer rich -> orange)
    let color;
    
    if (mixtureRatio < 2.0) {
        // Fuel rich - more blue
        color = new THREE.Color(0x88aaff);
    } else if (mixtureRatio > 3.0) {
        // Oxidizer rich - more orange
        color = new THREE.Color(0xff8800);
    } else {
        // Balanced - white/blue core
        color = new THREE.Color(0xddffff);
    }
    
    // Adjust for engine status
    if (engineStatus === 'Ignition Sequence') {
        // More orange during ignition
        color.r = Math.min(1, color.r * 1.5);
        color.g = Math.min(1, color.g * 0.8);
        color.b = Math.min(1, color.b * 0.5);
    } else if (engineStatus === 'Startup') {
        // Transitioning to normal color
        color.r = Math.min(1, color.r * 1.2);
    }
    
    return color;
}

/**
 * Get combustion effect opacity based on engine status
 */
function getCombustionOpacity(engineStatus) {
    switch (engineStatus) {
        case 'Nominal Operation':
            return 0.8;
        case 'Startup':
            return 0.6;
        case 'Ignition Sequence':
            return 0.4;
        case 'Shutdown Sequence':
            return 0.3;
        default:
            return 0;
    }
}

/**
 * Get exhaust color based on engine status and mixture ratio
 */
function getExhaustColor(engineStatus, mixtureRatio) {
    // Base color depends on mixture ratio
    let color;
    
    if (mixtureRatio < 2.0) {
        // Fuel rich - more sooty/yellow
        color = new THREE.Color(0xffdd66);
    } else if (mixtureRatio > 3.0) {
        // Oxidizer rich - clearer/blue
        color = new THREE.Color(0xaaddff);
    } else {
        // Balanced - transparent/white
        color = new THREE.Color(0xeeeeff);
    }
    
    // Adjust for engine status
    if (engineStatus === 'Startup') {
        // More orange/smoky during startup
        color.r = Math.min(1, color.r * 1.2);
        color.g = Math.min(1, color.g * 0.9);
    }
    
    return color;
}

/**
 * Calculate exhaust plume length based on engine parameters
 */
function getPlumeLength(engineStatus, chamberPressure, exitDiameter) {
    let baseLength = exitDiameter * 5; // Base length is 5x exit diameter
    
    // Adjust for chamber pressure
    baseLength *= (0.5 + chamberPressure/2);
    
    // Adjust for engine status
    if (engineStatus === 'Startup') {
        baseLength *= 0.6; // Shorter during startup
    } else if (engineStatus === 'Shutdown Sequence') {
        baseLength *= 0.3; // Much shorter during shutdown
    } else if (engineStatus === 'Ignition Sequence') {
        baseLength *= 0.1; // Minimal during ignition
    }
    
    return baseLength;
}

/**
 * Get effect intensity based on engine status
 */
function getEffectIntensity(engineStatus) {
    switch (engineStatus) {
        case 'Nominal Operation':
            return 1.0;
        case 'Startup':
            return 0.7;
        case 'Ignition Sequence':
            return 0.3;
        case 'Shutdown Sequence':
            return 0.5;
        default:
            return 0;
    }
}

// Export functions if in a module environment
if (typeof module !== 'undefined') {
    module.exports = {
        createRocketEngineGeometry,
        createBellNozzle,
        createInjectorPlate,
        createCoolingChannels,
        createFeedLines,
        createEngineEffects,
        getFlameColor,
        getCombustionOpacity,
        getExhaustColor,
        getPlumeLength,
        getEffectIntensity
    };
} 