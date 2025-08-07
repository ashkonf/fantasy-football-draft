"""Defines the main executable."""

import collections
import logging
from typing import Any, Callable, Dict, List, Tuple

import matplotlib
import numpy
import scipy.optimize

import charting
import infra
import settings
from infra import Player


logger = logging.getLogger(__name__)


def build_position_map(players: List[Player]) -> Dict[str, List[Player]]:
    position_map: Dict[str, List[Player]] = collections.defaultdict(list)
    for player in players:
        if player.position:
            position_map[player.position].append(player)
    return position_map


def rank_players_by_draft_value(
    draft_position: int,
    remaining_player_names: List[str],
    players: List[Player],
    fitted_function: Callable[[float], float],
) -> None:
    pairs: List[Tuple[Player, float]] = []
    for name in remaining_player_names:
        player: Player = infra.Player(name).find_match(players)
        value: float = calculate_draft_value(player, draft_position, fitted_function)
        pairs.append((player, value))
    pairs.sort(key=lambda pair: pair[1], reverse=True)

    print("Ranking:")
    print("========")
    for player, value in pairs:
        print(f"{player} (draft value = {value})")


def calculate_draft_value(
    player: Player, draft_position: int, fitted_function: Callable[[float], float]
) -> float:
    return player.get_average_projected_ppg() - fitted_function(
        draft_position + settings.LEAGUE_SIZE
    )


def fit_curve(
    point_set: charting.PointSet,
) -> Tuple[Callable[..., Any], Any]:
    def func(
        x_value: float,
        coefficient1: float,
        coefficient2: float,
        x_intercept: float,
        exponent: float,
        y_intercept: float,
    ) -> Any:
        return (
            coefficient1 / numpy.power(coefficient2 * (x_value + x_intercept), exponent)
            + y_intercept
        )

    x_values: List[float] = point_set.x_values()
    y_values: List[float] = point_set.y_values()

    # Removing QB points that mess up function
    filtered_x_values: List[float] = [
        x for i, x in enumerate(x_values) if point_set.name != "QB" or y_values[i] > 200
    ]
    filtered_y_values: List[float] = [
        y for i, y in enumerate(y_values) if point_set.name != "QB" or y > 200
    ]

    try:
        params, _ = scipy.optimize.curve_fit(
            func,
            filtered_x_values,
            filtered_y_values,
            maxfev=10000,
        )
    except RuntimeError as exc:
        raise RuntimeError(f"curve fitting failed for {point_set.name}: {exc}") from exc

    return func, params


def main() -> None:
    logging.basicConfig(level=logging.DEBUG if settings.VERBOSE else logging.INFO)

    players: List[Player] = infra.load_players()

    plot_data: charting.ScatterPlotData = charting.ScatterPlotData()
    for position in build_position_map(players).keys():
        point_set: charting.PointSet = charting.PointSet(position)
        plot_data.append(point_set)

    for player in players:
        for source in player.rank_map:
            if source in player.projected_ppg_map:
                point: charting.Point = charting.Point(
                    player.get_rank(source), player.get_projected_ppg(source)
                )
                plot_data.add_point(point, player.position)

    functions: Dict[str, Callable[..., Any]] = {}
    parameters: Dict[str, Any] = {}

    for point_set in plot_data:
        try:
            func, params = fit_curve(point_set)
        except RuntimeError as exc:
            logger.warning(
                "Skipping %s due to curve-fitting error: %s", point_set.name, exc
            )
            continue

        functions[point_set.name] = func
        parameters[point_set.name] = params

        def additional_charting_behavior(
            ps: charting.PointSet,
            x_min: float,
            x_max: float,
            x_range: float,
            x_step: float,
            y_min: float,
            y_max: float,
            y_range: float,
            color: str,
        ) -> None:
            if ps.name not in functions:
                return

            func: Callable[..., Any] = functions[ps.name]
            params: Any = parameters[ps.name]
            lsrl_x_values: numpy.ndarray = numpy.arange(
                x_min - x_range * 0.2, x_max + x_range * 0.2 + x_step / 2.0, x_step
            )
            lsrl_y_values: List[Any] = [
                func(x_value, *params) for x_value in lsrl_x_values
            ]

            logger.debug("%s", ps.name)
            logger.debug("%s", lsrl_x_values)
            logger.debug("%s", lsrl_y_values)
            logger.debug("")

            # Removing points outside first quadrant
            filtered_lsrl_x_values: List[float] = [
                x
                for i, x in enumerate(lsrl_x_values)
                if x >= 0 and lsrl_y_values[i] >= 0 and lsrl_y_values[i] < 1000.0
            ]
            filtered_lsrl_y_values: List[float] = [
                y
                for i, y in enumerate(lsrl_y_values)
                if lsrl_x_values[i] >= 0 and y >= 0 and y < 1000.0
            ]

            matplotlib.pyplot.plot(
                filtered_lsrl_x_values, filtered_lsrl_y_values, "--", c=color
            )

        point_set.additional_charting_behavior = additional_charting_behavior

    charting.plot(
        plot_data, chart_title="Position-Specific PPG/Draft Order Trade Off Curves"
    )


if __name__ == "__main__":
    main()
