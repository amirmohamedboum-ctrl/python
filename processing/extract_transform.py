import re

def extract(row:str):
    pattern=re.compile(r'(?P<month>\w{3})\s(?P<day>\d{1,2})\s(?P<time>\d{2}:\d{2}:\d{2})\s.+:\s(?P<message>\w+)')
    match=re.search(pattern,row)
    if match:
        print(match.groupdict())
        
def filter_failed(rows: list[str]) -> list[str]:
    return [row for row in rows if "Failed" in row or "Invalid" in row]         