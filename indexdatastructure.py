from typing import List


from search import Search
from collections import deque 
class IndexDataStucture:
    """
    Maintain a datastucture to give the first 
    occurance of a primary_index very quickly.

    This is maintained in memory.
    """
    def __init__(self, index_arr , counts: List[int]):
        self.depth = len(counts)
        self.nested_tree = []
        self.initialize_datastructure(counts)
        self.index_arr = index_arr 
        self.fill_datastructure(self.index_arr)
            
    def initialize_datastructure(self, counts):
        #tree structure (start pos, end pos, next indexing)
        q = deque([self.nested_tree])
        for i,c in enumerate(counts):
            tmp = len(q)
            for _ in range(tmp):
                curr = q.popleft()
                if i == len(counts)-1:
                    curr.extend([[-1,-1, None] for _ in range(c)])#initlaize all starts and end to -1, -1
                else:
                    for _ in range(c):
                        tt = [] 
                        curr.append([-1,-1,tt])
                        q.append(tt)

    def fill_datastructure(self, index_arr):
        q = deque([(self.nested_tree, 0 , index_arr[0].size()-1)])
        for i_idx in range(len(index_arr)):
            tmp = len(q)
            for _ in range(tmp):
                node,l,r = q.popleft()
                for key in range(len(node)):
                    left = Search.bisect_left(index_arr[i_idx], key, l, r)
                    right = Search.bisect_right(index_arr[i_idx], key, l,r)
                    if right-left>=0:
                        node[key][0] = left #updatehing the node values in tree
                        node[key][1] = right-1 
                        if i_idx!=len(index_arr)-1:
                            q.append( (node[key][2], left, right-1))
    
    def search_node(self, keys:List[int]):
        if len(keys)>self.depth: raise Exception("nubmer of keys more than depth")
        curr = self.nested_tree 
        for k in keys:
            curr = curr[k]
        return curr #(left_pos, right_pos, nextNode)

    
         

    
