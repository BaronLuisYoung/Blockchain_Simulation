# server.py
# this process accepts an arbitrary number of client connections
# it echoes any message received from any client to console
# then broadcasts the message to all clients
import socket
from threading import *
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
request_cond = threading.Condition()
print_lock = threading.Lock()
user_input_lock = threading.Lock()
user_input_cond = threading.Condition(user_input_lock)


processing_cond = Condition()

block_lock = threading.Lock()

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
new_ballot_is_larger_or_eq = lambda A, B: (int(A[0]) > int(B[0])) or (int(A[0]) == int(B[0]) and int(A[1]) >= int(B[1]))

def check_user_input(user_input_string):
	valid_strings = ["post", "comment", "blog", "view", "read"]
	result = user_input_string in valid_strings
	if not result:
		print("INVALID INPUT")
	return result
    
LOCAL_BLOG = Blog()
LOCAL_BLOCKCHAIN = Blockchain()

user_requests_q = Queue()
msg_requests_q = Queue()
#accept_q = Queue()
out_socks = [None] * 6
RECV_VALS = []
curr_curr_user_data = completed_request = None
accept_count = 0
#__________________________________________________________________#

def handle_user_request(): 
	global LOCAL_BLOG, LOCAL_BLOCKCHAIN, ACCEPT_VAL, CURRENT_LEADER_ID, BALLOT_NUM
	global user_requests_q, curr_user_data, completed_request, accept_count

	while True: 
		with request_cond:
			
			while user_requests_q.empty():
				request_cond.wait()

			processing_cond.acquire()
			
			curr_user_data = user_requests_q.queue[0]
			accept_count = 0
			request_type = curr_user_data[0]
			
			if CURRENT_LEADER_ID == None:
				begin_election()

			with user_input_cond:
				ACCEPT_VAL[0] = curr_user_data[1]	# username = data[1]
				ACCEPT_VAL[1] = curr_user_data[2] 	# title = data[2]
				ACCEPT_VAL[2] = curr_user_data[3]	# content = data[3]	
				if request_type == "post":
					if LOCAL_BLOG.find_post_by_title(curr_user_data[2]) != None:
						print("DUPLICATE TITLE")
						return
					else:
						ACCEPT_VAL[3] = 0	# post = 0
				elif request_type == "comment":
					if LOCAL_BLOCKCHAIN.chain_len == 0 or LOCAL_BLOG.find_post_by_title(curr_user_data[2]) == None:
						print("CANNOT COMMENT")	
						return
					else:
						ACCEPT_VAL[3] = 1	# post = 0
				
				user_input_cond.notify()
		
				if CURRENT_LEADER_ID != None:
						BALLOT_NUM[0] += 1	
						handle_bcast_msg(("ACCEPT", BALLOT_NUM, myVal))


			#WORKS FOR NOW BUT VERY DANGEROUS
			processing_cond.wait() 

			processing_cond.release()
			
			request_cond.notify()
		
def get_user_input():

	global CURRENT_LEADER_ID
	global out_socks
	global user_requests_q

	threading.Thread(target=handle_user_request).start()

	while True:
		data = input().split(",")
		user_input_string = data[0]


		if user_input_string == "exit":
			exit()
		elif user_input_string == "ballotnum":
				print(BALLOT_NUM)
		elif user_input_string == "queue":
			print(list(user_requests_q.queue))
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
		elif user_input_string == "blockchain":
			LOCAL_BLOCKCHAIN.print_chain()
		elif user_input_string == "blog":
			LOCAL_BLOG.view_all_posts()
		elif user_input_string == "view":	
			LOCAL_BLOG.view_user_posts(data[1])
		elif user_input_string == "read":
			LOCAL_BLOG.view_post_by_title(data[1])
		elif check_user_input(user_input_string) == True and data[1] and data[2] and data[3]:
			with request_cond:
				user_requests_q.put(data)
				#print("User request placed in queue!", flush=True)
				request_cond.notify()
				#print("Notifying request handler.", flush=True)
		else:
			continue

def handle_bcast_msg(data):
	global out_socks
	wait(3)
	print(f"Bcasting to all: {data}")
	for sock in out_socks: 
		wait(1)
		if sock != None:
			try:
				sock.sendall(bytes(f"{data}", "utf-8"))
			except:
				print(f"exception in sending to port", flush=True)
				exc_type = sys.exc_info()[0]
				print("Exception type:", exc_type)
				continue
	

def send_to_server(my_tuple, PID):
	wait(3)
	try:
		data = str(my_tuple).encode()
		out_socks[PID].sendall(data) 
		print(f"sent to server {9000+PID}: {my_tuple}")
	except:
		exc_type = sys.exc_info()[0]
		print("Exception type:", exc_type)
		print(f"exception in sending to leader", flush=True)


