import pandas as pd
from datetime import datetime

class data_collection:
    def __init__(self):
        self.file_found = 0
        self.records = []
        self.start_time = None

    def record_sample(self, data):
        current_time = datetime.now()
        if self.start_time is None:
            self.start_time = current_time

        time_passed = round((current_time - self.start_time).total_seconds(), 3)
        timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        self.records.append({
            "Timestamp": timestamp_str,
            "Time Passed": time_passed,
            "mag_x": data["x"],
            "mag_y": data["y"],
            "mag_z": data["z"]
        })

    def save_csv(self, filename):
        self.store_file = filename
        if not self.records:
            return False, 0
        df = pd.DataFrame(self.records)
        df.to_csv(self.store_file, index = False)
        return True, len(self.records)