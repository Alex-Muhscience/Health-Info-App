from datetime import datetime

def parse_date(date_str, format='%Y-%m-%d'):
    try:
        return datetime.strptime(date_str, format).date()
    except (ValueError, TypeError):
        return None

def parse_datetime(datetime_str, format='%Y-%m-%d %H:%M:%S'):
    try:
        return datetime.strptime(datetime_str, format)
    except (ValueError, TypeError):
        return None