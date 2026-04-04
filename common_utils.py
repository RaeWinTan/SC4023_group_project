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

def normalize_number(val):
    f = float(val)
    return int(f) if f.is_integer() else f
def month_fill(val):
    val = int(val)
    return f"{val:02d}"


def decode_matric(matric):
    DIGIT_TO_YEAR = {
        '5': 2015, '6': 2016, '7': 2017, '8': 2018, '9': 2019,
        '0': 2020, '1': 2021, '2': 2022, '3': 2023, '4': 2024
    }
    # Extract only the digit characters
    digits = [c for c in matric if c.isdigit()]

    last_digit        = digits[-1]   # target year
    second_last_digit = digits[-2]   # start month

    target_year  = DIGIT_TO_YEAR[last_digit]
    start_month  = 10 if second_last_digit == '0' else int(second_last_digit)
    town_values = [int(d) for d in digits] 
    return target_year, start_month, list(set(town_values))

def increase_year_month(t,mths):
    year,month = t
    year-=1 
    month-=1 
    return (1+year+(month+mths)//12, 1 + (month+mths)%12)
#increase lower bound
def year_month_change_fn(val, rg):
    new_start = increase_year_month(val, 1)
    return (new_start, rg[1])
#set uppwer bound
def price_per_area_change_fn(val, rg):
    return (rg[0], val)
#area and town hard set 
def fixed_change_fn(val, rg):
    return rg
def change_fn(condition_value_change_fn,call_back_names):
    call_back_fun_idx= 0 
    def inner(val, rg):
        nonlocal call_back_fun_idx
        rtn = (condition_value_change_fn(val, rg), call_back_fun_idx)
        call_back_fun_idx = min(len(call_back_names)-1, call_back_fun_idx+1)
        return rtn 
    return inner 