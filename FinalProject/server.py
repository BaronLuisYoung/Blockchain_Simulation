# server.py
# this process accepts an arbitrary number of client connections
# it echoes any message received from any client to console
# then broadcasts the message to all clients
import socket
import threading
import os
import sys
import ast

from sys import stdout
from time import sleep
from blog import *
from blockchain import *
#___________________________FOR SERVER CMDs________________________#
election_lock = threading.Lock()
connection_lock = threading.Lock()

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
	while True:
		user_input_string = input()
		print(f"cmd: {user_input_string}")
		if user_input_string == "exit":
			exit()
		elif user_input_string == "connections":
			for port in PORTS:
				print(PORTS[port])
		elif user_input_string == "leader":
			print(CURRENT_LEADER_ID)
		elif user_input_string == "Post":
			#tbd
			pass
		elif user_input_string == "Comment":
			pass

def handle_send_msg(data):
	for sock in out_socks: 
		conn = sock[0]
		try:
			conn.sendall(bytes(f"{data}", "utf-8"))
			print(f"sent message to port", flush=True)
		except:
			print(f"exception in sending to port", flush=True)
			continue

def send_to_leader(my_tuple):
	try:
		data = str(my_tuple).encode()
		PORTS[CURRENT_LEADER_ID + 9000].sendall(data) #send back to leader , BALLOT_NUM, ACCEPT_NUM, ACCEPT_VAL)
		print(f"sent message to port", flush=True)
	except:
		print(f"exception in sending to port", flush=True)


def handle_recv_msg(conn):
	global CURRENT_LEADER_ID
	global BALLOT_NUM
	global QUORUM_COUNT
	while True:
		try:
			data = conn.recv(1024).decode()
			print(f"data: {data}")
			recv_tuple = ast.literal_eval(data)
		except:
			print(f"exception in receiving", flush=True)
			break

		if not data:
			conn.close()
			print(f"connection closed", flush=True)
			break
		
		recv_msg = recv_tuple[0]
		match recv_msg:
			case "PREPARE":
				recv_bal = recv_tuple[1]

				election_lock.acquire()

				if new_ballot_is_larger(recv_bal, BALLOT_NUM):
					CURRENT_LEADER_ID = recv_bal[1]
					BALLOT_NUM = recv_bal			
					send_to_leader(("PROMISE", BALLOT_NUM))

				election_lock.release()

			case "PROMISE":
				election_lock.acquire()
				QUORUM_COUNT +=1
				election_lock.release()
				print("test got here!!!")
			case "ACCEPT":
				print("test")
			case "ACCEPTED":
				print("test")
			case "DECIDE":
				print("test")
			case _:
				print("default-test")

def send_out_connections(i): #i is the other servers PID we want to connect to
	global out_socks
	global PORTS
	out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while True:
		try:
			out_sock.connect((IP, 9000+i))
			print(f"sucess connection to server: {9000+i}")
			
			wait(2)
			
			remote_sock = out_socks[-1][0]
			
			raddr_ = remote_sock.getpeername()[1]
			raddr = out_sock.getpeername()[1] #(1,2)

			PORTS[raddr] = remote_sock

			#print(PORTS)
			# print(laddr_, raddr_ )
			# print(laddr, raddr)

			threading.Thread(target=handle_recv_msg, args=(out_sock,)).start()
			break
		except:
			continue

# def send_my_id(PID, conn):
# 	out_socks.append((conn, addr))

def begin_election():
	global CURRENT_LEADER_ID
	global QUORUM_COUNT

	BALLOT_NUM[0] +=1 
	while CURRENT_LEADER_ID == None and QUORUM_COUNT != 2:
		handle_send_msg(("PREPARE", BALLOT_NUM))
		wait(6)
	CURRENT_LEADER_ID = PID


if __name__ == "__main__":
	QUORUM_COUNT = 0
	IP = socket.gethostname()
	PID = int(sys.argv[1])
	PORTS = {}
	PORT = 9000 + PID
	LOCAL_BLOG = Blog()
	LOCAL_BLOCKCHAIN = Blockchain()
	CURRENT_LEADER_ID = None
	BALLOT_NUM = [0,PID] #<ballotNum, processID>
	ACCEPT_NUM = [0,0] #<,>
	ACCEPT_VAL = None

	in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	in_sock.bind((IP, PORT))
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


		
