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
            month_year = row_dict.get("month", "").strip()
            if not month_year:
                continue
            if month_year.count("-") != 1:
                continue
            mon_str, yy = month_year.split("-")
            if mon_str not in month_map:
                continue
            if not (yy.isdigit() and len(yy) == 2):
                continue
            year = int("20" + yy)
            if year < 2000 or year > 2100:
                continue
            del row_dict["month"]
            month = month_map[mon_str]
            row_dict["time"] = convert_year_month_to_time(year, month)
            yield row_dict