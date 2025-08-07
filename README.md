# Fantasy Football Draft Analyzer

This project analyzes fantasy football draft data to help you make better decisions. It scrapes player ranking and projection data from ESPN and FantasyPros, then generates visualizations to show the trade-offs between player draft order and projected points per game (PPG).

## Features

- Scrapes data from multiple sources (ESPN, FantasyPros).
- Calculates player value based on draft position and projected PPG.
- Fits curves to the data to model player value.
- Generates scatter plots to visualize the data.

## Installation

1. **Prerequisites**
   - Python 3.13 or newer
   - [uv](https://github.com/astral-sh/uv) for dependency management

2. **Clone the repository**
   ```bash
   git clone https://github.com/your-user/fantasy-football-draft.git
   cd fantasy-football-draft
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e .
   ```

## Data Sources

The analyzer expects ranking and projection data from ESPN and FantasyPros.
Download the latest data from each site and place the files in the `Data`
directory using the following structure:

```
Data/
├── ESPN/
│   ├── Rankings.html
│   └── Projections/
├── FantasyPros/
│   ├── Rankings.html
│   └── Projections/
```

Sample HTML pages are included in the repository to show the expected layout.

## Configuration

You can configure the following settings in `src/settings.py`:

- `LEAGUE_SIZE`: number of teams in your league
- `VERBOSE`: set to `True` for additional debug output
- `TEAM_NAMES`: list of NFL team names used for data cleaning

## Usage

Run the analysis and generate the plots with:

```bash
uv run python src/main.py
```

This command:
1. Loads and parses the data from the `Data` directory
2. Fits curves to the data for each position
3. Displays a scatter plot showing the relationship between draft order and projected PPG

## Development

The repository includes tooling for linting, type checking, and tests:

```bash
uv run ruff check .
uv run pyright
uv run pytest
```
