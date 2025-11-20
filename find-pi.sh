#!/bin/bash

echo "🔍 Discovering Raspberry Pi on local network..."

# Function to test SSH connection
test_ssh() {
    local ip=$1
    echo "🧪 Testing SSH connection to $ip..."
    
    if timeout 5 sshpass -p '2308' ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no pi@$ip 'echo "Pi found!"' 2>/dev/null | grep -q "Pi found!"; then
        return 0
    else
        return 1
    fi
}

# Function to update deploy.js
update_deploy() {
    local ip=$1
    echo "✅ Updating deploy.js with Pi IP: $ip"
    
    # Use sed to replace the PI_IP line (macOS compatible)
    sed -i '' "s/const PI_IP = '[^']*';/const PI_IP = '$ip';/" deploy.js
}

# Get local IP and derive network
LOCAL_IP=$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
if [[ "$LOCAL_IP" == *"192.168."* ]]; then
    NETWORK=$(echo $LOCAL_IP | sed 's/\.[0-9]*$/.*/')
    echo "📡 Scanning network: $NETWORK"
    
    # Scan for Raspberry Pi MAC addresses
    echo "🔍 Looking for Raspberry Pi devices..."
    
    # Use nmap if available, otherwise ping sweep
    if command -v nmap >/dev/null 2>&1; then
        # Scan with nmap
        POSSIBLE_IPS=$(nmap -sn ${LOCAL_IP%.*}.0/24 2>/dev/null | grep -B 2 -i "raspberry\|b8:27:eb\|dc:a6:32\|e4:5f:01" | grep "Nmap scan report" | awk '{print $5}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')
    else
        # Fallback: ping sweep + arp check
        echo "📡 Performing ping sweep (nmap not found)..."
        POSSIBLE_IPS=""
        for i in {1..254}; do
            (ping -c 1 -W 1 ${LOCAL_IP%.*}.$i >/dev/null 2>&1 && echo ${LOCAL_IP%.*}.$i) &
        done | head -20  # Limit to first 20 responses
        wait
        
        # Check ARP table for Raspberry Pi MACs
        POSSIBLE_IPS=$(arp -a | grep -i "b8:27:eb\|dc:a6:32\|e4:5f:01" | awk '{print $2}' | sed 's/[()]//g')
    fi
    
    # Test each possible IP
    for ip in $POSSIBLE_IPS; do
        if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "🎯 Found potential Pi at: $ip"
            if test_ssh "$ip"; then
                echo "🎉 Successfully connected to Pi at $ip!"
                update_deploy "$ip"
                echo ""
                echo "🚀 Ready to deploy! You can now run:"
                echo "   npm run dev-simple"
                echo "   npm run deploy"
                exit 0
            else
                echo "❌ Could not SSH to $ip"
            fi
        fi
    done
fi

# Try hostname fallback
echo ""
echo "🔄 Trying hostname fallback (raspberrypi.local)..."
if test_ssh "raspberrypi.local"; then
    echo "✅ Found Pi via hostname: raspberrypi.local"
    update_deploy "raspberrypi.local"
    echo ""
    echo "🚀 Ready to deploy!"
    exit 0
fi

echo ""
echo "❌ No Raspberry Pi found on local network."
echo ""
echo "💡 Troubleshooting:"
echo "   1. Make sure your Pi is connected to the same network"
echo "   2. Check that SSH is enabled on the Pi"
echo "   3. Verify the password is still '2308'"
echo "   4. Try manually: ssh pi@raspberrypi.local"
echo ""
exit 1