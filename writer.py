import csv 

class Writer:
    
    def __init__(self):
        self.pointer = 0
        # initialize work book to write as well
    def setCsvWriter(self, file_name):
        file = open(file_name, "w", newline="")
        self.writer = csv.writer(file)
    def write(self, column_names, values):
        if self.pointer ==0:
            self.writer.writerow(column_names)
        self.writer.writerow(values)

        self.pointer+=1     