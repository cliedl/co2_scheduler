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
    task_list = []
    for i in range(len(tasks)):
        task_dict = {}
        task_dict[tasks.task_type.iloc[i]] = list(tasks.iloc[i][['task_duration', 'datetime']])
        task_list.append(task_dict)

    for i in range(len(task_list)):
        for key, value in task_list[i].items():
            length = value[0]
            date = value[1]
            temp_list = []
            for j in range(length):
                temp_list.append(date + datetime.timedelta(hours=j))
        task_list[i][key] = temp_list

    return task_list


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
            x=list(trace.values())[0],
            y=df[df.time_axis.isin(list(trace.values())[0])].co2_predictions,
            name=list(trace.keys())[0],
        ).update_layout(barmode='overlay')
    return fig
