# Feeds and Speeds Calculator

This project is a CNC milling calculator that helps you determine the optimal feedrate, width of cut (WOC) and depth of cut (DOC) for your CNC milling operations. The calculator is implemented as a Python script using PyQt6 for the GUI.

## Running the Source Code

To run the source code, follow these steps:

1. Ensure you have Python 3.x installed on your system.
2. Install the required dependencies by running:
   ```
   pip install pyinstaller PyQt6
   ```
3. Run the `feeds_and_speeds.py` script:
   ```
   python feeds_and_speeds.py
   ```

## Using the Binaries

"Precompiled" (using Pyinstaller) binaries for different operating systems are available in the `binaries` directory. To use the binaries, follow these steps:

1. Download the appropriate binary for your operating system from the `binaries` directory.
2. Make the binary executable (if necessary):
   - On Linux and macOS:
     ```
     chmod +x <binary_name>
     ```
3. Run the binary:
   - On Linux and macOS:
     ```
     ./<binary_name>
     ```
   - On Windows:
     ```
     <binary_name>.exe
     ```

