from typing import List

from column_store import  ZoneMap, Indexes, ComparatorFunction

class Search:
    VECTOR_SIZE = 4
    @classmethod
    def set_vector_size(cls, sz):
        cls.VECTOR_SIZE = sz 
    @staticmethod
    def bisect_left(indexes:Indexes, x, l, r):
        #return index such that this index and up is >= x 
        rtn = l 
        while l<=r:
            mid = l + (r-l)//2 
            if indexes.get(mid)>=x:
                rtn = mid 
                r = mid-1 
            else:
                l = mid+ 1 
        return rtn 
    @staticmethod
    def bisect_right(indexes:Indexes, x,l,r):
        #return index such taht this index and up is >x 
        rtn = r+1 
        while l<=r:
            mid = l + (r-l)//2 
            if indexes.get(mid)>x:
                rtn = mid 
                r = mid -1 
            else:
                l = mid+1 
        return rtn 
    @staticmethod
    def binary_search(index:Indexes, rg, l, r):#rg = (lower bound, upper bound)
        left = Search.bisect_left(index, rg[0], l, r)
        right = Search.bisect_right(index, rg[1], l, r)
        return (left, right-1)    
    @staticmethod
    def zone_map_search(zone_maps:List[ZoneMap], conditions, values:List[ComparatorFunction], condition_call_backs, change_fns, l,r):
        rtn = -1 
        idx = l 
        current_call_back_indexes = [0]*len(values)
        while idx<r+1:
            #lazy evaluation of conditions to prevent unneccessary zonemap reads 
            if any((not zm.checkInside(idx, conditions[i])) for i,zm in enumerate(zone_maps) ):
                idx = zone_maps[0].nextIdx(idx)
            else:
                end = min(zone_maps[0].nextIdx(idx), r+1)
                for j in range(idx, end, Search.VECTOR_SIZE):
                    tmp = Search.vectorization(j, min(j+Search.VECTOR_SIZE-1, end-1), values, conditions, current_call_back_indexes, condition_call_backs, change_fns)
                    if tmp!=-1: rtn = tmp 
                idx = end 
        return rtn 
    @staticmethod
    def vectorization(l,r, values:List[ComparatorFunction], conditions_values, current_call_back_indexes, conditions_call_backs, change_fn):#l,r is somewhat define by the zone map
        rtn = -1 
        for idx in range(l,r+1):
            #lazy evaluation of condititions to prevent unneccessary column store/indexes reads
            if all(c.comparator_callbacks[conditions_call_backs[i][current_call_back_indexes[i]]](idx, conditions_values[i]) for i,c in enumerate(values)):
                for i in range(len(values)):
                    conditions_values[i], current_call_back_indexes[i] = change_fn[i](values[i].get(idx), conditions_values[i])
                    rtn = idx 
        return rtn 

