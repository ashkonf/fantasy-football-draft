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

def main():
    players = infra.load_players()

    plot_data = charting.ScatterPlotData()
    for position in build_position_map(players).keys():
        def additional_charting_behavior(point_set, x_min, x_max, x_range, x_step, y_min, y_max, y_range, color):
            def func(x_value, power, coefficient):
                return coefficient * (math.e ** ((x_value) * power))
            
            power, coefficient = scipy.optimize.curve_fit(func, point_set.x_values(), point_set.y_values(), maxfev=10000)[0]
            lsrl_x_values = numpy.arange(x_min - x_range * 0.2, x_max + x_range * 0.2 + x_step / 2.0, x_step)
            lsrl_y_values = [func(x_value, power, coefficient) for x_value in lsrl_x_values]
            matplotlib.pyplot.plot(lsrl_x_values, lsrl_y_values, "--", c=color)
    
        point_set = charting.PointSet(position, additional_charting_behavior=additional_charting_behavior)
        plot_data.append(point_set)

    for player in players:
        for source in player.rank_map:
            if source in player.projected_ppg_map:
                point = charting.Point(player.get_rank(source), player.get_projected_ppg(source))#, player.name)
                plot_data.add_point(point, player.position)
    
    charting.plot(plot_data, chart_title="Position-Specific PPG/Draft Order Trade Off Curves")

if __name__ == "__main__":
    main()

