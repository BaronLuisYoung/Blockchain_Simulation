

from hashlib import sha256
from random import randint
from time import sleep
hash_func = lambda x: sha256(x.encode('utf-8')).hexdigest()
#___________________BLOCK_CHAIN_CLASSES_____________________#

#block to contain a hash ptr - H , transaction - T and nonce - N
class Block:
    def compute_hash(self, trans): #trans here is prev.trans
        computed_nonce = 0 
        while True:     
            digest = hash_func(str(self.prev.hashed_prev_block) + (str(trans[0]) + str(trans[1]) + "$"+ str(trans[2])) + str(computed_nonce))
            #print(int(digest[0], 16))
            if int(digest[0], 16) <= 3:
                #print(self.prev.hashed_prev_block, str(trans[0]), str(trans[1]), str(trans[2]), str(computed_nonce))
                return (digest, computed_nonce)
            computed_nonce = computed_nonce + 1 
    def __init__(self, prev, trans):
        if prev is None: #if genesis block
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

    def add_block(self, trans):
        self.head = Block(self.head, trans)

    def check_balance(self, client_id, trans_amt): #client_id is the sender
        balance = 10    
        curr = self.head
        while curr is not None: 
            if curr.trans[0] == client_id:      #if loss
                balance -= int(curr.trans[2])  
            elif curr.trans[1] == client_id:    #if  gain 
                balance += int(curr.trans[2])   
            curr = curr.prev

        if (balance - trans_amt) < 0:
            return -1 
        else:
            return balance - trans_amt

    def print_chain(self):
        curr = self.head
        if curr == None:
            return "[]"
        else: 
            #create chain list
            chain = []
            while curr is not None:
                chain.append(( "(" + curr.trans[0] + "," + curr.trans[1] + ","+ "$" + curr.trans[2] +  "," + curr.hashed_prev_block + ")"))
                curr = curr.prev
            
            #reverse chain list in chronological order 
            chain_str = ""
            for x in reversed(chain):
                chain_str = chain_str + x
            return ("[" + chain_str.replace(")(" , "),(") + "]").replace(",", ", ") #fix formatting 
        
#___________________________________________________________#