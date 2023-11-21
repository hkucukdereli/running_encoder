import os
import numpy as np
import serial
import csv
import time
from datetime import datetime
import argparse

# Set the system arguments
parser = argparse.ArgumentParser(description="Serial communication.")
parser.add_argument("port_name", type=str, help="Port name.")
parser.add_argument("--freq", type=int, default=20, help="Frequency in Hz.")
parser.add_argument("--timer", type=int, default=0, help="Set timer in sec.")
parser.add_argument('--verbose', action='store_true', default=False)
# Parse the system arguments
args = parser.parse_args()
port_name = args.port_name
freq = args.freq
timer = args.timer

# Configure the serial port and baud rate
SERIAL_PORT = f'{port_name}'
BAUD_RATE = 115200 

# CSV file
current_timestamp = datetime.now()
formatted_timestamp = current_timestamp.strftime("%Y_%m_%d_%H_%M_%S.%f")[:-3]
user_dir = os.path.expanduser("~")
data_dir = fr"{user_dir}\\Documents\\serial_data"
os.makedirs(data_dir, exist_ok=True)
file_path = fr'{data_dir}\\serial_data_{formatted_timestamp}.csv'

def read_serial_data():
    # Open the serial connection
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        ser.write(f"A {freq}\n".encode())
        time.sleep(0.01) # Delay the start to give the mcu time to process
        ser.write("S\n".encode())

        # Open the CSV file
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            last_timestamp = None 
            last_pos = 0 # Use this to offset the position
            counter = 0 # Count the cycles

            try:
                current_timestamp = datetime.now()
                formatted_timestamp = current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                writer.writerow(['Started recording:', formatted_timestamp, f"at {freq} Hz"])
                writer.writerow(['Counter','Timestamp', 'Period', 'Position'])
                while True:
                    counter = counter + 1

                    # Read the data from the seril
                    pos = int(ser.readline().decode('utf-8').strip())
                    if counter==1:
                        last_pos = pos

                    # Check if there's data
                    if pos:
                        # Get the current timestamp
                        current_timestamp = datetime.now()

                        # Calculate time difference
                        if last_timestamp is not None:
                            time_diff = np.round((current_timestamp - last_timestamp).total_seconds() * 1000, 2)
                        else:
                            time_diff = 0

                        # Update last timestamp
                        last_timestamp = current_timestamp
                        # Offset the position
                        pos = pos - last_pos

                        # Format the current timestamp
                        formatted_timestamp = current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                        # Write the cycle number, timestamp, time difference, and data to the CSV file
                        writer.writerow([counter, formatted_timestamp, time_diff, pos])
                        if args.verbose: print(f"{counter}-> (Δt={time_diff} ms): {pos}")

                    # Sleep for a very short period so nothing gets too overwhelmed
                    time.sleep(0.001)

            except KeyboardInterrupt:
                # Terminate gracefully and let the user know
                ser.write("E\n".encode())
                print(f"Data recording stopped by user. {counter} cycles recorded.")

if __name__ == "__main__":
    read_serial_data()
    print("Serial data recording complete.")
