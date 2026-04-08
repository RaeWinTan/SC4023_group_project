import csv
from common_utils import convert_year_month_to_time
month_map = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}
def read_processed_rows(filepath):
    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)

        for row in reader:
            row_dict = dict(zip(headers, row))

            month_year = row_dict["month"]
            del row_dict["month"]
            mon_str, yy = month_year.split("-")
            month = month_map[mon_str]
            year = int("20" + yy)
            row_dict["time"] = convert_year_month_to_time(year, month)
            yield row_dict  