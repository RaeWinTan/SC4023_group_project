#CALLBACKS MOSTLY USED FOR ZONEMAPS ENCODING
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

#CALLBACKS USED FOR DATA PRESENTATION
def normalize_number(val):
    f = float(val)
    return int(f) if f.is_integer() else f
def month_fill(val):
    val = int(val)
    return f"{val:02d}"

#METHODS USED FOR PARSING QUERIES
def decode_matric(matric):
    DIGIT_TO_YEAR = {
        '5': 2015, '6': 2016, '7': 2017, '8': 2018, '9': 2019,
        '0': 2020, '1': 2021, '2': 2022, '3': 2023, '4': 2024
    }
    digits = [c for c in matric if c.isdigit()]
    last_digit        = digits[-1]   # target year
    second_last_digit = digits[-2]   # start month
    target_year  = DIGIT_TO_YEAR[last_digit]
    start_month  = 10 if second_last_digit == '0' else int(second_last_digit)
    town_values = [int(d) for d in digits] 
    return target_year, start_month, list(set(town_values))

def getQueryParameters(x,mat_id):
    start_year, start_month, town_values = decode_matric(mat_id)
    (end_year, end_month) = increase_year_month((start_year, start_month), x-1)
    town_values_encoded = bit_encoded(town_values) 
    return start_year, start_month, end_year, end_month, town_values_encoded

#LOGIC TO INCREASE YEAR MONTH
def increase_year_month(t,mths):
    year,month = t
    year-=1 
    month-=1 
    return (1+year+(month+mths)//12, 1 + (month+mths)%12)

#CALLBACKS MOSTLY USED FOR VECTORIZATION CONDITIONAL BOUNDS USED IN CONJECTION WITH change_fn
def year_month_change_fn(val, rg):
    new_start = increase_year_month(val, 1)
    return (new_start, rg[1])
def price_per_area_change_fn(val, rg):
    return (rg[0], val)
def fixed_change_fn(val, rg):
    return rg

#HANDLER CONTAINING LOGIC TO FACILITATE CHANGE CONDITIONS IN VECTORIZE SEARCH
class ConditionHandler:
    def __init__(self, on_row_hit_condition_change_fn, on_zone_condition_change_fn, call_back_names):
        self.on_row_hit_condition_change_fn = on_row_hit_condition_change_fn 
        self.on_zone_condition_change_fn = on_zone_condition_change_fn
        self.call_back_names = call_back_names 
        self.call_back_fun_idx = 0 
    def on_row_hit(self, val, rg):
        rtn = self.on_row_hit_condition_change_fn(val, rg)
        self.call_back_fun_idx = min(len(self.call_back_names)-1, self.call_back_fun_idx+1)
        return rtn 
    def on_zone_hit(self, val, rg):#update 
        return rtn 
    def get_call_back_name(self):
        return self.call_back_names[self.call_back_fun_idx]
#can put logic in condition handler?

class EarlyStopping:
    def __init__(self, conditions, check_condition_fns):
        self.conditions = conditions 
        self.check_condition_fns = check_condition_fns 
    def can_stop(self):
        return any(self.check_condition_fns[i](self.conditions[i]) for i in range(len(self.conditions)))


#should have a codntion handler here as well
#condtion handle for some condition
#handle the coindition where 
#while scanning the zones
#check Zone Scnning handler: while scanning hte zone 
    #update lower bound of year,monh,
    #update upper bound of price/sqm


"""
JUMP CONDITIONS:
    if there is a hit:
        jump to next different year, month
    elif zone price/sqm lower bound [above, equal or above] condition upper bound:
        jump to next different year, month
    #CAN USE DP O(1) can 

STOPPING CONDITIONS:
    #zone year month lower bound above condition upper bound

simple early stopong only one element for now
one zone check
in the zonemap search
    if zone_maps[0].getZone(idx)
    the lower bound is 
"""
