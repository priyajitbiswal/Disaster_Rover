// Connect to Socket.IO server
const socket = io();

// DOM elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const clearLogBtn = document.getElementById('clearLogBtn');
const roverStatus = document.getElementById('roverStatus');
const batteryLevel = document.getElementById('batteryLevel');
const roverPosition = document.getElementById('roverPosition');
const sessionId = document.getElementById('sessionId');
const accelX = document.getElementById('accelX');
const accelY = document.getElementById('accelY');
const accelZ = document.getElementById('accelZ');
const ultrasonicDistance = document.getElementById('ultrasonicDistance');
const ultrasonicDetection = document.getElementById('ultrasonicDetection');
const irReflection = document.getElementById('irReflection');
const rfidDetection = document.getElementById('rfidDetection');
const movementHistory = document.getElementById('movementHistory');
const logEntries = document.getElementById('logEntries');
const survivorsCount = document.getElementById('survivorsCount');
const survivorsList = document.getElementById('survivorsList');
const noSurvivorsMessage = document.getElementById('noSurvivorsMessage');
const pathCanvas = document.getElementById('pathCanvas');
const pathCtx = pathCanvas.getContext('2d');

// Path visualization settings
const pathSettings = {
    roverSize: 10,
    survivorSize: 8,
    pathColor: 'green',
    roverColor: 'blue',
    survivorColor: 'red',
    startColor: 'orange',
    padding: 30,
    maxPositions: 50  // Maximum number of positions to track
};

// Rover state
let roverState = {
    startingPosition: null,
    currentPosition: [0, 0],
    currentDirection: 'forward',
    path: [],
    survivors: [],
    survivorsCount: 0
};

// Initialize the path visualization
function initPathVisualization() {
    // Clear the canvas
    pathCtx.clearRect(0, 0, pathCanvas.width, pathCanvas.height);
    
    // Draw a border
    pathCtx.strokeStyle = '#ccc';
    pathCtx.lineWidth = 1;
    pathCtx.strokeRect(0, 0, pathCanvas.width, pathCanvas.height);
}

// Calculate the scale for the path visualization
function calculatePathScale(positions) {
    if (!positions || positions.length === 0) {
        return { scaleX: 1, scaleY: 1, minX: 0, minY: 0, maxX: 0, maxY: 0 };
    }
    
    // Find min and max coordinates
    let minX = positions[0][0];
    let maxX = positions[0][0];
    let minY = positions[0][1];
    let maxY = positions[0][1];
    
    positions.forEach(pos => {
        minX = Math.min(minX, pos[0]);
        maxX = Math.max(maxX, pos[0]);
        minY = Math.min(minY, pos[1]);
        maxY = Math.max(maxY, pos[1]);
    });
    
    // Add some padding
    minX -= 1;
    maxX += 1;
    minY -= 1;
    maxY += 1;
    
    // Calculate scale
    const rangeX = maxX - minX;
    const rangeY = maxY - minY;
    
    const scaleX = (pathCanvas.width - pathSettings.padding * 2) / (rangeX || 1);
    const scaleY = (pathCanvas.height - pathSettings.padding * 2) / (rangeY || 1);
    
    return { scaleX, scaleY, minX, minY, maxX, maxY };
}

// Convert rover coordinates to canvas coordinates
function pathCoordinates(x, y, scale) {
    const canvasX = pathSettings.padding + (x - scale.minX) * scale.scaleX;
    const canvasY = pathCanvas.height - pathSettings.padding - (y - scale.minY) * scale.scaleY;
    return { x: canvasX, y: canvasY };
}

