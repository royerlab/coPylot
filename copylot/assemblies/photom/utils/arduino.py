import serial
import time
from tqdm import tqdm

"""
quick and dirty class to control the Arduino.

The arduino currently parses the following commands:
- U,duty_cycle,frequency,duration: Update the PWM settings
- S: Start the PWM
"""


class ArduinoPWM:
    def __init__(self, serial_port, baud_rate):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.ser = None
        self.connect()

    def __del__(self):
        self.close()

    def connect(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate)
            time.sleep(2)  # Wait for connection to establish
        except serial.SerialException as e:
            print(f"Error: {e}")

    def close(self):
        if self.ser:
            self.ser.close()
            print("Serial connection closed.")

    def send_command(self, command):
        print(f"Sending command: {command}")
        self.ser.write((command + '\n').encode())
        time.sleep(1)  # Wait for Arduino to process the command
        while self.ser.in_waiting:
            print(self.ser.readline().decode().strip())

    def set_pwm(self, duty_cycle, frequency, duration):
        command = f'U,{duty_cycle},{frequency},{duration}'
        self.send_command(command)

    def start(self):
        self.send_command('S')

    def start_timelapse(self, repetitions=1, time_interval_s=5):
        for i in tqdm(
            range(repetitions), desc='Timelapse', unit='repetition', total=repetitions
        ):
            self.start()
            time.sleep(time_interval_s)
