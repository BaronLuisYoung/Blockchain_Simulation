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
    stdout.flush()
    os._exit(0)

def get_user_input():
    user_input_id = sys.argv
    user_input_id = "P" + user_input_id[1]
    try:
        out_sock.sendall(bytes(user_input_id, "utf-8"))
    except:
        print("exception in sending to server")

    while True:
        user_input = input()
        #print(user_input)
        if user_input.split()[0] == "exit":
            exit()
        elif user_input.split()[0] == "wait":
            wait(int(user_input.split()[1]))
        else:
            try:
                out_sock.sendall(bytes(user_input, "utf-8")) 
            except:
                continue

if __name__ == "__main__":
    sleep(1) #for autograder

    SERVER_IP = socket.gethostname()
    SERVER_PORT = 8000
    out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    out_sock.connect((SERVER_IP, SERVER_PORT))
           

    #thrd. for user inputs 
    threading.Thread(target=get_user_input).start()

    #wait receive data from server 
    while True:
        try:
            data = out_sock.recv(1024)
            str_data = str(data.decode())
            if str_data:
                print(str_data, flush=True)
        except:
            continue
        if not data:
            out_sock.close() #close own socket since other end closed
            break
  
    