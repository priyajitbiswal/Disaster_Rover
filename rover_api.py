import requests
import time
from config import SESSION_ID

class RoverAPI:
    def __init__(self, session_id=None):
        self.session_id = session_id if session_id else SESSION_ID
        self.base_url = 'https://roverdata2-production.up.railway.app/api/rover'
        self.endpoints = {
            'status': f"{self.base_url}/status",
            'sensor-data': f"{self.base_url}/sensor-data",
            'move': f"{self.base_url}/move",
            'stop': f"{self.base_url}/stop"
        }
        self.last_battery = None
        
    def get_params(self):
        return {'session_id': self.session_id}
    
    def get_rover_status(self):
        """Get both status and sensor data from the rover"""
        try:
            status_response = requests.get(self.endpoints['status'], params=self.get_params())
            sensor_response = requests.get(self.endpoints['sensor-data'], params=self.get_params())
            
            if status_response.status_code == 200 and sensor_response.status_code == 200:
                try:
                    status_data = status_response.json()
                    sensor_data = sensor_response.json()
                    
                    if 'error' in status_data:
                        print(f"\nAPI Error: {status_data['error']}")
                        return None
                        
                    if 'error' in sensor_data:
                        print(f"\nAPI Error: {sensor_data['error']}")
                        return None
                    
                    # Track battery changes
                    current_battery = status_data.get('battery')
                    if self.last_battery is not None and current_battery != self.last_battery:
                        print(f"Battery changed: {self.last_battery} -> {current_battery}")
                    self.last_battery = current_battery
                    
                    return {
                        'status': status_data.get('status'),
                        'battery': current_battery,
                        'coordinates': status_data.get('coordinates'),
                        'sensor_data': {
                            'timestamp': sensor_data.get('timestamp'),
                            'accelerometer': sensor_data.get('accelerometer'),
                            'communication_status': sensor_data.get('communication_status'),
                            'ultrasonic': sensor_data.get('ultrasonic'),
                            'ir': sensor_data.get('ir'),
                            'rfid': sensor_data.get('rfid')
                        }
                    }
                except Exception as e:
                    print(f"Error parsing JSON response: {e}")
                    return None
            else:
                print(f"API Error - Status: {status_response.status_code}, Sensor: {sensor_response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching rover data: {e}")
            return None
            
    def send_move_command(self, direction):
        """Send movement command to the API"""
        try:
            # Convert direction to lowercase and validate
            direction = direction.lower()
            if direction not in ['forward', 'backward', 'left', 'right']:
                print(f"Invalid direction: {direction}")
                return None

            # Send command with direction in query parameters
            params = self.get_params()
            params['direction'] = direction
            
            response = requests.post(self.endpoints['move'], params=params)
            
            if response.status_code == 200:
                response_data = response.json()
                if 'error' in response_data:
                    print(f"\nAPI Error: {response_data['error']}")
                    return None
                print(f"Move command '{direction}' sent successfully")
                return response_data
            else:
                print(f"Move command failed with status code: {response.status_code}")
                if response.text:
                    print(f"Error message: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error sending move command: {e}")
            return None
            
    def send_stop_command(self):
        """Send stop command to the API"""
        try:
            response = requests.post(self.endpoints['stop'], params=self.get_params())
            
            if response.status_code == 200:
                response_data = response.json()
                if 'error' in response_data:
                    print(f"\nAPI Error: {response_data['error']}")
                    return None
                print("Stop command sent successfully")
                return response_data
            else:
                print(f"Stop command failed with status code: {response.status_code}")
                if response.text:
                    print(f"Error message: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error sending stop command: {e}")
            return None
