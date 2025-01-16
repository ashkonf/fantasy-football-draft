# Fantasy Football Draft Analyzer

This project analyzes fantasy football draft data to help you make better decisions. It scrapes player ranking and projection data from ESPN and FantasyPros, then generates visualizations to show the trade-offs between player draft order and projected points per game (PPG).

## Features

- Scrapes data from multiple sources (ESPN, FantasyPros).
- Calculates player value based on draft position and projected PPG.
- Fits curves to the data to model player value.
- Generates scatter plots to visualize the data.

## Setup

1. **Install dependencies:**
   The dependencies for this project are listed in `pyproject.toml`. You can install them using `uv`:
   ```bash
   uv pip install -e .
   ```

2. **Data:**
   The project expects to find data in the `Data` directory, with subdirectories for each source (e.g., `Data/ESPN`, `Data/FantasyPros`). Each source directory should contain:
    - `Rankings.html`: A file with the overall player rankings.
    - `Projections/`: A directory with files containing player projections.

    Example HTML files are included in the `Data` directory.

## Configuration

You can configure the following settings in `src/settings.py`:

- `LEAGUE_SIZE`: The number of teams in your league.
- `VERBOSE`: Set to `True` to print verbose output during data processing.
- `TEAM_NAMES`: A list of NFL team names used for data cleaning.

## Usage

To run the analysis and generate the plots, execute the following command:

```bash
uv run python src/main.py
```

This will:
1. Load and parse the data from the `Data` directory.
2. Fit curves to the data for each position.
3. Generate and display a scatter plot with the results.

## Linting and Type Checking

This project uses `ruff` for linting and `pyright` for type checking.

To run the linter, use the following command:

```bash
uv run ruff check .
```

To run the type checker, use the following command:

```bash
uv run pyright
```

