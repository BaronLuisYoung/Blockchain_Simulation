

from hashlib import sha256
from random import randint
hash_func = lambda x: sha256(x.encode('utf-8')).hexdigest()
#___________________BLOCK_CHAIN_CLASSES_____________________#

#block to contain a hash ptr - H , transaction - T and nonce - N
class Block:
    def compute_hash(self, trans): 
        computed_nonce = 0 
        #print(trans)
        # getto way to determine if first two bits are zero since only 0-3 have 00XX
        while True:      
            digest = hash_func(str(self.prev.hashed_prev_block) + (str(trans[0]) + str(trans[1]) + str(trans[2])) + str(computed_nonce))
            #print(int(digest[0], 16))
            if int(digest[0], 16) <= 3:
                return (digest, computed_nonce )
            computed_nonce = computed_nonce + 1 
        

    def __init__(self, prev, trans):
        #print(f"Building Block: {prev} and {trans}")
        if prev is None: #if genesis block
            self.prev = None
            #pntr whatever we want 
            self.trans = trans 
            self.hashed_prev_block = '0'*64
            self.nonce = '0'
            #same nonce calculation 
        else:
            self.prev = prev
            self.trans = trans 
            self.hashed_prev_block, self.nonce = self.compute_hash(self.prev.trans)

class Blockchain:
    def __init__(self):
        self.head = None

    def add_block(self, trans):
        self.head = Block(self.head, trans)

    def check_transfer(self, client_id, trans_amt): #client_id is the sender
        if self.head == None:
           if 10 - trans_amt < 0:
               return -1

        balance = 10
        curr = self.head
        while curr is not None: 
            if curr.trans[0] == client_id: #if transaction is a loss
                balance -= int(curr.trans[2][1]) #subtract from init balance 
            elif curr.trans[1] == client_id: #if transaction is a gain 
                balance += int(curr.trans[2][1])  #add to init balance 
            curr = curr.prev
    
        if (balance - trans_amt) < 0:
            #print(balance - trans_amt)
            return -1 
        elif (balance + trans_amt) > 0: #calculate the new balance to the recv
            return balance + trans_amt
    
    def check_balance(self, client_id):
        curr = self.head
        balance = 10
        if curr == None:
            return balance
        while curr is not None: 
            if curr.trans[0] == client_id: #if transaction is a loss
                balance -= int(curr.trans[2][1]) #subtract form init balance 
            elif curr.trans[1] == client_id: #if transaction is a gain 
                balance += int(curr.trans[2][1])  #add to init balance 
            curr = curr.prev
        return balance

    def print_chain(self):
        #print("Transaction History:")

        curr = self.head
        if curr == None:
            print("")
        else: 
            chain = []
            while curr is not None:
                #chain_str + "("+ curr.trans[0] +","+ curr.trans[1] +","+ curr.trans[2] +")"
                chain.append((str(curr.trans)[:-1]+ "," + curr.hashed_prev_block + ")").replace(" ", "").replace("'",""))
                curr = curr.prev
            chain_str = ""
            for x in reversed(chain):
                chain_str = chain_str + x
            print(("[" + chain_str.replace(")(" , "),(") + "]").replace(",", ", "), flush=True)
        
#___________________________________________________________#