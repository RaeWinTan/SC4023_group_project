from typing import List

from column_store import ColumnObject, ZoneMap, Indexes, ComparatorFunction

VECTOR_SIZE = 4 

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

def binary_search(index:Indexes, rg, l, r):#rg = (lower bound, upper bound)
    left = bisect_left(index, rg[0], l, r)
    right = bisect_right(index, rg[1], l, r)
    return (left, right-1)    

def zone_map_search(zone_maps:List[ZoneMap], conditions, values:List[ComparatorFunction], condition_call_backs, change_fns, l,r):
    rtn = -1 
    idx = l 
    current_call_back_indexes = [0]*len(values)
    while idx<r+1:
        if not all([zm.checkInside(idx, conditions[i]) for i,zm in enumerate(zone_maps)]):
            """
            print("MISED",[zm.checkInside(idx, conditions[i]) for i,zm in enumerate(zone_maps)])
            print(conditions)
            print([zm.getZone(idx) for i,zm in enumerate(zone_maps)])
            input()
            """
            idx = zone_maps[0].nextIdx(idx)
        else:
            #print("ZONE HIT")
            end = min(zone_maps[0].nextIdx(idx), r+1)
            for j in range(idx, end, VECTOR_SIZE):
                tmp = vectorization(j, min(j+VECTOR_SIZE-1, end-1), values, conditions, current_call_back_indexes, condition_call_backs, change_fns)
                if tmp!=-1: rtn = tmp 
            idx = end 
    return rtn 

def vectorization(l,r, values:List[ComparatorFunction], conditions_values, current_call_back_indexes, conditions_call_backs, change_fn):#l,r is somewhat define by the zone map
    rtn = -1 
    for idx in range(l,r+1):
        if all([c.comparator_callbacks[conditions_call_backs[i][current_call_back_indexes[i]]](idx, conditions_values[i]) for i,c in enumerate(values)]):
            #for a singular row all hits 
            #print("ALL HIT AT", [[cs.get(idx) for cs in v.column_objects] if type(v) == Indexes else v.get(idx) for v in values], idx)
            for i in range(len(values)):
                conditions_values[i], current_call_back_indexes[i] = change_fn[i](values[i].get(idx), conditions_values[i])
                rtn = idx 
    return rtn 
#now zone search 

"""

"""