import requests
import time
import json

# Base URL for the API
BASE_URL = "https://roverdata2-production.up.railway.app"

def print_response(response):
    """Print the response in a formatted way"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print("-" * 50)

# 1. Start a session
def start_session():
    url = f"{BASE_URL}/api/session/start"
    print(f"\nStarting a new session: POST {url}")
    response = requests.post(url)
    print_response(response)
    
    if response.status_code == 200:
        return response.json().get("session_id")
    return None

# 2. Charge rover
def charge_rover(session_id):
    url = f"{BASE_URL}/api/rover/charge"
    params = {"session_id": session_id}
    print(f"\nCharging rover: POST {url}")
    print(f"Parameters: {params}")
    response = requests.post(url, params=params)
    print_response(response)

# 3. Get rover status
def get_rover_status(session_id):
    url = f"{BASE_URL}/api/rover/status"
    params = {"session_id": session_id}
    print(f"\nGetting rover status: GET {url}")
    print(f"Parameters: {params}")
    response = requests.get(url, params=params)
    print_response(response)

# 4. Move rover
def move_rover(session_id, direction):
    url = f"{BASE_URL}/api/rover/move"
    params = {"session_id": session_id, "direction": direction}
    print(f"\nMoving rover {direction}: POST {url}")
    print(f"Parameters: {params}")
    response = requests.post(url, params=params)
    print_response(response)

# 5. Get sensor data
def get_sensor_data(session_id):
    url = f"{BASE_URL}/api/rover/sensor-data"
    params = {"session_id": session_id}
    print(f"\nGetting sensor data: GET {url}")
    print(f"Parameters: {params}")
    response = requests.get(url, params=params)
    print_response(response)

# 6. Stop rover
def stop_rover(session_id):
    url = f"{BASE_URL}/api/rover/stop"
    params = {"session_id": session_id}
    print(f"\nStopping rover: POST {url}")
    print(f"Parameters: {params}")
    response = requests.post(url, params=params)
    print_response(response)

def main():
    print("Testing RoverX API...")
    
    # Start a session and get session ID
    session_id = start_session()
    
    if not session_id:
        print("Failed to get session ID. Exiting.")
        return
    
    print(f"\n>>> Session ID: {session_id} <<<\n")
    
    # Test all rover functionalities
    get_rover_status(session_id)
    
    # Charge the rover
    charge_rover(session_id)
    
    # Wait a bit for charging
    print("\nWaiting 2 seconds for charging...")
    time.sleep(2)
    
    # Check status after charging
    get_rover_status(session_id)
    
    # Get sensor data
    get_sensor_data(session_id)
    
    # Move rover in different directions
    directions = ["forward", "backward", "left", "right"]
    for direction in directions:
        move_rover(session_id, direction)
        # Get sensor data after each move
        get_sensor_data(session_id)
    
    # Stop rover
    stop_rover(session_id)
    
    # Final status check
    get_rover_status(session_id)

if __name__ == "__main__":
    main()
