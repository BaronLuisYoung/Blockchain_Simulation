#CS 171 PA01 Baron Young 
#server.py

import socket 
import threading

from os import _exit 
from sys import stdout
from time import sleep
from blockchain import *

#_______________________________GLOBALS_______________________________________#
out_socks = [] #container for all client connections
active_clients = {} #[port] = id
Blockchain = Blockchain() #locally defined block chain
lock = threading.Lock() #lock used for adding block
#_____________________________________________________________________________#

def wait(t):
    sleep(t)

def exit():
    in_sock.close()
    for sock in out_socks:
        sock[0].close()
    print("exiting program", flush=True)
    stdout.flush() #from sys lib
    #exit w/ status 0 
    _exit(0) #imported from os lib

def send_msg_to_client(port, data):
    try:
        #convert message into bytes and send through socket
        port.sendall(bytes(f"{data}", "utf-8"))
        print(f"sent message to port {port}", flush=True)
        #handling exception in case trying to send data to a closed connection
    except:
        print(f"exception in sending port {port}", flush=True)

def process_transfer_request(port, recipient_id, amnt): #sender, recv, amnt 
    new_balance = Blockchain.check_transfer(active_clients[port], int(amnt[1]))
    if new_balance != -1: 
        #create block and add it to chain
        trans = (active_clients[port], recipient_id, amnt) # Trasaction of format <Sender, Reciever, amount>
        Blockchain.add_block(trans)
        return f"Transfer successful, {active_clients[port]} -> {recipient_id}"
    else:
        return "Transfer failed, insufficent funds"

def get_user_input():
    while True:
        user_input = input()
        if user_input == "Print":
            Blockchain.print_chain()   
        elif user_input == "exit":
            exit()
        elif user_input.split()[0] == "wait":
            wait(int(user_input.split()[1]))
        else:
            break


def init_client_id(client_id, port):
   #print(port, client_id)
   active_clients[port] = client_id.decode("utf-8")
   print(f"New client ID: {active_clients[port]} added on port {port}")

#simluates newtork delay then handles recieved message 
def handle_msg(data, addr):
    #simulate 3 seconds message-passing delay
    sleep(3)#imported from time library
    data = data.decode() #decode byte data into a string

    client_request = data.split() 

    if client_request[0] == "Transfer": #process a transfer 
        if client_request[1] == active_clients[addr[1]]: #if user sends themselves money 
            #send back failed request
            data = "Failed Request, client cannot send money to themselves."
        else:
            lock.acquire()
            data = process_transfer_request(addr[1], client_request[1], client_request[2]) #passes: <port, recv client, amnt>
            print(data)
            lock.release()
    elif client_request[0] == "Balance" and len(client_request) > 1: #process a balance request
        data = "$" + str(Blockchain.check_balance(client_request[1]))#requester 
    # elif client_request[0] == "Balance": 
    #    for client in active_clients:
    #        print(client[active_clients])
    #        data += client[active_clients] + ":" + str(Blockchain.check_balance(client[active_clients])) + " "
    #    pass #imlement for other request that fail
    else:
        pass
    #sends back message to console 
    print(f"{addr[1]}: {data}", flush=True)
    #bcast to all clients by iterating through stored connections
    for sock in out_socks:
        conn = sock[0]
        recv_addr = sock[1]
        #echo message back to client
        try:
            #convert message into bytes and send through socket
            conn.sendall(bytes(f"{addr[1]}: {data}", "utf-8"))
            print(f"sent message to port {recv_addr[1]}", flush=True)
            #handling exception in case trying to send data to a closed connection
        except:
            print(f"exception in sending port {recv_addr[1]}", flush=True)
            continue
   
#handles a new connection by waiting to recieve from connection 
def respond(conn, addr):
    print(f"accepted connection from port: {addr[1]}", flush=True)
    try:
        #wait to reveive new data, 1024 is receive buffer size
        client_id_data = conn.recv(1024) #may need to be smaller
    except:
        #handle exception in case something happened to connection
        #but it's not properly closed 
        print(f"exception in user ID receving from {addr[1]}", flush=True)
    init_client_id(client_id_data, addr[1])
    #infinite loop to keep waiting to receive new data from this client
    while True:
        try:
            #wait to reveive new data, 1024 is receive buffer size
            data = conn.recv(1024) #may need to be larger 
        except:
            #handle exception in case something happened to connection
            #but it's not properly closed 
            print(f"exception in receving from {addr[1]}", flush=True)
            break

        #if cilents socket closed it will signal closing without any data 
        if not data:
            #close own sock since client end closed
            conn.close()
            print(f"connection closed from {addr[1]}", flush=True)
            break 
        #else we spawn a new thread to handle message sent from client
        #so the simulated network delay and message handling don't block receive
        threading.Thread(target=handle_msg, args=(data, addr)).start()

if __name__ == "__main__":
    IP = socket.gethostname() #gets the IP (address) of local machine 
    PORT = 9000 #3000-49151 are genreally usable 

    #creates socket object
    #AF_INET addr. family (used IPV4), SOCK_STREAM specifies TCP communication 
    in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #sock ramains open after shutdown (1-2mins), TIME-WAIT state
    #set REUSEADDR to disable "socket already in use"
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    in_sock.bind((IP, PORT)) #bind socket to the specified addrs

    in_sock.listen() #begin accepting connections 

    #spawn thread to wait for user input (this will terminate server)
    threading.Thread(target=get_user_input).start()

    while True:
        # wait to accept any incoming connections
		# conn: socket object used to send to and receive from connection
		# addr: (IP, port) of connection 
        try:
          conn, addr = in_sock.accept()
        except:
          print("exception in accept", flush=True)
          break
        #add client connection to list 
        out_socks.append((conn, addr))
        #spawn a thread for each client connection 
        threading.Thread(target=respond, args=(conn,addr)).start()
    
       
    

'''
Genesis block 
use 64 zeros for 

both server and client will need wait and sleep cmd functions 

add genesis block only when we add the first block
can we print to console 

'''

