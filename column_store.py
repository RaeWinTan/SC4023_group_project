from typing import List, Any, override
from collections.abc import Callable
from enum import Enum
from collections import defaultdict
from external_sorting import ExternalSorting
class DataType(Enum):
    STRING = 1
    INTEGER = 2
    BIT = 3 


class ComparatorFunction:
    def __init__(self):
        self.comparator_callbacks = {
            "inRange": self.inRange, 
            "isLesserThanEqualToUpperBound": self.isLesserThanEqualToUpperBound,
            "isLesserThanUpperBound": self.isLesserThanUpperBound
            }
    def size(self):pass
    def get(self, idx):pass
    def inRange(self, idx, rg): pass 
    def isLesserThanEqualToUpperBound(self, idx, rg): pass 
    def isLesserThanUpperBound(self, idx, rg): pass 

class ColumnObject(ComparatorFunction):

    def __init__(self, column_name, data_type: DataType):
        super().__init__()
        self.column_name = column_name
        self.data_type = data_type
        self.data = []
        self.is_compressed = False
    
    @override 
    def inRange(self, idx, rg):
        if self.data_type in [DataType.STRING, DataType.INTEGER]: 
            return rg[0]<=self.data[idx]<=rg[1]
        return ((1<<self.data[idx]) & rg) > 0
    @override
    def size(self):
        return len(self.data)

    def load(self, value):
        if self.data_type==DataType.STRING:
            self.data.append(value)
        else:self.data.append(float(value))
    
    def reorder(self, permutation):
        self.data = ExternalSorting.reorder(permutation, self.data)
    
    @override
    def get(self, idx):
        return self.data[idx]

    def set(self, idx, val):
        self.data[idx] = val

    def make_compress(self, hm):  # word -> integer,
        self.is_compressed = True
        self.data_type = DataType.BIT
        self.hm = hm.copy()
        # the non intresting guys are just the last option
        self.ihm = defaultdict(lambda: len(self.hm)-1)
        # this will still work because i will never write a guy that is not in the hashmap list in our case
        for k, v in hm.items():
            self.ihm[v] = k
        for i, e in enumerate(self.data):
            self.data[i] = self.hm[e]

    def get_original_value(self, idx):
        if self.is_compressed:
            return self.ihm[self.data[idx]]
        return self.data[idx]

class Indexes(ComparatorFunction):
    def __init__(self, column_objects:List[ColumnObject], aggregate_fn):
        #the feature we need is baisclaly check value kinda thing
        #in this case check is mallsr
        super().__init__()
        self.column_objects = column_objects 
        self.aggregate_fn = aggregate_fn
    @override 
    def size(self):
        return self.column_objects[0].size()
    @override 
    def get(self, idx):
        return self.aggregate_fn(*[c.get(idx) for c in self.column_objects])
    @override 
    def inRange(self, idx, rg):
        return rg[0]<=self.get(idx)<=rg[1]
    @override 
    def isLesserThanEqualToUpperBound(self, idx, rg):
        return self.get(idx)<=rg[1]
    @override 
    def isLesserThanUpperBound(self, idx, rg):
        return self.get(idx)< rg[1]

class ZoneMap:
    def __init__(self, obj:ComparatorFunction, aggregate_fn: Callable[[list[tuple[int, ...]]], Any], check_fn: Callable[[tuple[int, ...]], bool], span=16):
        self.SPAN = span 
        self.size = obj.size()
        self.zones = [None]*((self.size//self.SPAN) + 1)
        for l in range(0, self.size, self.SPAN):
            r = min(l+self.SPAN, self.size)
            self.zones[l//self.SPAN] = aggregate_fn([obj.get(idx) for idx in range(l, r)])
        self.check_fn = check_fn 
    def getZone(self, idx):
        return self.zones[idx//self.SPAN]
    def checkInside(self, idx, value):
        return self.check_fn(self.zones[idx//self.SPAN], value)
    def nextIdx(self, idx):#where detect a mis continue next indexi like that
        return min(((idx+self.SPAN)//self.SPAN)*self.SPAN, self.size)
