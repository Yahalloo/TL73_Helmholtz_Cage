# Code for Phone Magnetometer and GUI Connection

import requests

class Helmholtz_Calibration:
    def __init__(self):

        # Set the variables to 0 as well as determine the magnetic field offset values
        self.phyphox_url = None
        self.is_connected = False
        self.offset = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.raw_field = {"x": 0.0, "y": 0.0, "z": 0.0}

    # This function grabs the phyphox url from the GUI and establishes a connection with the URL
    def set_phyphox_url(self, url_text):

        # Cleans the url text to set it as a link
        clean_url = url_text.strip().rstrip('/')
        if not clean_url.startswith("https://") and not clean_url.startswith("http://"):
            clean_url = "http://" + clean_url

        self.phyphox_url = f"{clean_url}/get?mag_x&mag_y&mag_z&magX&magY&magZ"

        # Establishes a connection with the URL
        try:
            requests.get(f"{clean_url}/control?cmd=start", timeout=0.5)
            r = requests.get(self.phyphox_url, timeout=0.5)
            if r.status_code == 200:
                print("Connected")
                self.is_connected = True
                return True

        except Exception as e:
            print(f"Connection test failed: {e}")

        self.is_connected = False
        return False

    # Grabs the magnetometer data from the phyphox URL
    def read_mag_data(self):

        # Checks the connection with the phyphox URL
        if not self.is_connected or not self.phyphox_url:
            return {"x": 0.0, "y": 0.0, "z": 0.0}

        # Stores the magnetometer values into variables
        try:
            r = requests.get(self.phyphox_url, timeout=0.08).json()
            buffers = r.get("buffer", {})
            if "mag_x" in buffers:
                bx_list = buffers["mag_x"]["buffer"]
                by_list = buffers["mag_y"]["buffer"]
                bz_list = buffers["mag_z"]["buffer"]
            elif "magX" in buffers:
                bx_list = buffers["magX"]["buffer"]
                by_list = buffers["magY"]["buffer"]
                bz_list = buffers["magZ"]["buffer"]
            else:
                print(f"Available buffer keys: {list(buffers.keys())}")
                return self.raw_field

            if bx_list and by_list and bz_list:
                bx, by, bz = bx_list[-1], by_list[-1], bz_list[-1]
                if bx is not None and by is not None and bz is not None:
                    self.raw_field = {"x": float(bx), "y": float(by), "z": float(bz)}
        except Exception as e:
            print(f"Error reading phyphox: {e}")

        return {
            "x": round(self.raw_field["x"] - self.offset["x"], 2),
            "y": round(self.raw_field["y"] - self.offset["y"], 2),
            "z": round(self.raw_field["z"] - self.offset["z"], 2)
        }