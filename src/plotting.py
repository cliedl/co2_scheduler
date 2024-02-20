import numpy as np
import matplotlib.pyplot as plt


def plot_prediction(x, y):
    fig, ax = plt.subplots(figsize=(6, 2))
    # plot only the outline of the polygon, and capture the result
    poly, = ax.fill(x, y, facecolor='none')
    # get the extent of the axes
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    # create a dummy image
    img_data = np.arange(ymin, ymax, (ymax-ymin)/100.)
    img_data = img_data.reshape(img_data.size, 1)

    # plot and clip the image
    im = ax.imshow(img_data, aspect='auto', origin='lower', cmap="RdYlGn", extent=[
        xmin, xmax, ymin, ymax], vmin=y.min(), vmax=y.max())

    im.set_clip_path(poly)
    return fig
