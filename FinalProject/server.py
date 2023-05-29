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
connection_cond = threading.Condition(connection_lock)
request_lock = threading.Lock()
request_cond = threading.Condition(request_lock)

user_input_lock = threading.Lock()
user_input_cond = threading.Condition(user_input_lock)

def wait(t):
    sleep(t)

def exit():
	in_sock.close()
	for sock in out_socks:
		if sock != None:
			sock.close()
	stdout.flush() 
	os._exit(0) 
    
#UTILITY 
new_ballot_is_larger = lambda A, B: (int(A[0]) > int(B[0])) or (int(A[0]) == int(B[0]) and int(A[1]) > int(B[1]))

LOCAL_BLOG = Blog()
LOCAL_BLOCKCHAIN = Blockchain()
user_requests_q = Queue()
out_socks = [None] * 5
RECV_VALS = []
#__________________________________________________________________#
def handle_user_request():
	global user_requests_q
	global LOCAL_BLOG
	global LOCAL_BLOCKCHAIN
	global ACCEPT_VAL
	while True:
		with request_cond:

			while user_requests_q.empty():
				request_cond.wait()

			data = user_requests_q.get()
			print(data)

			request_type = data[0]
			if request_type == "post":
				print("newest post")
				# username = data[1]
				# title = data[2]
				# content = data[3]
				with user_input_cond:
					ACCEPT_VAL[0] = data[1]
					ACCEPT_VAL[1] = data[2] 
					ACCEPT_VAL[2] = data[3]
					user_input_cond.notify()
					
				print("userinput",ACCEPT_VAL, flush=True)
				# LOCAL_BLOG.make_new_post(username,title,content)
				# LOCAL_BLOCKCHAIN.add_block(str(data))


			elif request_type == "comment":
				pass
			elif request_type == "blog":
				pass
			elif request_type == "view":	
				pass
			elif request_type == "read":
				pass
			request_cond.notify()
		
def get_user_input():
	global CURRENT_LEADER_ID
	global out_socks
	global user_requests_q

	threading.Thread(target=handle_user_request).start()

	while True:
		data = input().split(", ")
		user_input_string = data[0]
		if user_input_string == "exit":
			exit()
		elif user_input_string == "ports":
			for port in PORTS:
				print(PORTS[port].getpeername()[1])
		elif user_input_string == "outsocks":
			for sock in out_socks:
				if sock != None:
					print(sock.getpeername()[1])
			print(out_socks)
		elif user_input_string == "leader":
			print(CURRENT_LEADER_ID)
		elif user_input_string == "qcount":
			print(QUORUM_COUNT)
		elif user_input_string == "posts":
			LOCAL_BLOG.view_all_posts()
		elif user_input_string == "blockchain":
			LOCAL_BLOCKCHAIN.print_chain()
		else:
			if CURRENT_LEADER_ID == None:
					begin_election()
					wait(5)

			with request_cond:
				while user_requests_q.full():
					request_cond.wait()
				user_requests_q.put(data)
				request_cond.notify()

def handle_bcast_msg(data):
	global out_socks
	print(f"Bcasting to all: {data}")
	#print(out_socks)
	for sock in out_socks: 
		if sock != None:
			try:
				sock.sendall(bytes(f"{data}", "utf-8"))
			except:
				print(f"exception in sending to port", flush=True)
				exc_type = sys.exc_info()[0]
				print("Exception type:", exc_type)
				continue
	

def send_to_server(my_tuple, PID):
	try:
		data = str(my_tuple).encode()
		out_socks[PID].sendall(data) #send back to leader , BALLOT_NUM, ACCEPT_NUM, ACCEPT_VAL)
		print(f"sent to server: {my_tuple}")
	except:
		exc_type = sys.exc_info()[0]
		print("Exception type:", exc_type)
		print(f"exception in sending to leader", flush=True)

