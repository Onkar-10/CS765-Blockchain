// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;





contract Payment {
  uint numUsers;
  event Debug(uint message);
  mapping (uint => string) public userNames;
  struct Edge {
    uint dest;
    uint bal;
  }

  mapping(uint => Edge[]) private adjList;
 mapping(uint => uint) private dist;
    mapping(uint => bool) private visited;
    // mapping(uint => uint) private prev; 
  constructor() {
    numUsers = 0;
  }

  function registerUser(uint user_id, string memory user_name) public returns (bool){
    if(bytes(userNames[user_id]).length > 0){
      return false;
    }
    userNames[user_id] = user_name;
    numUsers+=1;
    return true;
  } 

  function createAcc(uint user_id_1, uint user_id_2, uint init_balance) public {

    adjList[user_id_1].push(Edge({dest: user_id_2, bal: init_balance}));
    adjList[user_id_2].push(Edge({dest: user_id_1, bal: init_balance}));
  }

function sendAmount(uint start, uint end) public returns (uint[] memory) {
    require(start != end, "Start and end nodes cannot be the same");
    
    for (uint i = 0; i < numUsers; i++) {
        dist[i] = 100000; // set initial distances to infinity
        visited[i] = false; // mark all nodes as unvisited
    }
    
    dist[start] = 0; // set distance of start node to zero
    visited[start] = true; // mark start node as visited
    
    uint[] memory queue = new uint[](numUsers);
    uint[] memory prev = new uint[](numUsers);
    uint front = 0;
    uint rear = 0;
    
    queue[rear++] = start; // add start node to the queue
    
    while (front != rear) {
        uint curr = queue[front++]; // dequeue the front node
        
        for (uint i = 0; i < adjList[curr].length; i++) {
            uint neighbor = adjList[curr][i].dest;
            
            if (!visited[neighbor]) {
                visited[neighbor] = true; // mark neighbor as visited
                dist[neighbor] = dist[curr] + 1; // update distance to neighbor
                prev[neighbor] = curr; // update previous node for neighbor
                queue[rear++] = neighbor; // enqueue neighbor
            }
            
            if (neighbor == end) {
                // shortest path found, construct path and return it
                uint[] memory path = new uint[](dist[neighbor] + 1);
                uint j = dist[neighbor];
                path[j] = end;
                
                while (j > 0) {
                    j--;
                    path[j] = prev[path[j+1]];
                }
                
                assert(path.length > 0);
                uint flag1=0;
                for (uint i1=0; i1<path.length-1; i1++) {
                    uint j1 = i1+1;
                    uint ii = path[i1];
                    uint jj = path[j1];
                    for (uint k=0; k<adjList[ii].length; k++) {
                        if (adjList[ii][k].dest == jj) {
                            if(adjList[ii][k].bal==0){
                              flag1=1;
                              break;
                            }
                            adjList[ii][k].bal -= 1;
                            break;
                        }
                    }
                    if(flag1==1){
                      break;
                    }
                   
                    for (uint k=0; k<adjList[jj].length; k++) {
                        if (adjList[jj][k].dest == ii) {
                            adjList[jj][k].bal += 1;
                            break;
                        }
                    }
                }
                if(flag1==1){
                  //path[dist[neighbor]+1]=75;
                  return new uint[](0);
                }
                return path;
            }
        }
    }

    
    
    uint[] memory path1 = new uint[](2);
    path1[0]=2;
    path1[1]=2;
    return path1;
}




//   function sendAmount(uint user_id_1, uint user_id_2) public returns (uint[] memory) {
//     uint[] memory path;
//     if (user_id_1 == user_id_2) {
//         path = new uint[](1);
//         path[0] = user_id_1;
//         return path;
//     }
//     for (uint i = 0; i < numUsers; i++) {
//         dist[i] = 2**256-1;
//         visited[i] = false;
//     }
//     dist[user_id_1] = 0;
//     visited[user_id_1] = true;
//     uint[] memory queue = new uint[](numUsers);
//     uint queue_front = 0;
//     uint queue_back = 0;
//     queue[queue_back++] = user_id_1;
//     while (queue_front != queue_back) {
//         uint u = queue[queue_front++];
//         for (uint i = 0; i < adjList[u].length; i++) {
//             Edge memory e = adjList[u][i];
//             uint v = e.dest;
//             uint alt = dist[u] + e.bal;
//             if (alt < dist[v]) {
//                 dist[v] = alt;
//                 prev[v] = u;
//                 if (!visited[v]) {
//                     visited[v] = true;
//                     queue[queue_back++] = v;
//                 }
//             }
//             if (v == user_id_2) {
//                 path = new uint[](dist[v] / 2 + 1);
//                 uint current = user_id_2;
//                 uint index = path.length - 1;
//                 while (current != user_id_1) {
//                     path[index--] = current;
//                     current = prev[current];
//                 }
//                 path[index] = user_id_1;
//                 return path;
//             }
//         }
//     }
//     return path;
// }



// // Helper function to find the node with the minimum distance value
// function findMinDist(mapping(uint => uint) storage dist1, mapping(uint => bool) storage visited1) private view returns (uint) {
//     uint minDist = 10000;
//     uint minNode;
//     for (uint i = 0; i < numUsers; i++) {
//         if (!visited1[i] && dist1[i] <= minDist) {
//             minDist = dist1[i];
//             minNode = i;
//         }
//     }
//     return minNode;
// }


// function findPrevNode(uint current, mapping(uint => uint) storage dist1) private view returns (uint) {
//     uint prevNode = 10000;
//     uint minIndex = numUsers;
//     for (uint i = 0; i < adjList[current].length; i++) {
//         uint node = adjList[current][i].dest;
//         uint weight = adjList[current][i].bal;
//         if (dist1[node] + weight == dist1[current]) {
//             if (node < minIndex) {
//                 minIndex = node;
//                 prevNode = node;
//             }
//         }
//     }
//     if (prevNode == 10000) {
//         return current;
//     }
//     return prevNode;
// }



  

  function closeAccount(uint user_id_1, uint user_id_2) public returns(bool){
    if(bytes(userNames[user_id_1]).length == 0){
      return false;
    }
    if(bytes(userNames[user_id_2]).length == 0){
      return false;
    }
    for(uint i=0; i<adjList[user_id_1].length; i++){
      if(adjList[user_id_1][i].dest == user_id_2){
        adjList[user_id_1][i] = adjList[user_id_1][adjList[user_id_1].length-1];
        adjList[user_id_1].pop();
        break;
      }
      if(i == adjList[user_id_1].length-1) return false;
    }
    for(uint i=0; i<adjList[user_id_2].length; i++){
      if(adjList[user_id_2][i].dest == user_id_1){
        adjList[user_id_2][i] = adjList[user_id_2][adjList[user_id_2].length-1];
        adjList[user_id_2].pop();
        break;
      }
      if(i == adjList[user_id_2].length-1) return false;
    }
    return true;
  }
}


