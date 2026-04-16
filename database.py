from collections import OrderedDict
from collections.abc import Iterable, Sequence, Sized
from typing import Any, List
from column_store import ColumnObject, DataType, ZoneMap, Indexes
from writer import Writer
from search import Search
from common_utils import ConditionHandler, TimeInt, TownInt, reduce_upper_bound
from external_sorting import ExternalSorting
from indexdatastructure import IndexDataStucture

class DataBase:
    QUERY_CALLED = 0 
    def __init__(self, column_names: str, data_types: list[DataType], requirements):
        self.column_requirements = {c:requirements[i] for i,c in enumerate(column_names)}
        self.column_stores: dict[str, ColumnObject] = dict()
        for i, name in enumerate(column_names):
            self.column_stores[name] = ColumnObject(name, data_types[i])
        self.writer = Writer()
        self.size = 0 
        self.indexes: dict[tuple[str, ...] | str, Indexes] = OrderedDict()
        self.zone_maps: dict[tuple[str, ...], ZoneMap] = OrderedDict()
    
    @classmethod 
    def get_query_called(cls):
        return cls.QUERY_CALLED
    
    def load_data(self, data):
        assert set(data.keys())==set(self.column_stores.keys()), "All columns must match columns in database"
        data_items = [(name, v) for name, v in data.items()] 
        for name, v in data_items:
            accepted, val =  self.column_requirements[name](v)
            if not accepted: return # do not add that row to the data store
            data[name] = val 
        for name, v in data.items():
            cs:ColumnObject = self.column_stores[name]
            cs.load(v)
        self.size += 1

    def compress_column(self, column_name, hm):
        self.column_stores[column_name].make_compress(hm)

    def index_columns(self, sorting_order_of_precedence:list[tuple[str, ...]], aggregate_fns, index_datastructure_sizes: Sequence[int]):
        """
        Creates a clustered sparse/dense primary index over the database.
        Args
        ====
            sorting_order_of_precedence: list[tuple[str]]
                determines the *source* columns to sort on. They can either be single columns or compound columns.
            aggregate_fns: list[Callable]
                each entry in sorting_order_of_precedence can specify either a single column or multiple columns.
                entries will be transformed by the provided aggregate_fns, which is particularly helpful for combining
                multiple columns into one.
                The underlying data will be sorted according to the projected columns.
            index_datastructure_sizes: Sequence[int]
                Number of projected columns to use for the index and number of distinct values per column. 
                This will use the first N projected columns to form a N-tier index, where tier 1 is based
                on the first projected column, teir 2 is the second and so on...
        """
        sort_map: dict[tuple[str, ...] | str, Indexes[Any]] = dict()
        # transform each entry into projected columns
        # add projected columns to the sort order
        for col, agg in zip(sorting_order_of_precedence, aggregate_fns):
            key = col[0] if len(col) == 1 else col
            sort_map[key] = Indexes([self.column_stores[c] for c in col], agg)
        # sort all columns based on the index_map
        ExternalSorting.index_sorting(self.size, sort_map.values(), self.column_stores)
        # the index map is constructed from the first N projected columns
        index_arr = list(sort_map.values())[:len(index_datastructure_sizes)] # python obeys insertion-order
        ColumnObject.set_index_datastructure(IndexDataStucture(index_arr, index_datastructure_sizes))
        self.indexes = sort_map
        
    def zone_map_columns(self, index_name: tuple[str,...], aggregate_fn):
        obj = self.indexes[index_name]
        self.zone_maps[index_name] = ZoneMap(obj, aggregate_fn)

    def write_data(self, x,y,row_number, columns,aggregation_columns, aggregation_functions, data_types,
                   output_names):
        if row_number == -1:#no solution case
            rtn = [f"({x}, {y})", "No result"]+ [""]*(len(output_names)-2)
            self.writer.write(output_names, rtn)
            return 
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

    def query(self, x: int, y: int, start_time: TimeInt, end_time: TimeInt, town_values: list[TownInt]) -> tuple[int, TimeInt, int]:
        DataBase.QUERY_CALLED+=1
        town_index_ds = [ColumnObject.index_datastructure.search_node([t]) for t in town_values]
        rtn = -1 
        price_per_area_condition = [0, 4725] 
        price_per_area_handler = ConditionHandler(price_per_area_condition, ["isLesserThanEqualToUpperBound", "isLesserThanUpperBound"], reduce_upper_bound)
        time,area=-1, -1
        for l,r,time_ds in town_index_ds:
            if (l,r)!=(-1,-1):#skip missing towns
                for t in range(start_time, end_time+1):
                    lt,rt,_ = time_ds[t]
                    if (lt,rt)!=(-1,-1):#skip missing time for that particular town in question 
                        floor_area_start_idx = Search.bisect_left(self.indexes["floor_area_sqm"], y, lt, rt)
                        if floor_area_start_idx<=rt:#when there is such a floor_area_sqm >=y
                            tmp, values = Search.zone_map_search(self.zone_maps[("resale_price", "floor_area_sqm")], floor_area_start_idx, rt, price_per_area_handler)
                            if tmp!=-1: 
                                time = t 
                                area = values[1] 
                                rtn = tmp 
        return rtn, time, area
