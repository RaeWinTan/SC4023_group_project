from database import DataBase
from column_store import DataType
from collections import defaultdict
from common_utils import MinMax, haveOverLap, inSet, bit_encoded, normalize_number, month_fill
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
column_names = ["year",           "month",          "town",         "block",        "street_name",
                "flat_type",    "flat_model",   "storey_range", "floor_area_sqm",    "lease_commence_date", "resale_price"]
column_types = [DataType.INTEGER, DataType.INTEGER, DataType.STRING, DataType.STRING, DataType.STRING,
                DataType.STRING, DataType.STRING, DataType.STRING, DataType.INTEGER, DataType.STRING, DataType.INTEGER]
db = DataBase(column_names, column_types)
for row_dict in read_processed_rows("ResalePricesSingapore.csv"):
    db.load_data(row_dict)
db.compress_column("town", town_to_digit) 
db.index_columns([("year", "month"), ("resale_price", "floor_area_sqm")], [
                 lambda a, b: (a, b), lambda a, b: ((a*1.0)/b)])
"""
INDEXING DATASTUCTYURE: [town-> start psotiion ]

town (10) DATASTRUCURE : value -> very first position
[]10 key-> value parit 
120 * 10

(town, yearmont, price/sqf)
sorting precendence
1. ((2020, 1), (100)) -> from db 
2. (2020, 1), (110)
3. (2020, 2), (90)

"""
#sorting precendence-> (2020, 1)
db.zone_map_columns([("year", "month"), ("resale_price", "floor_area_sqm"), ("floor_area_sqm"), ("town")], [
                    MinMax, MinMax, MinMax, bit_encoded], [haveOverLap, haveOverLap, haveOverLap, inSet])
#0 15, hougang, bp, c : 10110
matids = ["U2340246H"]
for MATID in matids:
    db.writer.setCsvWriter(f"ScanResult_{MATID}_generated.csv")
    for x in range(7, 8):
        for y in range(124, 133):
            rtn = db.query(x, y, MATID)
            if rtn != -1:
                db.write_data(x, y, rtn,
                            ["year", "month", "town", "block", "floor_area_sqm",
                            "flat_model", "lease_commence_date"],
                            [["resale_price", "floor_area_sqm"]], [
                                lambda a, b: (a*1.0)/b],
                            [int, month_fill, str, str,
                            normalize_number, str, str, round],
                            ["(x, y)", "Year","Month","Town", "Block","Floor_Area", "Flat_Model", "Lease_Commence_Date"	,"Price_Per_Square_Meter"])
    db.writer.close()