def handle_request_type(recv_tuple):
	global msg_requests_q, user_requests_q, out_socks 
	global CURRENT_LEADER_ID, BALLOT_NUM, QUORUM_COUNT
	global PORTS, ACCEPT_VAL, ACCEPT_NUM, RECV_VALS
	global accept_count, myVal, curr_user_data
	flag3 = flag2 = flag1 =  True
	recv_msg = recv_tuple[0]

	match recv_msg:
			case "PREPARE":
				print(f"RECEIVED PREPARE: {recv_tuple}")
				recv_bal = recv_tuple[1]

				election_lock.acquire()

				if new_ballot_is_larger_or_eq(recv_bal, BALLOT_NUM):
					CURRENT_LEADER_ID = recv_bal[1]
					BALLOT_NUM = recv_bal
					print(f"NEW LEADER: {CURRENT_LEADER_ID}")	
					send_to_server(("PROMISE", BALLOT_NUM, ACCEPT_NUM, ACCEPT_VAL), CURRENT_LEADER_ID)

				election_lock.release()

			case "PROMISE":
				with election_lock:  #each thrd the recv adds to count and appends their promise
					QUORUM_COUNT +=1
					print(f"MESSAGE RECIEVED: {recv_tuple}")
					RECV_VALS.append(recv_tuple) # 
					
					if QUORUM_COUNT < 2: #they simply return if havent reached quorum
							return

					if QUORUM_COUNT >= 2 and MY_PID != CURRENT_LEADER_ID and flag1:
						flag1 = False
						print("ELECTED")
						CURRENT_LEADER_ID = MY_PID
					else:
						return
					
				with user_input_cond:
					while ACCEPT_VAL == None:
						#print("waiting on user_input_cond, thread waiting ...", flush=True) 
						user_input_cond.wait()
					#print("user_input has data, thread awake ...", flush=True)  
					

					temp_vals = []
					for vals in RECV_VALS:
						temp_vals.append(vals[3][0])

					#print("from tempvals",temp_vals)
					if  all(element is None for element in temp_vals):
						myVal = ACCEPT_VAL
						#print("from promise here", myVal)

					else:	#myVal = received val with highest b 
						myVal = max(RECV_VALS, key=lambda x: (x[1][0], x[1][1]))[3] #sort by acceptNum (bval)
					#print("from promise", myVal)
					RECV_VALS = []
					temp_vals = []
					QUORUM_COUNT = 0
					flag1 = True
				handle_bcast_msg(("ACCEPT", BALLOT_NUM, myVal))

			case "ACCEPT":
				recv_bal = recv_tuple[1]
				print(f"MESSAGE RECEIVED (ACCEPTOR): {recv_tuple}")
				if new_ballot_is_larger_or_eq(recv_bal, BALLOT_NUM) and LOCAL_BLOCKCHAIN.chain_len() <= BALLOT_NUM[2]:

					ACCEPT_NUM = recv_tuple[1] #AcceptNum <- b (BallotNum)
					ACCEPT_VAL = recv_tuple[2] #AcceptVal <- V (myVal)

					send_to_server(("ACCEPTED", recv_tuple[1], recv_tuple[2]), CURRENT_LEADER_ID)
				'''
					"7. An acceptor should NOT reply ACCEPTED to an ACCEPT if the acceptor’s 
					blockchain is deeper than the depth from the ballot number"
				'''


			case "ACCEPTED":
				with block_lock:
					accept_count +=1
					print(f"MESSAGE RECEIVED: {recv_tuple}")
					if accept_count < MAX_QUORUM or accept_count > MAX_QUORUM :
						return

				if accept_count >= MAX_QUORUM:
					print("ACCEPTED MAJORITY RECIEVED", flush=True)
					#flag2 = False #might be able to remove flag
					with block_lock:
						
						if recv_tuple[2][3] == 0: #0 for post
							LOCAL_BLOG.make_new_post(recv_tuple[2][0], recv_tuple[2][1], recv_tuple[2][2])
						else: #1 for comment
							LOCAL_BLOG.comment_on_post(recv_tuple[2][0], recv_tuple[2][1], recv_tuple[2][2])
						
						LOCAL_BLOCKCHAIN.add_block(str(recv_tuple[2]))
						
						BALLOT_NUM[2] += 1
						
						print(f"DECIDED: {ACCEPT_VAL}")
						handle_bcast_msg(("DECIDE", BALLOT_NUM, ACCEPT_VAL))
						
						curr_user_data = None
			
						with processing_cond:
							#print("GOT HEERE")
							processing_cond.notify()
							completed_request = user_requests_q.get()
							print("Request completed:", completed_request, flush=True)
							#print("thread notified in handle_user_request")
				else:
					return
				

			case "DECIDE":
				with block_lock:
						if recv_tuple[2][3] == 0: #0 for post
							LOCAL_BLOG.make_new_post(recv_tuple[2][0], recv_tuple[2][1], recv_tuple[2][2])
						else: #1 for comment
							LOCAL_BLOG.comment_on_post(recv_tuple[2][0], recv_tuple[2][1], recv_tuple[2][2])
						LOCAL_BLOCKCHAIN.add_block(str(recv_tuple[2]))
						BALLOT_NUM[2] += 1
						print("DECIDED:", recv_tuple[2])
			case _:
				print("default-test")


def handle_recv_msg(conn):
	global msg_requests_q, out_socks 
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
			recv_tuple = msg_requests_q.get() #DEQUE WHEN WE HAVE DECIED
		else:
			recv_tuple = msg_requests_q.get()
		
		# with print_lock:
		# 	print(f"Message recieved: {recv_tuple}")
		handle_request_type(recv_tuple)


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
	BALLOT_NUM = [0, MY_PID, 0] #<ballotNum/seqNum, processID, depth> 
	ACCEPT_NUM = 0 #<,>
	ACCEPT_VAL = [None, None, None, None] #<username, title, content, OP>

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


