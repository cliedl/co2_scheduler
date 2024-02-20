import sys
import uuid
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
sys.path.append("..")
from src.plotting import plot_prediction


# Mock data - replace this with model prediction
time_axis = pd.date_range("2024-02-20", periods=24, freq="H")
co2_predictions = np.sin(2*np.pi*np.arange(24)/24)**2

# Title
st.title("CO2 Emissions Predictor")

# Plot the CO2 emissions over the next 24 hours
st.subheader("g CO2/kWh prediction for the next 24 hours")
fig = plot_prediction(time_axis, co2_predictions)
st.pyplot(fig)


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

for task in st.session_state["tasks"]:
    task_data = generate_task(task)
    task_collection.append(task_data)

menu = st.columns(2)

with menu[0]:
    st.button("Add task", on_click=add_task)


# def calculate_co2_impact(data):

if len(task_collection) > 0:
    st.subheader("Calculate Co2 footprint")
    display = st.columns(2)
    data = pd.DataFrame(task_collection)
    data.loc[:, "consumption (kWh)"] = data["task_type"].apply(
        lambda x: co2_dictionary[x]) * data["task_duration"]
    st.write(data.head())


# # Compute CO2 emissions for selected time period
# selected_period = time_axis[selected_time:selected_time+task_duration+1]
# total_co2_emissions = np.sum(
#     co2_predictions[selected_time:selected_time+task_duration+1])

# st.write(
#     f"Total CO2 emissions for selected period: {total_co2_emissions:.2f} gCO2")
