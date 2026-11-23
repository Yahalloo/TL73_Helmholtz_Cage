import pandas as pd
from datetime import datetime

# Output file names
MAGNETOMETER_FILE = "mag_data.csv"

class data_collection:
    def __init__(self):
        self.mag_file = MAGNETOMETER_FILE
        self.records = []
        self.start_time = None

    def record_sample(self, data):
        current_time = datetime.now()
        if self.start_time is None:
            self.start_time = current_time

        time_passed = round((current_time - self.start_time).total_seconds(), 3)

        self.records.append({
            "Time Passed": time_passed,
            "mag_x": data["x"],
            "mag_y": data["y"],
            "mag_z": data["z"]
        })

    def save_csv(self, filepath = None):
        if not self.records:
            return False, 0
        target_path = filepath if filepath else self.mag_file
        df = pd.DataFrame(self.records)
        df.to_csv(self.store_file, index = False)
        return True, len(self.records)

    def clear(self):
        self.records.clear()
        self.start_time = None