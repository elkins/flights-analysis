# ✈️ Flight Data Visualization

A modern Python project for visualizing global flight routes using Pandas, Matplotlib, and Cartopy.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

## 📊 Features

- **Two visualization methods:**
  - 🗺️ **GCMapper**: Simplified great circle route mapping
  - 🎨 **Matplotlib/Cartopy**: High-quality, customizable maps with modern cartographic projections
  
- **Real-time flight data** from ADS-B Exchange and OpenSky Network
- **Track specific flights** by callsign (e.g., UA262) with live updates
- **Customizable color schemes** for screen display or print output
- **Flight frequency visualization** with gradient coloring
- **Great circle route calculations** for accurate flight paths
- **Geographic filtering** by bounding box or radius

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hugoch/flights-analysis.git
   cd flights-analysis
   ```

2. **Install dependencies:**

   Using pip:
   ```bash
   pip install -r requirements.txt
   ```

   Or using the project directly:
   ```bash
   pip install -e .
   ```

   For development with additional tools:
   ```bash
   pip install -e ".[dev]"
   ```

   For Jupyter notebook support:
   ```bash
   pip install -e ".[notebook]"
   ```

3. **Set up pre-commit hooks (optional, for developers):**
   ```bash
   pre-commit install
   ```

### Usage

#### Fetch Real-Time Flight Data (NEW!):
```bash
# Fetch current flights worldwide
python fetch_flights.py -o realtime.csv

# Filter by region (e.g., North America)
python fetch_flights.py -o northamerica.csv --bounds 25 -125 50 -65

# Filter by radius (e.g., 100km around NYC)
python fetch_flights.py -o nyc.csv --center 40.7128 -74.0060 --radius 100
```

#### Track Specific Flights (NEW! 🆕):
```bash
# Track United Airlines flight 262
python track_flight_opensky.py UA262 -v

# Track with live updates every 30 seconds
python track_flight_opensky.py UA262 --follow --interval 30

# Save track and plot the path
python track_flight_opensky.py UA262 --follow --updates 20 -o ua262.csv --plot

# Or use make
make track-flight FLIGHT=UA262
```

#### Visualize Flight Tracks (NEW! 🆕):
```bash
# Visualize tracked flight data
python visualize_track_simple.py example_ual2212_track.csv -o analysis.png

# Or use make
make visualize FILE=example_ual2212_track.csv
```

#### Generate map with GCMapper:
```bash
python plot_gcmap.py
```

With CLI options:
```bash
python plot_gcmap.py -i data.csv -o output.png --width 4000 --height 2000 -v
```

#### Generate map with Matplotlib/Cartopy:
```bash
python plot_mpl.py
```

With CLI options:
```bash
python plot_mpl.py -i data.csv -o output.png --color-mode print --dpi 300 -v
```

#### Complete Real-Time Workflow:
```bash
# 1. Fetch current flights
python fetch_flights.py -o realtime.csv --min-flights 2 -v

# 2. Visualize
python plot_mpl.py -i realtime.csv -o current_traffic.png --dpi 300
```

#### Using configuration file:
Both scripts support YAML configuration via `config.yaml`:
```bash
python plot_mpl.py -c custom_config.yaml
```

#### Interactive analysis with Jupyter:
```bash
jupyter notebook notebooks/flight_analysis_tutorial.ipynb
```

#### Advanced programmatic usage:
See `example_advanced_usage.py` for examples of:
- Programmatic configuration
- Batch processing multiple maps
- Custom color schemes
- Library usage (importing functions)

```bash
python example_advanced_usage.py
```

### CLI Options

Both scripts support these common options:

- `-i, --input`: Input CSV file path
- `-o, --output`: Output PNG file path
- `-c, --config`: Custom configuration file
- `-v, --verbose`: Enable verbose logging

**plot_gcmap.py specific:**
- `--width`: Map width in pixels
- `--height`: Map height in pixels

**plot_mpl.py specific:**
- `--color-mode`: Color scheme (`screen` or `print`)
- `--absolute`: Use absolute color scaling
- `--dpi`: Output image DPI
- `--width`: Figure width in inches
- `--height`: Figure height in inches

## 📁 Project Structure

```
flights-analysis/
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions CI/CD pipeline
├── notebooks/
│   └── flight_analysis_tutorial.ipynb # Interactive tutorial
├── data.csv                            # Static flight route data
├── fetch_flights.py                    # Fetch real-time data from ADS-B Exchange
├── track_flight_opensky.py             # Track specific flights (OpenSky Network)
├── track_flight.py                     # Track specific flights (ADS-B Exchange)
├── example_ual2212_track.csv           # Example: Tracked flight data
├── plot_gcmap.py                       # GCMapper visualization script
├── plot_mpl.py                         # Matplotlib/Cartopy visualization script
├── config.yaml                         # Configuration file
├── pyproject.toml                      # Modern Python project configuration
├── requirements.txt                    # Python dependencies
├── .pre-commit-config.yaml            # Pre-commit hooks configuration
├── .gitignore                          # Git ignore rules
├── ADSBEXCHANGE_INTEGRATION.md        # Real-time data integration guide
├── FLIGHT_TRACKING_EXAMPLES.md        # Flight tracking examples & analysis
├── TRACKING_SPECIFIC_FLIGHTS.md       # Specific flight tracking guide
├── README.md                           # This file
└── LICENSE.md                          # MIT License
```

## 📊 Data Format

### Static Data (`data.csv`)
The CSV file should contain flight route data with the following columns:
- `DepLat`, `DepLon`: Departure coordinates
- `ArrLat`, `ArrLon`: Arrival coordinates
- `NbFlights`: Number of flights on this route
- `CO2Intensity`: CO2 emissions intensity

### Real-Time Data (via `fetch_flights.py`)
Fetches current flight data from ADS-B Exchange and converts it to the same CSV format. See `ADSBEXCHANGE_INTEGRATION.md` for complete documentation.

### Flight Tracking Data (via `track_flight_opensky.py`)
Tracks specific flights by callsign with position updates over time. Outputs detailed CSV with timestamp, position, altitude, speed, and heading. See `FLIGHT_TRACKING_EXAMPLES.md` for examples and `example_ual2212_track.csv` for sample data.

## 🎨 Customization

### Configuration File

The `config.yaml` file allows you to customize all aspects of the visualizations without editing code:

```yaml
# Output settings
output:
  dpi: 150
  format: "png"

