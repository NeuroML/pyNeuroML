#!/usr/bin/env python3
"""
Utilities used in plotting functions

File: pyneuroml/plot/utils.py

Copyright 2022 NeuroML contributors
"""


import typing
import logging

import numpy as np
from matplotlib.lines import Line2D


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LineDataUnits(Line2D):
    """
    Taken from https://stackoverflow.com/questions/19394505/expand-the-line-with-specified-width-in-data-unit
    """

    def __init__(self, *args, **kwargs):
        _lw_data = kwargs.pop("linewidth", 1)
        super().__init__(*args, **kwargs)
        self._lw_data = _lw_data

    def _get_lw(self):
        if self.axes is not None:
            ppd = 72.0 / self.axes.figure.dpi
            trans = self.axes.transData.transform
            return ((trans((1, self._lw_data)) - trans((0, 0))) * ppd)[1]
        else:
            return 1

    def _set_lw(self, lw):
        self._lw_data = lw

    _linewidth = property(_get_lw, _set_lw)


def get_sphere_surface(
    x: float, y: float, z: float, radius: float, resolution: int = 20
) -> typing.Any:
    """Get surface points of a sphere centered at x, y, z with radius.

    Reference: https://stackoverflow.com/a/71053527/375067

    :param x: center x
    :type x: float
    :param y: center y
    :type y: float
    :param z: center z
    :type z: float
    :param radius: radius of sphere
    :type radius: float
    :param resolution: resolution (number of points in the surface)
    :type resolution: int
    :returns: list of [x, y, z] values


    """
    logger.debug(f"Sphere: got: {x}, {y}, {z}, {radius}")
    u, v = np.mgrid[0 : 2 * np.pi : resolution * 2j, 0 : np.pi : resolution * 1j]  # type: ignore
    X = radius * np.cos(u) * np.sin(v) + x
    Y = radius * np.sin(u) * np.sin(v) + y
    Z = radius * np.cos(v) + z

    return X, Y, Z


def get_frustrum_surface(
    x1: float,
    y1: float,
    z1: float,
    radius1: float,
    x2: float,
    y2: float,
    z2: float,
    radius2: typing.Optional[float] = None,
    resolution: int = 3,
    angular_resolution: int = 4,
    capped: bool = False,
) -> typing.Any:
    """Get surface points of a capped frustrum with centers at (x1, y1, z1) and
    (x2, y2, z2) and radii radius1 and radius2 respectively.

    If radius2 is not given, or radius1 and radius2 are the same, this results
    in a cylinder.

    Reference: https://stackoverflow.com/a/32383775/375067

    :param x1: proximal center x
    :type x1: float
    :param y1: proximal center y
    :type y1: float
    :param z1: proximal center z
    :type z1: float
    :param radius1: proximal radius of cylinder
    :type radius1: float
    :param x1: distal center x
    :type x1: float
    :param y1: distal center y
    :type y1: float
    :param z1: distal center z
    :type z1: float
    :param radius2: distal radius of cylinder
    :type radius2: float
    :param resolution: resolution (number of intermediate points on axis)
    :type resolution: int
    :param angular_resolution: resolution (number of angles for drawing the
        frustrum surface). More angles would result in a smoother surface, but
        also in a heavier (and so possibly slower) plot
    :type angular_resolution: int
    :param capped: whether the cylinder should be capped at the distal end
    :type capped: bool
    :returns: x, y, z, x_cap, y_cap, z_cap: surface points (None for the cap
        surface if capped is False)

    """
    if radius2 is None:
        radius2 = radius1

    logger.debug(
        f"Frustrum: got: {x1}, {y1}, {z1}, {radius1} -> {x2}, {y2}, {z2}, {radius2}"
    )

    p_proximal = np.array([x1, y1, z1])
    p_distal = np.array([x2, y2, z2])
    axis_vector = p_distal - p_proximal
    axis_mag = np.linalg.norm(axis_vector)

    axis_unit_vector = axis_vector / axis_mag

    somev = np.array([1, 0, 0])
    if (axis_unit_vector == somev).all():
        somev = np.array([0, 1, 0])

    perpv1 = np.cross(axis_unit_vector, somev)
    perpv1_unit = perpv1 / np.linalg.norm(perpv1)
    perpv2_unit = np.cross(axis_unit_vector, perpv1_unit)

    t = np.linspace(0.0, axis_mag, resolution)
    r = np.linspace(radius1, radius2, resolution)
    theta = np.linspace(0, 2 * np.pi, angular_resolution)

    t_grid, theta_grid = np.meshgrid(t, theta)
    r_grid, _ = np.meshgrid(r, theta)

    X, Y, Z = [
        p_proximal[i]
        + axis_unit_vector[i] * t_grid
        + r_grid * np.sin(theta_grid) * perpv1_unit[i]
        + r_grid * np.cos(theta_grid) * perpv2_unit[i]
        for i in [0, 1, 2]
    ]

    # create the cap surface, a circle at the distal end
    X_cap = None
    Y_cap = None
    Z_cap = None
    if capped:
        # does not need high resolution
        # enough to have points at the center and the circumference
        cap_r = np.linspace(0, radius2, 2)
        cap_r_grid, theta_grid2 = np.meshgrid(cap_r, theta)

        X_cap, Y_cap, Z_cap = [
            p_distal[i]
            + cap_r_grid * np.sin(theta_grid2) * perpv1_unit[i]
            + cap_r_grid * np.cos(theta_grid2) * perpv2_unit[i]
            for i in [0, 1, 2]
        ]

    return X, Y, Z, X_cap, Y_cap, Z_cap
