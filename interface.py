#!/usr/bin/python3

import os
import io
import time
import logging
import socketserver
import threading
from http import server
import subprocess

import json

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Import the controllers
from controls import MotorController, LightController, CameraController

# Create an instance of MotorController
motor_controller = MotorController()
light_controller = LightController()

# Get all the relevant numbers from controls
# ESC
MIN_SPEED = motor_controller.MIN_SPEED
MAX_SPEED = motor_controller.MAX_SPEED
# Servo
ZERO_ANGLE = motor_controller.ZERO_ANGLE 
STEERING_STEP = motor_controller.STEERING_STEP
MAX_ANGLE = motor_controller.MAX_ANGLE
MIN_ANGLE = motor_controller.MIN_ANGLE

# Increments which control the acceleration
ACCELERATION = config["ACCELERATION"]
DECELERATION = config["DECELERATION"]

# Streamin settings
VIDEO_RESOLUTION_X = config["VIDEO_RESOLUTION_X"]
VIDEO_RESOLUTION_Y = config["VIDEO_RESOLUTION_Y"]
VIDEO_QUEUE = config["VIDEO_QUEUE"]
VIDEO_BUFFER = config["VIDEO_BUFFER"]

# Video save folder
VIDEO_DIRECTORY = os.path.join("videos")

# Read the HTML interface from the file index.html
with open("index.html") as page_html:
    PAGE = page_html.read()

# State Variables
current_speed = 0  # Motor speed (0-100%)
current_steering_angle = ZERO_ANGLE  # Steering angle (0 = left, 90 = straight, 180 = right)

# **Updated State Variables**
keysPressed = {
    "ArrowUp": False,
    "ArrowDown": False,
    "ArrowLeft": False,
    "ArrowRight": False
}

