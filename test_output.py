import csv

def csv_equal(file1, file2):
    with open(file1, newline='') as f1, open(file2, newline='') as f2:
        reader1 = list(csv.reader(f1))
        reader2 = list(csv.reader(f2))
    return reader1 == reader2

def get_generated_file(name):
    return name.replace("Expected_", "")
import os 
if __name__ == "__main__":
    count = 0 
    for file in os.listdir("."):
        # pick only original files (not generated ones)
        if file.startswith("Expected_ScanResult_U") and file.endswith(".csv") and "_generated" not in file:
            generated = get_generated_file(file)
            # check if generated file exists
            if not os.path.exists(generated):
                raise FileNotFoundError(f"Missing generated file for {file}")
            count+=1 
            print(f"comparing {file} against {generated}")
            assert csv_equal(file, generated), f"ERROR comparing {file}"
    print(f"ALL GOOD ✅ for {count} generated files")