from database import DataBase
from column_store import DataType, ZoneMap, ColumnObject
from collections import defaultdict
from common_utils import MinMax, TimeInt, decode_matric, get_end_time, normalize_number, convert_time_to_month_year
from parsing_input import read_processed_rows
from math import floor 

matids = [
    "U1234567A",
    "U7654321B",
    "U2345678C",
    "U8765432D",
    "U3456789E",
    "U9876543F",
    "U4567890G",
    "U0987654H",
    "U5678901I",
    "U1098765J",
    "U6789012K",
    "U2109876L",
    "U7890123M",
    "U3210987N",
    "U8901234O",
    "U4321098P",
    "U9012345Q",
    "U5432109R",
    "U1122334S",
    "U9988776T",
    "U2340793K",
    "U2340246H",
    "U2221633B",
    "U2240731L",
]
town_to_digit = defaultdict(lambda: 10, {
    "BEDOK": 0,
    "BUKIT PANJANG": 1,
    "CLEMENTI": 2,
    "CHOA CHU KANG": 3,
    "HOUGANG": 4,
    "JURONG WEST": 5,
    "PASIR RIS": 6,
    "TAMPINES": 7,
    "WOODLANDS": 8,
    "YISHUN": 9
})
column_names = ["time",          "town",         "block",        "street_name",
                "flat_type",    "flat_model",   "storey_range", "floor_area_sqm",    "lease_commence_date", "resale_price"]
column_types = [DataType.INTEGER, DataType.STRING, DataType.STRING, DataType.STRING,
                DataType.STRING, DataType.STRING, DataType.STRING, DataType.INTEGER, DataType.STRING, DataType.INTEGER]
db = DataBase(column_names, column_types)
for row_dict in read_processed_rows("ResalePricesSingapore.csv"): db.load_data(row_dict)
#database preprocessing on selected columns
db.compress_column("town", town_to_digit) 
db.index_columns(sorting_order_of_precedence=[["town"], ["time"], ["floor_area_sqm"], ["resale_price", "floor_area_sqm"]],
                 aggregate_fns=[lambda a: a]*3 + [lambda a,b: (a*1.0)/b],
                 index_datastructure_sizes=[11, 132])#index_datastructures only created for first two indexes
db.zone_map_columns(index_name=("resale_price", "floor_area_sqm"), aggregate_fn = MinMax)
#preformance statistics variables 
query_count = (9-1)*(151 - 80)*len(matids)
total_zone_read = 0 
total_column_read = 0
for MATID in matids:
    start_time, towns = decode_matric(MATID)
    db.writer.setCsvWriter(f"ScanResult_{MATID}_generated.csv") 
    #dynamic programming to reduce unneccessary db.query() calls
    dp = [[float("inf")]*8 for _ in range(151-80)]
    for x in range(8,0,-1):#((8,0, -1))
        end_time = get_end_time(x=x, start_time=start_time)
        for y in range(80, 151):
            before_zone_read = ZoneMap.getZoneRead()
            before_column_read = ColumnObject.getColumnRead()
            rtn = dp[y-80][x-1]
            if rtn==float("inf"):#never seen before case 
                rtn,time,area = db.query(x, y, start_time=start_time, end_time=end_time, town_values=towns)
                zone_read = ZoneMap.getZoneRead() - before_zone_read
                column_read = ColumnObject.getColumnRead() - before_column_read
                total_zone_read+=zone_read
                total_column_read+=column_read
                if rtn!=-1:
                    for tx in range(time-start_time,x):
                        for ty in range(y, min(floor(area)+1, 151)):
                            dp[ty-80][tx] = rtn 
                else:
                    for tx in range(0, x):
                        for ty in range(y, 151):
                            dp[ty-80][tx] = -1 
    
    #write result from saved row numbers of solution to excel file when such a result exist
    for x in range(1, 9):
        for y in range(80, 151):
            rtn = dp[y-80][x-1]
            if rtn != -1:
                db.write_data(x, y, rtn,
                            ["time", "town", "block", "floor_area_sqm",
                            "flat_model", "lease_commence_date"],
                            [["resale_price", "floor_area_sqm"]], [
                                lambda a, b: (a*1.0)/b],
                            [convert_time_to_month_year, str, str,
                            normalize_number, str, str, round],
                            ["(x, y)", "Year","Month","Town", "Block","Floor_Area", "Flat_Model", "Lease_Commence_Date"	,"Price_Per_Square_Meter"])
    db.writer.close()
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

print(f"total queries: {GREEN}{query_count}{RESET}")
print(f"total db.query() calls: {GREEN}{DataBase.get_query_called()}{RESET}")
print(f"total db.query() savings: {GREEN}{query_count-DataBase.get_query_called()}{RESET}")


print(
    f"total zone reads: {CYAN}{total_zone_read}{RESET} "
    f"total column reads: {CYAN}{total_column_read}{RESET}"
)

print(
    f"average zone reads per query: {YELLOW}{total_zone_read/query_count:.2f}{RESET} | "
    f"average column reads per query: {YELLOW}{total_column_read/query_count:.2f}{RESET}"
)