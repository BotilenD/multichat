import socket
import select
import datetime

MAX_MSG_LENGTH = 1024
SERVER_PORT = 5555
SERVER_IP = '0.0.0.0'

MANAGERS = {"manager1", "manager2"}
muted_users = set()
clients = {}

def log_to_server(issuer, command_num, target=None, message=None):
    issuer_len = len(issuer)
    log_msg = f"{issuer_len}{issuer}{command_num}"
    if target:
        target_len = len(target)
        log_msg += f"{target_len}{target}"
    if message:
        message_len = len(message)
        log_msg += f"{message_len}{message}"
    print(log_msg)

def broadcast_message(message, exclude_client=None):
    for client_socket in clients:
        if client_socket != exclude_client:
            try:
                client_socket.send(message.encode())
            except:
                client_socket.close()
                clients.pop(client_socket)

def handle_client_message(client_socket):
    try:
        message = client_socket.recv(MAX_MSG_LENGTH).decode()
        client_name = clients[client_socket]

        if message.lower() == "quit":
            broadcast_message(f"{get_time()} {client_name} has left the chat.")
            print(f"{client_name} disconnected.")
            client_socket.close()
            clients.pop(client_socket)
            return

        if message.startswith("@"):
            command_parts = message.split(" ", 2)
            command = command_parts[0]

            if command == "!view-managers":
                connected_managers = [name for name in clients.values() if name in MANAGERS]
                manager_list = ", ".join(connected_managers) if connected_managers else "No managers connected."
                client_socket.send(f"Current managers: {manager_list}\n".encode())
                return

            if client_name not in MANAGERS:
                client_socket.send("No permissions.\n".encode())
                return

            if command == "@kick":
                target_name = command_parts[1]
                if target_name not in clients.values():
                    client_socket.send("Username not found in the system.\n".encode())
                else:
                    kick_user(client_socket, target_name)
                    log_to_server(client_name, 3, target_name)
                    print(f"{target_name} disconnected.")

            elif command == "@mute":
                target_name = command_parts[1]
                if target_name not in clients.values():
                    client_socket.send("Username not found in the system.\n".encode())
                else:
                    mute_user(target_name)
                    log_to_server(client_name, 4, target_name)

            elif command == "@promote":
                target_name = command_parts[1]
                if target_name not in clients.values():
                    client_socket.send("Username not found in the system.\n".encode())
                else:
                    promote_user(target_name)
                    log_to_server(client_name, 2, target_name)
            return

        if message.startswith("!"):
            command_parts = message.split(" ", 2)
            command = command_parts[0]

            if command == "!private":
                recipient_name = command_parts[1]
                if recipient_name not in clients.values():
                    client_socket.send("Username not found in the system.\n".encode())
                else:
                    private_message(client_socket, recipient_name, command_parts[2])
                    log_to_server(client_name, 5, recipient_name, command_parts[2])
            return

        if client_name in muted_users:
            client_socket.send("You are muted and cannot send messages.".encode())
            return

        formatted_message = f"{get_time()} {client_name}: {message}"
        broadcast_message(formatted_message, exclude_client=client_socket)
        client_socket.send(f"You: {get_time()} {message}\n".encode())
        log_to_server(client_name, 1, message=message)

    except:
        client_socket.close()
        clients.pop(client_socket)

def get_time():
    return datetime.datetime.now().strftime("%H:%M")

def kick_user(admin_socket, username):
    for client_socket, client_name in list(clients.items()):
        if client_name == username:
            try:
                client_socket.send("You have been kicked from the chat!".encode())
                client_socket.close()
                clients.pop(client_socket)
                broadcast_message(f"{username} has been kicked from the chat by {clients[admin_socket]}.")
            except:
                client_socket.close()
                clients.pop(client_socket)

def mute_user(username):
    for client_socket, client_name in clients.items():
        if client_name == username:
            muted_users.add(client_name)
            broadcast_message(f"{username} has been muted.")

def promote_user(username):
    MANAGERS.add(username)
    broadcast_message(f"{username} has been promoted to manager.")

def private_message(sender_socket, recipient_name, message):
    for client_socket, client_name in clients.items():
        if client_name == recipient_name:
            try:
                client_socket.send(f"Private message from {clients[sender_socket]}: {message}".encode())
            except:
                client_socket.close()
                clients.pop(client_socket)

def main():
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()

    print("Server is listening for clients...")

    while True:
        ready_sockets, _, _ = select.select([server_socket] + list(clients.keys()), [], [])

        for sock in ready_sockets:
            if sock is server_socket:
                client_socket, client_address = server_socket.accept()
                client_name = client_socket.recv(MAX_MSG_LENGTH).decode().strip()

                if client_name.startswith("@"):
                    client_socket.send("Invalid name. Names cannot start with '@'. Please try again.\n".encode())
                    continue

                clients[client_socket] = client_name

                if client_name in MANAGERS:
                    broadcast_message(f"{get_time()} @{client_name} has joined the chat!")
                else:
                    broadcast_message(f"{get_time()} {client_name} has joined the chat!")

                print(f"New client: {client_name} from {client_address}")

            else:
                handle_client_message(sock)

if __name__ == "__main__":
    main()
