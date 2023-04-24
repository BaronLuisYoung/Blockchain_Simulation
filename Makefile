compile:

server: 
	python3 -u server.py

client1: 
	python3 -u client.py 1

client2: 
	python3 -u client.py 2

client3: 	
	python3 -u client.py 3

clean:
	rm -fr __pycache__