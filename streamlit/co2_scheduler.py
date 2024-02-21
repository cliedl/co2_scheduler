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
#st.set_page_config(layout="wide")

sys.path.append("..")
from src.plotting import plot_prediction
from api import get_weather_df, do_interpolation

# in units of kW: https://www.daftlogic.com/information-appliance-power-consumption.htm
co2_dictionary = {
    "Washing Machine": 0.5,
    "Dishwasher": 1.35,
    "Oven": 2.15,
    "A100 GPU": 0.5
}

if 'prediction_done' not in st.session_state:
    st.session_state.prediction_done = None

if "df_prediction" not in st.session_state:
    st.session_state.df_prediction = None

if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

if "data" not in st.session_state:
    st.session_state["data"] = None



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


st.title("CO2 Emissions Predictor")
if st.button("Make prediction", key="make_predicion_button"):
    with st.spinner('AI magic is happening...'):
        time.sleep(0)
        st.session_state.df_prediction = predict()
        st.session_state.prediction_done = True
        st.success('Done! 🔥')

if st.session_state.prediction_done == True:
    # Plot the CO2 emissions over the next 24 hours
    st.subheader("g CO2/kWh prediction for the next 3 days")
    
    fig = plot_prediction(st.session_state.df_prediction, st.session_state.data)
    st.plotly_chart(fig)

def add_task():
    element_id = uuid.uuid4()
    st.session_state["tasks"].append(str(element_id))

def remove_task(task_id):
    st.session_state["tasks"].remove(str(task_id))

def generate_task(task_id):
    task_container = st.empty()
    task_columns = task_container.columns(5)

    with task_columns[0]:
        task_type = st.selectbox("Select task type",
                                 list(co2_dictionary.keys()),
                                 key=f"task_{task_id}")
    with task_columns[1]:
        date = st.date_input('Select date', 
                             min_value=datetime.datetime.now(), 
                             max_value=datetime.datetime.now()+datetime.timedelta(days=5),
                             key=f"date_{task_id}") 

    with task_columns[2]:
        start_time = st.slider("Select time",
                               min_value=0, max_value=23, value=(17), step=1,
                               key=f"time_{task_id}")    
    with task_columns[3]:
        task_duration = st.number_input(
            "Task duration (hours)",
            min_value=1, max_value=24, step=1, value=2,
            key=f"duration_{task_id}")
        
    with task_columns[4]:
        st.button("Remove task", key=f"del_{task_id}",
                  on_click=remove_task, args=[task_id])

    return {"task_type": task_type, "task_duration": task_duration, "start_time": start_time, "start_date": date}


st.title("Task list")

task_collection = [] 


for task in st.session_state["tasks"]:
    task_data = generate_task(task)
    task_collection.append(task_data)

st.button("Add task", on_click=add_task)



def calculate_co2_impact(datetime, duration, consumption):
    index_start_time =  st.session_state.df_prediction[st.session_state.df_prediction["time_axis"]==datetime].index[0]
    return consumption*st.session_state.df_prediction[index_start_time:index_start_time+duration]["co2_predictions"].sum()

def optimize_schedule(duration, consumption):
    g_co2_per_kW = [np.sum(st.session_state.df_prediction["co2_predictions"].iloc[i:i+duration])\
                    for i in range(len(st.session_state.df_prediction)-duration)]
    min_g_co2 = np.min(g_co2_per_kW)*consumption
    max_g_co2 = np.max(g_co2_per_kW)*consumption

    datetime_min_g_co2 = st.session_state.df_prediction["time_axis"].iloc[np.argmin(g_co2_per_kW)]

    return min_g_co2, datetime_min_g_co2, max_g_co2

if len(task_collection) > 0:
    st.subheader("Calculate Co2 footprint")
    display = st.columns(2)
    data = pd.DataFrame(task_collection)
    data.loc[:, "consumption (kW)"] = data["task_type"].apply(
        lambda x: co2_dictionary[x]) * data["task_duration"]
    data.loc[:, "datetime"] = data["start_time"].apply(
        lambda time: datetime.datetime.strptime(str(data["start_date"].iloc[0])+'-'+str(time), "%Y-%m-%d-%H"))

   
    index_start_time =  st.session_state.df_prediction[st.session_state.df_prediction["time_axis"]==data["datetime"].iloc[0]].index[0]

    data.loc[:, "CO2 impact (g)"] = [calculate_co2_impact(data["datetime"].iloc[i], data["task_duration"].iloc[i], data["consumption (kW)"].iloc[i]) \
                  for i in range(len(data))]

    
    optimized = [(optimize_schedule(data["task_duration"].iloc[i], data["consumption (kW)"].iloc[i])) \
                 for i in range(len(data))]
    
    data.loc[:, "optimized CO2 impact (g)"] = [opt[0] for opt in optimized]
    data.loc[:, "optimal datetime"] = [opt[1] for opt in optimized]
    data.loc[:, "worst CO2 impact (g)"] = [opt[2] for opt in optimized]
    st.session_state["data"] = data
    
    st.write(data[["task_type", "datetime", "optimal datetime", "CO2 impact (g)", "optimized CO2 impact (g)"]])

    total_co2_optimized = data["optimized CO2 impact (g)"].sum()
    total_co2_worst_case = data["worst CO2 impact (g)"].sum()
    total_co2_selected = data["CO2 impact (g)"].sum()

    st.write(f"By optimizing your task schedule, you can:")
    st.write(f"reduce CO2 emissions by {total_co2_optimized-total_co2_selected} g!")
    st.write(f"This is a reduction by {int(100-100*total_co2_selected/total_co2_optimized)} %!")

    #st.write(list(optimized[0]), list(optimized[1]))
    st.write(data.head())
    st.write(data.dtypes)

    val = (total_co2_selected-total_co2_worst_case)/(total_co2_optimized-total_co2_worst_case)
    x = np.linspace(0, 1, 101)
    x[x > val] = None

    image = np.tile(x, 10)
    image = image.reshape((10, len(x)))

    fig, ax = plt.subplots()
    ax.imshow(image, cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()

    st.pyplot(fig)

