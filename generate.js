#!/usr/bin/env node

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Create local pics directory for testing
const PICS_DIR = path.join(__dirname, 'pics');
if (!fs.existsSync(PICS_DIR)) {
    fs.mkdirSync(PICS_DIR);
}

// E-ink display dimensions
const WIDTH = 800;
const HEIGHT = 480;

async function generateThreeJSScene() {
    console.log('Generating Three.js scene with random cubes...');
    
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    
    // Set viewport to e-ink dimensions
    await page.setViewport({ width: WIDTH, height: HEIGHT });
    
    // Create HTML with Three.js scene
    const html = `
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background: #000; }
            canvas { width: 100%; height: 100%; }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <script>
            // Scene setup
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, ${WIDTH}/${HEIGHT}, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(${WIDTH}, ${HEIGHT});
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.body.appendChild(renderer.domElement);

            // Lights
            // Red light from the side (left)
            const redLight = new THREE.DirectionalLight(0xff4444, 1.2);
            redLight.position.set(-5, 2, 2);
            redLight.castShadow = true;
            scene.add(redLight);

            // White light from the top
            const whiteLight = new THREE.DirectionalLight(0xffffff, 0.8);
            whiteLight.position.set(0, 5, 0);
            whiteLight.castShadow = true;
            scene.add(whiteLight);

            // Ambient light (subtle)
            const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
            scene.add(ambientLight);

            // Create random cubes with much more variety
            const objects = [];
            const numCubes = Math.floor(Math.random() * 30) + 5; // 5-35 cubes (huge range)

            for (let i = 0; i < numCubes; i++) {
                const size = Math.random() * 2.5 + 0.1; // Size between 0.1-2.6 (much bigger range)
                const geometry = new THREE.BoxGeometry(size, size, size);
                const material = new THREE.MeshLambertMaterial({ 
                    color: 0xcccccc 
                });
                
                const cube = new THREE.Mesh(geometry, material);
                
                // Much wider spread positions
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

            // Add one sphere to every scene
            const sphereRadius = Math.random() * 1.5 + 0.3; // 0.3-1.8 radius
            const sphereGeometry = new THREE.SphereGeometry(sphereRadius, 16, 12);
            const sphereMaterial = new THREE.MeshLambertMaterial({ 
                color: 0xdddddd 
            });
            
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
            
            // Position sphere randomly
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
            
            // Signal completion
            window.renderComplete = true;
        </script>
    </body>
    </html>`;
    
    await page.setContent(html);
    
    // Wait for Three.js to render - give it time to complete
    await page.waitForTimeout(2000);
    
    // Take screenshot
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `cubes-${timestamp}.png`;
    const filepath = path.join(PICS_DIR, filename);
    
    await page.screenshot({ 
        path: filepath,
        type: 'png',
        fullPage: false
    });
    
    await browser.close();
    
    console.log(`✅ Generated: ${filename}`);
    return filepath;
}

async function main() {
    console.log('Visual generation starting...');
    console.log('Generated images will be saved to:', PICS_DIR);
    
    try {
        await generateThreeJSScene();
        console.log('🎨 Generation complete!');
    } catch (error) {
        console.error('❌ Generation failed:', error);
    }
}

if (require.main === module) {
    main();
}