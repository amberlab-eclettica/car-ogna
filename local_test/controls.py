import time
import os
#from gpiozero import PWMOutputDevice, AngularServo, LED
#from gpiozero.pins.pigpio import PiGPIOFactory

#from picamera2.encoders import MJPEGEncoder, H264Encoder
#from picamera2.outputs import FileOutput
import numpy as np
import json
# Set the pin factory to use pigpio
#factory = PiGPIOFactory()

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

def string_to_function(expression):
    """
    Converts a string representing a mathematical expression into a Python function that takes variables.
    
    Parameters:
    expression (str): The mathematical expression as a string.
    
    Returns:
    function: A function that evaluates the expression for given variables.
    """
    def generated_function(**kwargs):
        # Pass kwargs as the local dictionary for variable substitution
        return eval(expression, {"np": np}, kwargs)
    
    return generated_function

class MotorController:
    def __init__(self):
        # Load configuration values from JSON
        self.ESC_PIN = config["ESC_PIN"]  # GPIO pin for the ESC signal
        self.ESC_FREQUENCY = config["ESC_FREQUENCY"] # Works at 50 Hz
        self.SERVO_PIN = config["SERVO_PIN"]  # GPIO pin for the servo

        # ESC options
        self.MIN_SPEED = config["MIN_SPEED"]
        self.MAX_SPEED = config["MAX_SPEED"]
        self.ACCELERATION_FUNCTION = config["ACCELERATION_FUNCTION"]

        # Servo options
        self.ZERO_ANGLE = config["ZERO_ANGLE"]
        self.STEERING_STEP = config["STEERING_STEP"] # needs to be multiple of max and min angle
        self.MAX_ANGLE = config["MAX_ANGLE"]
        self.MIN_ANGLE = config["MIN_ANGLE"]

        # Set up PWM for ESC using gpiozero
        #self.pwm_esc = PWMOutputDevice(self.ESC_PIN, pin_factory=factory, frequency=self.ESC_FREQUENCY)
        # Set up AngularServo for steering with min/max pulse widths
        #self.servo = AngularServo(self.SERVO_PIN, min_angle=self.MIN_ANGLE, max_angle=self.MAX_ANGLE, pin_factory=factory)

        # Start PWM signals
        #self.set_speed(0)  # ESC starts at 0% speed
        #self.steer(self.ZERO_ANGLE)  # Servo starts at zero angle

    def calibrate_esc(self):
        """Calibrate ESC to recognize throttle range."""
        print("Calibrating ESC...")
        #self.pwm_esc.value = 0.1  # Full throttle (10%)
        time.sleep(2)
        #self.pwm_esc.value = 0.05  # Zero throttle (neutral position)
        time.sleep(2)
        print("Calibration complete.")

    def speed_function(self, x):
        """Define time vs. speed increase function"""
        function = string_to_function(self.ACCELERATION_FUNCTION)
        speed = function(x=x)
        return speed

    def set_speed(self, speed):
        """Set the speed of the brushless motor (0-100%)."""
        print("Speed set to ", self.speed_function(speed))
        #self.pwm_esc.value = 0.05 + (self.speed_function(speed) / 2000)  # the ESC uses a 0.5 - 0.1 scale for PWM

    def steer(self, angle):
        """Set the steering angle for the servo motor."""
        print("Steer set to ", angle)
        #self.servo.angle = angle  # Set the angle for the AngularServo

    def cleanup(self):
        """Clean up and stop PWM signals."""
        print("Cleanup")
        #self.pwm_esc.off()
        #self.servo.detach()


class LightController:
    def __init__(self):
        # Load configuration values from JSON
        self.PIN_FANALE_1 = config["PIN_FANALE_1"]
        self.PIN_FANALE_2 = config["PIN_FANALE_2"]
        self.PIN_FANALE_RETRO = config["PIN_FANALE_RETRO"]

        # Set up LEDs using gpiozero
        #self.fanale_1 = LED(self.PIN_FANALE_1, pin_factory=factory)
        #self.fanale_2 = LED(self.PIN_FANALE_2, pin_factory=factory)
        #self.fanale_retro = LED(self.PIN_FANALE_RETRO, pin_factory=factory)

    def toggle_fanale_1(self):
        """Toggle the first light (fanale_1) on or off."""
        #self.fanale_1.toggle()

    def toggle_fanale_2(self):
        """Toggle the second light (fanale_2) on or off."""
        #self.fanale_2.toggle()

    def toggle_fanale_retro(self):
        """Toggle the rear light (fanale_retro) on or off."""
        #self.fanale_retro.toggle()

class CameraController:
    def __init__(self, camera, output_directory):
        self.camera = camera
        self.recording = False
        self.output_directory = output_directory
        os.makedirs(self.output_directory, exist_ok=True)
        self.video_path = None  # To hold the path of the current video

    def start_recording(self):
        if not self.recording:
            # Create an encoder and path for recording
            encoder = H264Encoder()
            self.video_path = os.path.join(self.output_directory, "video_" + time.strftime("%Y%m%d_%H%M%S") + ".h264")
            self.camera.start_recording(encoder, FileOutput(self.video_path))
            self.recording = True
            print(f"Started recording: {self.video_path}")

    def stop_recording(self):
        if self.recording:
            self.camera.stop_recording()  # Stop only the recording
            self.recording = False
            print("Stopped recording")

if __name__ == "__main__":
    motor_controller = MotorController()
    light_controller = LightController()
    
    try:
        # Example usage
        motor_controller.set_speed(motor_controller.MAX_SPEED/3)  # Move forward at 30% speed
        motor_controller.steer(motor_controller.MAX_ANGLE-10)  # Turn left

        # Toggle lights individually
        light_controller.toggle_fanale_1()  # Toggle fanale_1
        light_controller.toggle_fanale_2()  # Toggle fanale_2
        light_controller.toggle_fanale_retro()  # Toggle fanale_retro

        print('Setting motor to 0.1 and steering left.')
        time.sleep(1)

        motor_controller.steer(0)  # Turn back at 0 degrees
        light_controller.toggle_fanale_1()  # Toggle fanale_1
        light_controller.toggle_fanale_2()  # Toggle fanale_2
        light_controller.toggle_fanale_retro()  # Toggle fanale_retro
        time.sleep(1)
    finally:
        motor_controller.cleanup()  # Ensure cleanup on exit
