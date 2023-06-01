

from hashlib import sha256
from random import randint
from time import sleep
hash_func = lambda x: sha256(x.encode('utf-8')).hexdigest()
#___________________BLOCK_CHAIN_CLASSES_____________________#

#block to contain a hash ptr - H , user_operation - T and nonce - N
class Block:
    def compute_hash(self, user_operation): #user_operation here is prev.user_operation
        print("computing hash ...")
        computed_nonce = 0 
        while True:     
            digest = hash_func(str(self.prev.hashed_prev_block) + (str(user_operation)) + str(computed_nonce))
            
            if int(digest[0], 16) <= 1: ##[TODO] now needs to be first 3 bits
                return (digest, computed_nonce)
            computed_nonce = computed_nonce + 1 ##[TODO]some random computation 

    def __init__(self, prev, user_operation):
        if prev is None:
            self.prev = None
            self.user_operation = user_operation 
            self.hashed_prev_block = '0'*64
            self.nonce = '0' #nonce not needed for gen. blk
        else:
            self.prev = prev
            self.user_operation = user_operation
            self.hashed_prev_block, self.nonce = self.compute_hash(self.prev.user_operation)
        print("Block generated")

class Blockchain:
    def __init__(self):
        self.head = None

    def add_block(self, user_operation):
        self.head = Block(self.head, user_operation)

    def chain_len(self):
         len = 0
         curr = self.head
         while curr is not None:
                len +=1
                curr = curr.prev
         return len

    def print_chain(self):
        curr = self.head
        if curr == None:
            return "[]"
        else: 
            #create chain list
            chain = []
            while curr is not None:
                chain.append(( "(" + curr.user_operation +  ", " + curr.hashed_prev_block + ") "))
                curr = curr.prev
            
            #reverse chain list in chronological order 
            chain_str = ""
            for x in reversed(chain):
                chain_str = chain_str + x
            print(f"{chain_str}") #[TODO]fix formatting !!
        