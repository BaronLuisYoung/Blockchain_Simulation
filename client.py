#CS 171 PA01 Baron Young 
#client.py
import socket 
import threading 

import sys
import os 

from sys import stdout
from time import sleep 

def wait(t):
    sleep(t)

def exit():
    out_sock.close()
    #flush console ouput buffer in case there are remaining prints
    stdout.flush()
    os._exit(0)

def get_user_input():
    #print("Please input user ID:")
    user_input_id = sys.argv
    sleep(int(sys.argv[1]))
    user_input_id = "P" + user_input_id[1]
    try:
        #send user input string to server, converted into bytes
        out_sock.sendall(bytes(user_input_id, "utf-8"))
        #handling exception in case trying to send data to closed connection 
    except:
        print("exception in sending to server")
        

    #print("Please input transaction or query current balance:")
    while True:
        user_input = input()
        if user_input.split()[0] == "exit":
            exit()
        elif user_input.split()[0] == "wait":
            wait(int(user_input.split()[1]))
        else:
            try:
                #send user input string to server, converted into bytes
                out_sock.sendall(bytes(user_input, "utf-8"))
                #handling exception in case trying to send data to closed connection 
            except:
                #print("exception in sending to server")
                continue
        #print("sent latest input to server")

def handle_msg(data):
    #sleep(3)
    #decode data into string 
    data = data.decode()
    print(data)

if __name__ == "__main__":
    sleep(1)
    #specify servers socket address so client can connect to it 
    #client and server are just different processes on the same machine
    #server's IP is just local machine's IP
    SERVER_IP = socket.gethostname()
    SERVER_PORT = 9000

    #create a socket object, SOCK_STREAM specifies a TCP socket
    #do not need to specify address for own socket for making an outboud connection
    out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #attempt to connect own socket to server's socket address 
    
    while True:
        try:
            out_sock.connect((SERVER_IP, SERVER_PORT))
            break
        except:
            #print(f"connection failed on address: {SERVER_IP}, port: {SERVER_PORT}\n")
            sleep(2)
            #print("attempting to connect ... \n")
            continue
    #print("sucess, connected to server")

    #spawn new thread to keep waiting for user inputs 
    #so user input and socket receive do not block eachother
    threading.Thread(target=get_user_input).start()

    #infinite loop to keep waiting to receive new data from server 
    while True:
        try:
        #wait to recive new data, 1024
            data = out_sock.recv(1024)
            print(f"{data.decode()}")
    #handle exception in case connection failure
        except:
            #print("exception in receiving")
            break 
        if not data:
            #close own socket since other end closed
            out_sock.close()
            #print("connection close from server")
            break

    #spawn a new thread to handle message 
    # so simulated network delay and message handling dont block receive
    threading.Thread(target=handle_msg, args=(data,)).start()
    