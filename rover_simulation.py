import requests
import json
import time
from datetime import datetime
import random
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Base URL for the API
BASE_URL = "https://roverdata2-production.up.railway.app"

class RoverSimulation:
    def __init__(self):
        self.session_id = None
        self.battery = 0
        self.position = {"x": 0, "y": 0}
        self.status = "idle"
        self.last_direction = None
        self.movement_count = 0
        
        # Battery thresholds
        self.RECHARGE_START = 5  # Start recharging at 5%
        self.RECHARGE_STOP = 80  # Stop recharging at 80%
        self.COMMS_LOSS = 10     # Communication lost below 10%
        
        # Movement directions
        self.directions = ["forward", "backward", "left", "right"]
    
    def print_status(self):
        """Print the current rover status with formatting"""
        # Battery color based on level
        if self.battery >= 50:
            battery_color = Fore.GREEN
        elif self.battery >= 20:
            battery_color = Fore.YELLOW
        else:
            battery_color = Fore.RED
        
        # Status color and text
        if "moving" in self.status.lower() or self.last_direction:
            status_text = f"Moving {self.last_direction}" if self.last_direction else self.status
            status_color = Fore.MAGENTA
        else:
            status_text = self.status
            status_color = Fore.CYAN
        
        # Print status line
        print(f"{Fore.WHITE}[{datetime.now().strftime('%H:%M:%S')}] "
              f"Status: {status_color}{status_text:<15}{Style.RESET_ALL} | "
              f"Battery: {battery_color}{self.battery:>3}%{Style.RESET_ALL} | "
              f"Position: {Fore.BLUE}X={self.position['x']:<3}, Y={self.position['y']:<3}{Style.RESET_ALL}")
    
    def start_session(self):
        """Start a new session and get session ID"""
        print(f"{Fore.CYAN}{Style.BRIGHT}Starting new rover session...{Style.RESET_ALL}")
        
        url = f"{BASE_URL}/api/session/start"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                print(f"{Fore.GREEN}Session started successfully!{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Session ID: {Fore.YELLOW}{self.session_id}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}Failed to start session. Status code: {response.status_code}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Error starting session: {str(e)}{Style.RESET_ALL}")
            return False
    
    def update_status(self):
        """Update rover status from the API"""
        if not self.session_id:
            print(f"{Fore.RED}No active session.{Style.RESET_ALL}")
            return False
        
        # Get rover status
        url = f"{BASE_URL}/api/rover/status"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.status = data.get("status", "Unknown")
                self.battery = data.get("battery", 0)
                coords = data.get("coordinates", [0, 0])
                self.position = {"x": coords[0], "y": coords[1]}
                return True
            else:
                print(f"{Fore.RED}Failed to get rover status. Status code: {response.status_code}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Error getting rover status: {str(e)}{Style.RESET_ALL}")
            return False
    
    def update_sensor_data(self):
        """Update sensor data from the API"""
        if not self.session_id:
            return False
        
        url = f"{BASE_URL}/api/rover/sensor-data"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                # Update position and battery from sensor data
                pos = data.get("position", {"x": 0, "y": 0})
                self.position = {"x": pos["x"], "y": pos["y"]}
                self.battery = data.get("battery_level", 0)
                
                return True
            else:
                return False
        except Exception:
            return False
    
    def charge_rover(self):
        """Charge the rover"""
        if not self.session_id:
            print(f"{Fore.RED}No active session.{Style.RESET_ALL}")
            return False
        
        url = f"{BASE_URL}/api/rover/charge"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print(f"{Fore.GREEN}Started charging rover{Style.RESET_ALL}")
                self.status = "Charging"
                self.last_direction = None
                return True
            else:
                print(f"{Fore.RED}Failed to charge rover. Status code: {response.status_code}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Error charging rover: {str(e)}{Style.RESET_ALL}")
            return False
    
    def move_rover(self, direction=None):
        """Move the rover in a specified or random direction"""
        if not self.session_id:
            print(f"{Fore.RED}No active session.{Style.RESET_ALL}")
            return False
        
        # If charging and battery not high enough, don't move
        if self.status.lower() == "charging" and self.battery < self.RECHARGE_STOP:
            return False
        
        # Choose a random direction if none specified
        if direction is None:
            direction = random.choice(self.directions)
        
        url = f"{BASE_URL}/api/rover/move"
        params = {"session_id": self.session_id, "direction": direction}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                self.movement_count += 1
                self.last_direction = direction
                self.status = f"Moving {direction}"
                print(f"{Fore.BLUE}Moving rover {direction}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}Failed to move rover. Status code: {response.status_code}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Error moving rover: {str(e)}{Style.RESET_ALL}")
            return False
    
    def stop_rover(self):
        """Stop the rover"""
        if not self.session_id:
            print(f"{Fore.RED}No active session.{Style.RESET_ALL}")
            return False
        
        url = f"{BASE_URL}/api/rover/stop"
        params = {"session_id": self.session_id}
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print(f"{Fore.GREEN}Rover stopped{Style.RESET_ALL}")
                self.status = "Idle"
                self.last_direction = None
                return True
            else:
                print(f"{Fore.RED}Failed to stop rover. Status code: {response.status_code}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Error stopping rover: {str(e)}{Style.RESET_ALL}")
            return False
    
    def run_simulation(self, max_iterations=100):
        """Run the rover simulation for a specified number of iterations"""
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'RoverX Simulation':^60}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 60}")
        
        # Start a session
        if not self.start_session():
            print(f"{Fore.RED}Failed to start session. Exiting.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Starting rover simulation...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Battery rules:{Style.RESET_ALL}")
        print(f"  - Recharging starts at {self.RECHARGE_START}% and stops at {self.RECHARGE_STOP}%")
        print(f"  - Rover cannot move while recharging")
        print(f"  - Simulation will run for {max_iterations} iterations\n")
        
        # Initial status update
        self.update_status()
        self.print_status()
        
        try:
            for i in range(max_iterations):
                # Update rover status
                self.update_sensor_data()
                
                # Print current status
                self.print_status()
                
                # Handle battery management
                if self.battery <= self.RECHARGE_START and self.status.lower() != "charging":
                    # Battery critically low, start charging
                    print(f"{Fore.YELLOW}Battery critically low ({self.battery}%). Starting recharge...{Style.RESET_ALL}")
                    self.charge_rover()
                    time.sleep(1)  # Give time for charging to start
                
                # If charging and battery is above threshold, stop charging by moving
                if self.status.lower() == "charging" and self.battery >= self.RECHARGE_STOP:
                    print(f"{Fore.GREEN}Battery charged to {self.battery}%. Resuming operation.{Style.RESET_ALL}")
                    # Move to indicate we're no longer charging
                    self.move_rover()
                
                # If not charging and battery is above minimum, move randomly
                if self.status.lower() != "charging" and self.battery > self.RECHARGE_START:
                    # Move in a random direction
                    self.move_rover()
                
                # Sleep to simulate real-time operation
                time.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Simulation stopped by user.{Style.RESET_ALL}")
        finally:
            # Stop the rover before exiting
            self.stop_rover()
            
            # Final status
            self.update_status()
            self.print_status()
            print(f"\n{Fore.CYAN}Simulation completed with {self.movement_count} movements.{Style.RESET_ALL}")


if __name__ == "__main__":
    simulation = RoverSimulation()
    simulation.run_simulation(30)  # Run for 30 iterations
