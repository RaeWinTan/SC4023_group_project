
class ExternalSorting:

    @staticmethod
    def index_sorting(size, indexes, column_stores):
        arr = [] 
        for i in range(size): 
            row_val = [] 
            for idx in indexes:
                row_val.append(idx.get(i))
            arr.append((tuple(row_val), i))
        arr.sort()
        permutation = [i for _,i in arr]
        #standardizing order of data across all column stores 
        for _, cs in column_stores.items():
            cs.data = ExternalSorting.reorder(permutation, cs.data)
        return 

    @staticmethod
    def reorder(permutation, data):
        rtn = [None]*len(data)
        for i, p in enumerate(permutation):
            rtn[i] = data[p]
        return rtn 