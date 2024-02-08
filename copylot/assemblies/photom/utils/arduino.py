import serial
import time

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
        self.time.sleep(2)  # Wait for Arduino to process the command
        while self.ser.in_waiting:
            print(self.ser.readline().decode().strip())
