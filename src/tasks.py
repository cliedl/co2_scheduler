import uuid

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