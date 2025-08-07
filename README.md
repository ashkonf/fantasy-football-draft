# Fantasy Football Draft

A Python project for analyzing fantasy football projections and optimizing your draft strategy.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project aggregates player projections from multiple sources and provides tools to compare them so you can draft with confidence.

## Installation

1. Ensure [Python](https://www.python.org/) 3.13 or later is installed.
2. Install the project and its dependencies:

   ```bash
   pip install -e .
   ```

   Alternatively, with [uv](https://github.com/astral-sh/uv):

   ```bash
   uv sync
   ```

## Usage

After installation, run the main script to generate draft insights:

```bash
python src/main.py
```

## Data Sources

Raw projection data is stored under the `Data/` directory. Subdirectories such as `FantasyPros`, `CBS`, and `ESPN` contain sample exports from various providers.

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests with improvements or new features.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
