import csv

def csv_equal(file1, file2):
    with open(file1, newline='') as f1, open(file2, newline='') as f2:
        reader1 = list(csv.reader(f1))
        reader2 = list(csv.reader(f2))
    return reader1 == reader2


if __name__ == "__main__":
    frr = [["ScanResult_U2340246H.csv", "ScanResult_U2340246H_generated.csv"], 
           ["ScanResult_U2240731L.csv", "ScanResult_U2240731L_generated.csv"]] 
    for a in frr:
        assert csv_equal(*a), "!!!!!!!!! GOT ERRORR !!!!!!!"
    print("ALL GOOD")