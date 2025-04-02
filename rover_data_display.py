import requests
import json
import time
from datetime import datetime
import os
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Base URL for the API
BASE_URL = "https://roverdata2-production.up.railway.app"

class RoverDataDisplay:
    def __init__(self):
        self.session_id = None
        self.status_data = None
        self.sensor_data = None
        self.movement_history = []
    
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{text}")
        print(f"{Fore.CYAN}{'=' * len(text)}")
    
    def print_section(self, text):
        """Print a section header"""
        print(f"\n{Fore.BLUE}{Style.BRIGHT}{text}")
        print(f"{Fore.BLUE}{'-' * len(text)}")
    
    def print_success(self, text):
        """Print a success message"""
        print(f"{Fore.GREEN}[SUCCESS] {text}")
    
    def print_error(self, text):
        """Print an error message"""
        print(f"{Fore.RED}[ERROR] {text}")
    
    def print_info(self, text):
        """Print an info message"""
        print(f"{Fore.WHITE}{text}")
    
    def start_session(self):
        """Start a new session and get session ID"""
        self.print_header("STARTING NEW SESSION")
        
        url = f"{BASE_URL}/api/session/start"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                self.print_success(f"Session started successfully!")
                self.print_info(f"Session ID: {Fore.YELLOW}{self.session_id}")
                return True
            else:
                self.print_error(f"Failed to start session. Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error starting session: {str(e)}")
            return False
    
    def get_rover_status(self):
        """Get the rover status"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("ROVER STATUS")
        
        url = f"{BASE_URL}/api/rover/status"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                self.status_data = response.json()
                
                status = self.status_data.get("status", "Unknown")
                battery = self.status_data.get("battery", 0)
                coordinates = self.status_data.get("coordinates", [0, 0])
                
                # Display status with color based on battery level
                battery_color = Fore.GREEN if battery > 70 else Fore.YELLOW if battery > 30 else Fore.RED
                
                self.print_info(f"Status: {Fore.CYAN}{status}")
                self.print_info(f"Battery: {battery_color}{battery}%")
                self.print_info(f"Position: {Fore.MAGENTA}X={coordinates[0]}, Y={coordinates[1]}")
                
                return True
            else:
                self.print_error(f"Failed to get rover status. Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error getting rover status: {str(e)}")
            return False
    
    def charge_rover(self):
        """Charge the rover"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("CHARGING ROVER")
        
        url = f"{BASE_URL}/api/rover/charge"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"{data.get('message', 'Charging successful')}")
                return True
            else:
                self.print_error(f"Failed to charge rover. Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error charging rover: {str(e)}")
            return False
    
    def move_rover(self, direction):
        """Move the rover in the specified direction"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        valid_directions = ["forward", "backward", "left", "right"]
        if direction not in valid_directions:
            self.print_error(f"Invalid direction. Choose from: {', '.join(valid_directions)}")
            return False
        
        self.print_header(f"MOVING ROVER {direction.upper()}")
        
        url = f"{BASE_URL}/api/rover/move"
        params = {"session_id": self.session_id, "direction": direction}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"{data.get('message', 'Movement successful')}")
                
                # Add to movement history
                self.movement_history.append({
                    "direction": direction,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "result": data.get('message', 'Success')
                })
                
                return True
            else:
                self.print_error(f"Failed to move rover. Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error moving rover: {str(e)}")
            return False
    
    def get_sensor_data(self):
        """Get sensor data from the rover"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("ROVER SENSOR DATA")
        
        url = f"{BASE_URL}/api/rover/sensor-data"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                self.sensor_data = response.json()
                
                # Extract data
                timestamp = self.sensor_data.get("timestamp", 0)
                position = self.sensor_data.get("position", {"x": 0, "y": 0})
                accel = self.sensor_data.get("accelerometer", {"x": 0, "y": 0, "z": 0})
                battery = self.sensor_data.get("battery_level", 0)
                comm_status = self.sensor_data.get("communication_status", "Unknown")
                recharging = self.sensor_data.get("recharging", False)
                ultrasonic = self.sensor_data.get("ultrasonic", {"distance": None, "detection": False})
                ir = self.sensor_data.get("ir", {"reflection": False})
                rfid = self.sensor_data.get("rfid", {"tag_detected": False})
                
                # Format timestamp
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                # Display data with formatting
                self.print_section("Basic Information")
                self.print_info(f"Timestamp: {time_str}")
                self.print_info(f"Position: {Fore.MAGENTA}X={position['x']}, Y={position['y']}")
                
                # Battery with color coding
                battery_color = Fore.GREEN if battery > 70 else Fore.YELLOW if battery > 30 else Fore.RED
                self.print_info(f"Battery: {battery_color}{battery}%{' (Recharging)' if recharging else ''}")
                
                # Communication status
                comm_color = Fore.GREEN if comm_status.lower() == "active" else Fore.RED
                self.print_info(f"Communication: {comm_color}{comm_status}")
                
                # Accelerometer
                self.print_section("Accelerometer")
                self.print_info(f"X: {accel['x']:.2f}, Y: {accel['y']:.2f}, Z: {accel['z']:.2f}")
                
                # Sensors
                self.print_section("Sensors")
                
                # Ultrasonic
                ultrasonic_distance = ultrasonic['distance'] if ultrasonic['distance'] is not None else "N/A"
                ultrasonic_color = Fore.YELLOW if ultrasonic['detection'] else Fore.GREEN
                self.print_info(f"Ultrasonic: {ultrasonic_color}Distance={ultrasonic_distance}, Detection={ultrasonic['detection']}")
                
                # IR
                ir_color = Fore.YELLOW if ir['reflection'] else Fore.GREEN
                self.print_info(f"IR: {ir_color}Reflection={ir['reflection']}")
                
                # RFID
                rfid_color = Fore.YELLOW if rfid['tag_detected'] else Fore.GREEN
                self.print_info(f"RFID: {rfid_color}Tag Detected={rfid['tag_detected']}")
                
                return True
            else:
                self.print_error(f"Failed to get sensor data. Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error getting sensor data: {str(e)}")
            return False
    
    def stop_rover(self):
        """Stop the rover"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("STOPPING ROVER")
        
        url = f"{BASE_URL}/api/rover/stop"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"{data.get('message', 'Rover stopped successfully')}")
                return True
            else:
                self.print_error(f"Failed to stop rover. Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Error stopping rover: {str(e)}")
            return False
    
    def show_movement_history(self):
        """Display the movement history"""
        if not self.movement_history:
            self.print_info("No movement history available.")
            return
        
        self.print_header("MOVEMENT HISTORY")
        
        for i, move in enumerate(self.movement_history, 1):
            direction_color = {
                "forward": Fore.GREEN,
                "backward": Fore.RED,
                "left": Fore.BLUE,
                "right": Fore.MAGENTA
            }.get(move["direction"], Fore.WHITE)
            
            print(f"{i}. {direction_color}{move['direction'].capitalize()}{Style.RESET_ALL} at {move['timestamp']} - {move['result']}")
    
    def run_demo(self):
        """Run a complete demo of all rover functionalities"""
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'RoverX Data Display Demo':^60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")
        
        # Start a session
        if not self.start_session():
            self.print_error("Failed to start session. Exiting.")
            return
        
        # Get initial rover status
        self.get_rover_status()
        
        # Charge the rover
        self.charge_rover()
        
        # Wait a bit for charging
        print(f"\n{Fore.YELLOW}Waiting 2 seconds for charging...")
        time.sleep(2)
        
        # Get rover status after charging
        self.get_rover_status()
        
        # Get sensor data
        self.get_sensor_data()
        
        # Move rover in different directions
        directions = ["forward", "backward", "left", "right"]
        for direction in directions:
            self.move_rover(direction)
            # Get sensor data after each move
            self.get_sensor_data()
        
        # Show movement history
        self.show_movement_history()
        
        # Stop rover
        self.stop_rover()
        
        # Final status check
        self.get_rover_status()
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'Demo Completed':^60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")


if __name__ == "__main__":
    # Create and run the rover data display
    display = RoverDataDisplay()
    display.run_demo()
