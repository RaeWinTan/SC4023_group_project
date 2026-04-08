from database import DataBase
from column_store import DataType, ZoneMap, ColumnObject
from collections import defaultdict
from common_utils import MinMax, normalize_number, convert_time_to_month_year
from parsing_input import read_processed_rows

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
matids = ["U2340246H", "U2240731L"]
query_count = (9-1)*(151 - 80)*len(matids)
total_zone_read = 0 
total_column_read = 0
for MATID in matids:
    db.writer.setCsvWriter(f"ScanResult_{MATID}_generated.csv") 
    for x in range(1, 9):
        for y in range(80, 151):
            before_zone_read = ZoneMap.getZoneRead()
            before_column_read = ColumnObject.getColumnRead()
            rtn = db.query(x, y, MATID)
            zone_read = ZoneMap.getZoneRead() - before_zone_read
            column_read = ColumnObject.getColumnRead() - before_column_read
            total_zone_read+=zone_read
            total_column_read+=column_read 
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
print(f"total queries: {query_count}")
print(f"total zone reads: {total_zone_read} total column reads: {total_column_read}")
print(f"average zone reads per query: {total_zone_read/query_count:2f} | average column reads: {total_column_read/query_count:2f}")