#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

// E-ink display dimensions
const WIDTH = 800;
const HEIGHT = 480;

// Create local pics directory for testing
const PICS_DIR = path.join(__dirname, 'pics');
if (!fs.existsSync(PICS_DIR)) {
    fs.mkdirSync(PICS_DIR);
}

function generateSimple3DScene() {
    console.log('Generating simple 3D scene with 2D canvas...');
    
    const canvas = createCanvas(WIDTH, HEIGHT);
    const ctx = canvas.getContext('2d');
    
    // Black background
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    
    // Generate random cubes and sphere
    const objects = [];
    const numCubes = Math.floor(Math.random() * 30) + 5; // 5-35 cubes
    
    // Add cubes
    for (let i = 0; i < numCubes; i++) {
        const size = Math.random() * 120 + 10; // Size between 10-130px
        const x = Math.random() * (WIDTH - size);
        const y = Math.random() * (HEIGHT - size);
        const rotation = Math.random() * 60 - 30; // -30 to +30 degrees
        const depth = Math.random(); // 0-1 for z-ordering
        
        objects.push({
            type: 'cube',
            x, y, size, rotation, depth
        });
    }
    
    // Add one sphere
    const sphereRadius = Math.random() * 80 + 20; // 20-100px radius
    const sphereX = Math.random() * (WIDTH - sphereRadius * 2) + sphereRadius;
    const sphereY = Math.random() * (HEIGHT - sphereRadius * 2) + sphereRadius;
    const sphereDepth = Math.random();
    
    objects.push({
        type: 'sphere',
        x: sphereX,
        y: sphereY,
        radius: sphereRadius,
        depth: sphereDepth
    });
    
    // Sort by depth (back to front)
    objects.sort((a, b) => a.depth - b.depth);
    
    // Draw objects with lighting simulation
    objects.forEach(obj => {
        if (obj.type === 'cube') {
            drawCube(ctx, obj);
        } else if (obj.type === 'sphere') {
            drawSphere(ctx, obj);
        }
    });
    
    return canvas;
}

function drawCube(ctx, cube) {
    const { x, y, size, rotation } = cube;
    
    ctx.save();
    ctx.translate(x + size/2, y + size/2);
    ctx.rotate(rotation * Math.PI / 180);
    
    // Simulate 3D cube with multiple faces
    const faceSize = size * 0.8;
    const offset = size * 0.2;
    
    // Back face (darkest)
    ctx.fillStyle = '#333333';
    ctx.fillRect(-faceSize/2 + offset, -faceSize/2 + offset, faceSize, faceSize);
    
    // Left face (red lighting from left)
    ctx.fillStyle = '#ff4444';
    ctx.fillRect(-faceSize/2, -faceSize/2, faceSize, faceSize);
    
    // Top face (white lighting from top)
    ctx.fillStyle = '#cccccc';
    ctx.fillRect(-faceSize/2, -faceSize/2, faceSize, offset);
    
    // Main face (gradient)
    const gradient = ctx.createLinearGradient(-faceSize/2, -faceSize/2, faceSize/2, faceSize/2);
    gradient.addColorStop(0, '#ff6666'); // Red side
    gradient.addColorStop(0.5, '#999999'); // Middle
    gradient.addColorStop(1, '#333333'); // Shadow side
    
    ctx.fillStyle = gradient;
    ctx.fillRect(-faceSize/2, -faceSize/2, faceSize, faceSize);
    
    ctx.restore();
}

function drawSphere(ctx, sphere) {
    const { x, y, radius } = sphere;
    
    // Create radial gradient for sphere lighting
    const gradient = ctx.createRadialGradient(
        x - radius * 0.3, y - radius * 0.3, 0, // Red light position (left-top)
        x, y, radius
    );
    
    gradient.addColorStop(0, '#ffffff'); // Bright center
    gradient.addColorStop(0.3, '#ff8888'); // Red tint
    gradient.addColorStop(0.7, '#666666'); // Gray
    gradient.addColorStop(1, '#000000');   // Dark edge
    
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();
}

async function main() {
    console.log('Simple 3D visual generation starting...');
    console.log('Generated images will be saved to:', PICS_DIR);
    
    try {
        const canvas = generateSimple3DScene();
        
        // Save to file
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `cubes-simple-${timestamp}.png`;
        const filepath = path.join(PICS_DIR, filename);
        
        const buffer = canvas.toBuffer('image/png');
        fs.writeFileSync(filepath, buffer);
        
        console.log(`✅ Generated: ${filename}`);
        console.log('🎨 Generation complete!');
    } catch (error) {
        console.error('❌ Generation failed:', error);
    }
}

if (require.main === module) {
    main();
}