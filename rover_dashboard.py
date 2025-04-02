import requests
import json
import time
import os
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama
init()

# Base URL for the API
BASE_URL = "https://roverdata2-production.up.railway.app"

class RoverDashboard:
    def __init__(self):
        self.session_id = None
        self.last_status = None
        self.last_sensor_data = None
        self.movement_history = []
    
    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * len(text)}{Style.RESET_ALL}")
    
    def print_success(self, text):
        """Print a success message"""
        print(f"{Fore.GREEN}{text}{Style.RESET_ALL}")
    
    def print_warning(self, text):
        """Print a warning message"""
        print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
    
    def print_error(self, text):
        """Print an error message"""
        print(f"{Fore.RED}{text}{Style.RESET_ALL}")
    
    def print_info(self, text):
        """Print an info message"""
        print(f"{Fore.BLUE}{text}{Style.RESET_ALL}")
    
    def start_session(self):
        """Start a new session and get session ID"""
        self.print_header("Starting New Session")
        url = f"{BASE_URL}/api/session/start"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                self.print_success(f"Session started successfully!")
                self.print_info(f"Session ID: {self.session_id}")
                return True
            else:
                self.print_error(f"Failed to start session. Status code: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error starting session: {str(e)}")
            return False
    
    def charge_rover(self):
        """Charge the rover"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("Charging Rover")
        url = f"{BASE_URL}/api/rover/charge"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Charging result: {data.get('message', 'Success')}")
                return True
            else:
                self.print_error(f"Failed to charge rover. Status code: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error charging rover: {str(e)}")
            return False
    
    def get_rover_status(self):
        """Get the rover status"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("Rover Status")
        url = f"{BASE_URL}/api/rover/status"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                self.last_status = response.json()
                status = self.last_status.get("status", "Unknown")
                battery = self.last_status.get("battery", 0)
                coordinates = self.last_status.get("coordinates", [0, 0])
                
                # Display status with color based on battery level
                battery_color = Fore.GREEN if battery > 70 else Fore.YELLOW if battery > 30 else Fore.RED
                
                print(f"Status: {Fore.CYAN}{status}{Style.RESET_ALL}")
                print(f"Battery: {battery_color}{battery}%{Style.RESET_ALL}")
                print(f"Position: {Fore.MAGENTA}X={coordinates[0]}, Y={coordinates[1]}{Style.RESET_ALL}")
                
                return True
            else:
                self.print_error(f"Failed to get rover status. Status code: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error getting rover status: {str(e)}")
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
        
        self.print_header(f"Moving Rover {direction.capitalize()}")
        url = f"{BASE_URL}/api/rover/move"
        params = {"session_id": self.session_id, "direction": direction}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Movement result: {data.get('message', 'Success')}")
                self.movement_history.append({
                    "direction": direction,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "result": data.get('message', 'Success')
                })
                return True
            else:
                self.print_error(f"Failed to move rover. Status code: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error moving rover: {str(e)}")
            return False
    
    def get_sensor_data(self):
        """Get sensor data from the rover"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("Rover Sensor Data")
        url = f"{BASE_URL}/api/rover/sensor-data"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                self.last_sensor_data = response.json()
                
                # Extract data
                timestamp = self.last_sensor_data.get("timestamp", 0)
                position = self.last_sensor_data.get("position", {"x": 0, "y": 0})
                accel = self.last_sensor_data.get("accelerometer", {"x": 0, "y": 0, "z": 0})
                battery = self.last_sensor_data.get("battery_level", 0)
                comm_status = self.last_sensor_data.get("communication_status", "Unknown")
                recharging = self.last_sensor_data.get("recharging", False)
                ultrasonic = self.last_sensor_data.get("ultrasonic", {"distance": None, "detection": False})
                ir = self.last_sensor_data.get("ir", {"reflection": False})
                rfid = self.last_sensor_data.get("rfid", {"tag_detected": False})
                
                # Format timestamp
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                # Display data with formatting
                print(f"Timestamp: {time_str}")
                print(f"Position: {Fore.MAGENTA}X={position['x']}, Y={position['y']}{Style.RESET_ALL}")
                
                # Battery with color coding
                battery_color = Fore.GREEN if battery > 70 else Fore.YELLOW if battery > 30 else Fore.RED
                print(f"Battery: {battery_color}{battery}%{Style.RESET_ALL} {'(Recharging)' if recharging else ''}")
                
                # Communication status
                comm_color = Fore.GREEN if comm_status.lower() == "active" else Fore.RED
                print(f"Communication: {comm_color}{comm_status}{Style.RESET_ALL}")
                
                # Accelerometer
                print(f"\nAccelerometer:")
                print(f"  X: {accel['x']:.2f}, Y: {accel['y']:.2f}, Z: {accel['z']:.2f}")
                
                # Sensors
                print(f"\nSensors:")
                
                # Ultrasonic
                ultrasonic_distance = ultrasonic['distance'] if ultrasonic['distance'] is not None else "N/A"
                ultrasonic_color = Fore.YELLOW if ultrasonic['detection'] else Fore.GREEN
                print(f"  Ultrasonic: {ultrasonic_color}Distance={ultrasonic_distance}, Detection={ultrasonic['detection']}{Style.RESET_ALL}")
                
                # IR
                ir_color = Fore.YELLOW if ir['reflection'] else Fore.GREEN
                print(f"  IR: {ir_color}Reflection={ir['reflection']}{Style.RESET_ALL}")
                
                # RFID
                rfid_color = Fore.YELLOW if rfid['tag_detected'] else Fore.GREEN
                print(f"  RFID: {rfid_color}Tag Detected={rfid['tag_detected']}{Style.RESET_ALL}")
                
                return True
            else:
                self.print_error(f"Failed to get sensor data. Status code: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error getting sensor data: {str(e)}")
            return False
    
    def stop_rover(self):
        """Stop the rover"""
        if not self.session_id:
            self.print_error("No active session. Please start a session first.")
            return False
        
        self.print_header("Stopping Rover")
        url = f"{BASE_URL}/api/rover/stop"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Stop result: {data.get('message', 'Success')}")
                return True
            else:
                self.print_error(f"Failed to stop rover. Status code: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error stopping rover: {str(e)}")
            return False
    
    def show_movement_history(self):
        """Display the movement history"""
        if not self.movement_history:
            self.print_warning("No movement history available.")
            return
        
        self.print_header("Movement History")
        for i, move in enumerate(self.movement_history, 1):
            direction_color = {
                "forward": Fore.GREEN,
                "backward": Fore.RED,
                "left": Fore.BLUE,
                "right": Fore.MAGENTA
            }.get(move["direction"], Fore.WHITE)
            
            print(f"{i}. {direction_color}{move['direction'].capitalize()}{Style.RESET_ALL} at {move['timestamp']} - {move['result']}")
    
    def display_dashboard(self):
        """Display a complete dashboard with all rover information"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'RoverX Dashboard':^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
        
        if not self.session_id:
            self.print_warning("No active session. Please start a session first.")
            return
        
        print(f"{Fore.BLUE}Session ID: {self.session_id}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        
        # Get latest status and sensor data
        self.get_rover_status()
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        self.get_sensor_data()
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        self.show_movement_history()
    
    def interactive_menu(self):
        """Display an interactive menu for controlling the rover"""
        while True:
            self.clear_screen()
            print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}{'RoverX Interactive Control':^60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
            
            if self.session_id:
                print(f"{Fore.BLUE}Active Session: {self.session_id}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}No active session{Style.RESET_ALL}")
            
            print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}1. Start New Session{Style.RESET_ALL}")
            print(f"{Fore.WHITE}2. Get Rover Status{Style.RESET_ALL}")
            print(f"{Fore.WHITE}3. Charge Rover{Style.RESET_ALL}")
            print(f"{Fore.WHITE}4. Move Rover{Style.RESET_ALL}")
            print(f"{Fore.WHITE}5. Get Sensor Data{Style.RESET_ALL}")
            print(f"{Fore.WHITE}6. Stop Rover{Style.RESET_ALL}")
            print(f"{Fore.WHITE}7. Show Movement History{Style.RESET_ALL}")
            print(f"{Fore.WHITE}8. Display Dashboard{Style.RESET_ALL}")
            print(f"{Fore.WHITE}9. Exit{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
            
            choice = input(f"{Fore.GREEN}Enter your choice (1-9): {Style.RESET_ALL}")
            
            if choice == '1':
                self.start_session()
                input("\nPress Enter to continue...")
            
            elif choice == '2':
                self.get_rover_status()
                input("\nPress Enter to continue...")
            
            elif choice == '3':
                self.charge_rover()
                input("\nPress Enter to continue...")
            
            elif choice == '4':
                self.clear_screen()
                self.print_header("Move Rover")
                print(f"{Fore.WHITE}1. Forward{Style.RESET_ALL}")
                print(f"{Fore.WHITE}2. Backward{Style.RESET_ALL}")
                print(f"{Fore.WHITE}3. Left{Style.RESET_ALL}")
                print(f"{Fore.WHITE}4. Right{Style.RESET_ALL}")
                
                move_choice = input(f"{Fore.GREEN}Enter direction (1-4): {Style.RESET_ALL}")
                direction_map = {'1': 'forward', '2': 'backward', '3': 'left', '4': 'right'}
                
                if move_choice in direction_map:
                    self.move_rover(direction_map[move_choice])
                else:
                    self.print_error("Invalid choice")
                
                input("\nPress Enter to continue...")
            
            elif choice == '5':
                self.get_sensor_data()
                input("\nPress Enter to continue...")
            
            elif choice == '6':
                self.stop_rover()
                input("\nPress Enter to continue...")
            
            elif choice == '7':
                self.show_movement_history()
                input("\nPress Enter to continue...")
            
            elif choice == '8':
                self.display_dashboard()
                input("\nPress Enter to continue...")
            
            elif choice == '9':
                self.print_info("Exiting RoverX Dashboard. Goodbye!")
                break
            
            else:
                self.print_error("Invalid choice. Please enter a number between 1 and 9.")
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    # Create a requirements.txt file if it doesn't exist
    if not os.path.exists("requirements.txt"):
        with open("requirements.txt", "w") as f:
            f.write("requests\ncolorama\n")
        print("Created requirements.txt file. Please run 'pip install -r requirements.txt' before running this script.")
    
    # Check if colorama is installed
    try:
        import colorama
    except ImportError:
        print("Colorama is not installed. Please run 'pip install colorama' before running this script.")
        exit(1)
    
    dashboard = RoverDashboard()
    dashboard.interactive_menu()
