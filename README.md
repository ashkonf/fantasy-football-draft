# Fantasy Football Draft

A Python project for analyzing fantasy football projections and optimizing your draft strategy.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Data Sources](#data-sources)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project aggregates player projections from multiple sources and provides tools to compare them, helping you draft with confidence.

Key features include:
- Scraping and parsing data from multiple sources (e.g., ESPN, FantasyPros).
- Calculating player value based on draft position and projected Points Per Game (PPG).
- Fitting curves to the data to model player value by position.
- Generating scatter plots to visualize the data and identify trends.

## Installation

1.  **Prerequisites**
    -   Python 3.13 or newer.
    -   [uv](https://github.com/astral-sh/uv) for dependency management.

2.  **Clone the repository**
    ```bash
    git clone https://github.com/ashkonfarhangi/fantasy-football-draft.git
    cd fantasy-football-draft
    ```

3.  **Install dependencies**
    Create a virtual environment and install the required packages using `uv`:
    ```bash
    uv venv
    uv sync
    ```
    This will install all dependencies listed in `pyproject.toml`.

## Data Sources

The analyzer expects ranking and projection data from sources like ESPN and FantasyPros.

1.  Download the latest data from each site. These are typically HTML files.
2.  Place the files in the `data/` directory using the following structure:

    ```
    data/
    ├── ESPN/
    │   ├── Rankings.htm
    │   └── Projections/
    │       ├── 1.htm
    │       └── ...
    ├── FantasyPros/
    │   ├── Rankings.htm
    │   └── Projections/
    │       ├── 2018 QB Projections - ...
    │       └── ...
    ```

Sample HTML files are included in the repository to show the expected format.

## Configuration

You can configure the following settings in `src/settings.py`:

-   `LEAGUE_SIZE`: The number of teams in your league.
-   `VERBOSE`: Set to `True` for additional debug output.
-   `TEAM_NAMES`: A list of NFL team names used for data cleaning.

## Usage

After installation and configuration, run the main script to generate draft insights:

```bash
uv run python src/main.py
```

This command will:
1.  Load and parse the data from the `data/` directory.
2.  Fit curves to the data for each position.
3.  Display a scatter plot showing the relationship between draft order and projected PPG.

## Development

The repository includes tooling for linting, type checking, and testing. You can run these checks using `uv`:

-   **Linting:**
    ```bash
    uv run ruff check .
    ```
-   **Type Checking:**
    ```bash
    uv run pyright
    ```
-   **Testing:**
    ```bash
    uv run pytest
    ```

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests with improvements or new features.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
