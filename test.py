import time

import pyautogui
#time.sleep(3)
#print(pyautogui.position())
import wmi
import time

# Create an instance of the WMI client
c = wmi.WMI()


# Function to get a list of currently connected USB devices
def get_connected_devices():
    devices = set()
    for usb in c.query("SELECT * FROM Win32_USBHub"):
        if usb.PNPDeviceID:
            devices.add(usb.PNPDeviceID)
    return devices


# Function to handle USB connection events
def log_usb_events():
    print("Monitoring USB events...")

    # Initialize the set of connected devices
    previous_devices = get_connected_devices()

    while True:
        current_devices = get_connected_devices()

        # Detect devices that were added
        new_devices = current_devices - previous_devices
        if new_devices:
            for device in new_devices:
                print(f"Device connected: {device}")

        # Detect devices that were removed
        removed_devices = previous_devices - current_devices
        if removed_devices:
            for device in removed_devices:
                print(f"Device disconnected: {device}")

        # Update the previous devices list
        previous_devices = current_devices

        # Wait for a short period before checking again
        time.sleep(1)


if __name__ == "__main__":
    log_usb_events()
