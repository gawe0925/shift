from datetime import timedelta

def calculate_end_date(start_date, dura):
    if not dura:
        return None
    elif dura == 'week':
        return start_date + timedelta(7)
    elif dura == 'fort':
        return start_date + timedelta(14)
    # for monthly
    elif start_date.month in [1, 3, 5, 7, 8, 10, 12]:
        return start_date + timedelta(30)
    elif start_date.month in [4, 6, 9, 11]:
        return start_date + timedelta(29)
    else:
        return start_date + timedelta(27)