#Name:
#Group Number:
#Purpose: 
#Input:
#Output

import sys
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import *
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QGridLayout, QFileDialog)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import pandas as pd

from controller import HelmholtzController

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

#GUI function
class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helmholtz Cage GUI")
        self.resize(800,400)

        self.backend = HelmholtzController()

        #Create a Grid Layout
        layout = QGridLayout()

    #Magnetic Field Measurements GUI Section
        self.label1 = QLabel("Magnetic Field Measurements")
        self.label1.setFont(QFont('Arial', 14))
        layout.addWidget(self.label1, 0, 0)

        #X-axis
        self.label2 = QLabel("X-axis")
        layout.addWidget(self.label2, 1, 0)
        self.result_X = QLineEdit()
        self.result_X.setReadOnly(True)
        layout.addWidget(self.result_X, 1, 1, 1, 1)

        #Y-axis
        self.label3 = QLabel("Y-axis")
        layout.addWidget(self.label3, 2, 0)
        self.result_Y = QLineEdit()
        self.result_Y.setReadOnly(True)
        layout.addWidget(self.result_Y, 2, 1, 1, 1)

        #Z-axis
        self.label4 = QLabel("Z-axis")
        layout.addWidget(self.label4, 3, 0)
        self.result_Z = QLineEdit()
        self.result_Z.setReadOnly(True)
        layout.addWidget(self.result_Z, 3, 1, 1, 1)

    #Calibration GUI Section
        self.label5 = QLabel("Calibration")
        self.label5.setFont(QFont('Arial', 14))
        layout.addWidget(self.label5, 4, 0)
        self.calibrate_box = QLineEdit()
        self.calibrate_box.setReadOnly(True)
        layout.addWidget(self.calibrate_box, 5, 0, 1, 1)

        #Calibration button
        self.calibrate_button = QPushButton("Calibrate Helmholtz Cage")
        self.calibrate_button.clicked.connect(self.calibration)
        layout.addWidget(self.calibrate_button, 5, 1, 1, 1)

    #Set Static Values
        self.label6 = QLabel("Static Testing")
        self.label6.setFont(QFont('Arial', 14))
        layout.addWidget(self.label6, 6, 0)

        #X-axis
        self.label7 = QLabel("X-axis")
        layout.addWidget(self.label7, 7, 0)
        self.entry1 = QLineEdit()
        layout.addWidget(self.entry1, 7, 1)

        #Y-axis
        self.label8 = QLabel("Y-axis")
        layout.addWidget(self.label8, 8, 0)
        self.entry2 = QLineEdit()
        layout.addWidget(self.entry2, 8, 1)

        #Z-axis
        self.label9 = QLabel("Z-axis")
        layout.addWidget(self.label9, 9, 0)
        self.entry3 = QLineEdit()
        layout.addWidget(self.entry3, 9, 1)

        #Submit Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.set_coils)
        layout.addWidget(self.submit_button, 10, 1, 1, 1)

        self.static_box = QLineEdit()
        self.static_box.setReadOnly(True)
        layout.addWidget(self.static_box, 10, 0, 1, 1)

    #Dynamic Testing
        self.label10 = QLabel("Dynamic Testing")
        self.label10.setFont(QFont('Arial', 14))
        layout.addWidget(self.label10, 11, 0)

        self.upload_file = QPushButton("Upload File")
        self.upload_file.clicked.connect(self.upload)
        layout.addWidget(self.upload_file, 12, 0, 1, 1)

        self.submit_file = QPushButton("Submit")
        self.submit_file.clicked.connect(self.file_open)
        layout.addWidget(self.submit_file, 12, 1, 1, 1)

        self.upload_box = QLineEdit()
        self.upload_box.setReadOnly(True)
        layout.addWidget(self.upload_box, 12, 2, 1, 1)

    # MCU box to show connection
        self.mcu_box = QLineEdit()
        self.mcu_box.setReadOnly(True)
        layout.addWidget(self.mcu_box, 0, 2, 1, 1)

    #MATLAB GUI
        self.label11 = QLabel("MATLAB Plot")
        self.label11.setFont(QFont('Arial', 14))
        layout.addWidget(self.label11, 0, 3)

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas, 1, 3, 10, 10)

    # Check the connection 10 times every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_routine)
        self.timer.start(100)
        

    #Set the layout for the GUI system
        self.setLayout(layout)

# Check the connection of the MCU and reads the coils if connected.
    def update_routine(self):
        mcu_work = self.backend.check_mcu()
        if mcu_work:
            self.read_coils
            self.mcu_box.setText("Connected")
        else:
            self.mcu_box.setText("No Connection")

#Calibration setting that sets up the Helmholtz cage calibration
    def calibration(self):
        self.calibrate_box.clear()
        # Ask backend to run the calibration sequence
        success = self.backend.run_calibration()

        if success:
            self.calibrate_box.setText("Success")
        else:
            self.calibrate_box.setText("Error: Check Connection")

#Read coil values from the MCU
    def read_coils(self):
        # Fetch coil data
        data = self.backend.read_mcu_data()

        self.result_X.setText(str(data["x"]))
        self.result_Y.setText(str(data["y"]))
        self.result_Z.setText(str(data("z")))

#Set coil values for the static test
    def set_coils(self):

        self.static_box.clear()
        try:
            x_num = float(self.entry1.text())
            y_num = float(self.entry2.text())
            z_num = float(self.entry3.text())

            self.backend.send_values(x_num, y_num, z_num)
            self.static_box.setText("Success")
        except ValueError:
            self.static_box.setText("Error: Incorrect Value")

#Opens file explorer to find the file to be opened and stores it
    def upload(self):
        self.upload_box.clear()
        # PyQt5 built in file explorer
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Dynamic Trajectory File", "", "CSV Files (*csv);;Text Files (*txt)")
        if filepath:
            self.upload_box.setText(filepath)

#Opens the file and reads it to send over to MCU
    def file_open(self):
        filepath = self.upload_box.text()
        if filepath:
            self.backend.process_dynamic_file(filepath)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUI()
    window.show()
    sys.exit(app.exec_())
