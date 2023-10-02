import socket
import cv2
import pickle
import struct
import threading

def stream_video_with_telemetry(cam_id, server_socket):
    if server_socket is not None:
        server_socket.close()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    port = 9999 if cam_id == 0 else 9977  # Used different ports for left and right cameras

    socket_address = (host_ip, port)

    server_socket.bind(socket_address)
    server_socket.listen(5)
    print(f'Listening At:', socket_address)

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Got connection from {addr} for Camera {cam_id}")
        if client_socket:
            print(cam_id)
            vid = cv2.VideoCapture(cam_id)
            try:
                while vid.isOpened():
                    img, frame = vid.read()
                    if not img:
                        break

                    # Telemetry data example (modify as needed)
                    telemetry_data = {
                        "camera_id": cam_id,
                        "fps": vid.get(cv2.CAP_PROP_FPS),
                        # Add more telemetry data as needed
                    }

                    frame_data = pickle.dumps({"frame": frame, "telemetry": telemetry_data})
                    message = struct.pack("Q", len(frame_data)) + frame_data
                    client_socket.sendall(message)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        client_socket.close()
                        vid.release()
                        cv2.destroyAllWindows()
                        break
            except Exception as e:
                print(f"Camera {cam_id} error:", str(e))

def received_command(client_socket):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    port = 9988
    client_socket.bind((host_ip, port))
    client_socket.listen(5)

    try:
        client, _ = client_socket.accept()
        print("<============== Machine Start Working ==================>")
        while True:
            command = client.recv(1024).decode()
            if command == 'quit':
                raise KeyboardInterrupt()
            print('Received Command:', command)
            # Handle the command (implement as needed)
    except KeyboardInterrupt:
        pass
    finally:
        client_socket.close()

def run():
    ser_soc_left = threading.Thread(target=stream_video_with_telemetry, args=(0, None))
    ser_soc_right = threading.Thread(target=stream_video_with_telemetry, args=(1, None))
    ser_soc_rece = threading.Thread(target=received_command, args=(None,))

    ser_soc_left.start()
    ser_soc_right.start()
    ser_soc_rece.start()

    ser_soc_left.join()
    ser_soc_right.join()
    ser_soc_rece.join()

if __name__ == "__main__":
    run()