// Draw the path visualization
function drawPathVisualization() {
    // Initialize the canvas
    initPathVisualization();
    
    // If we don't have any path data yet, return
    if (roverState.path.length === 0) {
        return;
    }
    
    // Calculate scale based on all positions (path + current + survivors)
    const allPositions = [...roverState.path];
    if (roverState.currentPosition) {
        allPositions.push(roverState.currentPosition);
    }
    if (roverState.survivors && roverState.survivors.length > 0) {
        allPositions.push(...roverState.survivors);
    }
    
    const scale = calculatePathScale(allPositions);
    
    // Draw the path
    if (roverState.path.length > 1) {
        pathCtx.strokeStyle = pathSettings.pathColor;
        pathCtx.lineWidth = 2;
        pathCtx.beginPath();
        
        const startCoords = pathCoordinates(roverState.path[0][0], roverState.path[0][1], scale);
        pathCtx.moveTo(startCoords.x, startCoords.y);
        
        for (let i = 1; i < roverState.path.length; i++) {
            const coords = pathCoordinates(roverState.path[i][0], roverState.path[i][1], scale);
            pathCtx.lineTo(coords.x, coords.y);
        }
        
        pathCtx.stroke();
    }
    
    // Draw the starting position
    if (roverState.startingPosition) {
        const startCoords = pathCoordinates(roverState.startingPosition[0], roverState.startingPosition[1], scale);
        
        pathCtx.fillStyle = pathSettings.startColor;
        pathCtx.beginPath();
        pathCtx.arc(startCoords.x, startCoords.y, pathSettings.roverSize / 1.5, 0, Math.PI * 2);
        pathCtx.fill();
        
        // Add an X inside
        pathCtx.strokeStyle = '#fff';
        pathCtx.lineWidth = 2;
        pathCtx.beginPath();
        pathCtx.moveTo(startCoords.x - 5, startCoords.y - 5);
        pathCtx.lineTo(startCoords.x + 5, startCoords.y + 5);
        pathCtx.moveTo(startCoords.x + 5, startCoords.y - 5);
        pathCtx.lineTo(startCoords.x - 5, startCoords.y + 5);
        pathCtx.stroke();
    }
    
    // Draw survivors
    if (roverState.survivors && roverState.survivors.length > 0) {
        pathCtx.fillStyle = pathSettings.survivorColor;
        
        roverState.survivors.forEach(pos => {
            const coords = pathCoordinates(pos[0], pos[1], scale);
            
            pathCtx.beginPath();
            pathCtx.arc(coords.x, coords.y, pathSettings.survivorSize, 0, Math.PI * 2);
            pathCtx.fill();
            
            // Add a cross inside
            pathCtx.strokeStyle = '#fff';
            pathCtx.lineWidth = 1;
            pathCtx.beginPath();
            pathCtx.moveTo(coords.x - 4, coords.y);
            pathCtx.lineTo(coords.x + 4, coords.y);
            pathCtx.moveTo(coords.x, coords.y - 4);
            pathCtx.lineTo(coords.x, coords.y + 4);
            pathCtx.stroke();
        });
    }
    
    // Draw the current rover position
    if (roverState.currentPosition) {
        const coords = pathCoordinates(roverState.currentPosition[0], roverState.currentPosition[1], scale);
        
        pathCtx.fillStyle = pathSettings.roverColor;
        pathCtx.beginPath();
        pathCtx.arc(coords.x, coords.y, pathSettings.roverSize, 0, Math.PI * 2);
        pathCtx.fill();
        
        // Add direction indicator
        pathCtx.fillStyle = '#fff';
        pathCtx.beginPath();
        
        // Adjust the triangle orientation based on direction
        switch(roverState.currentDirection) {
            case 'forward':
                // Point up
                pathCtx.moveTo(coords.x, coords.y - pathSettings.roverSize/1.2);
                pathCtx.lineTo(coords.x + pathSettings.roverSize/2, coords.y);
                pathCtx.lineTo(coords.x - pathSettings.roverSize/2, coords.y);
                break;
            case 'backward':
                // Point down
                pathCtx.moveTo(coords.x, coords.y + pathSettings.roverSize/1.2);
                pathCtx.lineTo(coords.x + pathSettings.roverSize/2, coords.y);
                pathCtx.lineTo(coords.x - pathSettings.roverSize/2, coords.y);
                break;
            case 'left':
                // Point left
                pathCtx.moveTo(coords.x - pathSettings.roverSize/1.2, coords.y);
                pathCtx.lineTo(coords.x, coords.y + pathSettings.roverSize/2);
                pathCtx.lineTo(coords.x, coords.y - pathSettings.roverSize/2);
                break;
            case 'right':
                // Point right
                pathCtx.moveTo(coords.x + pathSettings.roverSize/1.2, coords.y);
                pathCtx.lineTo(coords.x, coords.y + pathSettings.roverSize/2);
                pathCtx.lineTo(coords.x, coords.y - pathSettings.roverSize/2);
                break;
            default:
                // Default triangle (up)
                pathCtx.moveTo(coords.x, coords.y - pathSettings.roverSize/2);
                pathCtx.lineTo(coords.x + pathSettings.roverSize/2, coords.y + pathSettings.roverSize/2);
                pathCtx.lineTo(coords.x - pathSettings.roverSize/2, coords.y + pathSettings.roverSize/2);
        }
        
        pathCtx.closePath();
        pathCtx.fill();
    }
}

