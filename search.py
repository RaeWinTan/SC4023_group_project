
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
    def zone_map_search(zone_maps,l,r, price_per_area_handler: ConditionHandler, mn_sqm,y):
        indexes = zone_maps.indexes 
        idx = l 
        rtn = -1 
        while idx <=r:
            if indexes.comparator_callbacks[price_per_area_handler.get_call_back_name()](idx, price_per_area_handler.condition):
                tmp,val = indexes.get_with_val(idx)
                if tmp <mn_sqm and val[1]>=y:
                    mn_sqm = tmp 
                    rtn = idx 
            idx+=1 
        return rtn, mn_sqm 
