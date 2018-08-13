import os
import sys
import re
import bs4
import ntpath
import collections
import math
import matplotlib

import numpy
import scipy

import ashlib.util.file_
import ashlib.util.dir_
import ashlib.util.str_

import charting
import util
import infra

def build_position_map(players):
    position_map = {}
    for player in players:
        if player.position is not None:
            if player.position not in position_map:
                position_map[player.position] = []
            position_map[player.position].append(player)
    return position_map

LEAGUE_SIZE = 10

def calculate_draft_value(player, draft_position):
    return player.get_average_projected_ppg() - f(draft_position + LEAGUE_SIZE)

def rank_players_by_draft_value(draft_position, remaining_player_names):
    pairs = []
    
    for name in remaining_player_names:
        player = infra.Player(name).find_match(players)
        value = calculate_draft_value(player, draft_position)
        pairs.apppend((player, value))
        
    pairs = sorted(pairs, key=lambda pair: pair[1], reverse=True)
    
    print "Ranking:"
    print "========"
    for pair in pairs:
        print pair[0], "(draft value = %s)" % (pair[1],)

def fit_curve(point_set):
    def func(x_value, coefficient1, coefficient2, x_intercept, exponent, y_intercept):
        return coefficient1 / numpy.power(coefficient2 * (x_value + x_intercept), exponent) + y_intercept
        
    x_values = point_set.x_values()
    y_values = point_set.y_values()
    
    # Removing QB points that mess up function:
    filtered_x_values = []
    filtered_y_values = []
    for index, x_value in enumerate(x_values):
        y_value = y_values[index]
        if point_set.name != "QB" or y_value > 200:
            filtered_x_values.append(x_value)
            filtered_y_values.append(y_value)

    return (func, scipy.optimize.curve_fit(func, filtered_x_values, filtered_y_values, maxfev=1000000)[0])

def main():
    players = infra.load_players()

    plot_data = charting.ScatterPlotData()
    for position in build_position_map(players).keys():
        point_set = charting.PointSet(position)
        plot_data.append(point_set)

    for player in players:
        for source in player.rank_map:
            if source in player.projected_ppg_map:
                point = charting.Point(player.get_rank(source), player.get_projected_ppg(source))#, player.name)
                plot_data.add_point(point, player.position)

    parameters = {}
    functions = {}

    for point_set in plot_data:
        functions[point_set.name], parameters[point_set.name] = fit_curve(point_set)

        def additional_charting_behavior(point_set, x_min, x_max, x_range, x_step, y_min, y_max, y_range, color):
            func = functions[point_set.name]
            params = parameters[point_set.name]
            lsrl_x_values = numpy.arange(x_min - x_range * 0.2, x_max + x_range * 0.2 + x_step / 2.0, x_step)
            lsrl_y_values = [func(x_value, *params) for x_value in lsrl_x_values]
            
            print point_set.name
            print lsrl_x_values
            print lsrl_y_values
            print
            
            # Removing points outside first quandrant:
            filtered_lsrl_x_values = []
            filtered_lsrl_y_values = []
            for index, x_value in enumerate(lsrl_x_values):
                y_value = lsrl_y_values[index]
                if x_value >= 0 and y_value >= 0 and y_value < 1000.0:
                    filtered_lsrl_x_values.append(x_value)
                    filtered_lsrl_y_values.append(y_value)

            matplotlib.pyplot.plot(filtered_lsrl_x_values, filtered_lsrl_y_values, "--", c=color)

        point_set.additional_charting_behavior = additional_charting_behavior
    
    charting.plot(plot_data, chart_title="Position-Specific PPG/Draft Order Trade Off Curves")

if __name__ == "__main__":
    main()

