import time
import os
#from gpiozero import PWMOutputDevice, AngularServo, LED
#from gpiozero.pins.pigpio import PiGPIOFactory

#from picamera2.encoders import MJPEGEncoder, H264Encoder
#from picamera2.outputs import FileOutput

# Set the pin factory to use pigpio
#factory = PiGPIOFactory()

class MotorController:
    def __init__(self):
        # Set up constants
        self.ESC_PIN = 18  # GPIO pin for the ESC signal
        self.SERVO_PIN = 15  # GPIO pin for the servo

        # ESC options
        self.MIN_SPEED = 0
        self.MAX_SPEED = 100

        # Servo options
        self.ZERO_ANGLE = 0
        self.STEERING_STEP = 25 # needs to be multiple of max and min angle
        self.MAX_ANGLE = 50
        self.MIN_ANGLE = -50

        # Set up PWM for ESC using gpiozero
        #self.pwm_esc = PWMOutputDevice(self.ESC_PIN, pin_factory=factory)
        # Set up AngularServo for steering with min/max pulse widths
        #self.servo = AngularServo(self.SERVO_PIN, min_angle=self.MIN_ANGLE, max_angle=self.MAX_ANGLE, pin_factory=factory)

        # Start PWM signals
        self.set_speed(0)  # ESC starts at 0% speed
        self.steer(self.ZERO_ANGLE)  # Servo starts at zero angle

    def calibrate_esc(self):
        """Calibrate ESC to recognize throttle range."""
        pass

    def set_speed(self, speed):
        """Set the speed of the brushless motor (0-100%)."""
        pass

    def steer(self, angle):
        """Set the steering angle for the servo motor."""
        pass

    def cleanup(self):
        """Clean up and stop PWM signals."""
        pass


class LightController:
    def __init__(self):
        # Define PINs
        self.PIN_FANALE_1 = 17
        self.PIN_FANALE_2 = 27
        self.PIN_FANALE_RETRO = 22  
        pass

        # Set up LEDs using gpiozero
        #self.fanale_1 = LED(self.PIN_FANALE_1, pin_factory=factory)
        #self.fanale_2 = LED(self.PIN_FANALE_2, pin_factory=factory)
        #self.fanale_retro = LED(self.PIN_FANALE_RETRO, pin_factory=factory)

    def toggle_fanale_1(self):
        """Toggle the first light (fanale_1) on or off."""
        pass

    def toggle_fanale_2(self):
        """Toggle the second light (fanale_2) on or off."""
        pass

    def toggle_fanale_retro(self):
        """Toggle the rear light (fanale_retro) on or off."""
        pass

class CameraController:
    def __init__(self):
        pass
        #self.camera = camera
        #self.recording = False
        #self.output_directory = output_directory
        #os.makedirs(self.output_directory, exist_ok=True)
        #self.video_path = None  # To hold the path of the current video

    def start_recording(self):
        pass

    def stop_recording(self):
        pass

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
