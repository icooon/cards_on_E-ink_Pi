#!/usr/bin/env node

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

// E-ink display dimensions
const WIDTH = 800;
const HEIGHT = 480;

function generateCircles() {
    console.log('👻 Generating transparent circles for selective ghosting...');
    
    const canvas = createCanvas(WIDTH, HEIGHT);
    const ctx = canvas.getContext('2d');
    
    // Transparent background for ghosting
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    
    // Generate 1-3 circles in random positions
    const numCircles = Math.floor(Math.random() * 3) + 1;
    
    for (let i = 0; i < numCircles; i++) {
        // Random position (avoid edges)
        const x = 100 + Math.random() * (WIDTH - 200);
        const y = 100 + Math.random() * (HEIGHT - 200);
        
        // Random size
        const radius = 30 + Math.random() * 80;
        
        // Random color (black or red)
        const colors = ['#000000', '#ff0000'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        // Draw circle
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fill();
        
        console.log(`  Circle ${i+1}: ${color} at (${Math.round(x)}, ${Math.round(y)}) radius ${Math.round(radius)}`);
    }
    
    // Save image
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `circles-${timestamp}.png`;
    const filepath = path.join(__dirname, 'pics', filename);
    
    // Ensure pics directory exists
    if (!fs.existsSync(path.dirname(filepath))) {
        fs.mkdirSync(path.dirname(filepath), { recursive: true });
    }
    
    // Save
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(filepath, buffer);
    
    console.log(`✅ Generated: ${filename}`);
}

if (require.main === module) {
    generateCircles();
}

module.exports = { generateCircles };