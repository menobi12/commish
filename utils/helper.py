import pytz
from datetime import datetime, timedelta

def check_availability():
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    current_hour = now_est.hour
    current_day = now_est.weekday()

    if current_day == 1 and current_hour >= 4:  # Tuesday 4am onwards
        return True, now_est.strftime("%A")
    elif 1 < current_day < 4:  # All day Wednesday and Thursday until 7pm
        return True, now_est.strftime("%A")
    elif current_day == 4 and current_hour < 19:  # Thursday until 7pm
        return True, now_est.strftime("%A")
    else:
        return False, now_est.strftime("%A")
    

def get_current_week():
    date_to_week = {
        "9/5/2023": 1,
        "9/12/2023": 2,
        "9/19/2023": 3,
        "9/26/2023": 4,
        "10/3/2023": 5,
        "10/10/2023": 6,
        "10/17/2023": 7,
        "10/24/2023": 8,
        "10/30/2023": 9,
        "11/6/2023": 10,
        "11/13/2023": 11,
        "11/20/2023": 12,
        "11/27/2023": 13,
        "12/4/2023": 14,
        "12/11/2023": 15,
        "12/18/2023": 16
    }
    
    # Convert string dates to datetime objects
    date_to_week = {datetime.strptime(date, "%m/%d/%Y"): week for date, week in date_to_week.items()}
    
    # Sort the dictionary by date
    sorted_dates = sorted(date_to_week.keys())
    
    # Get current date
    current_date = datetime.now() - timedelta(hours=4)  # Adjusting for Eastern Standard Time
    
    # Find the current week
    current_week = 1
    for date in sorted_dates:
        if current_date < date:
            current_week = date_to_week[date]
            break
    
    return current_week
