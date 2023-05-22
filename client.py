#CS 171 PA01 Baron Young 
#client.py
import socket 
import threading 
import heapq
import sys
import os 

from sys import stdout
from time import sleep 

#_______________________________GLOBALS_______________________________________#
out_socks = {} #container for all client connections [port] = socket
active_clients = {} #[port] =  # id is client #
pri_queue = []
TIME_STAMP = 0
REPLIES = [False]* 3
lock = threading.Lock() #lock for stuff

#___________________________FOR SERVER CMDs___________________________________#
def wait(t):
    sleep(t)

def exit():
    out_sock_server.close()
    out_sock_client_a.close()
    out_sock_client_b.close()
    stdout.flush()
    os._exit(0)
#_____________________________________________________________________________#

def send_all_clients(data): # currently used for sending back release
    for sock in out_socks:
        try:
            out_socks[sock].sendall(bytes(data, "utf-8"))  
        except:
            print(f"send request failed", flush=True)
            continue

def get_user_input():
    global TIME_STAMP
    while True:
        user_input = input()
        if user_input.split()[0] == "exit":
            exit()
        elif user_input.split()[0] == "wait":
            wait(int(user_input.split()[1]))
        elif user_input.split()[0] == "queue":
            print(pri_queue, flush=True)
        elif user_input.split()[0] == "Transfer":
            TIME_STAMP += 1
            heapq.heappush(pri_queue, ((TIME_STAMP, CLIENT_ID), user_input))
            print(f"REQUEST {TIME_STAMP}", flush=True)
            #print(TIME_STAMP)
            for sock in out_socks:
                try:
                    msg = str(user_input) + " " + str(TIME_STAMP) + " " + str(CLIENT_ID)
                    out_socks[sock].sendall(bytes(msg, "utf-8"))  
                except:
                    print(f"send request failed", flush=True)
                    continue
        elif user_input.split()[0] == "Balance":
            TIME_STAMP += 1
            #msg = str(user_input) + " " + str(TIME_STAMP) + " " + str(CLIENT_ID)
            out_sock_server.sendall(bytes(user_input, "utf-8"))
        else:
            continue

def respond(addr, recv_time):
    global TIME_STAMP
    while True: 
        try: 
            client_id = active_clients[addr[1]]     #get socket
            sock = out_socks[8000 + int(client_id)]

            TIME_STAMP = max(TIME_STAMP, int(recv_time)) + 1
            sock.sendall(bytes(f"REPLY {TIME_STAMP} {CLIENT_ID}", "utf-8")) 
            print(f"REPLY: <{TIME_STAMP}, {CLIENT_ID}>", flush=True) #P{active_clients[addr[1]]}
            return
        except:
            print(f"failed to respond to: {8000 + client_id}", flush=True)
            continue

