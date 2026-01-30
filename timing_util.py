import pandas as pd
import time

def print_timings(timings, start, title=None, end="\n"):
    """ print cumulative and invidual elapsed times stored in timings """
    timings["end"] = time.time()
    timings -= start
    time_diff = timings.diff().fillna(timings.iloc[0])
    if title:
        print("\n" + title)
    else:
        print(end="\n")
    print("timings:\n", pd.DataFrame({"cumul":timings, "diff":time_diff}),
        sep="", end=end)