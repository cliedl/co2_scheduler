import plotly.express as px
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np


def get_tasks(df=None):
    if df is None:
        return []
    else:
        tasks = df.copy()
    for task in tasks.task_type:
        # date_time = datetime.datetime.fromisoformat(tasks[tasks.task_type == task].datetime.iloc[0])
        date_time = tasks[tasks.task_type == task].datetime.iloc[0]
        for i in range(tasks[tasks.task_type == task].task_duration.iloc[0]):
            tasks.loc[i + len(tasks)] = pd.NA
            tasks.loc[:, 'task_type'].iloc[-1] = task
            tasks.loc[:, 'datetime'].iloc[-1] = str(date_time + datetime.timedelta(hours=i + 1))
            tasks.loc[:, 'optimal datetime'].iloc[-1] = str(date_time + datetime.timedelta(hours=i + 1))

    tasks['datetime'] = pd.to_datetime(tasks['datetime'])
    tasks['optimal datetime'] = pd.to_datetime(tasks['optimal datetime'])

    tasks = tasks[['task_type', 'datetime', 'optimal datetime']]
    tasks_tp = []
    for i in tasks.task_type.unique():
        tasks_tp.append((tasks[tasks.task_type == i]))

    return tasks_tp


def plot_prediction(df, tasks):
    x = df["time_axis"]
    y = df["co2_predictions"]
    fig = px.bar(
        x=x,
        y=y,
        labels={"y": "g CO2 / kWh", "x": ""},
    )
    traces = get_tasks(tasks)
    for trace in traces:
        fig.add_bar(
            x=trace.datetime, y=df[df.time_axis.isin(trace.datetime)].co2_predictions, name=trace.task_type.iloc[0]
        ).update_layout(barmode='overlay')
    return fig
