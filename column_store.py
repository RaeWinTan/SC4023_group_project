from typing import List, override
from collections.abc import Callable
from enum import Enum
from collections import defaultdict

from indexdatastructure import IndexDataStucture
class DataType(Enum):
    STRING = 1
    INTEGER = 2


class ColumnObject:
    COLUMN_READ = 0 
    index_datastructure:IndexDataStucture = None 
    def __init__(self, column_name, data_type: DataType):
        super().__init__()
        self.column_name = column_name
        self.data_type = data_type
        self.data = []
        self.is_compressed = False

    @classmethod
    def set_index_datastructure(cls, val:IndexDataStucture):
        cls.index_datastructure = val 

    @classmethod 
    def getColumnRead(cls):
        return cls.COLUMN_READ

    def size(self):
        return len(self.data)

    def load(self, value):
        if self.data_type==DataType.STRING:
            self.data.append(value)
        else:self.data.append(float(value))
    
    def get(self, idx):
        ColumnObject.COLUMN_READ+=1 
        return self.data[idx]
    
    def make_compress(self, hm):
        self.is_compressed = True
        self.data_type = DataType.INTEGER
        self.hm = hm.copy()
        self.ihm = defaultdict(lambda: len(self.hm)-1)
        for k, v in hm.items():
            self.ihm[v] = k
        for i, e in enumerate(self.data):
            self.data[i] = self.hm[e]

    def get_original_value(self, idx):
        if self.is_compressed:
            return self.ihm[self.data[idx]]
        return self.data[idx]

class Indexes:
    def __init__(self, column_objects:List[ColumnObject], agg_fn):
        self.comparator_callbacks = {
            "isLesserThanEqualToUpperBound": self.isLesserThanEqualToUpperBound,
            "isLesserThanUpperBound": self.isLesserThanUpperBound
        }
        self.column_objects = column_objects 
        self.agg_fn = agg_fn 
     
    def size(self):
        return self.column_objects[0].size()
     
    def get(self, idx):
        return self.agg_fn(*[c_obj.get(idx) for c_obj in self.column_objects])
    
    def get_with_val(self, idx):
        val = [c_obj.get(idx) for c_obj in self.column_objects]
        return self.agg_fn(*val), val
     
    def isLesserThanEqualToUpperBound(self, idx, rg):
        return self.get(idx)<=rg[1]
     
    def isLesserThanUpperBound(self, idx, rg):
        return self.get(idx)< rg[1]

class ZoneMap:
    SPAN = 16
    ZONE_READ = 0 
    def __init__(self, obj:Indexes, aggregate_fn: Callable[[list[tuple[int, ...]]], any]):
        self.size = obj.size()
        self.zones = [None]*((self.size//self.SPAN) + (0 if ((self.size%self.SPAN)==0) else 1))
        for l in range(0, self.size, self.SPAN):
            r = min(l+self.SPAN, self.size)
            self.zones[l//self.SPAN] = aggregate_fn([obj.get(idx) for idx in range(l, r)])
        self.indexes = obj
    @classmethod 
    def getZoneRead(cls):
        return cls.ZONE_READ 
    def getZone(self, idx):
        ZoneMap.ZONE_READ+=1 
        return self.zones[idx//self.SPAN]
    def checkInside(self, idx, value):
        zl,zr = self.getZone(idx)
        return  not ( zr < value[0] or value[1] < zl)
    def nextIdx(self, idx):
        return min(((idx+self.SPAN)//self.SPAN)*self.SPAN, self.size)
    