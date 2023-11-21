# Running encoder scripts
Script to handle the communication with the encoder board. 
Steps to follow:
1. First, upload encoder_sync to the encoder board.
2. Identify the port the board is connected.
3. Run the following command `python read_encoder.py <PORT_NAME> --freq <SAMPLING_FREQUNECY> [optional] --verbose [optional]`
4. Saves the data read from the serial under your ~/Documents/serial_data
