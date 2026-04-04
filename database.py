from collections import OrderedDict
from typing import List, Dict, Any
from column_store import ColumnObject, DataType, ZoneMap, Indexes
from search import binary_search, zone_map_search
from common_utils import bit_encoded


class DataBase:
    def __init__(self, column_names: List[str], data_types: List[DataType]):
        self.column_stores: Dict[str, ColumnObject] = {
            name: ColumnObject(name, _type)
            for name, _type in zip(column_names, data_types)
        }
        self.size = 0
        self.indexes = OrderedDict()
        self.zone_maps = OrderedDict()

    def compress_column(self, column_name, hm):
        self.column_stores[column_name].make_compress(hm)

    def load_data(self, data):  # data is a dicionary for each column the values in i
        assert set(data.keys()) == set(self.column_stores.keys()), (
            "All columns must match columns in database"
        )
        self.size += 1
        for name, v in data.items():
            cs: ColumnObject = self.column_stores[name]
            cs.load(v)

    def index_columns(self, indexes: List[tuple[str, ...]], aggregate_fns):
        arr = []
        for ic, cols in enumerate(indexes):
            self.indexes[cols] = Indexes(
                [self.column_stores[c] for c in cols], aggregate_fns[ic]
            )
        for i in range(self.size):
            row_val = []
            for ic, cols in enumerate(indexes):
                v = []
                for c in cols:
                    col_obj: ColumnObject = self.column_stores[c]
                    v.append(col_obj.get(i))
                row_val.append(aggregate_fns[ic](*v))

            arr.append((tuple(row_val), i))
        arr.sort()  # order by the value defined in the tuple then indexfrom original
        permutation = [i for _, i in arr]
        for _, col_obj in self.column_stores.items():
            col_obj.reorder(permutation)

    def zone_map_columns(self, zones: List[tuple[str, ...]], aggregate_fns, check_fns):
        # same tupple idea
        for i, z in enumerate(zones):
            obj = self.indexes[z] if z in self.indexes else self.column_stores[z]
            self.zone_maps[z] = ZoneMap(obj, aggregate_fns[i], check_fns[i])

    def get(self, index: int, columns: List[str]) -> Dict[str, Any]:
        """
        Retrieves the requested attributes of the tuple stored at the given index.
        This is done by performing tuple reconstruction on the requested columns.
        Does not support aggregation / arbitrary expressions.

        Parameters
        ----------
        index : int
            The index of the tuple to retrieve
        columns : list[str]
            The list of attributes to retrieve
        """

        return {
            column: self.column_stores[column].get_original_value(index)
            for column in columns
        }

    def query(
        self, x: int, y: int, start_year: int, start_month: int, town_values: list[int]
    ):  # query either give back -1 or a row_number, -1 means no result
        (end_year, end_month) = increase_year_month((start_year, start_month), x - 1)
        (_, indexer) = next(iter(self.indexes.items()))
        (l, r) = binary_search(
            indexer,
            ((start_year, start_month), (end_year, end_month)),
            0,
            self.size - 1,
        )
        town_values_encoded = bit_encoded(town_values)
        zones = [v for k, v in self.zone_maps.items()]
        values = [
            self.indexes[z] if z in self.indexes else self.column_stores[z]
            for z in self.zone_maps.keys()
        ]
        rtn = zone_map_search(
            zones,
            [
                ((start_year, start_month), (end_year, end_month)),
                (0, 4725.0),
                (y, float("inf")),
                town_values_encoded,
            ],
            values,
            [
                ["inRange"],
                ["isLesserThanEqualToUpperBound", "isLesserThanUpperBound"],
                ["inRange"],
                ["inRange"],
            ],
            [
                change_fn(year_month_change_fn, ["inRange"]),
                change_fn(
                    price_per_area_change_fn,
                    ["isLesserThanEqualToUpperBound", "isLesserThanUpperBound"],
                ),
                change_fn(identity_change_fn, ["inRange"]),
                change_fn(identity_change_fn, ["inRange"]),
            ],
            l,
            r,
        )
        return rtn


def increase_year_month(t, mths):
    year, month = t
    year -= 1
    month -= 1
    return (1 + year + (month + mths) // 12, 1 + (month + mths) % 12)


# increase lower bound
def year_month_change_fn(val, rg):
    new_start = increase_year_month(val, 1)
    return (new_start, rg[1])


# set uppwer bound
def price_per_area_change_fn(val, rg):
    return (rg[0], val)


# area and town hard set
def identity_change_fn(val, rg):
    return rg


def change_fn(condition_value_change_fn, call_back_names):
    call_back_fun_idx = 0

    def inner(val, rg):
        nonlocal call_back_fun_idx
        rtn = (condition_value_change_fn(val, rg), call_back_fun_idx)
        call_back_fun_idx = min(len(call_back_names) - 1, call_back_fun_idx + 1)
        return rtn

    return inner
