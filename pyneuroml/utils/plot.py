#!/usr/bin/env python3
"""
Common utils to help with plotting

File: pyneuroml/utils/plot.py

Copyright 2023 NeuroML contributors
"""

from matplotlib.axes import Axes
import numpy


def add_text_to_2D_plot(ax: Axes, xv, yv, color, text: str):
    """Add text to a matplotlib plot between two points, center aligned
    horizontally, and bottom aligned vertically

    :param ax: matplotlib axis object
    :type ax: Axes
    :param xv: start and end coordinates in one axis
    :type xv: list[x1, x2]
    :param yv: start and end coordinates in second axix
    :type yv: list[y1, y2]
    :param color: color of text
    :type color: str
    :param text: text to write
    :type text: str

    """
    angle = int(numpy.rad2deg(numpy.arctan2((yv[1] - yv[0]), (xv[1] - xv[0]))))
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180

    ax.text((xv[0] + xv[1]) / 2, (yv[0] + yv[1]) / 2, text, color=color,
            horizontalalignment="center", verticalalignment="bottom",
            rotation_mode="default", rotation=angle)
