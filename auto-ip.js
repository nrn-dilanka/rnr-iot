#!/usr/bin/env node
/**
 * Auto IP Detection Script for RNR Solutions IoT Platform
 * Automatically detects and configures the local IP address
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

console.log('🔍 Detecting local IP address...');

/**
 * Get the local IP address
 */
function getLocalIP() {
    const interfaces = os.networkInterfaces();
    
    // Priority order: Ethernet, Wi-Fi, other interfaces
    const priorityOrder = ['Ethernet', 'Wi-Fi', 'en0', 'eth0', 'wlan0'];
    
    for (const interfaceName of priorityOrder) {
        const networkInterface = interfaces[interfaceName];
        if (networkInterface) {
            for (const address of networkInterface) {
                if (address.family === 'IPv4' && !address.internal) {
                    return address.address;
                }
            }
        }
    }
    
    // Fallback: find any non-internal IPv4 address
    for (const interfaceName of Object.keys(interfaces)) {
        const networkInterface = interfaces[interfaceName];
        for (const address of networkInterface) {
            if (address.family === 'IPv4' && !address.internal) {
                return address.address;
            }
        }
    }
    
    return null;
}

/**
 * Update file content with new IP
 */
function updateFileContent(filePath, oldPattern, newValue) {
    try {
        if (fs.existsSync(filePath)) {
            let content = fs.readFileSync(filePath, 'utf8');
            content = content.replace(new RegExp(oldPattern, 'g'), newValue);
            fs.writeFileSync(filePath, content);
            console.log(`  ✓ Updated ${filePath}`);
            return true;
        } else {
            console.log(`  ⚠ File not found: ${filePath}`);
            return false;
        }
    } catch (error) {
        console.error(`  ❌ Error updating ${filePath}:`, error.message);
        return false;
    }
}

// Detect IP
const detectedIP = getLocalIP();

if (!detectedIP) {
    console.log('❌ Could not detect IP address automatically');
    console.log('📝 Please set IP manually in .env files');
    process.exit(1);
}

console.log(`✅ Detected IP: ${detectedIP}`);

// Update files
console.log('📝 Updating configuration files...');

// Update main .env file
updateFileContent(
    '.env',
    'REACT_APP_API_URL=http://[^:]+:8000/api',
    `REACT_APP_API_URL=http://${detectedIP}:8000/api`
);
updateFileContent(
    '.env',
    'REACT_APP_WS_URL=ws://[^:]+:8000/ws',
    `REACT_APP_WS_URL=ws://${detectedIP}:8000/ws`
);

// Update frontend .env file
updateFileContent(
    'frontend/.env',
    'REACT_APP_API_URL=http://[^:]+:8000/api',
    `REACT_APP_API_URL=http://${detectedIP}:8000/api`
);
updateFileContent(
    'frontend/.env',
    'REACT_APP_WS_URL=ws://[^:]+:8000/ws',
    `REACT_APP_WS_URL=ws://${detectedIP}:8000/ws`
);

// Update docker-compose.yml
updateFileContent(
    'docker-compose.yml',
    'REACT_APP_API_URL: http://[^:]+:8000/api',
    `REACT_APP_API_URL: http://${detectedIP}:8000/api`
);
updateFileContent(
    'docker-compose.yml',
    'REACT_APP_WS_URL: ws://[^:]+:8000/ws',
    `REACT_APP_WS_URL: ws://${detectedIP}:8000/ws`
);

console.log(`✅ IP configuration updated to: ${detectedIP}`);
console.log('🚀 You can now run: docker-compose up --build -d');

// Display current configuration
console.log('\n📋 Current Configuration:');
console.log(`  • Frontend URL: http://${detectedIP}:3000`);
console.log(`  • API URL: http://${detectedIP}:8000`);
console.log(`  • WebSocket URL: ws://${detectedIP}:8000/ws`);
console.log(`  • RabbitMQ Management: http://localhost:15672`);
