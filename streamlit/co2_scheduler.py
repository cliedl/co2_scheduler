import sys
import uuid

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import datetime
import joblib
import time
import requests

import plotly.io as pio
pio.templates.default = 'plotly' 


import streamlit as st
from streamlit_datetime_range_picker import datetime_range_picker

sys.path.append("..")
from src.plotting import plot_prediction
from api import get_weather_df, do_interpolation


def predict(fetch_data=False):
    # Mock data - replace this with actual weather forecast
    df = pd.read_csv("../data/combined_data.csv")
    df = df.iloc[-24*3:] # Take last three days of training data
    
    if fetch_data:
        weather_df = get_weather_df()
        hourly_weather_df = do_interpolation(weather_df)
        hourly_weather_df.to_csv("../data/forecast_0.csv")
    else:
        hourly_weather_df = pd.read_csv("../data/forecast_0.csv")

    hourly_weather_df.loc[:, "datetime"] = pd.to_datetime(hourly_weather_df["time_unix"], unit='s')
    hourly_weather_df.loc[:, 'month'] = hourly_weather_df['datetime'].dt.month
    hourly_weather_df.loc[:, 'hour'] = hourly_weather_df['datetime'].dt.hour

    features = [key for key in df if "wind" in key] + ["month", "hour"]
    model = joblib.load("../models/xgb_1708455353.pkl")
    co2_predictions = model.predict(hourly_weather_df[features])
    time_axis = hourly_weather_df["datetime"]
    df_prediction = pd.DataFrame({'time_axis': time_axis, 'co2_predictions':co2_predictions})

    return df_prediction

# Title
st.title("CO2 Emissions Predictor")
if st.button("Make prediction"):
    with st.spinner('AI magic is happening...'):
        #time.sleep(3)
        df_prediction = predict()
        st.success('Done! 🔥')

    st.write(df_prediction.head())
    # Plot the CO2 emissions over the next 24 hours
    st.subheader("g CO2/kWh prediction for the next 3 days")

    fig = plot_prediction(df_prediction)
    st.plotly_chart(fig)


# in units of kW: https://www.daftlogic.com/information-appliance-power-consumption.htm
co2_dictionary = {
    "Washing Machine": 0.5,
    "Dishwasher": 1.35,
    "Oven": 2.15,
    "A100 GPU": 0.5
}

# initialize tasks_collection for the different tasks
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []
task_collection = []


def add_task():
    element_id = uuid.uuid4()
    st.session_state["tasks"].append(str(element_id))

def remove_task(task_id):
    st.session_state["tasks"].remove(str(task_id))

def generate_task(task_id):
    task_container = st.empty()
    task_columns = task_container.columns(4)

    with task_columns[0]:
        task_type = st.selectbox("Select task type",
                                 list(co2_dictionary.keys()),
                                 key=f"task_{task_id}")
    with task_columns[1]:
        task_duration = st.number_input(
            "Enter task duration (hours)",
            min_value=1, max_value=24, step=1, value=2,
            key=f"duration_{task_id}")
    with task_columns[2]:
        start_time = st.slider("Select time for the task",
                               min_value=0, max_value=23, value=(8), step=1,
                               key=f"time_{task_id}")
    with task_columns[3]:
        st.button("Remove task", key=f"del_{task_id}",
                  on_click=remove_task, args=[task_id])

    return {"task_type": task_type, "task_duration": task_duration, "start_time": start_time}


st.title("Task list")
date = st.date_input('Select date')
datetime_string = datetime_range_picker(start=0, end=24*5, unit='hours', key='range_picker', 
                                        picker_button={'is_show': False, 'button_name': 'Refresh last 30min'})

                           
for task in st.session_state["tasks"]:
    task_data = generate_task(task)
    task_collection.append(task_data)

st.button("Add task", on_click=add_task)


# def calculate_co2_impact(data):

if len(task_collection) > 0:
    st.subheader("Calculate Co2 footprint")
    display = st.columns(2)
    data = pd.DataFrame(task_collection)
    data.loc[:, "consumption (kWh)"] = data["task_type"].apply(
        lambda x: co2_dictionary[x]) * data["task_duration"]
    data.loc[:, "datetime"] = data["start_time"].apply(
        lambda time: datetime.datetime.strptime(str(date)+'-'+str(time), "%Y-%m-%d-%H"))

    st.write(data.head())