# Lock for thread-safe state updates
state_lock = threading.Lock()

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global is_accelerating, is_braking, is_turning_left, is_turning_right
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()

        elif self.path == "/config.html":
            try:
                # Set the path to your HTML file
                with open("config.html", "rb") as config_file:
                    content = config_file.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", len(content))
                    self.end_headers()
                    self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "Configuration page not found.")

        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception as e:
                logging.warning(
                    "Removed streaming client %s: %s", self.client_address, str(e)
                )

        elif self.path == "/videos":
            # List all items in the videos directory
            items = os.listdir(VIDEO_DIRECTORY)
            # Filter only video files (you can adjust the extension as needed)
            videos = [item for item in items if item.endswith(('.mjpeg', '.h264'))]

            # Send JSON response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({'videos': videos}).encode("utf-8"))


        elif self.path.startswith("/videos/"):
            video_file_name = self.path.split("/")[-1]
            video_file_path = os.path.join(VIDEO_DIRECTORY, video_file_name)

            print(f"Requested video file path: {video_file_path}")  # Debugging line

            if os.path.exists(video_file_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename={video_file_name}")
                self.end_headers()

                with open(video_file_path, "rb") as video_file:
                    self.wfile.write(video_file.read())
            else:
                self.send_error(404, "Video not found")

        elif self.path == "/toggle_switch_1":
            # Handle request to toggle the LED
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            # Toggle the PIN_FANALE_1 state
            light_controller.toggle_fanale_1()

        elif self.path == "/toggle_switch_2":
            # Handle request to toggle the LED
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            # Toggle the PIN_FANALE_2 state
            light_controller.toggle_fanale_2()

        elif self.path == "/toggle_switch_3":
            # Handle request to toggle the LED or perform another action
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            # Toggle whatever functionality you intend
            light_controller.toggle_fanale_retro()

        elif self.path.startswith("/button_"):
            # Handle button presses
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            button_number = self.path.split("_")[-1]
            print(f"Button {button_number} pressed")
            # Choose button function
            if button_number == "red":
                for i in range(8):  # Replace 10 with the number of iterations you want
                    light_controller.toggle_fanale_1()
                    light_controller.toggle_fanale_2()
                    time.sleep(0.1)
            elif button_number == "green":
                # Green button is still doing nothing
                pass
            elif button_number == "blue":
                recorder.start_recording()
            elif button_number == "yellow":
                recorder.stop_recording()
                # Need to restart the stream
                picam2.start_recording(MJPEGEncoder(), FileOutput(output))

        elif self.path == "/accelerate":
            with state_lock:
                keysPressed["ArrowUp"] = True  # Set the key state to True
            self.send_response(200)
            self.end_headers()

        elif self.path == "/stop_accelerating":
            with state_lock:
                keysPressed["ArrowUp"] = False  # Set the key state to False
            self.send_response(200)
            self.end_headers()

        elif self.path == "/brake":
            with state_lock:
                keysPressed["ArrowDown"] = True
            self.send_response(200)
            self.end_headers()

        elif self.path == "/release_brake":
            with state_lock:
                keysPressed["ArrowDown"] = False
            self.send_response(200)
            self.end_headers()

        elif self.path == "/steer_left":
            with state_lock:
                keysPressed["ArrowLeft"] = True
            self.send_response(200)
            self.end_headers()

        elif self.path == "/steer_right":
            with state_lock:
                keysPressed["ArrowRight"] = True
            self.send_response(200)
            self.end_headers()

        elif self.path == "/straighten":
            with state_lock:
                keysPressed["ArrowLeft"] = False
                keysPressed["ArrowRight"] = False
            self.send_response(200)
            self.end_headers()

        elif self.path == "/status":
            # Send the current speed and steering angle
            status = {
                'speed': current_speed,
                'steering_angle': current_steering_angle
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode("utf-8"))

    def do_POST(self):
        if self.path == '/save_config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                # Parse the JSON data from the POST request
                config_data = json.loads(post_data)

                # Convert strings to appropriate types
                config_data['ESC_PIN'] = int(config_data['ESC_PIN'])
                config_data['ESC_FREQUENCY'] = int(config_data['ESC_FREQUENCY'])
                config_data['SERVO_PIN'] = int(config_data['SERVO_PIN'])
                config_data['MIN_SPEED'] = int(config_data['MIN_SPEED'])
                config_data['MAX_SPEED'] = int(config_data['MAX_SPEED'])
                config_data['ACCELERATION_FUNCTION'] = config_data['ACCELERATION_FUNCTION']
                config_data['ZERO_ANGLE'] = int(config_data['ZERO_ANGLE'])
                config_data['STEERING_STEP'] = int(config_data['STEERING_STEP'])
                config_data['MAX_ANGLE'] = int(config_data['MAX_ANGLE'])
                config_data['MIN_ANGLE'] = int(config_data['MIN_ANGLE'])
                config_data['PIN_FANALE_1'] = int(config_data['PIN_FANALE_1'])
                config_data['PIN_FANALE_2'] = int(config_data['PIN_FANALE_2'])
                config_data['PIN_FANALE_RETRO'] = int(config_data['PIN_FANALE_RETRO'])
                config_data['ACCELERATION'] = int(config_data['ACCELERATION'])
                config_data['DECELERATION'] = int(config_data['DECELERATION'])
                config_data['VIDEO_BUFFER'] = int(config_data['VIDEO_BUFFER'])

                # Handle boolean values
                config_data['VIDEO_QUEUE'] = config_data['VIDEO_QUEUE'] == 'true'

                # Handle the resolution string for VIDEO_RESOLUTION_X and VIDEO_RESOLUTION_Y
                resolution = config_data['VIDEO_RESOLUTION'].split('x')
                config_data['VIDEO_RESOLUTION_X'] = int(resolution[0])
                config_data['VIDEO_RESOLUTION_Y'] = int(resolution[1])

                # Path to your configuration file
                config_file_path = 'config.json'

                # Check if the config file exists, if not create it
                if not os.path.exists(config_file_path):
                    with open(config_file_path, 'w') as f:
                        json.dump(config_data, f, indent=4)
                else:
                    # Load existing data, update with new data, and save back to file
                    with open(config_file_path, 'r+') as f:
                        data = json.load(f)

                        # Update data with the new config values
                        data.update(config_data)

                        # Move the file pointer to the beginning before writing
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()  # Make sure to truncate any extra content if the new data is smaller

                # Send response back to client indicating success
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': 'Configuration saved successfully!'}
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except Exception as e:
                # Handle error if parsing or file writing fails
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': f'Error: {str(e)}'}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/reload_server':
            try:
                # Run the shell command to restart the server
                subprocess.run(['sudo', 'systemctl', 'restart', 'interface.service'], check=True)
                response = {'message': 'Server reloaded successfully!'}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': f'Error reloading server: {str(e)}'}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Initialize Picamera2
picam2 = Picamera2()

# Configure the camera to minimize latency
picam2.configure(
    picam2.create_video_configuration(
        main={"size": (VIDEO_RESOLUTION_X, VIDEO_RESOLUTION_Y)}, queue=VIDEO_QUEUE, buffer_count=VIDEO_BUFFER
    )
)
output = StreamingOutput()
recorder = CameraController(picam2, VIDEO_DIRECTORY)
picam2.start_recording(MJPEGEncoder(), FileOutput(output))


def update_car_state():
    global current_speed, current_steering_angle

    with state_lock:
        # Handle acceleration
        if keysPressed["ArrowUp"]:
            if current_speed < MAX_SPEED:
                current_speed += ACCELERATION  # Gradually increase speed
        elif keysPressed["ArrowDown"]:
            current_speed = 0  # Immediate brake
        else:
            if current_speed > MIN_SPEED:
                current_speed -= DECELERATION  # Gradually decrease speed
            elif current_speed < DECELERATION:
                current_speed = MIN_SPEED # if speed is lower than deceleration, just stop

        # Handle steering
        if keysPressed["ArrowLeft"]:
            current_steering_angle = min(current_steering_angle + STEERING_STEP, MAX_ANGLE)  # Turn left
        elif keysPressed["ArrowRight"]:
            current_steering_angle = max(current_steering_angle - STEERING_STEP, MIN_ANGLE)  # Turn right
        else:
            # Gradually return to straight position
            if current_steering_angle < ZERO_ANGLE:
                current_steering_angle += STEERING_STEP
            elif current_steering_angle > ZERO_ANGLE:
                current_steering_angle -= STEERING_STEP

    # Apply updates to the motors
    motor_controller.set_speed(current_speed)
    motor_controller.steer(current_steering_angle)

# **Update loop remains the same**
def run_update_loop():
    while True:
        update_car_state()
        time.sleep(0.1)  # Update 10 times per second
        print(current_speed, current_steering_angle)

# Start the update loop in a separate thread
threading.Thread(target=run_update_loop, daemon=True).start()

try:
    address = ("", 8000)
    server = StreamingServer(address, StreamingHandler)
    print("Server started at http://0.0.0.0:8000")
    server.serve_forever()
except KeyboardInterrupt:
    print("Shutting down server.")

finally:
    picam2.stop_recording()
    motor_controller.cleanup()
