

from hashlib import sha256
from random import randint
from time import sleep
hash_func = lambda x: sha256(x.encode('utf-8')).hexdigest()
#___________________BLOCK_CHAIN_CLASSES_____________________#

#block to contain a hash ptr - H , user_operation - T and nonce - N
class Block:
    def compute_hash(self, user_operation): #trans here is prev.trans
        computed_nonce = 0 
        while True:     
            digest = hash_func(str(self.prev.hashed_prev_block) + (str(user_operation)) + str(computed_nonce))
            
            if int(digest[0], 16) <= 3: ##[TODO] now needs to be first 3 bits
                return (digest, computed_nonce)
            computed_nonce = computed_nonce + 1 ##[TODO]some random computation 

    def __init__(self, prev, trans):
        if prev is None:
            self.prev = None
            self.trans = trans 
            self.hashed_prev_block = '0'*64
            self.nonce = '0' #nonce not needed for gen. blk
        else:
            self.prev = prev
            self.trans = trans 
            self.hashed_prev_block, self.nonce = self.compute_hash(self.prev.trans)

class Blockchain:
    def __init__(self):
        self.head = None

    def add_block(self, user_operation):
        self.head = Block(self.head, user_operation)

    def print_chain(self):
        curr = self.head
        if curr == None:
            return "[]"
        else: 
            #create chain list
            chain = []
            while curr is not None:
                chain.append(( "(" + curr.user_operation[0] + "," + curr.user_operation[1] + ","+ "$" + curr.user_operation[2] +  "," + curr.hashed_prev_block + ")"))
                curr = curr.prev
            
            #reverse chain list in chronological order 
            chain_str = ""
            for x in reversed(chain):
                chain_str = chain_str + x
            return ("[" + chain_str.replace(")(" , "),(") + "]").replace(",", ", ") #[TODO]fix formatting !!
        