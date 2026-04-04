from collections import OrderedDict
from typing import List
from column_store import Writer, ColumnObject, ZoneMap, Indexes
from search import binary_search, zone_map_search
from common_utils import bit_encoded


class DataBase:
    def __init__(self, column_names, data_types):
        self.column_stores = dict()
        for i, name in enumerate(column_names):
            self.column_stores[name] = ColumnObject(name, data_types[i])
        self.writer = Writer()
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

    def write_data(
        self,
        x,
        y,
        row_number,
        columns,
        aggregation_column_names,
        aggregation_columns,
        aggregation_functions,
        data_types,
        output_names,
    ):
        values = []
        for name in columns:
            cs: ColumnObject = self.column_stores[name]
            values.append(cs.get_original_value(row_number))
        for i in range(len(aggregation_functions)):
            fn = aggregation_functions[i]
            col_names = aggregation_columns[i]
            col_values = [
                self.column_stores[nm].get_original_value(row_number)
                for nm in col_names
            ]
            values.append(fn(*col_values))
        self.writer.write(
            output_names,
            [f"({x}, {y})"] + [data_types[i](v) for i, v in enumerate(values)],
        )

    def query(
        self, x, y, mat_id
    ):  # query either give back -1 or a row_number, -1 means no result
        DIGIT_TO_TOWN = {
            "0": "BEDOK",
            "1": "BUKIT PANJANG",
            "2": "CLEMENTI",
            "3": "CHOA CHU KANG",
            "4": "HOUGANG",
            "5": "JURONG WEST",
            "6": "PASIR RIS",
            "7": "TAMPINES",
            "8": "WOODLANDS",
            "9": "YISHUN",
        }
        DIGIT_TO_YEAR = {
            "5": 2015,
            "6": 2016,
            "7": 2017,
            "8": 2018,
            "9": 2019,
            "0": 2020,
            "1": 2021,
            "2": 2022,
            "3": 2023,
            "4": 2024,
        }

        def decode_matric(matric):
            """
            Given a matric number like U2340246H, extract:
            - target year   (last digit of number portion)
            - start month   (second last digit; '0' = October)
            - towns         (all unique digits in matric)
            """
            # Extract only the digit characters
            digits = [c for c in matric if c.isdigit()]

            last_digit = digits[-1]  # target year
            second_last_digit = digits[-2]  # start month

            target_year = DIGIT_TO_YEAR[last_digit]
            start_month = 10 if second_last_digit == "0" else int(second_last_digit)
            town_values = [int(d) for d in digits]
            towns = list(
                dict.fromkeys(  # unique digits, preserve order
                    DIGIT_TO_TOWN[d] for d in digits if d in DIGIT_TO_TOWN
                )
            )
            return target_year, start_month, list(set(town_values))

        start_year, start_month, town_values = decode_matric(mat_id)
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
