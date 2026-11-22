# Code for the MCU and GUI system connection

import serial
import time

class HelmholtzController:
    def __init__(self):
        # Initialize serial connection with MCU
        self.is_calibrated = False
        self.mcu = None

        self._rx_buffer = b"" #--------#--------#--------#--------#--------#--------#--------
        self.last_data = {"x": 0.0, "y": 0.0, "z": 0.0} #--------#--------#--------#--------#--------
        self.last_command = None #--------#--------#--------#--------#--------#--------#--------

        try:
            self.mcu = serial.Serial('COM5', baudrate=115200, timeout = 1)
            time.sleep(2)
        except serial.SerialException as e:
            print("Initial connection failed.")

    # Function that check the MCU connection
    def check_mcu(self):
        if self.mcu and self.mcu.is_open:
            return True
        return False
#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------
    # Reads and stores the MCU coil values from the serial port
    def read_mcu_data(self):
        if not self.mcu or not self.mcu.is_open:
            return self.last_data.copy()

        try:
            available = self.mcu.in_waiting

            if available:
                chunk = self.mcu.read(available)
                self._rx_buffer += chunk

        except (serial.SerialException, OSError) as e:
            print(f"MCU read failed: {e}")
            return self.last_data.copy()

        while b"\n" in self._rx_buffer:
            raw_line, self._rx_buffer = self._rx_buffer.split(b"\n", 1)

            try:
                line = raw_line.decode("ascii").strip()

                if line.startswith("CMD:"):
                    fields = line[4:].split(",")

                    if len(fields) != 4:
                        raise ValueError("CMD requires four values")

                    b_des, i_cmd, duty1, duty2 = map(float, fields)

                    self.last_command = {
                        "b_des_uT": b_des,
                        "i_cmd_A": i_cmd,
                        "duty1": duty1,
                        "duty2": duty2,
                    }

                    print(
                        f"Received: B_des = {b_des:.3f} uT, "
                        f"I_cmd = {i_cmd:.3f} A, "
                        f"duty1 = {duty1:.3f}, "
                        f"duty2 = {duty2:.3f}"
                    )

                elif line.startswith("DATA:"):
                    fields = line[5:].split(",")

                    if len(fields) != 3:
                        raise ValueError("DATA requires three values")

                    x, y, z = map(float, fields)
                    self.last_data = {"x": x, "y": y, "z": z}

            except (UnicodeDecodeError, ValueError) as e:
                print(f"Invalid MCU message: {raw_line!r}: {e}")

        return self.last_data.copy()
#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------#--------
    # Sends the coil magnetic field to the MCU
    def send_values(self, x, y, z):

        # Logic to send the target fields to the MCU via UART/USB
        if not self.mcu:
            return False

        command = f"SET: {x}, {y}, {z}\n"
        self.mcu.write(command.encode('utf-8'))
        print(f"Transmitted: {command.strip()}")
        return True

    # Grabs a CSV file that the user put and extracts the magnetometer values
    def process_dynamic_file(self, filepath):
        # Open the CSV/txt file, parse the trajectory, and send to MCU
        print(f"Processing dynamic profile from: {filepath}")
        return True