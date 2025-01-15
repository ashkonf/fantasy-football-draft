import os
import re
import json
import collections
import math
import copy
import itertools

import scipy.stats
import matplotlib.pyplot as plt
import numpy

DEFAULT_COLORS = ["blue", "green", "red", "yellow", "orange", "purple"]

class Point:
    def __init__(self, x_value, y_value, label=None):
        self.x_value = x_value
        self.y_value = y_value
        self.label = label

    def __repr__(self):
        return f"{self.__class__.__name__}(x={self.x_value}, y={self.y_value}, label={self.label})"

class PointSet(list):
    def __init__(self, name, color=None, points=None, add_regression_line=False, additional_charting_behavior=None):
        super().__init__(points or [])
        self.name = name
        self.color = color
        self.add_regression_line = add_regression_line
        self.additional_charting_behavior = additional_charting_behavior
        for point in self:
            assert isinstance(point, Point)

    def append(self, point):
        assert isinstance(point, Point)
        super().append(point)

    def x_values(self):
        return [point.x_value for point in self]

    def y_values(self):
        return [point.y_value for point in self]

    def add_points_from_lists(self, x_values, y_values, labels=None):
        assert len(x_values) == len(y_values)
        if labels:
            assert len(labels) == len(y_values)
        
        for i, (x, y) in enumerate(zip(x_values, y_values)):
            label = labels[i] if labels else None
            self.append(Point(x, y, label=label))
        return self

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, points={super().__repr__()})"

class ScatterPlotData(list):
    def __init__(self, point_sets=None):
        super().__init__(point_sets or [])
        for ps in self:
            assert isinstance(ps, PointSet)
        assert len(set(ps.name for ps in self)) == len(self), "Point set names must be unique"

    def append(self, point_set):
        assert isinstance(point_set, PointSet)
        assert point_set.name not in [ps.name for ps in self], "Point set name must be unique"
        super().append(point_set)
    
    def add_point(self, point, set_name):
        for ps in self:
            if ps.name == set_name:
                ps.append(point)
                return
        raise ValueError(f"Point set not found: {set_name}")
    
    def all_points(self):
        return list(itertools.chain.from_iterable(self))

def plot(points, x_label=None, y_label=None, chart_title=None, show_vs_save=True, output_dir_path=None):
    plt.clf()
    plt.figure(figsize=(17, 10))
    
    all_points = points.all_points()
    x_min, x_max = min(p.x_value for p in all_points), max(p.x_value for p in all_points)
    y_min, y_max = min(p.y_value for p in all_points), max(p.y_value for p in all_points)
    x_range, y_range = float(x_max - x_min), float(y_max - y_min)
    x_step = x_range / 25.0
    
    plt.axis([
        x_min - x_range * 0.2, x_max + x_range * 0.2,
        y_min - y_range * 0.2, y_max + y_range * 0.2
    ])
    
    default_colors = copy.deepcopy(DEFAULT_COLORS)
    
    for point_set in points:
        color = point_set.color
        if not color:
            if not default_colors:
                raise ValueError("Too many point sets; ran out of default colors.")
            color = default_colors.pop(0)
        
        plt.scatter(point_set.x_values(), point_set.y_values(), s=100.0, alpha=0.25, c=color, label=point_set.name)
        for point in point_set:
            if point.label:
                fontdict = {"fontsize": 6, "horizontalalignment": "center", "color": color}
                plt.text(point.x_value, point.y_value, point.label, fontdict=fontdict)
    
        if point_set.add_regression_line:
            slope, intercept, _, _, _ = scipy.stats.linregress(point_set.x_values(), point_set.y_values())
            lsrl_x_values = numpy.arange(x_min - x_range * 0.2, x_max + x_range * 0.2 + x_step / 2.0, x_step)
            lsrl_y_values = [x * slope + intercept for x in lsrl_x_values]
            plt.plot(lsrl_x_values, lsrl_y_values, "--", c=color)

        if point_set.additional_charting_behavior:
            point_set.additional_charting_behavior(point_set, x_min, x_max, x_range, x_step, y_min, y_max, y_range, color)

    if len(points) > 1:
        plt.legend()
    
    if x_label:
        plt.xlabel(x_label)
    if y_label:
        plt.ylabel(y_label)
    if chart_title:
        plt.title(chart_title)

    if show_vs_save:
        plt.show()
    else:
        assert chart_title, "Chart title must be provided to save the file."
        assert output_dir_path, "Output directory must be provided to save the file."
        file_name = f"{chart_title}.pdf"
        file_path = os.path.join(output_dir_path, file_name)
        plt.savefig(file_path, bbox_inches="tight")
