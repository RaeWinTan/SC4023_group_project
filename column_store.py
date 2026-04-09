import math
from typing import Any
from collections.abc import Callable
from enum import Enum
from collections import defaultdict

from indexdatastructure import IndexDataStucture
class DataType(Enum):
    STRING = 1
    INTEGER = 2


class ColumnObject:
    COLUMN_READ: int = 0 
    index_datastructure: IndexDataStucture | None = None

    def __init__(self, column_name: str, data_type: DataType):
        super().__init__()
        self.column_name: str = column_name
        self.data_type: DataType = data_type
        self.data: list[Any] = []
        self.hm: dict[Any, int] = dict() # Lookup Table to map values to compressed versions
        self.ihm: dict[int, Any] = dict() # Reverse Lookup Table to map compressed values to uncompressed versions
        self.is_compressed: bool = False

    @classmethod
    def set_index_datastructure(cls, val:IndexDataStucture):
        cls.index_datastructure = val 

    @classmethod 
    def getColumnRead(cls) -> int:
        return cls.COLUMN_READ

    def size(self) -> int:
        return len(self)
    
    def __len__(self) -> int:
        return len(self.data)

    def load(self, value: Any):
        """Append a value to the store"""
        if self.data_type==DataType.STRING:
            self.data.append(value)
        else:self.data.append(float(value))
    
    def get(self, idx: int) -> Any:
        """
        Gets the *raw* value stored at the key specified, which may be compressed
        Increments the statistics counter
        """
        return self[idx]

    
    def __getitem__(self, key: int) -> Any:
        """
        Gets the *raw* value stored at the key specified, which may be compressed
        Increments the statistics counter
        """
        ColumnObject.COLUMN_READ+=1 
        return self.data[key]
    
    def make_compress(self, hm: dict[Any, int]):
        """
        Compresses a column given a mapping from values to compressed values
        """
        self.is_compressed = True
        self.data_type = DataType.INTEGER
        self.hm = hm.copy()
        self.ihm: dict[int, Any] = defaultdict(lambda: len(self.hm)-1)
        for k, v in hm.items():
            self.ihm[v] = k
        for i, e in enumerate(self.data):
            self.data[i] = self.hm[e]

    def get_original_value(self, idx: int) -> Any:
        """
        Gets the *original*, uncompressed value
        Increments the statistics counter
        """
        v = self[idx]
        return self.ihm[v] if self.is_compressed else v
class Indexes[R]:
    def __init__(self, column_objects:list[ColumnObject], agg_fn: Callable[..., R]):
        """
        Produces aggregated columns on the fly, similar to a VIEW in SQL.
        Each .get(idx) returns agg_fn(column_objects[0].get(idx), column_objects[1].get(idx), ...)

        Args
        ====
            column_objects: list[ColumnObject]
                list of columns to aggregate
            agg_fn : Callable
                Produce a single aggregated result from the values of aggregated columns
        """
        self.comparator_callbacks = {
            "isLesserThanEqualToUpperBound": self.isLesserThanEqualToUpperBound,
            "isLesserThanUpperBound": self.isLesserThanUpperBound
        }
        self.column_objects: list[ColumnObject] = column_objects 
        self.agg_fn: Callable[..., R] = agg_fn 
     
    def size(self) -> int:
        return len(self)
    
    def __len__(self) -> int:
        return len(self.column_objects[0])
    
    def get(self, idx: int) -> R:
        return self[idx]
    
    def __getitem__(self, key: int) -> R:
        collect = map(lambda c: c[key], self.column_objects)
        return self.agg_fn(*collect)
    
    def get_with_original_value(self, idx: int) -> tuple[R, list[Any]]:
        rtn = list(map(lambda c: c[idx], self.column_objects))
        return self.agg_fn(*rtn), rtn
    
    def isLesserThanEqualToUpperBound(self, idx, rg):
        val,ori = self.get_with_original_value(idx)
        return val<=rg[1], ori
     
    def isLesserThanUpperBound(self, idx, rg):
        val,ori = self.get_with_original_value(idx)
        return val< rg[1], ori

class ZoneMap[T]:
    SPAN: int = 16
    ZONE_READ: int = 0 
    def __init__(self, obj:Indexes[tuple[int, ...]], aggregate_fn: Callable[[list[tuple[int, ...]]], tuple[T,T]]):
        self.size = obj.size()
        self.zones: list[tuple[T,T]] = [] # [None]*((self.size//self.SPAN) + (0 if ((self.size%self.SPAN)==0) else 1))
        num_zones = math.ceil(len(obj) / self.SPAN)
        for i in range(num_zones):
            l = i * self.SPAN
            r = min(l+self.SPAN, self.size)
            self.zones.append(aggregate_fn([obj[idx] for idx in range(l, r)]))
        self.indexes = obj
    @classmethod 
    def getZoneRead(cls):
        return cls.ZONE_READ 
    def getZone(self, idx: int) -> tuple[T,T]:
        return self[idx]
    def __getitem__(self, key: int) -> tuple[T,T]:
        ZoneMap.ZONE_READ+=1 
        return self.zones[key//self.SPAN]
    def checkInside(self, idx: int, value: tuple[T,T]) -> bool:
        zl,zr = self[idx]
        return  not ( zr < value[0] or value[1] < zl) # pyright: ignore[reportOperatorIssue]
    def nextIdx(self, idx: int) -> int:
        """Skip ahead to the index where the next zone begins"""
        return min(((idx+self.SPAN)//self.SPAN)*self.SPAN, self.size)
    