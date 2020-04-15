#!/usr/local/bin/python3

import socket
import select
import time

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

LIST_UPDATE = "1" #sent when any user joins or leaves the chat room
NORMAL_MSG = "2" #normal message sent from user to server or another user

#format for the list update is : MESSAGE TYPE HEADER + MESSAGE TYPE + LIST HEADER + LIST
#format for the normal message is : MESSAGE TYPE HEADER + MESSAGE TYPE + USER HEADER + USER + MESSAGE HEADER + MESSAGE
#MESSAGE TYPES are differentiated on the client side. We can even do the implementation without sending the message
#type and sending the applying proper checks on the client side. but for now i have used the first approach.

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen(4)

sockets_list = [server_socket]
clients = {}
print(f'Listening for connections on {IP}:{PORT}...')

def listing_online_users():
    clients_online = ""
    for value in clients.values():
        clients_online += value['data'].decode('utf-8')
        clients_online += " "
    return clients_online

def sending_list_of_online_users():
    online_clients = listing_online_users()
    msg_type_header = f"{len(LIST_UPDATE):<{HEADER_LENGTH}}".encode('utf-8')
    msg_type = LIST_UPDATE.encode('utf-8')
    list_header = f"{len(online_clients):<{HEADER_LENGTH}}".encode('utf-8')
    online_clients = online_clients.encode('utf-8')
    for client_socket in clients:
        client_socket.send(msg_type_header + msg_type + list_header + online_clients)

def get_socket_pair(my_dict, dest): #to get the socket from the username available in value of CLIENT dictionary
    for item in my_dict.items():
        if item[1]["data"].decode('utf-8') == dest:
            return item[0]

def receive_message(client_socket):
    try:
        dest_header = client_socket.recv(HEADER_LENGTH)
        if not len(dest_header):
            return False
        dest_user_len = int(dest_header.decode('utf-8').strip())
        dest_user = client_socket.recv(dest_user_len)
        message_header = client_socket.recv(HEADER_LENGTH)
        message_length = int(message_header.decode('utf-8').strip())
        return {'dest_header':dest_header, 'dest_user': dest_user, 'header':message_header, 'data': client_socket.recv(message_length)}
    except:
        return False


while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept() # should negotiate the clients online with the server
            user = receive_message(client_socket)
            if user is False:
                continue
            sockets_list.append(client_socket)
            clients[client_socket] = user
            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
            #time.sleep(0.5)
            sending_list_of_online_users() #Sending the list of all users online to everyone when a user comes online
        else:
            message = receive_message(notified_socket)
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                sending_list_of_online_users() #sending the list again when users leave chatroom
                continue
            user = clients[notified_socket]
            print(f"Message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')} to {message['dest_user'].decode('utf-8')}")
            destination_client = message['dest_user'].decode('utf-8')
            msg_type_header = f"{len(NORMAL_MSG):<{HEADER_LENGTH}}".encode('utf-8')
            msg_type = NORMAL_MSG.encode('utf-8')

            if destination_client.lower() == "all": #if all then sending it to everyone in the chat room
                for client_socket in clients:
                    if client_socket != notified_socket:
                        client_socket.send(msg_type_header + msg_type + user['header'] + user['data'] + message['header'] + message['data'])
            else:
                #else we can send as per the name of the destination client. Proper checks are in place to make
                #sure that the destination username is not kept empty.
                destination_socket = get_socket_pair(clients, destination_client.lower())
                destination_socket.send(msg_type_header + msg_type + user['header'] + user['data'] + message['header'] + message['data'])

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        sending_list_of_online_users() #sending the list again when users leave chatroom
        del clients[notified_socket]
