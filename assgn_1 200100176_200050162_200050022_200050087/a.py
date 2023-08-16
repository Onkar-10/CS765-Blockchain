import os
import sys
import argparse
import random
import numpy as np
from heapq import *  # For the event queues
import networkx as nx # To graph the blockchain tree
import matplotlib.pyplot as plt # To plot the blockchain tree
# import pydot
from networkx.drawing.nx_pydot import graphviz_layout
import copy

# Beautifying the tree

    
def hierarchy_pos(G, root=None, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5):

    '''
    From Joel's answer at https://stackoverflow.com/a/29597209/2966723.  
    Licensed under Creative Commons Attribution-Share Alike 
    
    If the graph is a tree this will return the positions to plot this in a 
    hierarchical layout.
    
    G: the graph (must be a tree)
    
    root: the root node of current branch 
    - if the tree is directed and this is not given, 
      the root will be found and used
    - if the tree is directed and this is given, then 
      the positions will be just for the descendants of this node.
    - if the tree is undirected and not given, 
      then a random choice will be used.
    
    width: horizontal space allocated for this branch - avoids overlap with other branches
    
    vert_gap: gap between levels of hierarchy
    
    vert_loc: vertical location of root
    
    xcenter: horizontal location of root
    '''
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
        '''
        see hierarchy_pos docstring for most arguments

        pos: a dict saying where all nodes go if they have been assigned
        parent: parent of this branch. - only affects it if non-directed

        '''
    
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap, 
                                    vert_loc = vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent = root)
        return pos

            
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)


# Throughout the assignment time is in milliseconds

Ttx = 2000  # Ttx for transition inter arrival
TxnId = 0    # TxnID as a global variable to maintain uniqueness
max_transaction = 20 # Max transaction 
init_balance = 10000 # Initial balance of all peers
event_queue = [] # Transaction Events
block_queue = [] # Block events
all_transactions = []
all_blocks = []
BlkId = 1 # TxnID as a global variable to maintain uniqueness. Genesis has 0 as BlkId


class Block:
    def __init__(self, id):
        self.size = 1  # Size in KB. Default size of 1 KB
        self.id = id
        self.pid = -1
        self.time = 0  # Time at which block was added to blockchain
        self.length = 1 # Depth of the block in the respective tree
        self.miner = -1 # Peer who mined the block
        self.transactions = [] # All transactions seen by peer
        self.block_eyes = [] # To store the net number of coins in each peer 

    def set_parent(self, pid):
        self.pid = pid

    def set_time(self, t):
        self.time = t

    def set_miner(self, m):
        self.miner = m

    def add_transaction(self, tr_id):
        self.size = 1 + self.size # Transactions are of size 1KB
        self.transactions.append(all_transactions[tr_id-1]) # Transactions start from ID 1, hence tr_id-1 for list access

all_blocks.append(Block(0)) # Adding genesis block to all_blocks





