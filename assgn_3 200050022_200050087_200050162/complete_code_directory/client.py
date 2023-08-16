import json
from web3 import *
import sys
import itertools
import time
import argparse
import random
import numpy as np
import math
from heapq import *  # For the event queues

#connect to the local ethereum blockchain
provider = Web3.HTTPProvider('http://127.0.0.1:8545')
w3 = Web3(provider)
#check if ethereum is connected
if(w3.is_connected()):
    print(" Etherium connected successfully")

#replace the address with your contract address (!very important)
deployed_contract_address = '0x92542Dc9D81A75bcCb1f8AAD4aE7B4Cb4C440CCC'      

#path of the contract json file. edit it with your contract json file
compiled_contract_path ="build/contracts/Payment.json"
with open(compiled_contract_path) as file:
    contract_json = json.load(file)
    contract_abi = contract_json['abi']
contract = w3.eth.contract(address = deployed_contract_address, abi = contract_abi)



'''
#Calling a contract function createAcc(uint,uint,uint)
txn_receipt = contract.functions.createAcc(1, 2, 5).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':2409638})
txn_receipt_json = json.loads(w3.to_json(txn_receipt))
print(txn_receipt_json) # print transaction hash

# print block info that has the transaction)
print(w3.eth.get_transaction(txn_receipt_json)) 

#Call a read only contract function by replacing transact() with call()

'''

#Add your Code here 
''' 
1) need to make a class to make a connected graph
2) tranlate that graph into the solidity contract
3) fire 1000 txns 
4) close connections 
'''
np.random.seed(789)
class Simulator:
    def __init__(self, args):
        self.n = args.n # Number of peers
        self.txns = args.txns
        self.peers = None
        self.network = None
        self.success = None

    def registerUser(self,userid, username):
        txn_hash = contract.functions.registerUser(userid, username).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':6721975})
        return txn_hash

    def createAcc(self,id1, id2, amt):
        txn_hash = contract.functions.createAcc(id1, id2, amt).transact( {'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':6721975} )
        return txn_hash
    
    def sendAmount(self,id1, id2):
        global failed_txns
        result1 = contract.functions.sendAmount(id1, id2).call()
        if result1==[]:
            failed_txns+=1
        txn_hash = contract.functions.sendAmount(id1, id2).transact( {'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':6721975} )
        return txn_hash
    def closeAccount(self,id1, id2):
        txn_hash = contract.functions.closeAccount(id1, id2).transact( {'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':6721975} )
        return txn_hash
    
    def createNetwork(self):

        for i in range(self.n):
            # pass
            tx = self.registerUser(i, str(i))
            temp = None
            while temp is None:
                temp = w3.eth.get_transaction_receipt(tx)
                time.sleep(1)
            print("Registered", i, temp)
            # call register user 


        # def random_subset_with_weights(weights, m):
        #     mapped_weights = [(random.expovariate(w), i) for i, w in enumerate(weights)]
        #     return {i for _, i in sorted(mapped_weights)[:m]}

        # Initialise with a complete graph on m vertices.
                    # https://stackoverflow.com/a/59055822/6352364

        m=2
        neighbours = [set(range(m)) - {i} for i in range(m)]
        degrees = [m - 1 for i in range(m)]

        for i in range(m, self.n):
            # n_neighbours = random_subset_with_weights(degrees, m)
            mapped_weights = [(random.expovariate(w), j) for j, w in enumerate(degrees)]
            n_neighbours= {j for _, j in sorted(mapped_weights)[:m]}
            # add node with back-edges
            neighbours.append(n_neighbours)
            degrees.append(m)

            # add forward-edges
            for j in n_neighbours:
                neighbours[j].add(i)
                degrees[j] += 1

        self.peers=dict(enumerate(neighbours))
        # print("23 ",self.peers)

        visited = set()
        queue = []
        start_node = 0
        queue.append(start_node)
        # visited.add(start_node)

        # BFS to check if graph is connected
        
        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                queue.extend(self.peers[node] - visited)
        # print(len(visited))
        # if len(visited) == self.n:
        #     print("lol")

        for i, j in itertools.combinations(self.peers, 2):
            if j in self.peers[i]: # ensure that i and j are connected
                contri = np.random.exponential(scale=10,size=None)
                tx = self.createAcc(i, j, math.floor((contri+1)/2))
                receipt = None
                while receipt is None:
                    receipt = w3.eth.get_transaction_receipt(tx)
                    time.sleep(1)
                print("Account Created ", i, j, math.floor((contri+1)/2), receipt)

     

            
      
    def run(self):
        # pass
        global arr
        global failed_txns
       
        global arr
        for i in range(self.txns):
            source, dest = None, None
            while source == dest:
                source = random.randint(0, self.n - 1)
                dest = random.randint(0, self.n - 1)
            tx = self.sendAmount(source, dest)
            receipt = None
            while receipt is None:
                receipt = w3.eth.get_transaction_receipt(tx)
                time.sleep(0.5)
            print(i," Amt sending attempted", source, dest, receipt)
            if i%100==99:
                # arr[math.floor(i/100)]=failed_txns/100
                arr.append(failed_txns/100)
                # print(failed_txns)
                failed_txns=0
        if self.txns%100!=0:
            arr.append(failed_txns/(self.txns%100))
            # arr[math.floor(i/100)]=failed_txns/100
            # print(failed_txns)
            failed_txns=0



    def end(self):
        # print(self.peers)
        for i, j in itertools.combinations(self.peers, 2):
            if j in self.peers[i]: # ensure that i and j are connectedf
                tx = self.closeAccount(i,j)
                receipt = None
                while receipt is None:
                    receipt = w3.eth.get_transaction_receipt(tx)
                    time.sleep(1)
                print("Account Closed between", i, j,receipt)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int,default = 100)
    parser.add_argument("--txns", type=int,default = 1000)
    args = parser.parse_args()
    arr=[]
    failed_txns=0
    simulator = Simulator(args)
    simulator.createNetwork()
    simulator.run() 
    print("Success ratio of each 100 txns:")
    for i in arr:
        print("Success ratio of txns: ",1-i)
    # simulator.end() 

    
    
