import socket
import cv2
import pickle
import struct
import threading
import functools

# Define initial values for left_camera and right_camera
left_camera = True
right_camera = True

def receive_video_with_telemetry(left_socket, right_socket):
    data_left = b''
    data_right = b''

    payload_size = struct.calcsize('Q')

    while True:
        # Receive frames from the left camera
        while len(data_left) < payload_size:
            packet = left_socket.recv(4 * 1024)  # 4-kilobyte buffer
            if not packet:
                break
            data_left += packet

        packed_msg_size = data_left[:payload_size]
        data_left = data_left[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data_left) < msg_size:
            data_left += left_socket.recv(4 * 1024)
        frame_data = data_left[:msg_size]
        data_left = data_left[msg_size:]
        frame_info = pickle.loads(frame_data)
        frame_left = frame_info["frame"]
        telemetry_data_left = frame_info["telemetry"]

        # Receive frames from the right camera
        while len(data_right) < payload_size:
            packet = right_socket.recv(4 * 1024)  # 4-kilobyte buffer
            if not packet:
                break
            data_right += packet

        packed_msg_size = data_right[:payload_size]
        data_right = data_right[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data_right) < msg_size:
            data_right += right_socket.recv(4 * 1024)
        frame_data = data_right[:msg_size]
        data_right = data_right[msg_size:]
        frame_info = pickle.loads(frame_data)
        frame_right = frame_info["frame"]
        telemetry_data_right = frame_info["telemetry"]

        # Display frames in separate windows
        if left_camera:
            cv2.imshow('Left Camera', frame_left)
        if right_camera:
            cv2.imshow('Right Camera', frame_right)

        # Process telemetry data (modify as needed)
        print(f"Telemetry Data (Left Camera): {telemetry_data_left}")
        print(f"Telemetry Data (Right Camera): {telemetry_data_right}")

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    # Close the sockets at the end
    left_socket.close()
    right_socket.close()

def send_command(client_socket):
    global left_camera, right_camera

    while True:
        try:
            command = input("Enter Machine command:").strip()
            client_socket.sendall(command.encode("utf-8"))
            if command == 'quit':
                break
            elif command == 'right camera':
                left_camera = False
                right_camera = True
            elif command == 'left camera':
                right_camera = False
                left_camera = True

        except KeyboardInterrupt:
            break

def run():
    # Connect to the left and right camera server
    host_ip = '192.168.126.136'
    left_port, right_port, send_port = 9999, 9977, 9988

    left_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    right_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    left_socket.connect((host_ip, left_port))
    right_socket.connect((host_ip, right_port))
    send_socket.connect((host_ip, send_port))

    # Create a partial function to pass additional arguments
    send_command_partial = functools.partial(send_command, left_camera=left_camera, right_camera=right_camera)

    # Create threads for receiving video and sending commands
    receive_video_thread = threading.Thread(target=receive_video_with_telemetry, args=(left_socket, right_socket))
    send_command_thread = threading.Thread(target=send_command_partial, args=(send_socket,))

    receive_video_thread.start()
    send_command_thread.start()

    receive_video_thread.join()
    send_command_thread.join()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run()
