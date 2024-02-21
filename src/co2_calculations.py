import numpy as np
import pandas as pd

def calculate_co2_impact(datetime, duration, consumption, df):
    index_start_time =  df[df["time_axis"]==datetime].index[0]
    
    return consumption*df[index_start_time:index_start_time+duration]["co2_predictions"].sum()

def optimize_schedule(duration, consumption, df):
    g_co2_per_kW = [np.sum(df["co2_predictions"].iloc[i:i+duration])\
                    for i in range(len(df)-duration)]
    min_g_co2 = np.min(g_co2_per_kW)*consumption
    max_g_co2 = np.max(g_co2_per_kW)*consumption

    datetime_min_g_co2 = df["time_axis"].iloc[np.argmin(g_co2_per_kW)]

    return min_g_co2, datetime_min_g_co2, max_g_co2