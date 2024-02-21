import sys
import uuid

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import datetime
import time

import plotly.io as pio
pio.templates.default = 'plotly' 

import streamlit as st
st.set_page_config(layout="wide")

sys.path.append("..")
from src.plotting import plot_prediction
from api import get_weather_df, do_interpolation
import src.co2_dictionary
from src.model import predict
from src.co2_calculations import calculate_co2_impact, optimize_schedule

# in units of kW: https://www.daftlogic.com/information-appliance-power-consumption.htm
co2_dictionary = {
    "Washing Machine": 0.5,
    "Dishwasher": 1.35,
    "Oven": 2.15,
    "A100 GPU": 0.5
}

# Initialize session states
if 'prediction_done' not in st.session_state:
    st.session_state.prediction_done = None

if "df_prediction" not in st.session_state:
    st.session_state.df_prediction = None

if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

if "data" not in st.session_state:
    st.session_state["data"] = None

if "task_collection" not in st.session_state:
    st.session_state["task_collection"] = []

# Title of the app
st.title("CO2 Emissions Predictor :bulb:")

# Button: Make prediction
if st.button("Make prediction", key="make_predicion_button"):
    with st.spinner('AI magic is happening...'):
        time.sleep(3)
        st.session_state.df_prediction = predict()
        st.session_state.prediction_done = True
        st.success('Done! 🔥')

if st.session_state.prediction_done == True:
    # Plot the CO2 emissions over the next 5 days
    st.subheader("g CO2/kWh prediction for the next 5 days")
    
    fig = plot_prediction(st.session_state.df_prediction, st.session_state.data)
    st.plotly_chart(fig)


# Helper functions to generate task list dynamically
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
        start_date = st.date_input('Select date', 
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

    return {"task_type": task_type, "task_duration": task_duration, "start_time": start_time, "start_date": start_date}

# Task list
st.subheader("Task list")
task_collection = [] 

for task in st.session_state["tasks"]:
    task_data = generate_task(task)
    task_collection.append(task_data)

st.button("Add task", on_click=add_task)

# If task_collection is larger than 0, start calulations
if len(task_collection) > 0:
    st.subheader("Calculate CO2 footprint")
    
    # Create dataframe to save co2 calculations for each task
    data = pd.DataFrame(task_collection)

    # Calculate total consumption of each task
    data.loc[:, "consumption (kW)"] = data["task_type"].apply(
        lambda x: co2_dictionary[x]) * data["task_duration"]
    
    # Calculate datetime for each task from start_time     
    datetime_strings = [str(data["start_date"].iloc[i])+"-"+str(data["start_time"].iloc[i]) for i in range(len(data))]
    data.loc[:, "datetime"] = [datetime.datetime.strptime(t, "%Y-%m-%d-%H") for t in datetime_strings]

    # Calculate CO2 impact for each task
    data.loc[:, "CO2 impact (g)"] = [calculate_co2_impact(data["datetime"].iloc[i], \
                                                          data["task_duration"].iloc[i], \
                                                          data["consumption (kW)"].iloc[i],
                                                          st.session_state.df_prediction) \
                                                            for i in range(len(data))]

    # Calculate optimal co2 impact and optimal time for each task
    optimized = [(optimize_schedule(data["task_duration"].iloc[i], \
                                    data["consumption (kW)"].iloc[i], \
                                    st.session_state.df_prediction)) \
                                    for i in range(len(data))]

    data.loc[:, "optimized CO2 impact (g)"] = [opt[0] for opt in optimized]
    data.loc[:, "optimal datetime"] = [opt[1] for opt in optimized]
    data.loc[:, "worst CO2 impact (g)"] = [opt[2] for opt in optimized]
    
    # Save session state
    st.session_state["data"] = data

    # Print optimized schedule
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### This is your selected schedule:")
        st.write(data[["task_type", "datetime", "optimal datetime"]])
        st.markdown("")
        st.markdown("##### This is an optimized schedule:")
        st.write(data[["task_type", "CO2 impact (g)", "optimized CO2 impact (g)"]])

        total_co2_optimized = data["optimized CO2 impact (g)"].sum()
        total_co2_worst_case = data["worst CO2 impact (g)"].sum()
        total_co2_selected = data["CO2 impact (g)"].sum()

    with col2:
        st.markdown(f"##### By optimizing your task schedule, you can:")
        st.write(f"reduce CO2 emissions by {-(total_co2_optimized-total_co2_selected)/1e3:.2f} kg!")
        st.write(f"This is a reduction by {-int(100-100*total_co2_selected/total_co2_optimized)} %!")

        # Plot optimization progress bar
        st.markdown("##### Optimization progress")
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


# Rerun app if change in taks_collection is detected
if st.session_state["task_collection"] != task_collection:
    st.session_state["task_collection"] = task_collection
    st.experimental_rerun()   




