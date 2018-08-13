import os
import sys
import re
import json
import collections
import math
import copy

import scipy.stats
import matplotlib
import matplotlib.pyplot
import numpy

import ashlib.util.list_

import util

# TODO: provide more customizability to client. Callback function may help. Probably need more arbitrary formatting options as well.

DEFAULT_COLORS = ["blue", "green", "red", "yellow", "orange", "purple"]

class Point(object):

    def __init__(self, x_value, y_value, label=None):
        self.x_value = x_value
        self.y_value = y_value
        self.label = label

    def __repr__(self):
        return "%s(\n\tx value = %s, \n\ty value = %s\n\tlabel = %s\n)"% (self.__class__.__name__, self.x_value, self.y_value, self.label)

class PointSet(util.ListWrapper):

    def __init__(self, name, color=None, points=None, add_regression_line=False, additional_charting_behavior=None):
        self.name = name
        self.color = color
        
        if points is None: points = []
        for point in points:
            assert(isinstance(point, Point))
        super(PointSet, self).__init__(points)

        self.add_regression_line = add_regression_line
        self.additional_charting_behavior = additional_charting_behavior

    def append(self, point):
        assert(isinstance(point, Point))
        super(PointSet, self).append(point)

    def x_values(self):
        return [point.x_value for point in self]

    def y_values(self):
        return [point.y_value for point in self]

    def add_points_from_lists(self, x_values, y_values, labels=None):
        assert(len(x_values) == len(y_values))
        if labels is not None:
            assert(len(labels) == len(y_values))

        for index in range(len(x_values)):
            label = labels[index] if labels is not None else None
            self.append(Point(x_values[index], y_values[index], label=label))

        return self

    def __repr__(self):
        return "%s(\n\tx name = %s, \n\ty points = %s\n)"% (self.__class__.__name__, self.name, super(PointSet, self).__repr__())

class ScatterPlotData(util.ListWrapper):

    def __init__(self, point_sets=None):
        if point_sets is None: point_sets = []
        for point_set in point_sets:
            assert(isinstance(point_set, PointSet))
        assert(len(set(point_set.name for point_set in point_sets)) == len(point_sets)) # ensure names are unique
        super(ScatterPlotData, self).__init__(point_sets)

    def append(self, point_set):
        assert(isinstance(point_set, PointSet))
        assert(point_set.name not in [other_point_set.name for other_point_set in self]) # ensure names are unique
        super(ScatterPlotData, self).append(point_set)
    
    def add_point(self, point, set_name):
        def matching_point_set(set_name):
            for point_set in self:
                if point_set.name == set_name:
                    return point_set
            raise ValueError("Point set not found: %s" % (set_name,))
        
        matching_point_set(set_name).append(point)

    def all_points(self):
        return util.concatenate_lists(self)

def plot(points, x_label=None, y_label=None, chart_title=None, show_vs_save=True, output_dir_path=None):
    matplotlib.pyplot.clf()
    matplotlib.pyplot.figure(figsize=(17, 10))
    
    x_min = min(point.x_value for point in points.all_points())
    x_max = max(point.x_value for point in points.all_points())
    x_range = float(x_max) - float(x_min)
    x_step = x_range / 25.0
    
    y_min = min(point.y_value for point in points.all_points())
    y_max = max(point.y_value for point in points.all_points())
    y_range = float(y_max) - float(y_min)
    
    # Include a buffer of 20% the range size on every side:
    matplotlib.pyplot.axis([x_min - x_range * 0.2, x_max + x_range * 0.2, y_min - y_range * 0.2, y_max + y_range * 0.2])
    
    default_colors = copy.deepcopy(DEFAULT_COLORS)
    
    for point_set in points:
        # Determine appropriate color:
        if point_set.color is not None:
            color = point_set.color
        else:
            if len(default_colors) == 0:
                raise ValueError("Too many point sets without colors provided. Ran out of default colors.")
            color = default_colors[0]
            del default_colors[0]
        
        # Scatter plot:
        matplotlib.pyplot.scatter(point_set.x_values(), point_set.y_values(), s=100.0, alpha=0.25, c=color, label=point_set.name)
        for point in point_set:
            if point.label is not None:
                fontdict={"fontsize": 6, "horizontalalignment": "center", "color": color}
                matplotlib.pyplot.text(point.x_value, point.y_value, point.label, fontdict=fontdict)
    
        # Linear regression line:
        if point_set.add_regression_line:
            slope, intercept, r_value, p_value, stderr = scipy.stats.linregress(point_set.x_values(), point_set.y_values())
            lsrl_x_values = numpy.arange(x_min - x_range * 0.2, x_max + x_range * 0.2 + x_step / 2.0, x_step)
            lsrl_y_values = [x * slope + intercept for x in lsrl_x_values]
            matplotlib.pyplot.plot(lsrl_x_values, lsrl_y_values, "--", c=color)

        # Additional (custom) charting behavior:
        if point_set.additional_charting_behavior is not None:
            point_set.additional_charting_behavior(point_set, x_min, x_max, x_range, x_step, y_min, y_max, y_range, color)

    if len(points) > 1:
        matplotlib.pyplot.legend()
    
    if x_label is not None:
        matplotlib.pyplot.xlabel(x_label)
    if y_label is not None:
        matplotlib.pyplot.ylabel(y_label)
    if chart_title is not None:
        matplotlib.pyplot.title(chart_title)

    if show_vs_save:
        matplotlib.pyplot.show()
    
    else:
        assert(chart_title is not None)
        assert(output_dir_path is not None)
        file_name = "%s.pdf" % (chart_title,)
        file_path = os.path.join(output_dir_path, file_name)
        matplotlib.pyplot.savefig(file_path, bbox_inches="tight")
