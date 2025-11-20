#!/usr/bin/env node

const { exec } = require('child_process');
const fs = require('fs');
const os = require('os');

async function getLocalNetworks() {
    const interfaces = os.networkInterfaces();
    const networks = [];
    
    for (const [name, addrs] of Object.entries(interfaces)) {
        for (const addr of addrs) {
            if (addr.family === 'IPv4' && !addr.internal && addr.address !== '127.0.0.1') {
                // Convert IP to network range (e.g., 192.168.1.100 -> 192.168.1.0/24)
                const parts = addr.address.split('.');
                const network = `${parts[0]}.${parts[1]}.${parts[2]}.0/24`;
                if (!networks.includes(network)) {
                    networks.push(network);
                }
            }
        }
    }
    
    return networks;
}

async function scanForPi(network) {
    console.log(`🔍 Scanning network ${network} for Raspberry Pi...`);
    
    return new Promise((resolve, reject) => {
        // First try: scan for known Pi and test our known IP
        if (network === '30.30.10.0/24') {
            console.log('🎯 Testing known Pi IP 30.30.10.64...');
            resolve('30.30.10.64');
            return;
        }
        
        const command = `nmap -sn ${network} 2>/dev/null | grep -B 2 -i "raspberry\\|b8:27:eb\\|dc:a6:32\\|e4:5f:01" | grep "Nmap scan report" | awk '{print $5}' | head -1`;
        
        exec(command, (error, stdout, stderr) => {
            if (error) {
                // Fallback: try ping sweep for common Pi IPs
                const baseNetwork = network.split('/')[0].replace('.0', '');
                const commonIPs = [`${baseNetwork}.64`, `${baseNetwork}.100`, `${baseNetwork}.101`, `${baseNetwork}.10`];
                
                console.log(`🔄 Trying common Pi IPs: ${commonIPs.join(', ')}`);
                
                // Test each common IP
                let tested = 0;
                for (const ip of commonIPs) {
                    exec(`ping -c 1 -W 1 ${ip} 2>/dev/null`, (pingError, pingStdout) => {
                        tested++;
                        if (!pingError && pingStdout.includes('1 packets transmitted, 1 received')) {
                            resolve(ip);
                            return;
                        }
                        if (tested === commonIPs.length) {
                            resolve(null);
                        }
                    });
                }
            } else {
                resolve(stdout.trim());
            }
        });
    });
}

async function testPiConnection(ip) {
    console.log(`🧪 Testing SSH connection to ${ip}...`);
    
    return new Promise((resolve) => {
        const command = `sshpass -p '2308' ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no pi@${ip} 'echo "Pi found!"' 2>/dev/null`;
        
        exec(command, (error, stdout, stderr) => {
            resolve(!error && stdout.includes('Pi found!'));
        });
    });
}

async function updateDeployScript(piIP) {
    const deployPath = './deploy.js';
    let content = fs.readFileSync(deployPath, 'utf8');
    
    // Update the PI_IP line
    const updatedContent = content.replace(
        /const PI_IP = ['"][^'"]*['"];/,
        `const PI_IP = '${piIP}';`
    );
    
    fs.writeFileSync(deployPath, updatedContent);
    console.log(`✅ Updated deploy.js with Pi IP: ${piIP}`);
}

async function findPi() {
    console.log('🔍 Discovering Raspberry Pi on local network...\n');
    
    try {
        // Get local networks to scan
        let networks = await getLocalNetworks();
        
        // Add known Pi network if not detected
        if (!networks.some(n => n.startsWith('30.30.10'))) {
            networks.push('30.30.10.0/24');
        }
        
        console.log(`📡 Found local networks: ${networks.join(', ')}\n`);
        
        // Scan each network for Pi
        for (const network of networks) {
            const piIP = await scanForPi(network);
            
            if (piIP) {
                console.log(`🎯 Found potential Pi at: ${piIP}`);
                
                // Test SSH connection
                const canConnect = await testPiConnection(piIP);
                
                if (canConnect) {
                    console.log(`🎉 Successfully connected to Pi at ${piIP}!\n`);
                    
                    // Update deploy.js
                    await updateDeployScript(piIP);
                    
                    console.log('🚀 Ready to deploy! You can now run:');
                    console.log('   npm run dev-simple');
                    console.log('   npm run deploy');
                    
                    return piIP;
                } else {
                    console.log(`❌ Could not SSH to ${piIP} (wrong device or credentials)\n`);
                }
            }
        }
        
        // If we get here, no Pi was found
        console.log('❌ No Raspberry Pi found on local networks.');
        console.log('\n💡 Troubleshooting:');
        console.log('   1. Make sure your Pi is connected to the same network');
        console.log('   2. Check that SSH is enabled on the Pi');
        console.log('   3. Verify the password is still "2308"');
        console.log('   4. Try: ssh pi@raspberrypi.local');
        
        return null;
        
    } catch (error) {
        console.error('❌ Error during Pi discovery:', error.message);
        return null;
    }
}

// Also try hostname fallback
async function tryHostnameFallback() {
    console.log('\n🔄 Trying hostname fallback (raspberrypi.local)...');
    
    const canConnect = await testPiConnection('raspberrypi.local');
    if (canConnect) {
        console.log('✅ Found Pi via hostname: raspberrypi.local');
        await updateDeployScript('raspberrypi.local');
        return 'raspberrypi.local';
    }
    
    return null;
}

async function main() {
    console.log('🔍 Raspberry Pi Network Discovery\n');
    
    // Try network scanning first
    let piIP = await findPi();
    
    // If that fails, try hostname
    if (!piIP) {
        piIP = await tryHostnameFallback();
    }
    
    if (piIP) {
        console.log(`\n🎯 Pi configured at: ${piIP}`);
        process.exit(0);
    } else {
        console.log('\n❌ Could not find Raspberry Pi on any network.');
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { findPi, testPiConnection, updateDeployScript };