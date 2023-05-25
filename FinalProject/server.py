# server.py
# this process accepts an arbitrary number of client connections
# it echoes any message received from any client to console
# then broadcasts the message to all clients
import socket
import threading
import os
import sys
from sys import stdout
from time import sleep
from blog import *
from blockchain import *
#___________________________FOR SERVER CMDs________________________#
def wait(t):
    sleep(t)

def exit():
    in_sock.close()
    for sock in out_socks:
        sock[0].close()
    stdout.flush() 
    os._exit(0) 
#__________________________________________________________________#

def get_user_input():
	while True:
		user_input_string = input()
		print(f"cmd: {user_input_string}")
		if user_input_string == "exit":
			exit()
		elif user_input_string == "connections":
			for port in PORTS:
				print(PORTS[port])
		elif user_input_string == "Post":
			#tbd
			pass
		elif user_input_string == "comment":
			pass
		elif user_input_string == "test":
			handle_send_msg("test")

def handle_send_msg(data):
	for sock in out_socks: 
		conn = sock[0]
		try:
			conn.sendall(bytes(f"{data}", "utf-8"))
			print(f"sent message to port", flush=True)
		except:
			print(f"exception in sending to port", flush=True)
			continue

def handle_recv_msg(conn):
	while True:
		try:
			data = conn.recv(1024).decode()
			print(f"data: {data}")
		except:
			print(f"exception in receiving", flush=True)
			break
		
		if not data:
			conn.close()
			print(f"connection closed", flush=True)
			break

def send_out_connections(i): #i is the other servers PID we want to connect to
	out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while True:
		try:
			out_sock.connect((IP, 9000+i))
			print(f"sucess connection to server: {9000+i}")
			PORTS[i] = out_sock
			threading.Thread(target=handle_recv_msg, args=(out_sock,)).start()
			break
		except:
			continue

# def send_my_id(PID, conn):
# 	out_socks.append((conn, addr))

def begin_election():
	BALLOT_NUM[0] +=1 
	wait(3)
	handle_send_msg(BALLOT_NUM)


if __name__ == "__main__":
	IP = socket.gethostname()
	PID = int(sys.argv[1])
	PORTS = {}
	PORT = 9000 + PID
	LOCAL_BLOG = Blog()
	LOCAL_BLOCKCHAIN = Blockchain()
	CURRENT_LEADER_ID = None
	BALLOT_NUM = [0,PID]
	ACCEPT_NUM = [0,0]
	ACCEPT_VAL = None

	in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	in_sock.bind((IP, PORT))
	in_sock.listen()

	for i in range(1,6): #create a 'send' thread for each new connection 
		if i != PID:
			threading.Thread(target=send_out_connections, args=(i,)).start()
	
	out_socks = []
	threading.Thread(target=get_user_input).start()
	if CURRENT_LEADER_ID == None:
		threading.Thread(target=begin_election).start()
	while True:
		try:
			conn, addr = in_sock.accept()
			print(f"connected to other server: {addr}")
		except:
			print("exception in accept", flush=True)
			break
		out_socks.append((conn, addr))
		
