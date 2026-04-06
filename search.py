from typing import List

from column_store import  ZoneMap, Indexes, ComparatorFunction
from common_utils import ConditionHandler, EarlyStopping
class Search:
    VECTOR_SIZE = 4
    @classmethod
    def set_vector_size(cls, sz):
        cls.VECTOR_SIZE = sz 
    @staticmethod
    def bisect_left(indexes:(Indexes | ZoneMap), x, l, r):
        #return index such that this  is smallest index that satisfies indexes.get(index)>= x 
        rtn = l 
        while l<=r:
            mid = l + (r-l)//2 
            if indexes.get(mid)>=x:
                rtn = mid 
                r = mid-1 
            else:
                l = mid+ 1 
        return rtn 
    """
    EARLY STOPPING: 
        YEAR_MONTH: WHEN ZONE START > condition end 
    JUMP CONDITION:
        1. ON_CONDITION_HIT:
        2. WHEN price/sqm > condition -> price/sqm >=condition 
    
    3 callbacks:
        ON_ROW_HIT-> update condition 
        ON_PRICE_PER_SQM bellow upper bound(WILL CHANGE AS THINGS GOA BOUTN)
        ON_ZONE_START>CONDITION_END => EARLY STOPPGIN
    """
    #early stopping, when (year, month) start > (year, month) end->no need process nymore 
    #early stopping for year, month conditions
    #and
    #bascilly when a all hit in the row thing
        #want ot jump zones using binary search to the next guy 
    #early stopping(zone,map loop and vectoriztion) -> just check range not over lappign
    #two condtiion handlers only on_price_per_sqm, on_year_month_exceed
    @staticmethod
    def zone_map_search(zone_maps:List[ZoneMap], conditions, values:List[ComparatorFunction], condition_handlers:List,on_row_hit,l):
        rtn = -1 
        idx = l 
        r = zone_maps[0].size
        while idx<r:
            #lazy evaluation of conditions to prevent unneccessary zonemap reads 
            earlyBreak = False 
            for i in range(len(zone_maps)):
                zm = zone_maps[i]
                #condition handleres for this #zone regeion updaet, no increasement 
                condition_handlers[i].on_zone_update()#this will only 
                if not zm.checkInside(idx, conditions[i]): 
                    earlyBreak=True 
                    break 
            if not earlyBreak:#every thing is inside 
                pass 
            if any((not zm.checkInside(idx, conditions[i])) for i,zm in enumerate(zone_maps) ):
                #check condition here 
                for i in range()
                if conditions[0][0]<zone_maps[0].getZone(idx)[0]: #must update condition too for early stopping
                    conditions[0] = (zone_maps[0].getZone(idx)[0],conditions[0][1])
                 
                idx = zone_maps[0].nextIdx(idx)
            else:
                end = min(zone_maps[0].nextIdx(idx), r)
                tmp = -1 
                for j in range(idx, end, Search.VECTOR_SIZE):
                    tmp = Search.vectorization(j, min(j+Search.VECTOR_SIZE-1, end-1), values, conditions, condition_handlers, early_stopping)
                    if tmp!=-1:  rtn = tmp
        

                idx = end 
        return rtn 
    @staticmethod
    def vectorization(l,r, values:List[ComparatorFunction], conditions, condition_handlers:List[ConditionHandler], early_stopping:EarlyStopping):#l,r is somewhat define by the zone map
        rtn = -1 
        for idx in range(l,r+1):
            #lazy evaluation of condititions to prevent unneccessary column store/indexes reads
            if all(c.comparator_callbacks[condition_handlers[i].get_call_back_name()](idx, conditions[i]) for i,c in enumerate(values)):
                for i in range(len(values)):
                    conditions[i]= condition_handlers[i].on_row_hit(values[i].get(idx), conditions[i])
                    rtn = idx
                    #when a hit happens -> condition changes 
                if early_stopping.can_stop():
                    return rtn 

        return rtn 

