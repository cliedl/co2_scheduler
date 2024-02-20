import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def plot_prediction(x, y):
    cmap = plt.get_cmap("RdYlGn_r")

    y_scaled = (y-np.min(y))/(np.max(y)-np.min(y))

    plotly_colormap = [
        f'rgb{tuple(int(256 * x_) for x_ in cmap(y_)[:-1])}' for y_ in y_scaled]

    fig = px.bar(x=x, y=y, color=y,
                color_discrete_sequence=plotly_colormap)\
                    .update_layout(showlegend=False)\
                   
    return fig