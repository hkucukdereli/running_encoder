import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import QTimer
import serial
import serial.tools.list_ports
import time
from datetime import datetime
import csv

from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import pyqtSignal, pyqtSlot

class ClickableLineEdit(QLineEdit):
    clicked = pyqtSignal()  # Signal to be emitted when the line edit is clicked

    def __init__(self, *args, **kwargs):
        super(ClickableLineEdit, self).__init__(*args, **kwargs)
        self.setCursorPosition(0)  # Set cursor position to start

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selectAll()  # Emit the clicked signal

class SerialApp(QWidget):
    def __init__(self):
        super().__init__()
        self.loadConfig()
        self.initUI()
        self.serial_connection = None
        self.frequency = 20
        self.positions = []
        self.frame_count = 0
        self.csv_file = None
        self.last_timestamp = None
        self.last_subject = ""
        self.last_date = ""

        # Timer for flashing effect
        self.flashingTimer = QTimer(self)
        self.flashingTimer.timeout.connect(self.toggleFlashing)
        self.isFlashingOn = False       

    def loadConfig(self):
        # Load configuration from file
        self.config_file = 'config.json'
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                self.config = json.load(file)
        else:
            self.config = {'last_port': None, 'last_frequency': '20 Hz', 'last_directory': os.getcwd()}

    def toggleFlashing(self):
        if self.isFlashingOn:
            self.connectButton.setStyleSheet("background-color: gray; color: red;")
        else:
            self.connectButton.setStyleSheet("background-color: gray; color: white;")
        self.isFlashingOn = not self.isFlashingOn

    def initUI(self):
        layout = QVBoxLayout()

        # Create and add UI components (rows 1 to 4)...
        # This includes dropdown menus, buttons, input boxes, etc.

        # Row 1: Serial Port Selection and Connect/Disconnect Button
        self.portComboBox = QComboBox()
        self.portComboBox.addItems(self.getAvailableSerialPorts())
        self.portComboBox.currentIndexChanged.connect(self.onPortSelectionChange)
        self.portComboBox.setEditable(True)
        self.portComboBox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.portComboBox.setEditText(self.config.get('last_port', ''))

        self.connectButton = QPushButton('Connect')
        self.connectButton.setStyleSheet("background-color: gray; color: white;")
        self.connectButton.clicked.connect(self.toggleSerialConnection)
        row1 = QHBoxLayout()
        row1.addWidget(self.portComboBox)
        row1.addWidget(self.connectButton)
        layout.addLayout(row1)

        # Row 2: Recording Frequency Input and Start/Stop Button
        # self.freqInput = QLineEdit(self.config.get('last_frequency', '20'))  # Only the numeric value
        # self.freqLabel = QLabel("Hz")  # Label for the Hz suffix
        self.freqInput = ClickableLineEdit(self.config.get('last_frequency', '20'))
        self.freqInput.clicked.connect(self.freqInput.selectAll)
        self.freqLabel = QLabel("Hz")  # Label for the Hz suffix
        self.startStopButton = QPushButton('Start')
        self.updateStartStopButtonStyle(False)  # Initially deactivated
        self.startStopButton.clicked.connect(self.toggleRecording)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Recording Frequency:"))
        row2.addWidget(self.freqInput)
        row2.addWidget(self.freqLabel)  # Add the Hz label next to the input box
        row2.addWidget(self.startStopButton)
        layout.addLayout(row2)


        # Row 3: Browse Box for Data Directory
        # self.dataDirInput = QLineEdit(self.config.get('last_directory', os.getcwd()))
        self.dataDirInput = ClickableLineEdit(self.config.get('last_directory', os.getcwd()))
        self.dataDirInput.clicked.connect(self.dataDirInput.selectAll)
        self.browseButton = QPushButton('Browse')
        self.browseButton.clicked.connect(self.browseDataDirectory)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Data Directory:"))
        row3.addWidget(self.dataDirInput)
        row3.addWidget(self.browseButton)
        layout.addLayout(row3)

        # Row 4: Subject, Date, and Run Input Boxes
        # self.subjectInput = QLineEdit()
        self.subjectInput = ClickableLineEdit()
        self.subjectInput.clicked.connect(self.subjectInput.selectAll)
        # self.dateInput = QLineEdit()
        self.dateInput = ClickableLineEdit()
        self.dateInput.clicked.connect(self.dateInput.selectAll)
        # self.runInput = QLineEdit("001")
        self.runInput = ClickableLineEdit("001")
        self.runInput.clicked.connect(self.runInput.selectAll)
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Subject:"))
        row4.addWidget(self.subjectInput)
        row4.addWidget(QLabel("Date:"))
        row4.addWidget(self.dateInput)
        row4.addWidget(QLabel("Run:"))
        row4.addWidget(self.runInput)
        layout.addLayout(row4)
        self.subjectInput.textChanged.connect(self.onSubjectOrDateChanged)
        self.dateInput.textChanged.connect(self.onSubjectOrDateChanged)

        self.setLayout(layout)

    # Additional methods

    def closeEvent(self, event):
        # Handle closing of the application
        # Update config file, ensure data saving and serial disconnection
        self.updateConfig()
        # Additional cleanup if needed
        event.accept()

    def updateConfig(self):
        # Update configuration file with current settings
        with open(self.config_file, 'w') as file:
            json.dump(self.config, file)

    def getAvailableSerialPorts(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def onPortSelectionChange(self):
        selected_port = self.portComboBox.currentText()
        if selected_port:
            self.config['last_port'] = selected_port

    def disableUIElementsDuringRecording(self, disable):
        # Disable or enable UI elements related to the recording process
        self.portComboBox.setDisabled(disable)  # Disable the serial port dropdown
        self.connectButton.setDisabled(disable)  # Disable the connect/disconnect button
        self.freqInput.setDisabled(disable)  # Disable the frequency input box
        self.dataDirInput.setDisabled(disable)  # Disable the data directory input box
        self.browseButton.setDisabled(disable)  # Disable the browse button
        self.subjectInput.setDisabled(disable)  # Disable the subject input box
        self.dateInput.setDisabled(disable)  # Disable the date input box
        self.runInput.setDisabled(disable)  # Disable the run input box

    def toggleSerialConnection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.serial_connection = None
            self.connectButton.setText('Connect')
            self.connectButton.setStyleSheet("background-color: gray; color: white;")
            self.updateStartStopButtonStyle(False)  # Disable Start button when serial is disconnected
        else:
            try:
                selected_port = self.portComboBox.currentText()
                if not selected_port:
                    QMessageBox.warning(self, "Error", "No serial port is selected. Please select one.")
                    return
                self.serial_connection = serial.Serial(selected_port, 9600)
                self.connectButton.setText('Disconnect')
                self.connectButton.setStyleSheet("background-color: gray; color: red;")
                self.updateStartStopButtonStyle(True)  # Enable Start button when serial is connected
            except serial.SerialException:
                QMessageBox.warning(self, "Error", "Not the right port. Please select another one.")
                self.updateStartStopButtonStyle(False)  # Disable Start button on connection failure

    def toggleRecording(self):
        if self.startStopButton.text() == 'Start':
            # Check for empty fields
            missing_fields = []
            if not self.dataDirInput.text().strip():
                missing_fields.append("Data Directory")
            if not self.subjectInput.text().strip():
                missing_fields.append("Subject")
            if not self.dateInput.text().strip():
                missing_fields.append("Date")
            if not self.runInput.text().strip():
                missing_fields.append("Run")

            if missing_fields:
                # Display error message with missing fields
                QMessageBox.warning(self, "Error", f"Missing {', '.join(missing_fields)}.")
                return  # Do not proceed further
            
            # Extract and validate the recording frequency
            frequency_text = self.freqInput.text()
            try:
                frequency = int(frequency_text)
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.write(f"A {frequency}".encode())
                    time.sleep(0.1)
                    self.serial_connection.write("S".encode())
                    self.prepareCSVFile()
                    self.startDataListening()
                    self.startStopButton.setText('Stop')
                    self.updateStartStopButtonStyle(True)
                    self.disableUIElementsDuringRecording(True)

                    # Start flashing effect for the Disconnect button
                    self.connectButton.setText("Recording...")
                    self.flashingTimer.start(1000)  # Start flashing every 3 seconds
                else:
                    QMessageBox.warning(self, "Error", "Serial port is not connected.")
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid integer for the recording frequency.")
        else:
            # Stop the recording
            self.stopDataListening()
            self.startStopButton.setText('Start')
            self.updateStartStopButtonStyle(True)
            self.disableUIElementsDuringRecording(False)

            # Stop flashing effect and reset Disconnect button
            self.flashingTimer.stop()  # Stop the flashing
            self.connectButton.setText("Disconnect")
            self.connectButton.setStyleSheet("background-color: gray; color: red;")  # Reset to original style

    def prepareCSVFile(self):
        file_path = os.path.join(self.dataDirInput.text(), f"{self.subjectInput.text()}_{self.dateInput.text()}_{self.runInput.text()}.csv")
        self.csv_file = open(file_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Frame', 'Timestamp', 'Timestep', 'Position'])
        self.frame_count = 0
        self.last_timestamp = time.time()

    def recordDataToCSV(self, position):
        current_time = time.time()
        timestep = current_time - self.last_timestamp
        self.last_timestamp = current_time
        self.frame_count += 1
        self.csv_writer.writerow([self.frame_count, datetime.now(), timestep, position])

    def startDataListening(self):
        # Check if the serial connection is open
        if self.serial_connection and self.serial_connection.is_open:
            self.dataTimer = QTimer(self)
            self.dataTimer.timeout.connect(self.readSerialData)
            self.dataTimer.start(10)  # Polling interval in milliseconds

    def stopDataListening(self):
        if hasattr(self, 'dataTimer'):
            self.dataTimer.stop()
            del self.dataTimer
        if self.csv_file:
            self.csv_file.close()
            self.incrementRunNumber()
        elif self.subjectInput.text() and self.dateInput.text():
            self.incrementRunNumber()

    def readSerialData(self):
        if self.serial_connection.in_waiting:
            data = self.serial_connection.readline().decode().strip()
            try:
                position = int(data)  # Assuming data is an integer
                self.recordDataToCSV(position)
            except ValueError:
                pass  # Handle non-integer data or define other behavior as needed

    def incrementRunNumber(self):
        # Read the current run number, increment it, and update the run input box
        try:
            current_run = int(self.runInput.text())
            new_run = current_run + 1
            self.runInput.setText(f"{new_run:03}")  # Format the number as 3 digits (e.g., 002, 003)
        except ValueError:
            # If the current run number is not an integer, reset it to 001
            self.runInput.setText("001")

    def closeEvent(self, event):
        self.stopDataListening()
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.updateConfig()
        super().closeEvent(event)

    def disableUIElements(self, disable):
        # Disable or enable UI elements based on the recording state
        self.portComboBox.setDisabled(disable)
        self.connectButton.setDisabled(disable)
        self.freqInput.setDisabled(disable)
        self.dataDirInput.setDisabled(disable)
        self.browseButton.setDisabled(disable)
        self.subjectInput.setDisabled(disable)
        self.dateInput.setDisabled(disable)
        self.runInput.setDisabled(disable)

    def browseDataDirectory(self):
        # Open a dialog to select a directory. The dialog will start at the current directory path in self.dataDirInput
        directory = QFileDialog.getExistingDirectory(self, "Select Data Directory", self.dataDirInput.text())

        # Check if the user selected a directory
        if directory:
            # Update the data directory input box with the selected directory
            self.dataDirInput.setText(directory)
            # Update the config with the new directory
            self.config['last_directory'] = directory

    def onFrequencyChange(self, text):
        if not text:  # If the input box is empty, do nothing
            return

        try:
            # Attempt to convert the text to an integer
            frequency = int(text)
            self.config['last_frequency'] = str(frequency)  # Update the config with the valid frequency
        except ValueError:
            # If the text is not a valid integer, reset to the last valid frequency
            self.freqInput.blockSignals(True)  # Block signals to prevent recursion
            self.freqInput.setText(self.config.get('last_frequency', '20'))  # Reset to the last valid frequency
            self.freqInput.blockSignals(False)


 
    def updateStartStopButtonStyle(self, enabled):
        if self.startStopButton.text() == 'Start':
            if enabled:
                self.startStopButton.setStyleSheet("background-color: green; color: white;")
                self.startStopButton.setEnabled(True)
            else:
                self.startStopButton.setStyleSheet("background-color: lightgreen; color: lightgray;")
                self.startStopButton.setEnabled(False)
        elif self.startStopButton.text() == 'Stop':
            if enabled:
                self.startStopButton.setStyleSheet("background-color: red; color: white;")
                self.startStopButton.setEnabled(True)
            else:
                self.startStopButton.setStyleSheet("background-color: lightred; color: lightgray;")
                self.startStopButton.setEnabled(False)

    def onSubjectOrDateChanged(self):
        current_subject = self.subjectInput.text()
        current_date = self.dateInput.text()
        # Check if subject or date has changed
        if current_subject != self.last_subject or current_date != self.last_date:
            self.runInput.setText("001")
        # Update the last subject and date
        self.last_subject = current_subject
        self.last_date = current_date


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SerialApp()
    ex.show()
    sys.exit(app.exec())
