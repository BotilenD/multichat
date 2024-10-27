import socket
import msvcrt  # מאפשר קלט מיידי ב-Windows
import select

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5555
MAX_MSG_LENGTH = 1024

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
    except:
        print("Server is down.")
        return

    while True:
        name = input("Enter your Name: ")
        if name.startswith("@"):
            print("Invalid name. Names cannot start with '@'. Please try again.")
        else:
            client_socket.send(name.encode())
            break

    print("Connected to the chat server!")

    while True:
        try:
            ready_sockets, _, _ = select.select([client_socket], [], [], 0.1)

            for sock in ready_sockets:
                if sock is client_socket:
                    message = client_socket.recv(MAX_MSG_LENGTH).decode()
                    if not message:
                        print("Server has been closed.")
                        client_socket.close()
                        return
                    else:
                        print(message)

            if msvcrt.kbhit():
                message = input("Enter a message: ")
                client_socket.send(message.encode())

                if message.lower() == "quit":
                    print("Exiting chat...")
                    client_socket.send("quit".encode())
                    client_socket.close()
                    break

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print("Connection to the server was lost.")
            client_socket.close()
            break

if __name__ == "__main__":
    main()
