from column_store import Indexes 
from bisect import bisect_left 
class IndexDataStucture:
    """
    Maintain a datastucture to give the first 
    occurance of a primary_index very quickly.

    This is maintained in memory.
    """
    def __init__(self, primary_index: Indexes):
        self.size = primary_index.size() 
        self.keys = [] 
        self.first_occurance = []
        for idx in range(primary_index.size()):
            if idx==0 or primary_index.get(idx)!=primary_index.get(idx-1):
                self.keys.append(primary_index.get(idx))
                self.first_occurance.append(idx)
        self.first_occurance.append(self.size)

    def findFirstOccurance(self, val):
        return self.first_occurance[bisect_left(self.keys, val)]
        
                
    
         

    
