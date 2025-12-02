# ADS-B Exchange Integration Guide

## Overview

The `fetch_flights.py` module enables real-time flight data acquisition from ADS-B Exchange, allowing you to visualize current air traffic instead of using static historical data.

## What is ADS-B Exchange?

[ADS-B Exchange](https://www.adsbexchange.com/) is a community-driven, open-source flight tracking platform that provides unfiltered, real-time flight data from volunteer feeders worldwide. Unlike commercial services, it:

- ✅ **Open Source** - Free access to global flight data
- ✅ **Unfiltered** - Shows all aircraft (including military, private jets blocked from other services)
- ✅ **Community-Driven** - Powered by aviation enthusiasts
- ✅ **Real-Time** - Live tracking of thousands of aircraft

## Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Fetch Current Flights

```bash
# Fetch all current flights worldwide
python fetch_flights.py -o realtime.csv

# Visualize immediately
python plot_mpl.py -i realtime.csv
```

### 3. Filter by Geographic Area

```bash
# Flights over California
python fetch_flights.py -o california.csv --bounds 32.5 -124.5 42.0 -114.0

# Flights within 100km of New York City
python fetch_flights.py -o nyc.csv --center 40.7128 -74.0060 --radius 100

# High-traffic routes (minimum 5 flights)
python fetch_flights.py -o busy.csv --min-flights 5
```

## Usage Examples

### Example 1: Current Air Traffic Snapshot

Create a visualization of all current air traffic:

```bash
# Fetch current flights
python fetch_flights.py -o current_snapshot.csv -v

# Create map with high resolution
python plot_mpl.py -i current_snapshot.csv -o current_traffic.png --dpi 300
```

### Example 2: Regional Analysis

Analyze flight patterns over a specific region:

```bash
# Europe
python fetch_flights.py -o europe.csv --bounds 35 -10 70 40

# North America
python fetch_flights.py -o northamerica.csv --bounds 25 -125 50 -65

# Asia-Pacific
python fetch_flights.py -o asiapac.csv --bounds -10 90 50 180
```

### Example 3: Airport Traffic

Monitor flights near major airports:

```bash
# San Francisco Bay Area (SFO, OAK, SJC)
python fetch_flights.py -o sfo.csv --center 37.6213 -122.3790 --radius 50

# London area (LHR, LGW, STN, LTN)
python fetch_flights.py -o london.csv --center 51.5074 -0.1278 --radius 100

# Tokyo area (NRT, HND)
python fetch_flights.py -o tokyo.csv --center 35.6762 139.6503 --radius 75
```

### Example 4: Time-Series Analysis

Create snapshots over time to analyze traffic patterns:

```bash
#!/bin/bash
# Capture snapshots every hour for 24 hours

for hour in {0..23}; do
    timestamp=$(date +%Y%m%d_%H%M)
    python fetch_flights.py -o "snapshots/flights_${timestamp}.csv"
    echo "Captured snapshot at ${timestamp}"
    sleep 3600  # Wait 1 hour
done
```

## Command-Line Options

### Basic Options

```bash
-o, --output PATH        Output CSV file path
-v, --verbose            Enable verbose logging
--api-key KEY           ADS-B Exchange RapidAPI key (optional)
```

### Geographic Filtering

```bash
--bounds MIN_LAT MIN_LON MAX_LAT MAX_LON
                        Filter by bounding box
                        Example: --bounds 37.0 -123.0 38.5 -121.5

--center LAT LON        Center point for radius filter
                        Example: --center 40.7128 -74.0060

--radius KM             Radius in kilometers (requires --center)
                        Example: --radius 100
```

### Route Aggregation

```bash
--min-flights N         Minimum flights per route (default: 1)
                        Higher values show only busy routes

--grid-resolution DEG   Grid cell size in degrees (default: 1.0)
                        Smaller values = finer granularity
```

## Output Format

The output CSV uses the same format as the original `data.csv`:

```csv
DepLat;DepLon;ArrLat;ArrLon;NbFlights;CO2Intensity
37.7749;-122.4194;40.7128;-74.0060;5;50.0
```

**Note:** Route aggregation is heuristic-based. The tool:
1. Observes aircraft positions and headings
2. Projects approximate departure/arrival points
3. Aggregates flights along similar routes
4. Filters by minimum flight count threshold

## Integration with Existing Workflow

### Complete Workflow

```bash
# 1. Fetch real-time data
python fetch_flights.py -o realtime.csv --min-flights 3 -v

# 2. Visualize with Matplotlib/Cartopy
python plot_mpl.py -i realtime.csv -o realtime_map.png --dpi 300

# 3. Alternative: Use GCMapper style
python plot_gcmap.py -i realtime.csv -o realtime_gcmap.png

# 4. Explore interactively in Jupyter
jupyter notebook notebooks/flight_analysis_tutorial.ipynb
```

### Using Configuration Files

```bash
# Create custom config for real-time visualization
cat > realtime_config.yaml << EOF
output:
  directory: './realtime_maps'
  filename: 'traffic_{timestamp}.png'
  format: 'png'
  dpi: 300

visualization:
  colormap: 'hot'
  alpha: 0.7
  line_width: 1.5
  
colors:
  background: '#001a33'
  coastlines: '#ffffff'
  routes: '#ff6600'
EOF

# Fetch and visualize
python fetch_flights.py -o realtime.csv
python plot_mpl.py -i realtime.csv -c realtime_config.yaml
```

## Advanced Usage

### Programmatic Access

```python
from fetch_flights import ADSBExchangeFetcher, RouteAggregator, save_to_csv
from pathlib import Path

# Fetch flights
fetcher = ADSBExchangeFetcher()
aircraft = fetcher.fetch_current_flights()

# Filter for specific region (San Francisco Bay Area)
flights = list(fetcher.parse_flights(
    aircraft,
    bounds=(37.0, -123.0, 38.5, -121.5)
))

print(f"Found {len(flights)} flights in SF Bay Area")

# Aggregate into routes
aggregator = RouteAggregator(min_flights=2)
for flight in flights:
    aggregator.add_flight(
        flight['lat'],
        flight['lon'],
        flight.get('track'),
        flight.get('speed')
    )

routes = aggregator.get_routes()

# Save
save_to_csv(routes, Path('sf_routes.csv'))

# Now visualize
import subprocess
subprocess.run(['python', 'plot_mpl.py', '-i', 'sf_routes.csv'])
```

### Custom Filtering

```python
from fetch_flights import ADSBExchangeFetcher

fetcher = ADSBExchangeFetcher()
aircraft = fetcher.fetch_current_flights()

# Filter for specific aircraft types
boeing_777_flights = [
    flight for flight in fetcher.parse_flights(aircraft)
    if flight.get('type') and 'B77' in flight['type']
]

print(f"Found {len(boeing_777_flights)} Boeing 777 flights")

# Filter by altitude (cruise altitude)
cruise_flights = [
    flight for flight in fetcher.parse_flights(aircraft)
    if flight.get('altitude') and flight['altitude'] > 10000  # > 10km
]

print(f"Found {len(cruise_flights)} flights at cruise altitude")
```

## API Rate Limits

### Public API (No Key)
- **Rate Limit**: ~100 requests/hour
- **Coverage**: Global
- **Delay**: 5-10 seconds
- **Best For**: Personal projects, occasional queries

### RapidAPI (With Key)
- **Rate Limit**: Higher limits based on plan
- **Coverage**: Global
- **Delay**: Near real-time
- **Best For**: Frequent polling, production use

To use RapidAPI:
1. Sign up at [RapidAPI ADS-B Exchange](https://rapidapi.com/adsbx/api/adsbexchange-com1/)
2. Get your API key
3. Use with `--api-key YOUR_KEY`

## Comparison with Static Data

### Static Historical Data (`data.csv`)
- ✅ **Stable** - Consistent results
- ✅ **Complete** - Aggregated over time
- ✅ **Fast** - No API calls needed
- ❌ **Outdated** - Historical patterns only

### Real-Time Data (`fetch_flights.py`)
- ✅ **Current** - Live air traffic
- ✅ **Dynamic** - See patterns change
- ✅ **Unfiltered** - All aircraft
- ❌ **Variable** - Results change constantly
- ❌ **Sparse** - Single snapshot may miss routes

### Best Practice
- **Use static data** for consistent comparisons and demos
- **Use real-time data** for monitoring current traffic and live analysis
- **Combine both** for time-series analysis

## Troubleshooting

### No flights returned
```bash
# Check if API is accessible
curl https://globe.adsbexchange.com/data/aircraft.json

# Use verbose mode to debug
python fetch_flights.py -o test.csv -v
```

### Rate limit errors
- Wait a few minutes between requests
- Consider getting a RapidAPI key for higher limits
- Use geographic filters to reduce data size

### Too few routes
- Reduce `--min-flights` threshold
- Increase `--grid-resolution` for coarser grouping
- Expand geographic area with wider bounds/radius

## Future Enhancements

Potential improvements to the integration:

1. **Historical Polling**
   - Poll API every N minutes
   - Build up historical database
   - Aggregate true routes over time

2. **Flight Path Tracking**
   - Track individual aircraft over time
   - Reconstruct actual flight paths
   - Calculate true departure/arrival airports

3. **Airport Detection**
   - Identify major airports automatically
   - Filter by airport proximity
   - Generate airport-to-airport routes

4. **Enhanced Filtering**
   - Aircraft type filtering
   - Airline filtering
   - Altitude-based filtering
   - Speed-based filtering

5. **Data Enrichment**
   - Add airline information
   - Add aircraft age/model details
   - Calculate actual CO2 emissions
   - Add weather overlay

6. **Live Monitoring**
   - Real-time map updates
   - Web-based dashboard
   - Animated time-lapse
   - Alert system for specific routes/aircraft

## See Also

- Main README: `README.md`
- Configuration Guide: `config.yaml`
- Tutorial Notebook: `notebooks/flight_analysis_tutorial.ipynb`
- Advanced Examples: `example_advanced_usage.py`
- Contributing: `CONTRIBUTING.md`

## Credits

- **ADS-B Exchange**: Community-driven flight tracking platform
- **Your flightdata project**: Reference implementation at `~/aviation/flightdata`
