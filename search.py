from typing import Any

from common_utils import ConditionHandler
class Search:
    VECTOR_SIZE: int = 4
    @classmethod
    def set_vector_size(cls, sz: int):
        cls.VECTOR_SIZE = sz 
    @staticmethod
    def bisect_left(indexes: Any, x: Any, l: int, r: int) -> int:
        """
        return index such that this  is smallest index that satisfies indexes.get(index)>= x 
        """
        rtn = r+1
        while l<=r:
            mid = l + (r-l)//2 
            if indexes[mid]>=x:
                rtn = mid 
                r = mid-1 
            else:
                l = mid+ 1 
        return rtn 
    
    @staticmethod
    def bisect_right(indexes: Any, x: Any, l: int, r: int):
        """
        return index such that this is the smallest index that satisfies indexes.get(index)>x
        """
        rtn = r+1 
        while l<=r:
            mid = l + (r-l)//2 
            if indexes[mid]>x:
                rtn = mid 
                r = mid-1 
            else:
                l = mid+ 1 
        return rtn 
    
    @staticmethod
    def zone_map_search(zone_maps: Any, l: int, r: int, price_per_area_handler: ConditionHandler):
        indexes = zone_maps.indexes 
        idx = l 
        rtn = -1 
        rtn_value = -1 
        while idx <=r:
            nxtIdx = min(zone_maps.nextIdx(idx), r+1)
            if zone_maps.checkInside(idx, price_per_area_handler.condition):#check if in side zone then check 
                for i in range(idx, nxtIdx):
                    condition_hit, values = indexes.comparator_callbacks[price_per_area_handler.get_call_back_name()](i, price_per_area_handler.condition)
                    if condition_hit:
                        rtn = i
                        rtn_value = values 
                        price_per_area_handler(indexes[i])
            idx = nxtIdx
        return rtn, rtn_value
