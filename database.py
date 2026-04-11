from collections import OrderedDict
from typing import List
from column_store import ColumnObject, ZoneMap, Indexes
from writer import Writer
from search import Search
from common_utils import ConditionHandler, getQueryParameters, reduce_upper_bound
from external_sorting import ExternalSorting
from indexdatastructure import IndexDataStucture

class DataBase:
    QUERY_CALLED = 0 
    def __init__(self, column_names, data_types):
        self.column_stores = dict()
        for i, name in enumerate(column_names):
            self.column_stores[name] = ColumnObject(name, data_types[i])
        self.writer = Writer()
        self.size = 0 
        self.indexes = OrderedDict()
        self.zone_maps = OrderedDict()
    @classmethod 
    def get_query_called(cls):
        return cls.QUERY_CALLED
    def load_data(self, data):
        assert set(data.keys())==set(self.column_stores.keys()), "All columns must match columns in database"
        self.size += 1 
        for name, v in data.items():
            cs:ColumnObject = self.column_stores[name]
            cs.load(v)

    def compress_column(self, column_name, hm):
        self.column_stores[column_name].make_compress(hm)

    def index_columns(self, indexes:List[List[str]], agg_fn,ct_arr):
        ct = len(ct_arr)
        krr = [] 
        for ic, col in enumerate(indexes):
            key = tuple(col) if len(col)>1 else col[0]
            self.indexes[key] = Indexes([self.column_stores[c] for c in col], agg_fn[ic])
            krr.append(key)
        ExternalSorting.index_sorting(self.size, [self.indexes[k] for k in krr], self.column_stores)
        index_arr = [self.indexes[krr[i]] for i in range(ct)]
        ColumnObject.set_index_datastructure(IndexDataStucture(index_arr, ct_arr))
        
    def zone_map_columns(self, index: tuple[str,...], aggregate_fn):
        obj = self.indexes[index]
        self.zone_maps[index] = ZoneMap(obj, aggregate_fn)

    def write_data(self, x,y,row_number, columns,aggregation_columns, aggregation_functions, data_types,
                   output_names):
        values = [] 
        for name in columns:
            cs:ColumnObject = self.column_stores[name]
            values.append(cs.get_original_value(row_number)) 
        for i in range(len(aggregation_functions)):
            fn = aggregation_functions[i]
            col_names = aggregation_columns[i]
            col_values = [self.column_stores[nm].get_original_value(row_number) for nm in col_names]
            values.append(fn(*col_values))
        rtn = [f"({x}, {y})"]
        for i,v in enumerate(values):
            tmp = data_types[i](v)
            if isinstance(tmp, tuple): rtn.extend(list(tmp))
            else:rtn.append(tmp)
        self.writer.write(output_names, rtn)
        
        
    def query(self, x, y, mat_id):
        DataBase.QUERY_CALLED+=1
        start_time, end_time, town_values= getQueryParameters(x,mat_id)
        town_index_ds = [ColumnObject.index_datastructure.search_node([t]) for t in town_values]
        rtn = -1 
        mn_area = float("inf")
        price_per_area_condition = [0, 4725] 
        price_per_area_handler = ConditionHandler(price_per_area_condition, ["isLesserThanEqualToUpperBound", "isLesserThanUpperBound"], reduce_upper_bound)
        for l,r,time_ds in town_index_ds:
            if (l,r)!=(-1,-1):
                for t in range(start_time, end_time+1):
                    lt,rt,_ = time_ds[t]
                    if (lt,rt)!=(-1,-1):
                        floor_area_start_idx = lt
                        if floor_area_start_idx<=rt:
                            tmp, price_per_sqm = Search.zone_map_search(self.zone_maps[("resale_price", "floor_area_sqm")], floor_area_start_idx, rt, price_per_area_handler, mn_area, y)
                            if tmp!=-1: 
                                rtn = tmp 
                                mn_area = price_per_sqm
        return rtn 