// Update path with new position
function updatePath(position) {
    if (!position || position.length !== 2) return;
    
    // Set starting position if this is the first update
    if (!roverState.startingPosition) {
        roverState.startingPosition = [...position];
    }
    
    // Update current position
    roverState.currentPosition = [...position];
    
    // Add to path if it's a new position
    if (roverState.path.length === 0 || 
        roverState.path[roverState.path.length - 1][0] !== position[0] || 
        roverState.path[roverState.path.length - 1][1] !== position[1]) {
        
        roverState.path.push([...position]);
        
        // Limit the path length to avoid performance issues
        if (roverState.path.length > pathSettings.maxPositions) {
            roverState.path.shift();
        }
    }
    
    // Redraw the path visualization
    drawPathVisualization();
}

// Add log entry
function addLogEntry(entry) {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${entry.level}`;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    timestamp.textContent = `[${entry.timestamp}]`;
    
    logEntry.appendChild(timestamp);
    logEntry.appendChild(document.createTextNode(` ${entry.message}`));
    
    logEntries.appendChild(logEntry);
    logEntries.scrollTop = logEntries.scrollHeight;
}

// Add movement history item
function addMovementItem(direction, timestamp) {
    const item = document.createElement('li');
    item.className = 'list-group-item';
    
    // Set direction icon based on movement
    let icon = '';
    let dirClass = '';
    
    switch (direction.toLowerCase()) {
        case 'forward':
            icon = 'fa-arrow-up';
            dirClass = 'text-success';
            break;
        case 'backward':
            icon = 'fa-arrow-down';
            dirClass = 'text-danger';
            break;
        case 'left':
            icon = 'fa-arrow-left';
            dirClass = 'text-primary';
            break;
        case 'right':
            icon = 'fa-arrow-right';
            dirClass = 'text-warning';
            break;
        default:
            icon = 'fa-question';
            dirClass = 'text-secondary';
    }
    
    item.innerHTML = `
        <i class="fas ${icon} ${dirClass} me-2"></i>
        <span class="movement-direction ${dirClass}">${direction}</span>
        <span class="movement-time float-end">${timestamp}</span>
    `;
    
    movementHistory.prepend(item);
    
    // Limit history to 10 items
    if (movementHistory.children.length > 10) {
        movementHistory.removeChild(movementHistory.lastChild);
    }
}

// Add survivor to the list
function addSurvivor(position, timestamp) {
    // Hide the "no survivors" message
    noSurvivorsMessage.style.display = 'none';
    
    // Create a new survivor item
    const item = document.createElement('div');
    item.className = 'survivor-item';
    
    item.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <i class="fas fa-user-check text-danger me-2"></i>
                <span class="survivor-position">X=${position[0]}, Y=${position[1]}</span>
            </div>
            <span class="survivor-time">${timestamp}</span>
        </div>
    `;
    
    // Add to the survivors list
    survivorsList.prepend(item);
}

