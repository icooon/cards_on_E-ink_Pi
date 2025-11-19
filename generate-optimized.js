#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');
const { JSDOM } = require('jsdom');

// E-ink display dimensions
const WIDTH = 800;
const HEIGHT = 480;

// Create local pics directory for testing
const PICS_DIR = path.join(__dirname, 'pics');
if (!fs.existsSync(PICS_DIR)) {
    fs.mkdirSync(PICS_DIR);
}

async function generateThreeJSSceneOptimized() {
    console.log('Generating optimized Three.js scene...');
    
    // Set up DOM environment for Three.js
    const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`);
    global.window = dom.window;
    global.document = dom.window.document;
    global.HTMLElement = dom.window.HTMLElement;
    global.HTMLCanvasElement = dom.window.HTMLCanvasElement;
    global.ImageData = dom.window.ImageData;
    
    // Create canvas
    const canvas = createCanvas(WIDTH, HEIGHT);
    const context = canvas.getContext('2d');
    
    // Mock WebGL context for Three.js
    const gl = require('gl')(WIDTH, HEIGHT);
    
    // Override canvas.getContext to return our WebGL context
    canvas.getContext = function(type) {
        if (type === 'webgl' || type === 'experimental-webgl') {
            return gl;
        }
        return context;
    };
    
    // Set up Three.js
    const THREE = require('three');
    
    // Create scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, WIDTH / HEIGHT, 0.1, 1000);
    
    // Use WebGL renderer with our headless context
    const renderer = new THREE.WebGLRenderer({ 
        canvas: canvas,
        context: gl,
        antialias: false  // Disable for performance
    });
    renderer.setSize(WIDTH, HEIGHT);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.BasicShadowMap;  // Faster shadow type
    
    // Lights - same as before but optimized
    const redLight = new THREE.DirectionalLight(0xff4444, 1.2);
    redLight.position.set(-5, 2, 2);
    redLight.castShadow = true;
    redLight.shadow.mapSize.width = 512;   // Lower shadow quality for speed
    redLight.shadow.mapSize.height = 512;
    scene.add(redLight);

    const whiteLight = new THREE.DirectionalLight(0xffffff, 0.8);
    whiteLight.position.set(0, 5, 0);
    whiteLight.castShadow = true;
    whiteLight.shadow.mapSize.width = 512;
    whiteLight.shadow.mapSize.height = 512;
    scene.add(whiteLight);

    const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
    scene.add(ambientLight);

    // Create random cubes with variety
    const objects = [];
    const numCubes = Math.floor(Math.random() * 30) + 5; // 5-35 cubes

    for (let i = 0; i < numCubes; i++) {
        const size = Math.random() * 2.5 + 0.1; // Size between 0.1-2.6
        const geometry = new THREE.BoxGeometry(size, size, size);
        const material = new THREE.MeshLambertMaterial({ 
            color: 0xcccccc 
        });
        
        const cube = new THREE.Mesh(geometry, material);
        
        // Wide spread positions
        cube.position.x = (Math.random() - 0.5) * 15;
        cube.position.y = (Math.random() - 0.5) * 10;
        cube.position.z = (Math.random() - 0.5) * 12;
        
        // Random rotation
        cube.rotation.x = Math.random() * Math.PI * 2;
        cube.rotation.y = Math.random() * Math.PI * 2;
        cube.rotation.z = Math.random() * Math.PI * 2;
        
        cube.castShadow = true;
        cube.receiveShadow = true;
        
        objects.push(cube);
        scene.add(cube);
    }

    // Add one sphere
    const sphereRadius = Math.random() * 1.5 + 0.3; // 0.3-1.8 radius
    const sphereGeometry = new THREE.SphereGeometry(sphereRadius, 12, 8);  // Lower poly count
    const sphereMaterial = new THREE.MeshLambertMaterial({ 
        color: 0xdddddd 
    });
    
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    
    sphere.position.x = (Math.random() - 0.5) * 12;
    sphere.position.y = (Math.random() - 0.5) * 8;
    sphere.position.z = (Math.random() - 0.5) * 10;
    
    sphere.castShadow = true;
    sphere.receiveShadow = true;
    
    objects.push(sphere);
    scene.add(sphere);

    // Camera position
    camera.position.set(0, 0, 8);
    camera.lookAt(0, 0, 0);

    // Render
    renderer.render(scene, camera);
    
    // Convert WebGL buffer to image
    const pixels = new Uint8Array(WIDTH * HEIGHT * 4);
    gl.readPixels(0, 0, WIDTH, HEIGHT, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    
    // Create canvas with image data (flip Y axis)
    const outputCanvas = createCanvas(WIDTH, HEIGHT);
    const ctx = outputCanvas.getContext('2d');
    const imageData = ctx.createImageData(WIDTH, HEIGHT);
    
    for (let y = 0; y < HEIGHT; y++) {
        for (let x = 0; x < WIDTH; x++) {
            const srcIndex = (y * WIDTH + x) * 4;
            const dstIndex = ((HEIGHT - 1 - y) * WIDTH + x) * 4;  // Flip Y
            imageData.data[dstIndex] = pixels[srcIndex];       // R
            imageData.data[dstIndex + 1] = pixels[srcIndex + 1]; // G
            imageData.data[dstIndex + 2] = pixels[srcIndex + 2]; // B
            imageData.data[dstIndex + 3] = pixels[srcIndex + 3]; // A
        }
    }
    
    ctx.putImageData(imageData, 0, 0);
    
    // Save to file
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `cubes-optimized-${timestamp}.png`;
    const filepath = path.join(PICS_DIR, filename);
    
    const buffer = outputCanvas.toBuffer('image/png');
    fs.writeFileSync(filepath, buffer);
    
    console.log(`✅ Generated: ${filename}`);
    return filepath;
}

async function main() {
    console.log('Optimized visual generation starting...');
    console.log('Generated images will be saved to:', PICS_DIR);
    
    try {
        await generateThreeJSSceneOptimized();
        console.log('🎨 Generation complete!');
    } catch (error) {
        console.error('❌ Generation failed:', error);
    }
}

if (require.main === module) {
    main();
}