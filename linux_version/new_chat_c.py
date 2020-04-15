#!/usr/local/bin/python3
import socket
import select
import errno
import sys
import time
import threading
from queue import Queue

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ").strip()


online_users=[]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)

username = my_username.strip().encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
dest_user = "server".encode('utf-8')
dest_user_len = f"{len(dest_user):<{HEADER_LENGTH}}".encode('utf-8')

client_socket.send(dest_user_len + dest_user + username_header + username)

socketDesc = client_socket.fileno()
inputDesc  = sys.stdin.fileno()

readDescriptors = []
readDescriptors.append(socketDesc)
readDescriptors.append(inputDesc)

writeDescriptors = []
execptionDescriptors = []


def read_msg_type_header():
    msg_type_header = client_socket.recv(HEADER_LENGTH)
    if not len(msg_type_header):
        print('Connection closed by the server')
        sys.exit(1)
    msg_type_length = int(msg_type_header.decode('utf-8').strip())
    msg_type = client_socket.recv(msg_type_length).decode('utf-8')
    return int(msg_type)

def selection_menu(user_list): #to print the list of users available online
    if len(user_list) != 1:
        print("\n\nThe currently available users are :", end="\n")
        count = 1
        for name in user_list:
            if name != my_username:
                print(f"{count}. {name}", end="\n")
                count+=1
    else:
        print("\n\n No user is currently online")

def recv_online_users(): #function to receive the list update message on socket
    list_header = client_socket.recv(HEADER_LENGTH)
    list_length = int(list_header.decode('utf-8').strip())
    users_string = client_socket.recv(list_length).decode('utf-8')
    users_list = users_string.split()
    return users_list

def read_message():
    username_header = client_socket.recv(HEADER_LENGTH)
    username_length = int(username_header.decode('utf-8').strip())
    username = client_socket.recv(username_length).decode('utf-8')
    message_header = client_socket.recv(HEADER_LENGTH)
    message_length = int(message_header.decode('utf-8').strip())
    message = client_socket.recv(message_length).decode('utf-8')
    return username, message


def send_message(user_list):
    message=input()
    if "@" in message:
        recp = (message.split()[0]).split("@")[1] #extracting the username from message
        if (recp.lower() != my_username.lower()) and (recp.lower() in map(str.lower, user_list) or recp.lower() == "all"): #checking if the username is valid or not
            dest_user = f"{recp.strip()}"
            dest_user = dest_user.encode('utf-8')
            dest_user_len = f"{len(dest_user):<{HEADER_LENGTH}}".encode('utf-8')
            try :
                actual_message = message.split(' ', 1)[1]
                actual_message = actual_message.encode('utf-8')
                message_header = f"{len(actual_message):<{HEADER_LENGTH}}".encode('utf-8')
                client_socket.send(dest_user_len + dest_user + message_header + actual_message)
            except IndexError:
                print("\nError : Cannot send empty message")
        else:
            print("\nError : Please enter the correct username")
    else:
        print("\nPlease specify the @username before entering the message")

def receive_msg():
    try:
        while True:
            msg_type=read_msg_type_header()
            if msg_type == 1:
                global online_users
                online_users = recv_online_users()
                selection_menu(online_users)
            elif msg_type == 2:
                username , message = read_message()
                print(f'\n\n{username} > {message}')
            else:
                print('Connection closed by the server')
                sys.exit()
            print(f"\n{my_username} > ", end="")

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()
        pass

    except Exception as e:
        print('Reading error: '.format(str(e)))
        sys.exit()

try:
    time.sleep(1.0) #waiting for the socket to be ready to communicate
    msg_type = read_msg_type_header() #needed to traverse the first message which we will be recieving from server : online users list
    online_users = recv_online_users()
    print("\nUSE @all TO SEND MESSAGE TO EVERYONE IN THE CHAT ROOM OR @username TO SEND MESSAGE TO A PARTICULAR USER.",end="\n")
    print("FOR EXAMPLE: TO SEND MESSAGE TO Bob USE @Bob ", end="\n")
    if len(online_users) and online_users[0] != my_username:
        selection_menu(online_users)
    print(f"\n{my_username} > ",end="")
    while True:
        readReady, writeReady, exceptionReady = select.select(readDescriptors, writeDescriptors, execptionDescriptors)
        for desc in readReady:
            if desc is socketDesc:
                receive_msg()
                break
            if desc is inputDesc:
                send_message(online_users)
                print(f"\n{my_username} > ",end = "")
                break
except KeyboardInterrupt:
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    pass
