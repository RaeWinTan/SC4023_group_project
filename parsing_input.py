import csv

def read_processed_rows(filepath, month_map):
    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)

        for row in reader:
            row_dict = dict(zip(headers, row))

            month_year = row_dict["month"]
            del row_dict["month"]

            mon_str, yy = month_year.split("-")
            row_dict["month"] = month_map[mon_str]
            row_dict["year"] = "20" + yy

            yield row_dict  