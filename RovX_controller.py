from controller import Robot, Motor, Keyboard
from rover_api import RoverAPI
import time
import math

class RovXController:
    def __init__(self):
        # Initialize the Webots robot
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Initialize keyboard
        self.keyboard = self.robot.getKeyboard()
        self.keyboard.enable(self.timestep)
        
        # Initialize motors
        self.left_front = self.robot.getDevice('front left wheel')
        self.right_front = self.robot.getDevice('front right wheel')
        self.left_back = self.robot.getDevice('back left wheel')
        self.right_back = self.robot.getDevice('back right wheel')
        
        # Set motors to velocity control mode
        self.left_front.setPosition(float('inf'))
        self.right_front.setPosition(float('inf'))
        self.left_back.setPosition(float('inf'))
        self.right_back.setPosition(float('inf'))
        
        # Initialize velocities to 0
        self.left_front.setVelocity(0)
        self.right_front.setVelocity(0)
        self.left_back.setVelocity(0)
        self.right_back.setVelocity(0)
        
        # Initialize the API
        self.api = RoverAPI()
        
        # Motor speed constants
        self.MAX_SPEED = 6.28  # Maximum motor speed in rad/s
        self.current_direction = None
        
        # Position tracking
        self.position = [0, 0]  # [x, z]
        self.battery = 100
        self.last_update = time.time()
        
        # Battery and recharge settings
        self.is_recharging = False
        self.has_communication = True
        self.RECHARGE_START = 5  # Start recharge at 5%
        self.RECHARGE_STOP = 80  # Stop recharge at 80%
        self.RECHARGE_RATE = 10  # 10% per second
        self.DISCHARGE_RATE_MOVING = 2  # 2% per second when moving
        self.DISCHARGE_RATE_IDLE = 0.5  # 0.5% per second when idle
        
    def print_menu(self):
        """Print the control menu to the console"""
        print("\n=== RovX Controls ===")
        print("W - Move Forward")
        print("S - Move Backward")
        print("A - Turn Left")
        print("D - Turn Right")
        print("X - Stop")
        print("P - Print Status")
        print("H - Show this Menu")
        print("Q - Quit")
        print("========================")
        
    def set_speeds(self, left_speed, right_speed):
        """Set speeds for left and right side motors"""
        # Don't move if battery is dead or recharging
        if self.battery <= 0 or self.is_recharging:
            left_speed = right_speed = 0
            if self.battery <= 0:
                print("Cannot move: Battery depleted!")
            elif self.is_recharging:
                print("Cannot move: Recharging in progress!")
        
        # Ensure speeds are within bounds
        left_speed = max(min(left_speed, self.MAX_SPEED), -self.MAX_SPEED)
        right_speed = max(min(right_speed, self.MAX_SPEED), -self.MAX_SPEED)
        
        # Set motor velocities
        self.left_front.setVelocity(left_speed)
        self.left_back.setVelocity(left_speed)
        self.right_front.setVelocity(right_speed)
        self.right_back.setVelocity(right_speed)
        
    def move(self, direction):
        """Move the robot in the specified direction"""
        if direction == self.current_direction:
            return  # Already moving in this direction
            
        self.current_direction = direction
        speed = self.MAX_SPEED * 0.3  # Use 30% of max speed for better control
        
        if direction == 'forward':
            self.set_speeds(speed, speed)
        elif direction == 'backward':
            self.set_speeds(-speed, -speed)
        elif direction == 'left':
            self.set_speeds(-speed, speed)
        elif direction == 'right':
            self.set_speeds(speed, -speed)
        elif direction == 'stop':
            self.stop()
            
        # Update position and battery
        self.update_status(direction)
            
    def stop(self):
        """Stop all motors"""
        self.set_speeds(0, 0)
        self.current_direction = None
        
    def update_battery(self, time_delta):
        """Update battery level and handle recharging"""
        if self.is_recharging:
            # Charge battery
            self.battery = min(self.RECHARGE_STOP, self.battery + (self.RECHARGE_RATE * time_delta))
            if self.battery >= self.RECHARGE_STOP:
                print("\nRecharge complete!")
                self.is_recharging = False
        else:
            # Discharge battery
            discharge_rate = self.DISCHARGE_RATE_MOVING if self.current_direction else self.DISCHARGE_RATE_IDLE
            self.battery = max(0, self.battery - (discharge_rate * time_delta))
            
            # Start recharging if battery is low
            if self.battery <= self.RECHARGE_START:
                print("\nBattery critical! Starting recharge...")
                self.is_recharging = True
                self.stop()  # Stop movement when recharging starts
        
    def update_status(self, direction):
        """Update position and battery based on movement"""
        current_time = time.time()
        time_delta = current_time - self.last_update
        
        # Update battery
        self.update_battery(time_delta)
        
        # Update position based on direction
        if not self.is_recharging and self.battery > 0:
            move_speed = 0.5  # Units per second
            if direction == 'forward':
                self.position[1] += move_speed * time_delta
            elif direction == 'backward':
                self.position[1] -= move_speed * time_delta
            elif direction == 'left':
                self.position[0] -= move_speed * time_delta
            elif direction == 'right':
                self.position[0] += move_speed * time_delta
                
        self.last_update = current_time
        
    def print_status(self):
        """Print current rover status"""
        print(f"\nRover Status:")
        print(f"Battery: {self.battery:.1f}%")
        print(f"Position: [{self.position[0]:.1f}, {self.position[1]:.1f}]")
        print(f"Status: {'Recharging' if self.is_recharging else 'Moving ' + self.current_direction if self.current_direction else 'idle'}")
        
    def run(self):
        """Main control loop"""
        print("RovX controller starting...")
        self.print_menu()
        
        while self.robot.step(self.timestep) != -1:
            # Get keyboard input
            key = self.keyboard.getKey()
            
            if key == ord('W'):  # W key
                self.move('forward')
                print("Moving forward")
            elif key == ord('S'):  # S key
                self.move('backward')
                print("Moving backward")
            elif key == ord('A'):  # A key
                self.move('left')
                print("Turning left")
            elif key == ord('D'):  # D key
                self.move('right')
                print("Turning right")
            elif key == ord('X'):  # X key
                self.stop()
                print("Stopped")
            elif key == ord('P'):  # P key
                self.print_status()
            elif key == ord('H'):  # H key
                self.print_menu()
            elif key == ord('Q'):  # Q key
                print("Quitting...")
                break

# Main execution
if __name__ == "__main__":
    controller = RovXController()
    controller.run()
