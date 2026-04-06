from collections import OrderedDict
from typing import List
from column_store import ColumnObject, ZoneMap, Indexes, ComparatorFunction
from writer import Writer
from search import Search
from common_utils import year_month_change_fn, price_per_area_change_fn, \
    fixed_change_fn, ConditionHandler, getQueryParameters, EarlyStopping
from external_sorting import ExternalSorting
from indexdatastructure import IndexDataStucture

class DataBase:
    
    def __init__(self, column_names, data_types):
        self.column_stores = dict()
        for i, name in enumerate(column_names):
            self.column_stores[name] = ColumnObject(name, data_types[i])
        self.writer = Writer()
        self.size = 0 
        self.indexes = OrderedDict()
        self.zone_maps = OrderedDict()

    def load_data(self, data):
        assert set(data.keys())==set(self.column_stores.keys()), "All columns must match columns in database"
        self.size += 1 
        for name, v in data.items():
            cs:ColumnObject = self.column_stores[name]
            cs.load(v)

    def compress_column(self, column_name, hm):
        self.column_stores[column_name].make_compress(hm)

    def index_columns(self, indexes:List[tuple[str,...]], aggregate_fns):
        for ic, cols in enumerate(indexes):
            self.indexes[cols] = Indexes([self.column_stores[c] for c in cols], aggregate_fns[ic])
        ExternalSorting.index_sorting(self.size, indexes, self.column_stores, aggregate_fns)
        #index datastructuire follows the ordering of the primary index
        ColumnObject.set_index_datastructure(self.indexes[indexes[0]])
        
    def zone_map_columns(self, zones:List[tuple[str,...]], aggregate_fns, check_fns):
        for i,z in enumerate(zones):
            obj = self.indexes[z] if z in self.indexes else self.column_stores[z]
            self.zone_maps[z] = ZoneMap(obj, 
                                        aggregate_fns[i],
                                        check_fns[i]
                                        )

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
        self.writer.write(output_names, [f"({x}, {y})"]+[data_types[i](v) for i,v in enumerate(values)])

    def query(self, x, y, mat_id):
        start_year, start_month, end_year, end_month, town_values_encoded = getQueryParameters(x,mat_id)
        ym_indexer = self.indexes[("year", "month")]
        start_index = Search.bisect_left(ym_indexer, (start_year, start_month), 0, self.size-1)
        zones = [v for _,v in self.zone_maps.items()]
        values: List[ComparatorFunction] = [self.indexes[z] if z in self.indexes else self.column_stores[z] for z in self.zone_maps.keys()]
        conditions = [((start_year, start_month), (end_year, end_month)), (0, 4725.0), (y, float("inf")), 
                               town_values_encoded]
        rtn = Search.zone_map_search(zones, 
                              conditions, 
                              values,
                              
                              [ConditionHandler(year_month_change_fn, ["inRange"]), 
                               ConditionHandler(price_per_area_change_fn,["isLesserThanEqualToUpperBound","isLesserThanUpperBound"]), 
                               ConditionHandler(fixed_change_fn,["inRange"]), 
                               ConditionHandler(fixed_change_fn, ["inRange"])], 
                               EarlyStopping(conditions, [lambda a: a[1]<a[0]] + [lambda _: False]*3),
                               start_index)
        return rtn 
