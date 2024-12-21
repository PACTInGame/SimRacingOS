import socket
import struct

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to LFS
sock.bind(('127.0.0.1', 29998))


def unpack_data(data):
    size = len(data)

    # Basic header (always present)
    header_format = '<4sII'
    header_size = struct.calcsize(header_format)

    if size < header_size:
        return None

    header, id, time = struct.unpack(header_format, data[:header_size])

    result = {
        'header': header.decode(),
        'id': id,
        'time': time
    }

    remaining_size = size - header_size
    remaining_data = data[header_size:]

    # Try to unpack as much data as possible
    try:
        if remaining_size >= 36:  # 9 floats
            result['ang_vel'] = struct.unpack('<3f', remaining_data[:12])
            result['heading'], result['pitch'], result['roll'] = struct.unpack('<3f', remaining_data[12:24])
            result['accel'] = struct.unpack('<3f', remaining_data[24:36])
            remaining_data = remaining_data[36:]
            remaining_size -= 36

        if remaining_size >= 24:  # 6 floats
            result['vel'] = struct.unpack('<3f', remaining_data[:12])
            result['pos'] = struct.unpack('<3f', remaining_data[12:24])
            remaining_data = remaining_data[24:]
            remaining_size -= 24

        if remaining_size >= 20:  # 5 floats
            result['inputs'] = struct.unpack('<5f', remaining_data[:20])
            remaining_data = remaining_data[20:]
            remaining_size -= 20

        if remaining_size >= 16:  # 4 bytes + 3 floats
            result['gear'], _, _, _ = struct.unpack('<4B', remaining_data[:4])
            result['engine_data'] = struct.unpack('<2f', remaining_data[4:12])
            result['distance'] = struct.unpack('<2f', remaining_data[12:20])
            remaining_data = remaining_data[20:]
            remaining_size -= 20

        # Unpack wheel data if available
        result['wheels'] = []
        wheel_size = 40  # 10 floats per wheel
        for i in range(4):
            if remaining_size >= wheel_size:
                wheel_data = struct.unpack('<10f', remaining_data[:wheel_size])
                result['wheels'].append({
                    'susp_deflect': wheel_data[0],
                    'steer': wheel_data[1],
                    'x_force': wheel_data[2],
                    'y_force': wheel_data[3],
                    'vertical_load': wheel_data[4],
                    'ang_vel': wheel_data[5],
                    'lean_rel_to_road': wheel_data[6],
                    'air_temp': wheel_data[7],
                    'slip_fraction': wheel_data[8],
                    'touching': wheel_data[9]
                })
                remaining_data = remaining_data[wheel_size:]
                remaining_size -= wheel_size
            else:
                break

        if remaining_size >= 8:  # 2 floats
            result['extra'] = struct.unpack('<2f', remaining_data[:8])

    except struct.error as e:
        print(f"Error unpacking data: {e}")

    return result


while True:
    # Receive data
    data = sock.recv(280)
    if not data:
        break  # Lost connection

    # Unpack the data
    result = unpack_data(data)

    if result:
        print(f"Time: {result['time']}")
        if 'roll' in result:
            print(f"roll: {result['roll']}")
        if 'wheels' in result:
            print(f"Number of wheels: {len(result['wheels'])}")
            for i, wheel in enumerate(result['wheels']):
                print(f"Wheel {i + 1} - Suspension: {wheel['susp_deflect']:.2f}, Steer: {wheel['steer']:.2f}")
    else:
        print("Failed to unpack data")

# Release the socket
sock.close()