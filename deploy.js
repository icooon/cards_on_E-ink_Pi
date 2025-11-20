#!/usr/bin/env node

const { exec } = require('child_process');
const path = require('path');

// Configuration - update with your Pi's IP
const PI_IP = '30.30.10.64';
const PI_USER = 'pi';
const LOCAL_PICS = path.join(__dirname, 'pics');
const PI_PICS = '/home/pi/pics';
const PI_PROJECT = '/home/pi/cards_on_E-ink_Pi';

async function deployToPi() {
    console.log('Deploying to Pi...');
    
    // Sync generated images
    const syncPics = `rsync -avz -e "sshpass -p '2308' ssh -o StrictHostKeyChecking=no" ${LOCAL_PICS}/ ${PI_USER}@${PI_IP}:${PI_PICS}/`;
    
    // Sync project files
    const syncProject = `rsync -avz -e "sshpass -p '2308' ssh -o StrictHostKeyChecking=no" --exclude node_modules --exclude .git --exclude pics . ${PI_USER}@${PI_IP}:${PI_PROJECT}/`;
    
    try {
        console.log('Syncing images...');
        await runCommand(syncPics);
        
        console.log('Syncing project files...');
        await runCommand(syncProject);
        
        console.log('✅ Deploy complete!');
    } catch (error) {
        console.error('❌ Deploy failed:', error.message);
    }
}

function runCommand(command) {
    return new Promise((resolve, reject) => {
        exec(command, (error, stdout, stderr) => {
            if (error) reject(error);
            else resolve(stdout);
        });
    });
}

if (require.main === module) {
    deployToPi();
}

module.exports = { deployToPi };