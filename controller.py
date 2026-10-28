# controller code
import serial
import time

class HelmholtzController:
    def __init__(self):
        # Initialize serial connection with MCU
        self.is_calibrated = False
        self.mcu = None

    
        try:
            self.mcu = serial.Serial('COM3', baudrate=115200, timeout = 1)
            time.sleep(2)
        except serial.SerialException as e:
            print("Initial connection failed.")

    def check_mcu(self):
        if self.mcu and self.mcu.is_open:
            return True
        return False

    def run_calibration(self):
        if not self.mcu:
            return False

        # Send a message to the MCU
        self.mcu.write(b"CALIBRATE\n")

        # Returns true if successful, False if failed
        response = self.mcu.readline().decode('utf-8').strip()
        if response == "CAL":
            self.is_calibrated = True
            return True
        return False

    def read_mcu_data(self):
        # Logic to request and parse the X, Y, Z B-field data from the MCU
        if not self.mcu or not self.mcu.in_waiting:
            x=0
            y=0
            z=0

        try:
            raw_data = self.mcu.readline().decode('utf-8').strip()
            if raw_data.startswith("DATA:"):
                values = raw_data.replace("DATA:", "").split(",")

                return {
                    "x": float(values[0]),
                    "y": float(values[1]),
                    "z": float(values[2])
                }
        except (ValueError, IndexError) as e:
            print(f"Error parsing MCU data: {e}")

        # Returning dummy data for now
        return {"x": 0, "y": 0, "z": 0}

    def send_values(self, x, y, z):
        # Logic to send the target fields to the MCU via UART/USB
        if not self.mcu:
            return False

        command = f"SET: {x}, {y}, {z}\n"
        self.mcu.write(command.encode('utf-8'))
        print(f"Transmitted: {command.strip()}")
        return True

    def process_dynamic_file(self, filepath):
        # Open the CSV/txt file, parse the trajectory, and send to MCU
        print(f"Processing dynamic profile from: {filepath}")
        return True