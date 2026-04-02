from column_store import DataBase, DataType
from collections import defaultdict

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
column_names = ["Year",           "Month",          "Town",         "Block",        "Street_Name",  "Flat_Type",    "Flat_Model",   "Storey_Range", "Floor_Area",    "Lease_Commence_Date", "Resale_Price"]
column_types = [DataType.INTEGER, DataType.INTEGER, DataType.STRING,DataType.STRING,DataType.STRING,DataType.STRING,DataType.STRING,DataType.STRING,DataType.INTEGER,DataType.STRING,DataType.INTEGER] 
#must clean up the month and yesr part simple split will do 
def MinMax(arr: list[tuple[int, ...]]):
    mn,mx = arr[0],arr[0]
    for i in range(1, len(arr)):
        mn = min(arr[i], mn)
        mx = max(arr[i], mx)
    return (mn, mx)

def inRange(z, val):
    return z[0]<=val<=z[1]
def inSet(z, val):
    return (z & val)!=0 
def bit_encoded(arr):
    acc = 0 
    for (a) in arr:
        acc|=(1<<a)
    return acc 

db = DataBase(column_names, column_types)
#read. form csv then load 1 at a time 
#for loop to loade data readhing from csv until end of file 
db.load_data()
db.compress_column("Town", town_to_digit)
db.index_columns([["Year", "Month"], ["Resale_Price","Floor_Area"]], [lambda a,b: (a,b), lambda a,b: (a*1.0)/b])
db.zone_map_columns([("Year", "Month"), ("Floor_Area"), ("Town")], [MinMax, MinMax, bit_encoded], [inRange, inRange, inSet])

##queries here



"""

check in range 
zonemap columns
(year, month), (town), (area)
initialize db 

get data from the csv file

load_data to db 

compress_column 

index_column 

zone_map_columns

queries : declarative code using rxpy


if is compressed-> bit manipulation for zonemap
if indexed -> normal range find 

area >= 85 

early stopping 

as long as i find an answer in the year
month(this is because the price/area is 
sorted within the year,month)  

all those zones with the same year month 
can be skipped 

still need to vectorize ? 

for hte zone map part no need lah 

how to vectorize?

index by (year,month), price/floor_area

SHOULD ZONE MAP YEAR MONTH-> kicker
-> if i found the 
binary search (year, month)
within that span 
search through using zone map
area and town
shared scan area and town and price/floor_area
if all three zones hit: scan it 
    -> the first actual hit 
    -> update he answer
    -> skip all the way to the next year,mont
        -> basically check the getZone for year,month
        -> if start and end date the same then continue 


"""