class Peer:
    def __init__(self, id, slow, low_cpu, n):
        self.longest_chain = 1 # Length of longest chain. Default is 1 that of the genesis block.
        self.id = id
        self.slow = slow
        self.low_cpu = low_cpu
        self.n = n  # Number of peers in network
        self.hk = 0 # hk for Tk calculation
        self.coins = init_balance # Purse
        self.next_arrival = int(np.random.exponential(Ttx))+1 # Next generation of transaction in that peer, +1 to avoid it being 0
        self.block_wait = 0 # tk + Tk time is stored here
        self.connections = set() # Neighbor peers
        self.transactions = set() # Transactions not yet added to the blockchain
        self.block_cache = set() # Blocks whose parents are not yet seen by the peer
        genesis = Block(0)
        genesis.set_miner(id)

        for _ in range(n):
            genesis.block_eyes.append(init_balance)

        self.blockchain = [genesis] # Initializing blockchain with the genesis block
        # print(genesis.block_eyes)
        a = set()
        a.add(0)
        self.blocks = a # To store ids of blocks seen by peer for loopless transaction
        self.trans = set() # To store ids of transactions seen by peer for loopless transaction
        self.longest_holder = genesis # Endpoint of longest chain
        self.hold = Block(0) # Variable to hold the block waiting for time Tk

    def set_hk(self, h):
        self.hk = h
        
    def generate_transaction(self, n, time):
        # Generate a transaction with exponential interarrival time
        global TxnId
        TxnId = 1 + TxnId
        IDy = np.random.randint(0, n) # Enpoint of transaction
        C = np.random.randint(1, max_transaction + 1) # Number of coins transferred
        # Preventing sender to send money to himself
        if IDy == self.id:
            if self.id == 0:
                IDy = 1
            else:
                IDy = (IDy+1)%self.id

        # print(f"{TxnId}: {self.id} pays {IDy} {C} coins")
        all_transactions.append((TxnId, self.id, IDy, C)) # Adding transaction to all transaction
        heappush(event_queue, (time, TxnId, self.id)) # Adding transaction to the evnt queue

        
    def validate_block(self, blockcy, t):
        # Validate block transactions
        # Mining process stalled and the transactions added back to the list of transactions not in the blockchain
        block = copy.deepcopy(blockcy)
        for txn in self.hold.transactions:
            self.transactions.add(txn)


        print(f"Peer {self.id} validating {block.id} at time:{t}")
        success = True
        self.block_cache.add(block) # Add the block to the cache
        for par in self.blockchain:
            if par.id == block.pid: # Parent found
                self.block_cache.remove(block)
                block.time = t
                block.length = 1 + par.length # Tree Depth Increment
                block.block_eyes = par.block_eyes.copy()
                for txn in block.transactions: # Validating transaction. {TXNID, SENDER ID, RECEIVER ID, COINS}
                    block.block_eyes[txn[1]] -= txn[3] # Remove from sender
                    block.block_eyes[txn[2]] += txn[3] # Add to receiver
                    if block.block_eyes[txn[1]] < 0: # Invalid
                        success = False
                        # print(par.block_eyes)
                        # print(block.transactions)
                        # v = input()
                        return False

                if success:
                    self.blockchain.append(block) # Add to blockchain
                    self.blocks.add(block.id) # Add to seen blocks
                    for txn in block.transactions:
                        try:
                            self.transactions.remove(txn) # Remove transactions from the pool
                        except:
                            pass

                    if block.length > self.longest_chain: # Update longest chain. Fork handling
                        self.longest_chain = block.length
                        self.longest_holder = block

                    # Cache workaround. Add blocks from the cache if its parent is found now
                    new = set()
                    new.add(block)
                    fake_cache = self.block_cache.copy() # To iterate the original cache

                    for rem in self.block_cache:
                        for neu in new:
                            if rem.pid == neu.id: # Parent found
                                suc = True
                                fake_cache.remove(rem) # Remove from cache
                                rem.time = t
                                rem.length = 1 + neu.length # Depth update
                                rem.block_eyes = neu.block_eyes.copy()
                                for txn in rem.transactions: # Validate transactions
                                    rem.block_eyes[txn[1]] -= txn[3]
                                    rem.block_eyes[txn[2]] += txn[3]
                                    if rem.block_eyes[txn[1]] < 0:
                                        suc = False # Invalid transaction
                                        break

                                if suc:
                                    rem
                                    self.blockchain.append(rem) # Add to blockchain
                                    self.blocks.add(rem.id)
                                    for txn in rem.transactions:
                                        try:
                                            self.transactions.remove(txn) # Remove transactions from pool
                                        except:
                                            pass
                                        
                                        
                                    if rem.length > self.longest_chain: # Update longest chain. Fork handling
                                        self.longest_chain = rem.length
                                        self.longest_holder = rem

                                    new.add(rem)

                                break

                    self.block_cache = fake_cache # Set the updated cache

                    return True

                break 

        return True

    def mining(self, t):
        # print(f"Peer {self.id} mining {self.hold.id}")
        # Successful mining

            

        self.hold.set_parent(self.longest_holder.id) # Add block to the longest chain
        self.hold.time = t
        self.hold.miner = self.id
        self.hold.length = 1 + self.longest_holder.length

        self.coins = self.coins + 50 # Fees added to coinbase
        self.blockchain.append(self.hold)
        self.longest_holder = self.hold
        self.longest_chain = 1 + self.longest_chain
        self.blocks.add(self.hold.id)
        # print(f"Block {self.hold.id} created by peer {self.id}")
        ret = copy.deepcopy(self.hold)
        

        return ret

    
    def block_creation(self, I, t):
        # Simulate Block Creation
        global BlkId
        # print(f"Peer {self.id} creating block {BlkId}")
        self.block_wait = t + int(np.random.exponential(I/self.hk)) + 1 # Tk update
        block = Block(BlkId)
        BlkId += 1
        block.miner = self.id
        block.block_eyes = self.longest_holder.block_eyes.copy()

        txns = 0

        for txn in self.transactions:
            txns += 1

            if block.size == 1023: # 1 + 1022 + 1(coinbase)
                break

            if block.block_eyes[txn[1]] < txn[3]: # Ignore transaction if invalid
                continue

            block.block_eyes[txn[1]] -= txn[3] # Remove coins from sender
            block.block_eyes[txn[2]] += txn[3] # Add coins to sender


            block.add_transaction(txn[0]) # Adding transactions from the pool

        for txn in block.transactions:
            self.transactions.remove(txn) # Removing transactions from pool

        self.hold = block # Update hold
        all_blocks.append(self.hold)



    def ender(self):
        # print(f"The Peer is {self.id}, the number of blocks in the blockchain is {len(self.blockchain)}")
        # Printing blockchain info of peer
        # print(self.block_cache)
        # print(self.blocks)
        f = open(str(self.id)+".txt", "w")
        f.write(f"The Peer is {self.id}, the number of blocks in the blockchain is {len(self.blockchain)}\n")

        for block in self.blockchain:
            f.write(f"Time: {block.time/1000}, ID: {block.id}, PID: {block.pid}, Miner:{block.miner}, Size:{block.size}, number_of_transactions:{len(block.transactions)}\n")
            # f.write(str(block.block_eyes)+"\n")

        f.write("Cache\n")
        for block in self.block_cache:
            f.write(f"ID: {block.id}, PID: {block.pid}\n")

        G = nx.Graph()
        # print(len(self.blockchain))
        for block in self.blockchain:
            G.add_node(block.id)

        for block in self.blockchain:
            for bloc in self.blockchain:
                if bloc.id == block.pid:
                    G.add_edge(bloc.id, block.id)
                    break

        #os.remove(str(self.id)+".png")
        pos = hierarchy_pos(G, 0)    
        # nx.draw(G, pos) # Plot of the Blockchain Tree
        # plt.show()
        # plt.savefig(str(self.id)+".png")
        f.close()

        #print(f"Remaining transactions: {len(self.transactions)}")
        # print("Blocks:")
        # for block in self.blockchain:
        #     print(f"Block {block.id}, parent {block.pid}")



