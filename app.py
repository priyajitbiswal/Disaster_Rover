import os
import json
import time
from datetime import datetime
import random
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import requests
from rover_simulation import RoverSimulation

# Base URL for the API
BASE_URL = "https://roverdata2-production.up.railway.app"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'roverx-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
rover_simulation = None
simulation_thread = None
simulation_running = False
is_delivering_aid = False
aid_delivery_start_time = 0

# Rover data structure
rover_data = {
    "status": "idle",
    "battery": 0,
    "position": {"x": 0, "y": 0},
    "sensor_data": None,
    "movement_history": [],
    "log_entries": [],
    "path_history": [],
    "survivors_found": []
}

def add_log_entry(message, level="info"):
    """Add a log entry with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "message": message,
        "level": level  # info, success, warning, error
    }
    rover_data["log_entries"].append(entry)
    socketio.emit('log_update', entry)

def simulation_loop():
    """Autonomous rover simulation loop"""
    global simulation_running, rover_simulation, rover_data, is_delivering_aid, aid_delivery_start_time
    
    try:
        # Start a session
        if not rover_simulation.start_session():
            add_log_entry("Failed to start session. Exiting.", "error")
            simulation_running = False
            return
        
        # Store session ID in rover_data
        rover_data["session_id"] = rover_simulation.session_id
        add_log_entry(f"Session started with ID: {rover_simulation.session_id}", "success")
        
        # Initial status update
        update_rover_status()
        update_sensor_data()
        
        # Battery thresholds
        RECHARGE_START = 5  # Start recharging at 5%
        RECHARGE_STOP = 80  # Stop recharging at 80%
        COMMS_LOSS = 10  # Communication lost below 10%
        
        while simulation_running:
            # Update rover status and sensor data
            update_rover_status()
            update_sensor_data()
            
            # Handle aid delivery
            current_time = time.time()
            if is_delivering_aid and (current_time - aid_delivery_start_time) >= 5:
                # Aid delivery complete after 5 seconds
                is_delivering_aid = False
                add_log_entry("Aid delivery complete. Resuming exploration.", "success")
                rover_data["status"] = "Aid Delivered"
                socketio.emit('status_update', rover_data)
                time.sleep(1)  # Brief pause before resuming
                
            # Handle battery management
            if rover_data["battery"] <= RECHARGE_START and rover_simulation.status.lower() != "charging":
                # Battery critically low, start charging
                add_log_entry(f"Battery critically low ({rover_data['battery']}%). Starting recharge...", "warning")
                rover_simulation.charge_rover()
                rover_simulation.stop_rover()  # Ensure the rover stops moving
                rover_data["status"] = "Charging"  # Update status immediately
                socketio.emit('status_update', rover_data)  # Send immediate update to UI
                add_log_entry("Rover stopped for charging. Will resume at 80%.", "info")
                time.sleep(1)  # Give time for charging to start
            
            # Handle communication loss at low battery
            elif rover_data["battery"] <= COMMS_LOSS and rover_data["battery"] > RECHARGE_START and rover_simulation.status.lower() != "charging":
                # Battery low, communication degrading
                add_log_entry(f"Warning: Battery at {rover_data['battery']}%. Connection lost.", "warning")
                rover_data["status"] = "Connection Lost - Low Battery"
                socketio.emit('status_update', rover_data)
                
                # Stop the rover
                rover_simulation.stop_rover()
                add_log_entry("Rover stopped due to connection loss.", "warning")
                
                # Start charging immediately
                rover_simulation.charge_rover()
                rover_data["status"] = "Recharging"
                socketio.emit('status_update', rover_data)
                add_log_entry("Emergency recharge initiated.", "info")
            
            # If charging and battery is above threshold, stop charging by moving
            if rover_simulation.status.lower() == "charging" and rover_data["battery"] >= RECHARGE_STOP:
                # Set battery to exactly 80% when done charging
                rover_data["battery"] = 80
                add_log_entry(f"Battery charged to {rover_data['battery']}%. Resuming operation.", "success")
                rover_data["status"] = "Fully Charged"
                socketio.emit('status_update', rover_data)
                
                # Move to indicate we're no longer charging
                move_rover()
            
            # If not charging and battery is above minimum, move randomly
            if rover_simulation.status.lower() != "charging" and rover_data["battery"] > COMMS_LOSS and not is_delivering_aid:
                # Move in a random direction
                move_rover()
            elif rover_simulation.status.lower() == "charging":
                # If charging, emit a status update to show charging progress
                if rover_data["status"] != "Charging" and rover_data["status"] != "Recharging":
                    rover_data["status"] = "Charging"
                socketio.emit('status_update', rover_data)
                add_log_entry(f"Charging: Battery at {rover_data['battery']}%", "info")
            
            # Sleep to simulate real-time operation
            time.sleep(2)
            
    except Exception as e:
        add_log_entry(f"Simulation error: {str(e)}", "error")
    finally:
        # Stop the rover before exiting
        if rover_simulation:
            rover_simulation.stop_rover()
        simulation_running = False
        add_log_entry("Simulation stopped", "warning")

def update_rover_status():
    """Update rover status from the simulation"""
    global rover_data, rover_simulation
    
    if not rover_simulation:
        add_log_entry("No active simulation.", "error")
        return False
    
    try:
        # Update the rover status in the simulation
        rover_simulation.update_status()
        
        # Copy data from simulation to our data structure
        rover_data["status"] = rover_simulation.status
        rover_data["battery"] = rover_simulation.battery
        rover_data["position"] = rover_simulation.position
        
        # Update path history if position changed
        current_pos = [rover_simulation.position["x"], rover_simulation.position["y"]]
        if not rover_data["path_history"] or rover_data["path_history"][-1] != current_pos:
            rover_data["path_history"].append(current_pos)
        
        # Emit the updated data
        socketio.emit('status_update', rover_data)
        return True
    except Exception as e:
        add_log_entry(f"Error updating rover status: {str(e)}", "error")
        return False

def update_sensor_data():
    """Update sensor data from the simulation"""
    global rover_data, rover_simulation, is_delivering_aid, aid_delivery_start_time
    
    if not rover_simulation:
        add_log_entry("No active simulation.", "error")
        return False
    
    try:
        # Update the sensor data in the simulation
        rover_simulation.update_sensor_data()
        
        # Get the latest sensor data from the API
        if not rover_simulation.session_id:
            return False
        
        url = f"{BASE_URL}/api/rover/sensor-data"
        params = {"session_id": rover_simulation.session_id}
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            rover_data["sensor_data"] = data
            
            # Update position and battery from sensor data
            pos = data.get("position", {"x": 0, "y": 0})
            rover_data["position"] = {"x": pos["x"], "y": pos["y"]}
            
            # Ensure battery level doesn't exceed 100%
            battery_level = data.get("battery_level", 0)
            if battery_level > 100:
                battery_level = 100
            rover_data["battery"] = battery_level
            
            # Check for RFID tag detection (simulating survivor found)
            rfid = data.get("rfid", {"tag_detected": False})
            if rfid.get("tag_detected", False):
                # Simulate finding a survivor at current position
                current_pos = [pos["x"], pos["y"]]
                if current_pos not in rover_data["survivors_found"] and not is_delivering_aid:
                    rover_data["survivors_found"].append(current_pos)
                    add_log_entry(f"Survivor found at position X={pos['x']}, Y={pos['y']}!", "success")
                    
                    # Start aid delivery process
                    rover_simulation.stop_rover()  # Stop the rover
                    rover_data["status"] = "Delivering Aid"
                    socketio.emit('status_update', rover_data)
                    add_log_entry("Rover stopped. Delivering aid to survivor...", "info")
                    
                    # Set aid delivery flags
                    is_delivering_aid = True
                    aid_delivery_start_time = time.time()
            
            # Update path history if position changed
            current_pos = [pos["x"], pos["y"]]
            if not rover_data["path_history"] or rover_data["path_history"][-1] != current_pos:
                rover_data["path_history"].append(current_pos)
                # For debugging
                add_log_entry(f"Position updated: X={pos['x']}, Y={pos['y']}", "info")
            
            # Emit the updated data
            socketio.emit('sensor_update', data)
            
            # Send map update with current position, path history, and survivors
            map_data = {
                "position": current_pos,
                "path": rover_data["path_history"],
                "survivors": rover_data["survivors_found"]
            }
            socketio.emit('map_update', map_data)
            
            # For debugging
            print(f"Map update sent: Position={current_pos}, Path length={len(rover_data['path_history'])}, Survivors={len(rover_data['survivors_found'])}")
            
            return True
        else:
            add_log_entry(f"Failed to get sensor data. Status code: {response.status_code}", "error")
            return False
    except Exception as e:
        add_log_entry(f"Error updating sensor data: {str(e)}", "error")
        return False

def move_rover(direction=None):
    """Move the rover in a specified or random direction"""
    global rover_data, rover_simulation
    
    if not rover_simulation:
        add_log_entry("No active simulation.", "error")
        return False
    
    try:
        # Move the rover in the simulation
        result = rover_simulation.move_rover(direction)
        
        if result:
            # Add to movement history
            rover_data["movement_history"].append({
                "direction": rover_simulation.last_direction,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # Emit movement update
            socketio.emit('movement_update', {
                "direction": rover_simulation.last_direction,
                "history": rover_data["movement_history"]
            })
            
            # Update map with new direction
            map_data = {
                "position": [rover_data["position"]["x"], rover_data["position"]["y"]],
                "path": rover_data["path_history"],
                "survivors": rover_data["survivors_found"],
                "direction": rover_simulation.last_direction
            }
            socketio.emit('map_update', map_data)
            
            return True
        return False
    except Exception as e:
        add_log_entry(f"Error moving rover: {str(e)}", "error")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/start-simulation', methods=['POST'])
def api_start_simulation():
    global simulation_thread, simulation_running, rover_simulation, rover_data
    
    if simulation_running:
        return jsonify({"status": "error", "message": "Simulation already running"})
    
    # Reset rover data
    rover_data["movement_history"] = []
    rover_data["log_entries"] = []
    rover_data["path_history"] = []
    rover_data["survivors_found"] = []
    
    # Create a new rover simulation
    rover_simulation = RoverSimulation()
    
    # Start simulation in a separate thread
    simulation_running = True
    simulation_thread = threading.Thread(target=simulation_loop)
    simulation_thread.daemon = True
    simulation_thread.start()
    
    return jsonify({"status": "success", "message": "Simulation started"})

@app.route('/api/stop-simulation', methods=['POST'])
def api_stop_simulation():
    global simulation_running
    
    if not simulation_running:
        return jsonify({"status": "error", "message": "No simulation running"})
    
    simulation_running = False
    add_log_entry("Simulation stopped by user", "warning")
    
    return jsonify({"status": "success", "message": "Simulation stopped"})

@app.route('/api/rover-data', methods=['GET'])
def api_rover_data():
    return jsonify(rover_data)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
