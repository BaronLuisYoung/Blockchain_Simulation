#CS 171 PA01 Baron Young 
#server.py

import socket 
import threading

import os
from sys import stdout
from time import sleep
from blockchain import *

#_______________________________GLOBALS_______________________________________#
out_socks = [] #container for all client connections
active_clients = {} #[port] = id
Blockchain = Blockchain() #locally defined block chain
lock = threading.Lock() #lock used for adding block
TIME_STAMP = 0
#___________________________FOR SERVER CMDs___________________________________#
def wait(t):
    sleep(t)

def exit():
    in_sock.close()
    for sock in out_socks:
        sock[0].close()
    stdout.flush() 
    os._exit(0) 
#_____________________________________________________________________________#

def send_msg_to_client(port, data):
    try:
        port.sendall(bytes(data, "utf-8"))
        print("Sent data to client")
    except:
        print(f"exception in sending port {port}", flush=True)

def process_transfer_request(port, recipient_id, amnt): # T format: <Sender, Reciever-ID, amnt>
    global TIME_STAMP
    new_balance = Blockchain.check_balance(active_clients[port], int(amnt[1:])) #returns -1 if invalid 
   
    if new_balance != -1: 
        trans = (active_clients[port], recipient_id, amnt[1:], TIME_STAMP) #(S-ID, R-ID, Amnt, TS, )
        Blockchain.add_block(trans)
        return "RELEASE SUCCESS"
    else:
        return "RELEASE INCORRECT"

def get_user_input():
    while True:
        user_input = input()
        #print(user_input)
        if user_input == "Blockchain":
            chain_str = Blockchain.print_chain()
            print(chain_str)  
        elif user_input == "exit":
            exit()
        elif user_input.split()[0] == "wait":
            wait(int(user_input.split()[1])) # gets time arg in cmd: 'wait x', x = time
        elif user_input == "Balance":
            balance_str = "" 
            for i in range(1,4,1):
                balance_str = balance_str + "P" + str(i) + ": $" + str(Blockchain.check_balance("P" + str(i), 0)) + ", "
            print(balance_str.strip()[:-1]) #removes last comma 
        else:
            continue #ignore other inputs and continue

def handle_msg(data, addr):
    data = data.decode() #decode byte data into a string
    print(f"Data received: {data}")
    
    client_request = data.split() 
    if client_request[0] == "Transfer": #process a transfer 
        recv_time = int(client_request[3])
        if client_request[1] == active_clients[addr[1]]: #if user sends themselves money 
            #send back failed request
            data = "RELEASE Failed-Request"
        else:
            lock.acquire()
            print("about to process transfer", flush=True)
            data = process_transfer_request(addr[1], client_request[1], client_request[2]) #passes: <port, recv client, amnt>
            lock.release()
    elif client_request[0] == "Balance": #process a balance request
        lock.acquire()
        data = "Balance: $" + str(Blockchain.check_balance(client_request[1], 0))
        lock.release()
    else:
        
        return
        #invalid input send back nothing

    for sock in out_socks: #sends back message to console 
        if addr == sock[1]:
            wait(3)
            send_msg_to_client(sock[0], data)

def respond(conn, addr):
    try:
        client_id_data = conn.recv(1024)
    except:
        print(f"exception in user ID receving from {addr[1]}", flush=True)
    
    active_clients[addr[1]] = client_id_data.decode("utf-8") # add client to active clients
    while True:
        try:
            data = conn.recv(1024) 
        except:
            break #exception in receving from addr[1]

        #if cilents socket closed
        if not data:
            conn.close()
            break 
        
        #thread handles msg from client
        threading.Thread(target=handle_msg, args=(data, addr)).start()

if __name__ == "__main__":
    IP = socket.gethostname() 
    PORT = 8000 #3000-49151 are genreally usable 

    in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    in_sock.bind((IP, PORT)) #bind socket to the specified addrs

    in_sock.listen() #begin accepting connections 

    #thrd. for user input 
    threading.Thread(target=get_user_input).start()

    while True:
        try:
          conn, addr = in_sock.accept()
        except:
          print("exception in accept", flush=True)
          break
        out_socks.append((conn, addr))
        #thrd. for each client
        threading.Thread(target=respond, args=(conn,addr)).start()