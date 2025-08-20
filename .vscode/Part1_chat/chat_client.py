import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if not msg:
                break
            print(f"\nPerson 1: {msg}")
        except:
            break

# Connect to server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 12345))

# Start a thread to listen for incoming messages
threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

# Main loop for sending messages
while True:
    msg = input("You: ")
    client_socket.send(msg.encode())
