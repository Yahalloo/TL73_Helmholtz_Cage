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

        time_passed = (current_time - self.start_time).total_seconds()
