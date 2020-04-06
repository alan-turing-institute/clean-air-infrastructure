from datetime import timedelta, datetime
import pandas as pd

def add_timerange_group_col(scoot_df, start, end, n_hours):
    """
    Return the dataframe with a new column that has the timerange group that observation falls in.
    """
    n_hours = 3   # number of hours to increase group by

    scoot_df["measurement_start_utc"] = pd.to_datetime(scoot_df["measurement_start_utc"])

    start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    i = 0
    scoot_df["label"] = -1
    group_list = []
    while start < datetime.strptime(end, "%Y-%m-%d %H:%M:%S"):
        end = start +timedelta(hours=n_hours)
        scoot_df.loc[
            (scoot_df["measurement_start_utc"] >= start) & (scoot_df["measurement_start_utc"] < end), "label"
        ] = i
        i += 1
        group_list.append(dict(
            start=start,
            end=end,
        ))
        start = end
        
    gb = scoot_df.groupby(["label", "detector_id"])
    gb.get_group((1,"N00/002e1"))