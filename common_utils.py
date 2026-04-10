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

def convert_year_month_to_month(year, month):
    return year*12 + month -1 

def convert_year_month_to_time(year, month):
    return convert_year_month_to_month(year, month) - convert_year_month_to_month(2015, 1)

def convert_time_to_month_year(time):
    time+=convert_year_month_to_month(2015, 1)
    return (int(time//12) , month_fill(int((time%12) + 1)))

def getQueryParameters(x,mat_id):
    start_year, start_month, town_values = decode_matric(mat_id)
    start_time = convert_year_month_to_time(start_year, start_month)
    end_time = min(start_time + x-1, convert_year_month_to_time(2025, 12))
    return start_time, end_time, town_values

#condition to be fed as on_hit_row_fn 
def reduce_upper_bound(condition, val):
    return
    #condition[1] = val 
    #return 

#HANDLER CONTAINING LOGIC TO FACILITATE CHANGE CONDITIONS 
class ConditionHandler:
    #need to updateh condition 
    def __init__(self, condition, call_backs, on_hit_row_fn):
        self.condition = condition 
        self.call_back_fun_idx = 0
        self.call_back_names = call_backs
        self.on_hit_row_fn = on_hit_row_fn
    def __call__(self, val):
        #self.call_back_fun_idx = min(len(self.call_back_names)-1, self.call_back_fun_idx+1)
        self.on_hit_row_fn(self.condition, val)
        
        
    def get_call_back_name(self):
        return self.call_back_names[self.call_back_fun_idx]
