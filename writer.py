import csv 

class Writer:
    
    def __init__(self):
        self.pointer = 0
        self.file = None 
        self.writer = None
        # initialize work book to write as well
    def setCsvWriter(self, file_name):
        self.pointer = 0
        self.file = open(file_name, "w", newline="")
        self.writer = csv.writer(self.file)
    def write(self, column_names, values):
        if self.pointer ==0:
            self.writer.writerow(column_names)
        self.writer.writerow(values)
        self.pointer+=1     
    def close(self):
        if self.file:
            self.file.close()
            self.file = None
            self.pointer = 0 