import csv

def csv_equal(file1, file2):
    with open(file1, newline='') as f1, open(file2, newline='') as f2:
        reader1 = csv.reader(f1)
        reader2 = csv.reader(f2)

        for row1, row2 in zip(reader1, reader2):
            if row1 != row2:
                return False

        # Check if lengths differ
        if any(reader1) or any(reader2):
            return False

    return True


if __name__ == "__main__":
    frr = [["ScanResult_U2340246H.csv", "ScanResult_U2340246H_generated.csv"], 
           ["ScanResult_U2240731L.csv", "ScanResult_U2240731L_generated.csv"]] 
    for a in frr:
        assert csv_equal(*a), "!!!!!!!!! GOT ERRORR !!!!!!!"
    print("ALL GOOD")