def handle_recv_msg(conn):
	msg_requests_q = Queue()
	global CURRENT_LEADER_ID, BALLOT_NUM, QUORUM_COUNT, out_socks 
	global PORTS, ACCEPT_VAL, ACCEPT_NUM, RECV_VALS
	while True:
		if msg_requests_q.empty():
			try:
				data = conn.recv(1024).decode()
			except:
				print(f"exception in receiving", flush=True)
				continue

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
				msg_requests_q.put(recv_request)
			recv_tuple = msg_requests_q.get()
		else:
			recv_tuple = msg_requests_q.get()
		

		print(f"message recieved: {recv_tuple}")

		recv_msg = recv_tuple[0]
		match recv_msg:
			case "PREPARE":
				recv_bal = recv_tuple[1]
				election_lock.acquire()

				if new_ballot_is_larger(recv_bal, BALLOT_NUM):
					CURRENT_LEADER_ID = recv_bal[1]
					print(f"NEW LEADER: {CURRENT_LEADER_ID}")
					BALLOT_NUM = recv_bal	
					wait(2)		
					send_to_server(("PROMISE", BALLOT_NUM, ACCEPT_NUM, ACCEPT_VAL), CURRENT_LEADER_ID)

				election_lock.release()

			case "PROMISE":
				election_lock.acquire()
				QUORUM_COUNT +=1
				RECV_VALS.append(recv_tuple)
				election_lock.release()

				if QUORUM_COUNT >= 2 and MY_PID != CURRENT_LEADER_ID:
					print("ELECTED")
					CURRENT_LEADER_ID = MY_PID
					RECV_VALS = sorted(RECV_VALS, key=lambda x: x[2], reverse=True) #sort by acceptNum (bval)
					
					with user_input_cond:
						user_input_cond.wait()
						print("from here", ACCEPT_VAL, flush= True)
						print("REC", RECV_VALS)
						for val in RECV_VALS:
							if val[3][0] != None:
								
								print("GOTMEEE", flush=True)
								ACCEPT_VAL = val[3]
								break
						
						LOCAL_BLOG.make_new_post(ACCEPT_VAL[0], ACCEPT_VAL[1], ACCEPT_VAL[2])
						LOCAL_BLOCKCHAIN.add_block(str(data))


					


	
				
			case "ACCEPT":
				print("test")
			case "ACCEPTED":
				print("test")
			case "DECIDE":
				print("test")
			case _:
				print("default-test")

def send_out_connections(i):
	global CURRENT_LEADER_ID
	global new_ID
	global out_socks
	new_out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while True:
		try:
			new_out_sock.connect((IP, 9000+i))
			print(f"success: {9000+i}")
		except:
			continue
		out_socks[i] = new_out_sock
		break

def begin_election():
	global BALLOT_NUM
	print("Beginning Election")
	BALLOT_NUM[0] +=1 
	handle_bcast_msg(("PREPARE", BALLOT_NUM))

if __name__ == "__main__":
	new_ID = None
	MAX_QUORUM = 2
	QUORUM_COUNT = 0
	IP = socket.gethostname()
	MY_PID = int(sys.argv[1])
	PORTS = {}
	MY_PORT = 9000 + MY_PID
	CURRENT_LEADER_ID = None
	BALLOT_NUM = [0, MY_PID] #<ballotNum, processID>
	ACCEPT_NUM = 0 #<,>
	ACCEPT_VAL = [None, None, None]

	in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	in_sock.bind((IP, MY_PORT))
	in_sock.listen()

	for i in range(1,6): #create a 'send' thread for each new connection 
		if i != MY_PID:
			threading.Thread(target=send_out_connections, args=(i,)).start()

	threading.Thread(target=get_user_input).start()
	
	while True:
		try:
			conn, addr = in_sock.accept()
			print(f"success, recieved: {addr}")
		except:
			print("exception in accept", flush=True)
			break
		threading.Thread(target=handle_recv_msg, args=(conn,)).start()


