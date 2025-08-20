import socket
import threading

# Function to handle receiving messages
def receive_messages(conn):
    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break
            print(f"\nPerson 2: {msg}")
        except:
            break

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("localhost", 12345))  # host, port
server_socket.listen(1)

print("Waiting for connection...")
conn, addr = server_socket.accept()
print(f"Connected with {addr}")

# Start a thread to listen for messages
threading.Thread(target=receive_messages, args=(conn,), daemon=True).start()

# Main loop for sending messages
while True:
    msg = input("You: ")
    conn.send(msg.encode())