def receive_request(conn, addr):
    global REPLIES
    global TIME_STAMP
    while True:
        try:
            data = conn.recv(1024) 
            string_data = data.decode('utf-8')
            #print(string_data)
        except:
            break 
        request = string_data.split()
        wait(3)
        if not data:
            conn.close()
            print(f"Connection to other client closed: {addr[1]}", flush=True)
            break
        elif request[0] == "REPLY":
            lock.acquire()
            REPLIES[int(request[-1])-1] = True
            #print(f"REPLY count: {REPLIES}")
            TIME_STAMP = max(TIME_STAMP, int(request[-2])) + 1
            print(f"REPLIED <{TIME_STAMP}, {request[-1]}>", flush=True)
    
            if all(REPLIES) and pri_queue[0][0][1] == CLIENT_ID: #q = [((TS, CID), Trans), ...]
                data = pri_queue[0][1]
                #update time stamp on msg
                TIME_STAMP+= 1
                # recv_time = pri_queue[0][0][0]
                data = data + " " + str(TIME_STAMP)
                print(f"AQUIRED MUTEX <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
                out_sock_server.sendall(bytes(data,"utf-8"))
                REPLIES = [False] * 3
                REPLIES[CLIENT_ID-1] = True
            lock.release()
        elif request[0] == "RELEASE":
            TIME_STAMP = max(TIME_STAMP, int(request[-2])) + 1
            print(f"RELEASED <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
            heapq.heappop(pri_queue)
            wait(1)
            if pri_queue and all(REPLIES) and pri_queue[0][0][1] == CLIENT_ID:
                TIME_STAMP += 1
                data = pri_queue[0][1]
                data = data + " " + str(TIME_STAMP)
                print(f"AQUIRED MUTEX <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
                out_sock_server.sendall(bytes(data,"utf-8"))  
                REPLIES = [False] * 3
                REPLIES[CLIENT_ID-1] = True
                
        elif request[0] == "Transfer":
            #print(f"Received Transfer request from: P{active_clients[addr[1]]}")
            lock.acquire()
            TIME_STAMP = max(TIME_STAMP, int(request[-2])) + 1
            print(f"RECEIVED TRANSFER <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
            heapq.heappush(pri_queue, ((int(request[-2]), int(request[-1])), string_data))
            lock.release()
    
            #print(request)
            recv_time = request[3]
            respond(addr, int(recv_time))
        elif request[0] == "Balance": #may not be needed
            print(string_data, flush=True)
        elif string_data[0] == 'P': #set up PID
            TIME_STAMP = 0 #for set up no time stamp needed
            active_clients[addr[1]] = string_data[1] 
            print(f"Client P{active_clients[addr[1]][0]} connected on port: {addr[1]}", flush=True)
        else:
            continue

#----------------------CONNECTION RELATED FUNCTIONS----------------------------#
def receive_connection_to_clients():
    while True:
        try:
            conn, addr = in_sock.accept()
            threading.Thread(target=receive_request, args=(conn,addr)).start()
        except:
            print("exception in accept", flush=True)
            break
        #thrd. for each client
    
def send_connection_to_clients(out_sock_client, port):
    while True:
        try: 
            out_sock_client.connect((SERVER_IP, port))
            out_socks[port] = out_sock_client
            break
        except:
            continue

def send_id(out_sock_client):
    while True:
        try:
            out_sock_client.sendall(bytes('P'+str(CLIENT_ID), "utf-8"))
            break
        except:
            continue
#----------------------------------------------------------------------------------#
if __name__ == "__main__":
    IP = socket.gethostname()
    CLIENT_ID = int(sys.argv[1])
    PORT = 8000 + CLIENT_ID #3000-49151 are genreally usable 
    print(f"Current Port number is {PORT}", flush=True)
    in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    in_sock.bind((IP, PORT)) #bind socket to the specified addrs

    in_sock.listen() #begin accepting connections

    SERVER_IP = socket.gethostname()
    SERVER_PORT = 8000

    out_sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    out_sock_client_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    out_sock_client_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    REPLIES[CLIENT_ID-1] = True

    if CLIENT_ID == 1:
        client_port_a = 8002
        client_port_b = 8003
    if CLIENT_ID == 2:
        client_port_a = 8001
        client_port_b = 8003
    if CLIENT_ID == 3:
        client_port_a = 8001
        client_port_b = 8002

    threading.Thread(target=send_connection_to_clients, args=(out_sock_client_a, client_port_a)).start()
    threading.Thread(target=send_connection_to_clients, args=(out_sock_client_b, client_port_b)).start()
    threading.Thread(target=receive_connection_to_clients).start() 
    
    threading.Thread(target=get_user_input).start() #thrd. for user inputs 
    
    threading.Thread(target=send_id, args=(out_sock_client_b,)).start()
    threading.Thread(target=send_id, args=(out_sock_client_a,)).start()

    while True:
        try:
            out_sock_server.connect((SERVER_IP, SERVER_PORT))
            print("Connected to Server")
            break
        except:
            continue 
    
    user_input_id = sys.argv
    user_input_id = "P" + user_input_id[1]
    try:
        out_sock_server.sendall(bytes(user_input_id, "utf-8"))
    except:
        print("exception in sending to server")

    #wait receive data from server 
    while True:
        try:
            data = out_sock_server.recv(1024)
            data = str(data.decode())
            if data:
                if data.split()[0] == "RELEASE": #if sucess or balance
                    lock.acquire()
                    TIME_STAMP+= 1
                    print(data.split()[1], flush=True)
                    print(f"RELEASE <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
                    lock.release()
                    send_all_clients(f"RELEASE {TIME_STAMP} {CLIENT_ID}")
                    heapq.heappop(pri_queue)
                    wait(1)
                    if pri_queue and all(REPLIES) and pri_queue[0][0][1] == CLIENT_ID:
                        TIME_STAMP += 1
                        data = pri_queue[0][1]
                        data = data + " " + str(TIME_STAMP)
                        print(f"AQUIRED MUTEX <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
                        out_sock_server.sendall(bytes(data,"utf-8"))  
                        REPLIES = [False] * 3
                        REPLIES[CLIENT_ID-1] = True

                elif data.split()[0] == "Balance:":
                    TIME_STAMP+=1
                    print(f"{data} <{TIME_STAMP}, {CLIENT_ID}>", flush=True)
            else:
                print("DATA SENT BACK EMPTY", flush=True)
        except:
            continue
        if not data:
            print("closing socket to server", flush=True)
            out_sock_server.close() #close own socket since other end closed
            break