# Visualization settings
visualization:
  color_mode: "screen"  # or "print"
  figure_size:
    width: 27
    height: 20
  line_width: 0.5
  alpha: 0.8

# Color schemes
color_schemes:
  screen:
    background: [0.0, 0.0, 0.0, 1.0]
    coastline: [0.8, 0.0, 0.6, 0.7]
  print:
    background: [1.0, 1.0, 1.0, 1.0]
    coastline: [0.04, 0.04, 0.04, 0.8]
```

### Color Modes

Both scripts support two color modes:

- **`screen`**: Optimized for digital displays (dark background)
- **`print`**: Printer-friendly colors (light background)

Use CLI flag: `--color-mode screen` or configure in `config.yaml`

### Map Configuration

Customize in `config.yaml` or via CLI:
- Figure size and DPI
- Line width and transparency
- Color gradients
- Map projection settings
- Power normalization gamma

## 🔄 Migrating from Old Version

This modernized version includes several improvements:

### What's Changed
- ✅ **Cartopy** replaces deprecated Basemap
- ✅ **Type hints** for better code documentation
- ✅ **pathlib** for cross-platform file handling
- ✅ **f-strings** for modern string formatting
- ✅ **pyproject.toml** for modern Python packaging
- ✅ Updated to **Python 3.10+** features
- ✅ **CLI support** with argparse
- ✅ **YAML configuration** files
- ✅ **GitHub Actions CI/CD** pipeline
- ✅ **Pre-commit hooks** for code quality
- ✅ **Jupyter notebook** tutorial
- ✅ **Logging** with configurable levels

### Migration Notes
If you're updating from the old version:
1. Remove old `environment.yml`
2. Uninstall basemap: `pip uninstall basemap`
3. Install new dependencies: `pip install -r requirements.txt`
4. Note: Cartopy handles map projections differently but provides better results

### New Features

#### Real-Time Flight Data (NEW! 🆕)
Fetch and visualize current air traffic from ADS-B Exchange:
```bash
# Fetch current flights
python fetch_flights.py -o realtime.csv --min-flights 2

# Visualize immediately
python plot_mpl.py -i realtime.csv -o live_traffic.png
```

See `ADSBEXCHANGE_INTEGRATION.md` for complete documentation on:
- Geographic filtering (bounding box, radius)
- Route aggregation strategies
- Time-series analysis
- Integration with existing workflow

#### CLI Interface
Both scripts now accept command-line arguments for flexible usage:
```bash
python plot_mpl.py -i custom_data.csv -o output.png --dpi 300 -v
```

#### Configuration Files
Customize visualizations without editing code:
```bash
python plot_mpl.py -c my_config.yaml
```

#### Jupyter Notebook
Interactive data exploration and visualization:
```bash
jupyter notebook notebooks/flight_analysis_tutorial.ipynb
```

#### CI/CD Pipeline
Automatic testing on every push:
- Code quality checks with Ruff and Black
- Type checking with MyPy
- Multi-platform testing (Linux, macOS, Windows)
- Python 3.10, 3.11, 3.12 compatibility

#### Pre-commit Hooks
Automatic code formatting and linting before commits:
```bash
pre-commit install
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- Original blog post: [Flight data visualisation with Pandas and Matplotlib](https://blog.hugo-larcher.com/flight-data-visualisation-with-pandas-and-matplotlib-ebbd13038647)
- Data visualization techniques inspired by the Python data science community
- Cartopy library for modern cartographic projections

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📬 Contact

For questions or suggestions, please open an issue on GitHub.

---

Made with ❤️ and Python
