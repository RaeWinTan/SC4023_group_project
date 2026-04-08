from database import DataBase
from column_store import DataType, ZoneMap, ColumnObject
from collections import defaultdict
from common_utils import MinMax, normalize_number, convert_time_to_month_year
from parsing_input import read_processed_rows
from math import floor 
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
db.compress_column("town", town_to_digit) 
db.index_columns([["town"], ["time"], ["floor_area_sqm"], ["resale_price", "floor_area_sqm"]], [lambda a: a]*3 + [lambda a,b: (a*1.0)/b],[11, 132])
db.zone_map_columns(("resale_price", "floor_area_sqm"), MinMax)
matids = ["U2221633B"]
query_count = (9-1)*(151 - 80)*len(matids)
total_zone_read = 0 
total_column_read = 0
for MATID in matids:
    db.writer.setCsvWriter(f"ScanResult_{MATID}_generated.csv") 
    dp = [[float("inf")]*8 for _ in range(151-80)]
    for x in range(8,0,-1):#((8,0, -1))
        for y in range(80, 151):
            before_zone_read = ZoneMap.getZoneRead()
            before_column_read = ColumnObject.getColumnRead()
            rtn = dp[y-80][x-1]
            if rtn==float("inf"):#never seen before case 
                rtn,time,area, start_time = db.query(x, y, MATID)
                zone_read = ZoneMap.getZoneRead() - before_zone_read
                column_read = ColumnObject.getColumnRead() - before_column_read
                total_zone_read+=zone_read
                total_column_read+=column_read
                if rtn!=-1:
                    for tx in range(time-start_time,x):
                        for ty in range(y, min(floor(area)+1, 151)):
                            dp[ty-80][tx] = rtn 
                else:
                    dp[y-80][x-1] = -1 
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

print(
    f"total zone reads: {CYAN}{total_zone_read}{RESET} "
    f"total column reads: {CYAN}{total_column_read}{RESET}"
)

print(
    f"average zone reads per query: {YELLOW}{total_zone_read/query_count:.2f}{RESET} | "
    f"average column reads: {YELLOW}{total_column_read/query_count:.2f}{RESET}"
)

"""
lets fix X

now if my Y is very small 

the first guy that satisfy that condition 

say Y = 10
let say havea area 30.5
should have floor(30.5 + 1 )
from 10 to 30: will shared the same value 

start time = 10 
end time = 28

say time 13
    the answer of the query has time 11
    we know from 11 to 13 it tihs tstsame 


shading squre problem


"""