// Update status display
function updateStatus(data) {
    // Update status badge
    roverStatus.textContent = data.status || "Unknown";
    
    // Update status badge color
    if (data.status && data.status.toLowerCase().includes('connection lost')) {
        roverStatus.className = 'status-value badge bg-danger';
    } else if (data.status && data.status.toLowerCase().includes('delivering aid')) {
        roverStatus.className = 'status-value badge bg-info';
        // Add a visual effect for aid delivery
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: "Delivering aid to survivor...",
            level: 'info'
        });
    } else if (data.status && data.status.toLowerCase().includes('aid delivered')) {
        roverStatus.className = 'status-value badge bg-success';
        // Add a visual effect for aid delivery complete
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: "Aid successfully delivered!",
            level: 'success'
        });
    } else if (data.status && data.status.toLowerCase().includes('recharging')) {
        roverStatus.className = 'status-value badge bg-warning text-dark';
    } else if (data.status && data.status.toLowerCase().includes('charging')) {
        roverStatus.className = 'status-value badge bg-warning text-dark';
    } else if (data.status && data.status.toLowerCase().includes('fully charged')) {
        roverStatus.className = 'status-value badge bg-success';
    } else if (data.status && data.status.toLowerCase().includes('moving')) {
        roverStatus.className = 'status-value badge bg-primary';
    } else if (data.status && data.status.toLowerCase() === 'idle') {
        roverStatus.className = 'status-value badge bg-secondary';
    } else {
        roverStatus.className = 'status-value badge bg-info';
    }
    
    // Update battery level
    const battery = Math.min(data.battery || 0, 100);  // Ensure battery never exceeds 100%
    batteryLevel.style.width = `${battery}%`;
    batteryLevel.textContent = `${battery}%`;
    
    // Get the battery container for additional styling
    const batteryContainer = batteryLevel.parentElement;
    
    // Remove any existing special classes
    batteryContainer.classList.remove('battery-charging', 'battery-critical');
    
    // Update battery color based on level
    if (battery > 70) {
        batteryLevel.className = 'progress-bar bg-success';
    } else if (battery > 30) {
        batteryLevel.className = 'progress-bar bg-warning';
    } else if (battery > 10) {
        batteryLevel.className = 'progress-bar bg-danger';
    } else if (battery > 5) {
        batteryLevel.className = 'progress-bar bg-danger';
    } else {
        batteryLevel.className = 'progress-bar bg-danger progress-bar-striped progress-bar-animated';
        batteryContainer.classList.add('battery-critical');
    }
    
    // Add charging indicator if charging
    if (data.status && (data.status.toLowerCase().includes('charging') || data.status.toLowerCase().includes('recharging'))) {
        batteryLevel.className += ' progress-bar-striped progress-bar-animated';
        
        // Add a log entry for charging if battery is low
        if (battery <= 10) {
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Battery low (${battery}%). Charging in progress...`,
                level: 'warning'
            });
        }
    }
    
    // Update position
    if (data.position) {
        roverPosition.textContent = `X=${data.position.x}, Y=${data.position.y}`;
    }
    
    // Update session ID if available
    if (data.session_id) {
        sessionId.textContent = data.session_id;
    }
}

// Update sensor display
function updateSensors(data) {
    if (!data) return;
    
    // Update accelerometer
    if (data.accelerometer) {
        accelX.textContent = data.accelerometer.x.toFixed(2);
        accelY.textContent = data.accelerometer.y.toFixed(2);
        accelZ.textContent = data.accelerometer.z.toFixed(2);
    }
    
    // Update ultrasonic sensor
    if (data.ultrasonic) {
        ultrasonicDistance.textContent = data.ultrasonic.distance !== null ? data.ultrasonic.distance : 'N/A';
        ultrasonicDetection.textContent = data.ultrasonic.detection ? 'Yes' : 'No';
        ultrasonicDetection.className = data.ultrasonic.detection ? 'sensor-value badge bg-warning' : 'sensor-value badge bg-secondary';
    }
    
    // Update IR sensor
    if (data.ir) {
        irReflection.textContent = data.ir.reflection ? 'Yes' : 'No';
        irReflection.className = data.ir.reflection ? 'sensor-value badge bg-warning' : 'sensor-value badge bg-secondary';
    }
    
    // Update RFID sensor
    if (data.rfid) {
        rfidDetection.textContent = data.rfid.tag_detected ? 'Yes' : 'No';
        rfidDetection.className = data.rfid.tag_detected ? 'sensor-value badge bg-warning' : 'sensor-value badge bg-secondary';
    }
}

// Update survivors information
function updateSurvivors(survivors) {
    if (!survivors) return;
    
    // Check if we have new survivors
    if (survivors.length > roverState.survivors.length) {
        // Get the new survivors
        const newSurvivors = survivors.slice(roverState.survivors.length);
        
        // Update the count
        roverState.survivorsCount = survivors.length;
        survivorsCount.textContent = roverState.survivorsCount;
        
        // Add animation effect to the counter
        survivorsCount.classList.add('survivor-found');
        setTimeout(() => {
            survivorsCount.classList.remove('survivor-found');
        }, 1000);
        
        // Add each new survivor to the list
        const timestamp = new Date().toLocaleTimeString();
        newSurvivors.forEach(position => {
            addSurvivor(position, timestamp);
        });
    }
    
    // Update the survivors state
    roverState.survivors = [...survivors];
    
    // Update the path visualization
    drawPathVisualization();
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    addLogEntry({
        timestamp: new Date().toLocaleTimeString(),
        message: 'Connected to server',
        level: 'info'
    });
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    addLogEntry({
        timestamp: new Date().toLocaleTimeString(),
        message: 'Disconnected from server',
        level: 'error'
    });
});

socket.on('status_update', (data) => {
    console.log('Status update:', data);
    updateStatus(data);
});

socket.on('sensor_update', (data) => {
    console.log('Sensor update:', data);
    updateSensors(data);
});

socket.on('movement_update', (data) => {
    console.log('Movement update:', data);
    if (data && data.direction && data.history && data.history.length > 0) {
        addMovementItem(data.direction, data.history[data.history.length - 1].timestamp);
    }
});

socket.on('log_update', (entry) => {
    console.log('Log update:', entry);
    addLogEntry(entry);
});

socket.on('map_update', (data) => {
    console.log('Map update received:', data);
    if (data) {
        // Update rover position
        if (data.position) {
            updatePath(data.position);
        }
        
        // Update survivors
        if (data.survivors) {
            updateSurvivors(data.survivors);
        }
        
        // Update direction
        if (data.direction) {
            roverState.currentDirection = data.direction;
            drawPathVisualization();
        }
    }
});

// Button event handlers
startBtn.addEventListener('click', async () => {
    try {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Starting...';
        
        const response = await fetch('/api/start-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Simulation';
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: 'Simulation started',
                level: 'success'
            });
        } else {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Simulation';
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Failed to start simulation: ${data.message}`,
                level: 'error'
            });
        }
    } catch (error) {
        console.error('Error starting simulation:', error);
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Simulation';
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: `Error starting simulation: ${error.message}`,
            level: 'error'
        });
    }
});

