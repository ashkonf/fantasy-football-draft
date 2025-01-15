import collections
import math

import matplotlib
import numpy
import scipy.optimize

import charting
import infra
import settings


def build_position_map(players):
    position_map = collections.defaultdict(list)
    for player in players:
        if player.position:
            position_map[player.position].append(player)
    return position_map


def rank_players_by_draft_value(draft_position, remaining_player_names, players, fitted_function):
    pairs = []
    for name in remaining_player_names:
        player = infra.Player(name).find_match(players)
        value = calculate_draft_value(player, draft_position, fitted_function)
        pairs.append((player, value))
    pairs.sort(key=lambda pair: pair[1], reverse=True)

    print("Ranking:")
    print("========")
    for player, value in pairs:
        print(f"{player} (draft value = {value})")


def calculate_draft_value(player, draft_position, fitted_function):
    return player.get_average_projected_ppg() - fitted_function(draft_position + settings.LEAGUE_SIZE)


def fit_curve(point_set):
    def func(x_value, coefficient1, coefficient2, x_intercept, exponent, y_intercept):
        return coefficient1 / numpy.power(coefficient2 * (x_value + x_intercept), exponent) + y_intercept

    x_values = point_set.x_values()
    y_values = point_set.y_values()

    # Removing QB points that mess up function
    filtered_x_values = [
        x for i, x in enumerate(x_values)
        if point_set.name != "QB" or y_values[i] > 200
    ]
    filtered_y_values = [
        y for i, y in enumerate(y_values)
        if point_set.name != "QB" or y > 200
    ]

    return func, scipy.optimize.curve_fit(func, filtered_x_values, filtered_y_values, maxfev=1000000)[0]


def main():
    players = infra.load_players()

    plot_data = charting.ScatterPlotData()
    for position in build_position_map(players).keys():
        point_set = charting.PointSet(position)
        plot_data.append(point_set)

    for player in players:
        for source in player.rank_map:
            if source in player.projected_ppg_map:
                point = charting.Point(player.get_rank(source), player.get_projected_ppg(source))
                plot_data.add_point(point, player.position)

    functions = {}
    parameters = {}

    for point_set in plot_data:
        functions[point_set.name], parameters[point_set.name] = fit_curve(point_set)

        def additional_charting_behavior(ps, x_min, x_max, x_range, x_step, y_min, y_max, y_range, color):
            func = functions[ps.name]
            params = parameters[ps.name]
            lsrl_x_values = numpy.arange(x_min - x_range * 0.2, x_max + x_range * 0.2 + x_step / 2.0, x_step)
            lsrl_y_values = [func(x_value, *params) for x_value in lsrl_x_values]

            print(ps.name)
            print(lsrl_x_values)
            print(lsrl_y_values)
            print()

            # Removing points outside first quadrant
            filtered_lsrl_x_values = [x for i, x in enumerate(lsrl_x_values) if x >= 0 and lsrl_y_values[i] >= 0 and lsrl_y_values[i] < 1000.0]
            filtered_lsrl_y_values = [y for i, y in enumerate(lsrl_y_values) if lsrl_x_values[i] >= 0 and y >= 0 and y < 1000.0]

            matplotlib.pyplot.plot(filtered_lsrl_x_values, filtered_lsrl_y_values, "--", c=color)

        point_set.additional_charting_behavior = additional_charting_behavior
    
    charting.plot(plot_data, chart_title="Position-Specific PPG/Draft Order Trade Off Curves")


if __name__ == "__main__":
    main()
