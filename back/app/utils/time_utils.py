import re

def parse_time_to_range(sched_str):
    """
    Parses complex time strings (e.g. '화 16:30(75)', '수 13:30-16:30') into minute ranges.
    """
    if not sched_str: 
        return []
    intervals = []
    
    # 1. format: 화 16:30(75) 507-102
    pattern1 = r'([월화수목금토일])\s*(\d{2}):(\d{2})\((\d+)\)'
    for day, hr, mn, dur in re.findall(pattern1, str(sched_str)):
        start_min = int(hr) * 60 + int(mn) 
        intervals.append({'day': day, 'start': start_min, 'end': start_min + int(dur)})
        
    # 2. format: 수 13:30-16:30 밀양M03-3350
    pattern2 = r'([월화수목금토일])\s*(\d{2}):(\d{2})-(\d{2}):(\d{2})'
    for day, shr, smn, ehr, emn in re.findall(pattern2, str(sched_str)):
        start_min = int(shr) * 60 + int(smn)
        end_min = int(ehr) * 60 + int(emn)
        intervals.append({'day': day, 'start': start_min, 'end': end_min})
        
    return intervals

def check_overlap(list1, list2):
    """
    Checks if any two time intervals overlap (Hard Constraint).
    """
    for time1 in list1:
        for time2 in list2:
            if time1['day'] == time2['day']:
                if max(time1['start'], time2['start']) < min(time1['end'], time2['end']): 
                    return True
    return False

def calculate_time_gap(list1, list2):
    """
    Calculates the gap (in minutes) between two lectures on the same day.
    Returns 0 if they don't share a day, or if they overlap.
    """
    min_gap = float('inf')
    has_gap = False
    for time1 in list1:
        for time2 in list2:
            if time1['day'] == time2['day']:
                # They are on the same day
                if time1['end'] <= time2['start']:
                    gap = time2['start'] - time1['end']
                    min_gap = min(min_gap, gap)
                    has_gap = True
                elif time2['end'] <= time1['start']:
                    gap = time1['start'] - time2['end']
                    min_gap = min(min_gap, gap)
                    has_gap = True
    return min_gap if has_gap else 0
