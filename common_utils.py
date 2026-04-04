def MinMax(arr: list[tuple[int, ...]]):
    mn,mx = arr[0],arr[0]
    for i in range(1, len(arr)):
        mn = min(arr[i], mn)
        mx = max(arr[i], mx)
    return (mn, mx)

def haveOverLap(z, val):
    if z[1]<val[0] or val[1]< z[0]: return False
    return True 
def inSet(z, val):
    return (z & val)!=0 
def bit_encoded(arr):
    acc = 0 
    for (a) in arr:
        acc|=(1<<a)
    return acc 