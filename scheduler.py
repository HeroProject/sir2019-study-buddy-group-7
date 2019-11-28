from datetime import datetime
import math

def make_schedule(time_est: int, time_remaining: int, start_hour=None, fudge_ratio=2.0):
    """Generates a pomodoro-like schedule with given parameters."""

    # Get the current hour if no start time is provided
    if start_hour is None:
        start_hour = float(datetime.now().hour)
        start_hour += math.ceil(2*(datetime.now().minute / 60))/2
    # We compensate for planning fallacy with a fudge ratio
    # time_needed = time_est * fudge_ratio
    # Next, we use a Pomodoro scheme to create work/break bins
    bins = int(2 * time_remaining)
    bin_assignments = []
    time_stamp = float(start_hour)
    last_activity = None
    for i in range(bins):
        btype = 'revise'
        if i % 3 == 0:
            btype = 'take a break'
        if i % 6 == 0 and time_stamp < 22:
            btype = 'have a snack'
        if i % 12 == 0:
            btype = 'get some exercise'
        if i == 0:
            btype = 'revise'
        if time_stamp < 7.0:
            btype = 'get some sleep'
        if btype != last_activity:
            bin_start = stringify_time(time_stamp)
            # bin_end = stringify_time(time_stamp + 0.5)
            bin_assignments.append(f'At {bin_start}, {btype}')
        last_activity = btype
        time_stamp += 0.5
        if time_stamp > 24.0:
            time_stamp -= 24.0
    if len(bin_assignments) > 8:
        return bin_assignments[:8]
    return bin_assignments


def stringify_time(hour: float):
    """Converts a float of time in hours to readable string"""
    hour = float(hour)
    if hour > 24.0:
        hour -= 24.0
    i_hour = int(hour)
    mins = int((hour - float(i_hour)) * 60)
    if mins > 1:
        return f'{i_hour} {mins}'
    else:
        return f'{i_hour}'
