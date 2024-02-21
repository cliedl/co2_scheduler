import plotly.express as px
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np


def get_tasks(df=None) -> list:
    """
    Returns a list of tasks based on the input dataframe. If the dataframe is None, an empty list is returned.
    If the dataframe is not None, creates a list of tasks with start times and durations based on the input dataframe.
    """
    if df is None:
        return []
    else:
        tasks = df.copy()
    task_list = []
    for i in range(len(tasks)):
        task_list.append(
            {
                tasks.task_type.iloc[i]: [
                    tasks.datetime.iloc[i] + datetime.timedelta(hours=j) for j in range(tasks.task_duration.iloc[i])
                ],
            }
        )

    return task_list


def plot_prediction(df: pd.DataFrame, tasks: pd.DataFrame) -> plt.figure:
    """
    Plot the CO2 predictions over time using the provided dataframe and tasks data.
    Args:
        df (pd.DataFrame): The dataframe containing the time axis and CO2 predictions.
        tasks (pd.DataFrame): The tasks data to be used for plotting.
    Returns:
        plt.figure: The plot figure showing the CO2 predictions over time.
    """
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