class Simulator:
    def __init__(self, args):
        self.time = 0 # Set Time to zero
        self.n = int(args.n) # Number of peers
        self.z0 = float(args.z0) # Fraction of slow peers
        self.z1 = float(args.z1) # Fraction of slow cpu
        self.peers = None
        self.accounts = []
        self.blockchain = [Block(0)]
        self.I = 600000 # I for Tk calculation, for normal network set 600000, for tree 600
        self.p = [] # pij (rho ij) calculation for latency
        self.runs = 10000000 # Total milliseconds to run, for normal network set 10000000, for tree 20000

    def createNetwork(self):
        # pij (rho ij) calculation for latency
        for i in range(self.n):
            l = []
            for i in range(self.n):
                l.append(random.randint(10, 500))
            self.p.append(l)

        for i in range(self.n):
            self.accounts.append(init_balance)

        self.peers = [Peer(i, random.random() < self.z0, random.random() < self.z1, self.n) for i in range(self.n)] # Add peers to network
        # Calculation of hk for Tk calculation
        a = 0 # Low cpu
        b = 0 # Fast cpu
        for i in range(self.n):
            if(self.peers[i].low_cpu):
                a += 1
            else:
                b += 1
        
        # 1 = c*a + 10*c*b; c = 1/(a + 10b)

        for i in range(self.n):
            if(self.peers[i].low_cpu):
                self.peers[i].set_hk(1/(10*b+a))
            else:
                self.peers[i].set_hk(10/(10*b+a))

        #connected = False
        # Check is network is connected

        while True:
            for i in range(self.n):
                self.peers[i].connections = set() # Initialize neighbors to nullset
            
            for i in range(self.n):
                connections = random.randint(4, 8) # Choose 3 to 6 neighbors

                for _ in range(connections):
                    connection = random.randint(0, self.n - 1) # Random neighbor id
                    if connection == i:
                        connection = (i+1)%self.n # Prevent self loop

                    self.peers[i].connections.add(connection) # Both way connection
                    # self.peers[connection].connections.add(i)

            visited = set()
            queue = []
            start_node = 0
            queue.append(start_node)
            visited.add(start_node)
            #BFS to check if graph is connected
            
            while queue:
                node = queue.pop(0)
                for neighbor in self.peers[node].connections:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            if len(visited) == self.n:
                break
            

    def run(self):
        # Initial Block creation
        for peer in self.peers:
            peer.block_creation(self.I, 0)


        run = 0

        while True:
            # print(f"Time is {run}")
            if run > self.runs:
                break

            run += 1
            # print(1)
            for peer in self.peers:
                if self.time == peer.next_arrival: # Transaction time
                    peer.next_arrival = self.time + int(np.random.exponential(Ttx)) + 1 # Update next transaction arrival
                    peer.generate_transaction(self.n, self.time) # Generate transaction

                if self.time == peer.block_wait:
                    # print(f"Mining, time = {self.time} at {peer.id}")
                    # Block maturity in mining
                    new_block = peer.mining(self.time) # Mine the block
                    peer.block_creation(self.I, self.time) # Create new block and wait for maturity
                    if new_block:
                        for neighbor in peer.connections:
                            c = 100000000 # In bits
                            if peer.slow or self.peers[neighbor].slow: # If atleast one of them is slow
                                c = 5000000

                            d = np.random.exponential(96000/c)
                            heappush(block_queue, (self.time + int(self.p[peer.id][neighbor] + new_block.size*8000*1000/c + d*1000), neighbor, new_block.id)) # Latency

            # print(2)
            # print(event_queue)

            while len(event_queue) > 0:
                item = heappop(event_queue) # Pop event
                # print(self.n)
                # print("txns")
                # print(len(all_transactions))
                # print(item)
                if item[0] > self.time: # Future event
                    heappush(event_queue, item)
                    break

                if item[1] in self.peers[item[2]].trans: # If transaction already seen ignore, for loopless transaction
                    continue

                self.peers[item[2]].transactions.add(all_transactions[item[1]-1]) # Add transaction
                self.peers[item[2]].trans.add(item[1]) # Add transaction id for loopless transaction
                for neighbor in self.peers[item[2]].connections:
                    if item[1] not in self.peers[neighbor].trans: # If neighbor has not seen the transaction
                        c = 100000000
                        if self.peers[item[2]].slow or self.peers[neighbor].slow:
                            c = 5000000

                        d = np.random.exponential(96000000/c)
                        heappush(event_queue, (self.time + int(self.p[self.peers[item[2]].id][neighbor] + 8000*1000/c + d), item[1], neighbor)) #Latency

            # print(3)

            while len(block_queue) > 0:
                item = heappop(block_queue) # Pop event
                if item[0] > self.time: # Future event
                    heappush(block_queue, item)
                    break

                if item[2] in self.peers[item[1]].blocks: # If block already seen ignore, for loopless block forecast
                    continue

                valid = self.peers[item[1]].validate_block(all_blocks[item[2]], self.time) # Validate the block
                self.peers[item[1]].blocks.add(item[2]) # Seen the block
                self.peers[item[1]].block_creation(self.I, self.time) # Continue with block creation
                if valid:
                    
                    for neighbor in self.peers[item[1]].connections:
                        if item[2] not in self.peers[neighbor].blocks:  # If neighbor has not seen the block
                            c = 100000000
                            if peer.slow or self.peers[neighbor].slow:
                                c = 5000000

                            d = np.random.exponential(96000000/c)
                            # print(self.time + int(self.p[self.peers[item[1]].id][neighbor] + new_block.size*8000*1000/c + d))
                            heappush(block_queue, (self.time + int(self.p[self.peers[item[1]].id][neighbor] + new_block.size*8000*1000/c + d), neighbor, item[2])) # Latency

            
            self.time += 1 # Increment time counter
        
        print(f"Number of transactions: {TxnId}") # Ender at the end of network runtime
        for peer in self.peers:
            peer.ender()




def main(args):
    simulator = Simulator(args)
    simulator.createNetwork()
    simulator.run()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", default = 10)
    parser.add_argument("--z0", default = 0.5)
    parser.add_argument("--z1", default = 0.5)

    args = parser.parse_args()
    main(args)