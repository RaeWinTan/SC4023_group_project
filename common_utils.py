import re

type TimeInt = int
type TownInt = int
"""
Town, in integer form
i.e. Bedok is represented as 0, Yishun is 9
"""
valid_matric = re.compile(r"^[A-Z]\d{7}[A-Z]", re.IGNORECASE)
"""
Regular expression to check if a string is a valid matriculation number, which we
assume to be one alpha seven digits one alpha
"""
def is_float(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False
#CALLBACKS FOR DATA VALIDATION
def required_range(a,b):
    def inner(val):
        nonlocal a, b 
        if is_float(val):
            val = float(val)
            return a<=val<=b, val 
        else: return False, "" 
    return inner
def required_string(val): 
    if len(val.strip())==0:
        return False, "" 
    else:
        return True, val 
def default_string(val):
    def inner(x):
        nonlocal val 
        if len(x.strip())==0:
            return True, val 
        return True, x 
    return inner 
def required_above_zero(x):
    if is_float(x):
        return float(x)>0, x 
    else:
        return False, 0


        

#CALLBACKS MOSTLY USED FOR ZONEMAPS ENCODING
def MinMax(arr: list[tuple[int, ...]]):
    mn,mx = arr[0],arr[0]
    for i in range(1, len(arr)):
        mn = min(arr[i], mn)
        mx = max(arr[i], mx)
    return (mn, mx)

#CALLBACKS USED FOR DATA PRESENTATION
def normalize_number(val):
    f = float(val)
    return int(f) if f.is_integer() else f
def month_fill(val):
    val = int(val)
    return f"{val:02d}"

#METHODS USED FOR PARSING QUERIES
def decode_matric(matric: str) -> tuple[TimeInt, list[TownInt]]:
    assert valid_matric.match(matric), "Invalid matriculation number"
    DIGIT_TO_YEAR  = [2020, 2021, 2022, 2023, 2024, 2015, 2016, 2017, 2018, 2019]
    digits = [int(c) for c in matric if c.isdigit()]
    last_digit        = digits[-1]   # start year
    second_last_digit = digits[-2]   # start month
    start_year = DIGIT_TO_YEAR[last_digit]
    start_month = 10 if second_last_digit == 0 else second_last_digit
    start_time = convert_year_month_to_time(start_year, start_month)
    town_values = set(digits)
    return start_time, list(town_values)

def convert_year_month_to_month(year: int, month: int) -> int:
    return year*12 + month -1 

def convert_year_month_to_time(year: int, month: int, base: tuple[int,int] = (2015, 1)) -> int:
    return convert_year_month_to_month(year, month) - convert_year_month_to_month(*base)

def convert_time_to_month_year(time: int) -> tuple[int, str]:
    time+=convert_year_month_to_month(2015, 1)
    return (int(time//12) , month_fill(int((time%12) + 1)))

def get_end_time(x: int, start_time: TimeInt) -> TimeInt:
    return min(start_time + x-1, convert_year_month_to_time(2025, 12))

#condition to be fed as on_hit_row_fn 
def reduce_upper_bound(condition, val):
    condition[1] = val 
    return 

#HANDLER CONTAINING LOGIC TO FACILITATE CHANGE CONDITIONS 
class ConditionHandler:
    #need to updateh condition 
    def __init__(self, condition, call_backs, on_hit_row_fn):
        self.condition = condition 
        self.call_back_fun_idx = 0
        self.call_back_names = call_backs
        self.on_hit_row_fn = on_hit_row_fn
    def __call__(self, val):
        self.call_back_fun_idx = min(len(self.call_back_names)-1, self.call_back_fun_idx+1)
        self.on_hit_row_fn(self.condition, val)
        
    def get_call_back_name(self):
        return self.call_back_names[self.call_back_fun_idx]
