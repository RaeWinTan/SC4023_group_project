
from common_utils import ConditionHandler
class Search:
    VECTOR_SIZE = 4
    @classmethod
    def set_vector_size(cls, sz):
        cls.VECTOR_SIZE = sz 
    @staticmethod
    def bisect_left(indexes, x, l, r):
        #return index such that this  is smallest index that satisfies indexes.get(index)>= x 
        rtn = r+1
        while l<=r:
            mid = l + (r-l)//2 
            if indexes.get(mid)>=x:
                rtn = mid 
                r = mid-1 
            else:
                l = mid+ 1 
        return rtn 
    
    @staticmethod
    def bisect_right(indexes, x, l, r):
        #return index such that this is the smallest index that satisfies indexes.get(index)>x
        rtn = r+1 
        while l<=r:
            mid = l + (r-l)//2 
            if indexes.get(mid)>x:
                rtn = mid 
                r = mid-1 
            else:
                l = mid+ 1 
        return rtn 
    
    @staticmethod
    def zone_map_search(zone_maps,l,r, price_per_area_handler: ConditionHandler, mn_sqm):
        indexes = zone_maps.indexes 
        idx = l 
        rtn = -1 
        while idx <=r:
            nxtIdx = min(zone_maps.nextIdx(idx), r+1)
            if zone_maps.checkInside(idx, price_per_area_handler.condition):#check if in side zone then check 
                for i in range(idx, nxtIdx):
                    if indexes.comparator_callbacks[price_per_area_handler.get_call_back_name()](i, price_per_area_handler.condition):
                        tmp = indexes.get(i)
                        if tmp <mn_sqm:
                            mn_sqm = tmp 
                            rtn = i 
            idx = nxtIdx
        return rtn, mn_sqm 