stopBtn.addEventListener('click', async () => {
    try {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Stopping...';
        
        const response = await fetch('/api/stop-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            stopBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Stop Simulation';
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: 'Simulation stopped',
                level: 'warning'
            });
        } else {
            stopBtn.disabled = false;
            stopBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Stop Simulation';
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Failed to stop simulation: ${data.message}`,
                level: 'error'
            });
        }
    } catch (error) {
        console.error('Error stopping simulation:', error);
        stopBtn.disabled = false;
        stopBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Stop Simulation';
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: `Error stopping simulation: ${error.message}`,
            level: 'error'
        });
    }
});

clearLogBtn.addEventListener('click', () => {
    logEntries.innerHTML = '';
    addLogEntry({
        timestamp: new Date().toLocaleTimeString(),
        message: 'Log cleared',
        level: 'info'
    });
});

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Initialize survivor count
    survivorsCount.textContent = '0';
    
    // Initialize path visualization
    initPathVisualization();
    
    // Add initial log entry
    addLogEntry({
        timestamp: new Date().toLocaleTimeString(),
        message: 'RoverX Dashboard initialized',
        level: 'info'
    });
    
    // Fetch initial rover data
    fetch('/api/rover-data')
        .then(response => response.json())
        .then(data => {
            console.log('Initial data:', data);
            updateStatus(data);
            if (data.sensor_data) {
                updateSensors(data.sensor_data);
            }
            if (data.survivors_found && data.survivors_found.length > 0) {
                updateSurvivors(data.survivors_found);
            }
        })
        .catch(error => {
            console.error('Error fetching initial data:', error);
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Error fetching initial data: ${error.message}`,
                level: 'error'
            });
        });
});
