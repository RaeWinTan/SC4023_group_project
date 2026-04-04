from database import DataBase
from column_store import DataType
from collections import defaultdict
from common_utils import MinMax, haveOverLap, inSet, bit_encoded
from typing import Generator, TypedDict

town_to_digit = defaultdict(
    lambda: 10,
    {
        "BEDOK": 0,
        "BUKIT PANJANG": 1,
        "CLEMENTI": 2,
        "CHOA CHU KANG": 3,
        "HOUGANG": 4,
        "JURONG WEST": 5,
        "PASIR RIS": 6,
        "TAMPINES": 7,
        "WOODLANDS": 8,
        "YISHUN": 9,
    },
)
column_names = [
    "year",
    "month",
    "town",
    "block",
    "street_name",
    "flat_type",
    "flat_model",
    "storey_range",
    "floor_area_sqm",
    "lease_commence_date",
    "resale_price",
]
column_types = [
    DataType.INTEGER,
    DataType.INTEGER,
    DataType.STRING,
    DataType.STRING,
    DataType.STRING,
    DataType.STRING,
    DataType.STRING,
    DataType.STRING,
    DataType.INTEGER,
    DataType.STRING,
    DataType.INTEGER,
]
# must clean up the month and yesr part simple split will do


db = DataBase(column_names, column_types)
# read. form csv then load 1 at a time
# for loop to loade data readhing from csv until end of file
import csv

with open("ResalePricesSingapore.csv", newline="") as f:
    reader = csv.reader(f)

    headers = next(reader)  # first row
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }
    for row in reader:
        row_dict = dict(zip(headers, row))
        month_year = row_dict["month"]
        del row_dict["month"]
        mon_str, yy = month_year.split("-")
        row_dict["month"] = month_map[mon_str]
        row_dict["year"] = "20" + yy
        db.load_data(row_dict)


def normalize_number(val):
    f = float(val)
    return int(f) if f.is_integer() else f


def month_fill(val):
    val = int(val)
    return f"{val:02d}"


db.compress_column("town", town_to_digit)
db.index_columns(
    [("year", "month"), ("resale_price", "floor_area_sqm")],
    [lambda a, b: (a, b), lambda a, b: (a * 1.0) / b],
)
# need to change index, index, coloum_object, column_objects
db.zone_map_columns(
    [
        ("year", "month"),
        ("resale_price", "floor_area_sqm"),
        ("floor_area_sqm"),
        ("town"),
    ],
    [MinMax, MinMax, MinMax, bit_encoded],
    [haveOverLap, haveOverLap, haveOverLap, inSet],
)


class Record(TypedDict):
    x: int
    y: int
    year: float
    month: float
    town: str
    block: str
    floor_area_sqm: float
    flat_model: str
    lease_commence_date: str
    resale_price: float


OutputRecord = TypedDict(
    "OutputRecord",
    {
        "(x, y)": str,
        "Year": int,
        "Month": str,
        "Town": str,
        "Block": str,
        "Floor_Area": int,
        "Flat_Model": str,
        "Lease_Commence_Date": str,
        "Price_Per_Square_Meter": int,
    },
)


def parse_matric(matric: str) -> tuple[int, int, list[int]]:
    """
    Given a matric number like U2340246H, extract:
    - target year   (last digit of number portion)
    - start month   (second last digit; '0' = October)
    - towns         (all unique digits in matric)
    """
    DIGIT_TO_YEAR = [2020, 2021, 2022, 2023, 2024, 2015, 2016, 2017, 2018, 2019]
    # DIGIT_TO_TOWN = ["BEDOK", "BUKIT PANJANG", "CLEMENTI", "CHOA CHU KANG", "HOUGANG", "JURONG WEST", "PASIR RIS", "TAMPINES","WOODLANDS", "YISHUN"]

    # Extract only the digit characters
    assert len(matric) == 9, "Invalid matriculation number, must have length of 9"
    digits = [int(c) for c in matric[1:-1] if c.isdigit()]
    assert len(digits) == 7, "Invalid matriculation number, must have 7 digits"

    last_digit = digits[-1]  # target year
    second_last_digit = digits[-2]  # start month

    target_year = DIGIT_TO_YEAR[last_digit]
    start_month = 10 if second_last_digit == 0 else second_last_digit
    towns = list(set(digits))

    return target_year, start_month, towns


def query(matric: str) -> Generator[Record, None, None]:
    """
    Queries the database to yield all valid (x,y) pairs and their representative tuples
    """
    start_year, start_month, town_values = parse_matric(matric)
    for x in range(1, 9):
        for y in range(80, 151):
            idx = db.query(x, y, start_year, start_month, town_values)

            if idx == -1:
                continue

            row = db.get(
                idx,
                columns=[
                    "year",
                    "month",
                    "town",
                    "block",
                    "floor_area_sqm",
                    "flat_model",
                    "lease_commence_date",
                    "resale_price",
                ],
            )

            yield dict(x=x, y=y, **row)  # type: ignore


def format(record: Record) -> OutputRecord:
    """
    Formats the raw results retrieved from DB for output to CSV
    """
    return {
        "(x, y)": f"({record['x']}, {record['y']})",
        "Year": int(record["year"]),
        "Month": f"{int(record['month']):02d}",
        "Town": record["town"],
        "Block": record["block"],
        "Floor_Area": int(record["floor_area_sqm"]),
        "Flat_Model": record["flat_model"],
        "Lease_Commence_Date": record["lease_commence_date"],
        "Price_Per_Square_Meter": round(
            float(record["resale_price"]) / record["floor_area_sqm"]
        ),
    }


if __name__ == "__main__":
    matric = "U2340246H"
    # 1. Read CSV

    # 2. create column store DB from CSV

    # 3. Prepare a file to stream query results to
    with open(f"ScanResult_{matric}.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "(x, y)",
                "Year",
                "Month",
                "Town",
                "Block",
                "Floor_Area",
                "Flat_Model",
                "Lease_Commence_Date",
                "Price_Per_Square_Meter",
            ],
        )

        writer.writeheader()

        # 3. Query the database
        for rec in query(matric):
            # 4. Stream results to csv files
            writer.writerow(format(rec))
