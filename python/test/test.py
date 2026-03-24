import serial
import time
import configparser
import os

def serial_vibrate(ser, level):
    """Direct serial vibration (0-20 scale)"""
    if ser:
        ser.write(f"Vibrate:{level};\n".encode())

def run_comprehensive_serial_test(ser):
    print("\n--- Starting Direct Serial Test (COM Only) ---")
    
    # 1. Ramp Test
    print("1. Testing Vibration Ramp (0-9 Lovense scale)...")
    for i in range(10):
        level_20 = round(i / 9 * 20)
        print(f"Level {i} (Serial Vibrate:{level_20})")
        serial_vibrate(ser, level_20)
        time.sleep(0.4)
    
    # 2. Pulse Test
    print("\n2. Testing Rapid Pulses...")
    for _ in range(3):
        print("Pulse HIGH (20)")
        serial_vibrate(ser, 20)
        time.sleep(0.3)
        print("Pulse LOW (0)")
        serial_vibrate(ser, 0)
        time.sleep(0.3)

    # 3. Pattern Simulation
    print("\n3. Testing Pattern Simulation (High/Low sequence)...")
    for i in range(4):
        val = 20 if i % 2 == 0 else 5
        print(f"Pattern step {i}: {val}")
        serial_vibrate(ser, val)
        time.sleep(0.5)

    print("\nStopping vibration...")
    serial_vibrate(ser, 0)
    print("--- Serial Test Complete ---")

def run_test():
    print("Initializing Direct Serial Test...")
    config = configparser.ConfigParser()
    # Find config.cfg in the PlatformIO directory
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "PlatformIO", "config.cfg")
    
    if not os.path.exists(config_path):
        print(f"Error: config.cfg not found at {config_path}")
        return

    config.read(config_path)
    port = config.get("Serial", "port", fallback="COM3")
    baud = config.getint("Serial", "baud_rate", fallback=115200)

    print(f"Connecting to {port} at {baud} baud...")
    
    try:
        # Open serial port
        ser = serial.Serial(port, baud, timeout=1, write_timeout=2)
        
        # Essential for many ESP32 to prevent staying in bootloader/reset
        ser.setDTR(False)
        ser.setRTS(False)
        
        print("Waiting 2 seconds for ESP32 to boot...")
        time.sleep(2)
        
        # Clear any junk in the buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        run_comprehensive_serial_test(ser)
        
        ser.close()
        print("Success: Device test completed via COM port.")
        
    except serial.SerialException as se:
        if "PermissionError" in str(se) or "Access is denied" in str(se):
            print(f"\nERROR: Port {port} is busy.")
            print("Please CLOSE the LS-Buttplug server or any other app using the COM port before running this test.")
        else:
            print(f"\nSerial Error: {se}")
    except Exception as e:
        print(f"\nUnexpected Error: {e}")

if __name__ == "__main__":
    run_test()
