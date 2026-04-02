
"""
indexing 
sorting 
binary search
vectororization 
shared scan
early stopping for final aggregate function





"""
from typing import List, Any
from collections.abc import Callable
from enum import Enum
from collections import defaultdict


class DataType(Enum):
    STRING = 1
    INTEGER = 2


class Writer:
    
    def __init__(self):
        self.pointer = 0
        # initialize work book to write as well

    def write(self, column_names, values):
        pass
        """
        if self.pointer ==0:
            write the columns names and the values 
        otherwise just write the values
        """


class ColumnObject:

    def __init__(self, column_name, data_type: DataType):
        self.column_name = column_name
        self.data_type = data_type
        self.data = []
        self.is_compressed = False

    def size(self):
        return len(self.data)

    def load(self, value):
        self.data.append(value)

    def reorder(self, permutation):
        rtn = self.data.copy()
        for i, p in enumerate(permutation):
            rtn[i] = self.data[p]
        self.data = rtn

    def get(self, idx):
        return self.data[idx]

    def set(self, idx, val):
        self.data[idx] = val

    def make_compress(self, hm):  # word -> integer,
        self.is_compressed = True
        self.hm = hm.copy()
        # the non intresting guys are just the last option
        self.ihm = defaultdict(lambda: len(self.hm)-1)
        # this will still work because i will never write a guy that is not in the hashmap list in our case
        for k, v in hm.items():
            self.ihm[v] = k
        for i, e in enumerate(self.data):
            self.data[i] = self.hm[e]

    def get_original_value(self, idx):
        if self.is_compressed:
            return self.ihm[self.data[idx]]
        return self.data[idx]
    
    #function to be used by query to get he value 


#check inside for columnObject 
#if columnObject is aof type the check inside is just raneg 
#if hte columnObject is compressed then it is check the bitmask
#get min max for he zone map 


class ZoneMap:
    SPAN = 16 #suppose page size is 16 objects long 
    #aggregate function for compresse data is bitmask 
    #aggreate function for normal number is just max and min
    #need to have custom comparator, just check inside or not 
    #aggregate function will give out like a range 
    def __init__(self, column_objects:List[ColumnObject], aggregate_fn: Callable[[list[tuple[int, ...]]], Any], check_fn: Callable[[tuple[int, ...]], bool]):
        self.size = column_objects[0].size()
        self.zones = [None]*((self.size//self.SPAN) + 1)
        for l in range(0, self.size, self.SPAN):
            r = min(l+self.SPAN, self.size)
            self.zones[l//self.SPAN] = aggregate_fn([(c.get(idx) for c in column_objects) for idx in range(l, r)])
        self.check_fn = check_fn 
    def getZone(self, idx):
        return self.zones[idx//self.SPAN]
    def checkInside(self, idx, value):
        return self.check_fn(self.zones[idx//self.SPAN], value)
    def nextIdx(self, idx):#where detect a mis continue next indexi like that
        return ((idx+self.SPAN)//self.SPAN)*self.SPAN 
    


class DataBase:
    
    def __init__(self, column_names, data_types):
        self.column_stores = dict()
        for i, name in enumerate(column_names):
            self.column_stores[name] = ColumnObject(name, data_types[i])
        self.writer = Writer()
        self.size = 0 
        self.indexes = []
        self.zone_maps = dict()

    def compress_column(self, column_name, hm):
        self.column_stores[column_name].make_compress(hm)

    def load_data(self, data):#data is a dicionary for each column the values in i
        assert set(data.keys())==set(self.column_stores.keys()), "All columns must match columns in database"
        self.size += 1 
        for name, v in data.items():
            cs:ColumnObject = self.column_stores[name]
            cs.load(v)

    def index_columns(self, indexes:List[List[str]], aggregate_fns):
        arr = []
        self.indexes = [v.copy() for v in indexes]
        for i in range(self.sz):
            for ic,cols in enumerate(indexes):
                v = []
                for c in cols:
                    col_obj:ColumnObject = self.column_stores[c]
                    v.append(col_obj.get(i))
                v = tuple(v)
                arr.append((aggregate_fns[ic](*v), i))
        arr.sort(key=lambda x: x[0])#order by the value defined in the tuple 
        permutation = [i for _,i in arr]
        for (_,col_obj) in self.column_stores.items():
            col_obj.reorder(permutation)        
    
    def zone_map_columns(self, zones:List[tuple[str,...]], aggregate_fns, check_fns):
        self.zone_maps
        #same tupple idea
        for i,z in enumerate(zones):
            self.zone_maps[z] = ZoneMap([self.column_stores[c] for c in z], 
                                        aggregate_fns[i],
                                        check_fns[i]
                                        )

    def write_data(self, row_number, columns, aggregation_column_names,aggregation_columns, aggregation_functions):
        values = [] 
        for name in columns:
            cs:ColumnObject = self.column_stores[name]
            values.append(cs.get_original_value(row_number)) 
        for i in range(len(aggregation_functions)):
            fn = aggregation_functions[i]
            col_names = aggregation_columns[i]
            col_values = [self.column_stores[nm].get_original_value(row_number) for nm in col_names]
            values.append(fn(*col_values))
        self.writer.write(columns+aggregation_column_names, values)

    def query(self, x, y, mat_id):#query either give back -1 or a row_number, -1 means no result
        DIGIT_TO_TOWN = {
            '0': 'BEDOK',
            '1': 'BUKIT PANJANG',
            '2': 'CLEMENTI',
            '3': 'CHOA CHU KANG',
            '4': 'HOUGANG',
            '5': 'JURONG WEST',
            '6': 'PASIR RIS',
            '7': 'TAMPINES',
            '8': 'WOODLANDS',
            '9': 'YISHUN'
        }
        DIGIT_TO_YEAR = {
            '5': 2015, '6': 2016, '7': 2017, '8': 2018, '9': 2019,
            '0': 2020, '1': 2021, '2': 2022, '3': 2023, '4': 2024
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

            last_digit        = digits[-1]   # target year
            second_last_digit = digits[-2]   # start month

            target_year  = DIGIT_TO_YEAR[last_digit]
            start_month  = 10 if second_last_digit == '0' else int(second_last_digit)
            towns        = list(dict.fromkeys(  # unique digits, preserve order
                            DIGIT_TO_TOWN[d] for d in digits if d in DIGIT_TO_TOWN
                        ))
            return target_year, start_month, towns
        start_year, start_month, towns = decode_matric(mat_id)
        #time span over here (start_year, start_month) + x 
        #binary search starts and ends 
        #binary 
        #now that that is started 
