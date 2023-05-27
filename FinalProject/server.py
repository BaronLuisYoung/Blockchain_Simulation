# server.py
# this process accepts an arbitrary number of client connections
# it echoes any message received from any client to console
# then broadcasts the message to all clients
import socket
import threading
import os
import sys
import ast
import re
from sys import stdout
from time import sleep
from blog import *
from blockchain import *

from queue import Queue
#___________________________FOR SERVER CMDs________________________#
election_lock = threading.Lock()
connection_lock = threading.Lock()
connection_lock2 = threading.Lock()

connection_cond = threading.Condition()
condition = threading.Condition()

def wait(t):
    sleep(t)

def exit():
    in_sock.close()
    for sock in out_socks:
        sock[0].close()
    stdout.flush() 
    os._exit(0) 
    
#UTILITY 
new_ballot_is_larger = lambda A, B: (int(A[0]) > int(B[0])) or (int(A[0]) == int(B[0]) and int(A[1]) > int(B[1]))

#__________________________________________________________________#

def get_user_input():
	global CURRENT_LEADER_ID
	global in_sock
	global out_socks
	while True:
		user_input_string = input()
		print(f"cmd: {user_input_string}")
		if user_input_string == "exit":
			exit()
		elif user_input_string == "ports":
			for port in PORTS:
				print(PORTS[port].getpeername()[1])
			print("In sock:", in_sock.getsockname()[1])
		elif user_input_string == "outsocks":
			print(out_socks)
		elif user_input_string == "leader":
			print(CURRENT_LEADER_ID)
		elif user_input_string == "qcount":
			print(QUORUM_COUNT)
		elif user_input_string == "Post":
			#tbd
			pass
		elif user_input_string == "Comment":
			pass

def handle_bcast_msg(data):
	print("Bcasting to all")
	for sock in out_socks: 
		wait(2)
		conn = sock[0]
		try:
			conn.sendall(bytes(f"{data}", "utf-8"))
		except:
			print(f"exception in sending to port", flush=True)
			continue

def send_to_leader(my_tuple):
	try:
		data = str(my_tuple).encode()
		PORTS[CURRENT_LEADER_ID + 9000].sendall(data) #send back to leader , BALLOT_NUM, ACCEPT_NUM, ACCEPT_VAL)
		print(f"sent to leader",my_tuple, flush=True)
	except:
		print(f"exception in sending to leader", flush=True)

def handle_recv_msg(conn):
	requests_q = Queue()
	global CURRENT_LEADER_ID
	global BALLOT_NUM
	global QUORUM_COUNT
	global out_socks 
	global MY_PORT
	global PORTS
	while True:
		recv_tuple = None
		if requests_q.empty():
			try:
				data = conn.recv(1024).decode()
			except:
				print(f"exception in receiving", flush=True)
				break

			if not data:
				conn.close()		
				if conn in out_socks:
					out_socks.remove(conn)				
				print(f"connection closed", flush=True)
				break

			data = re.sub(r'\)\(', ')*(', data)
			data_list = data.split('*')
			for request in data_list:
				recv_request = ast.literal_eval(request)
				requests_q.put(recv_request)
			recv_tuple = requests_q.get()

		else:
			recv_tuple = requests_q.get()
		
		recv_msg = recv_tuple[0]
		match recv_msg:
			case "INIT_ID":
				print(recv_tuple)
				my_tuple = ("INIT_ACK", MY_PORT, recv_tuple[2])
				handle_bcast_msg(my_tuple)
			case "INIT_ACK":
				print(recv_tuple)
				for sock in out_socks:
					if sock[0].getpeername()[1] == recv_tuple[2]:
						PORTS[recv_tuple[1]] = sock[0]
			case "PREPARE":
				recv_bal = recv_tuple[1]

				election_lock.acquire()

				if new_ballot_is_larger(recv_bal, BALLOT_NUM):
					CURRENT_LEADER_ID = recv_bal[1]
					BALLOT_NUM = recv_bal	
					wait(2)		
					send_to_leader(("PROMISE", BALLOT_NUM))

				election_lock.release()
			case "PROMISE":
				print("PROM tst")
				print(recv_tuple)
				election_lock.acquire()
				QUORUM_COUNT +=1
				election_lock.release()
				
			case "ACCEPT":
				print("test")
			case "ACCEPTED":
				print("test")
			case "DECIDE":
				print("test")
			case _:
				print("default-test")

def send_out_connections(i):
	out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while True:
		try:
			out_sock.connect((IP, 9000+i))
			print(f"sucess, connection to server: {9000+i}")
			threading.Thread(target=handle_recv_msg, args=(out_sock,)).start()
			break
		except:
			continue

def begin_election():
	global CURRENT_LEADER_ID
	global QUORUM_COUNT
	global out_socks

	BALLOT_NUM[0] +=1 

	with condition:
		while len(out_socks) != 2:
			condition.wait()
	wait(3)
	handle_bcast_msg(("PREPARE", BALLOT_NUM))


if __name__ == "__main__":
	QUORUM_COUNT = 0
	IP = socket.gethostname()
	PID = int(sys.argv[1])
	PORTS = {}
	MY_PORT = 9000 + PID
	LOCAL_BLOG = Blog()
	LOCAL_BLOCKCHAIN = Blockchain()
	CURRENT_LEADER_ID = None
	BALLOT_NUM = [0,PID] #<ballotNum, processID>
	ACCEPT_NUM = [0,0] #<,>
	ACCEPT_VAL = None

	in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	in_sock.bind((IP, MY_PORT))
	in_sock.listen()

	for i in range(1,5): #create a 'send' thread for each new connection 
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
		wait(2)
		
		
		try:
			data = str(("INIT_ID",  MY_PORT, addr[1])).encode()
			conn.sendall(data)
			print(f"sent INIT ID message to port")
		except:
			print(f"exception in sending INIT_ID to port", flush=True)
			continue

		if len(out_socks) == 2:
			with condition:
				condition.notify()