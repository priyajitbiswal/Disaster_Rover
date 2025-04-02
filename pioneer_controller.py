from controller import Robot, Motor, Keyboard
from rover_api import RoverAPI
import time

class PioneerController:
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
        
    def print_menu(self):
        """Print the control menu to the console"""
        print("\n=== Pioneer 3-AT Controls ===")
        print("W - Move Forward")
        print("S - Move Backward")
        print("A - Turn Left")
        print("D - Turn Right")
        print("X - Stop")
        print("P - Print Status")
        print("Q - Quit")
        print("========================")
        
    def set_speeds(self, left_speed, right_speed):
        """Set speeds for left and right side motors"""
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
        speed = self.MAX_SPEED * 0.5  # Use 50% of max speed for safety
        
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
            
    def stop(self):
        """Stop all motors"""
        self.set_speeds(0, 0)
        self.current_direction = None
        
    def print_status(self):
        """Print current rover status"""
        status = self.api.get_rover_status()
        if status:
            print(f"\nRover Status:")
            print(f"Battery: {status['battery']}%")
            print(f"Position: {status['coordinates']}")
            print(f"Status: {status['status']}")
        
    def run(self):
        """Main control loop"""
        print("Pioneer 3-AT controller starting...")
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
    controller = PioneerController()
    controller.run()
