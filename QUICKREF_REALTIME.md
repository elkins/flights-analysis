# Real-Time Flight Data - Quick Reference

## 🚀 Quick Commands

### Fetch Current Flights
```bash
# All flights (worldwide)
python fetch_flights.py -o realtime.csv

# With make
make fetch-realtime
```

### Track Specific Flights (NEW!)
```bash
# Track a specific flight (e.g., United 2212)
python track_flight_opensky.py UAL2212 -v

# Track with continuous updates
python track_flight_opensky.py UAL2212 --follow --interval 30

# Save track and plot
python track_flight_opensky.py UAL2212 --follow --updates 20 -o track.csv --plot

# With make
make track-flight FLIGHT=UAL2212

# See example_ual2212_track.csv for sample output
```

### Visualize Immediately
```bash
# Fetch and visualize in one go
python fetch_flights.py -o realtime.csv && python plot_mpl.py -i realtime.csv -o map.png
```

### Complete Demo
```bash
# Run interactive demo (recommended first time!)
python realtime_example.py
# or
make realtime-demo
```

## 🌍 Geographic Filtering

### By Bounding Box
```bash
# North America
python fetch_flights.py -o na.csv --bounds 25 -125 50 -65

# Europe
python fetch_flights.py -o eu.csv --bounds 35 -10 70 40

# Asia-Pacific
python fetch_flights.py -o ap.csv --bounds -10 90 50 180

# Custom region
python fetch_flights.py -o custom.csv --bounds MIN_LAT MIN_LON MAX_LAT MAX_LON
```

### By Radius (Around a Point)
```bash
# San Francisco Bay Area (100km radius)
python fetch_flights.py -o sf.csv --center 37.7749 -122.4194 --radius 100

# New York City (150km radius)
python fetch_flights.py -o nyc.csv --center 40.7128 -74.0060 --radius 150

# London (100km radius)
python fetch_flights.py -o london.csv --center 51.5074 -0.1278 --radius 100

# Custom location
python fetch_flights.py -o custom.csv --center LAT LON --radius KM
```

## 🎛️ Route Aggregation

### Filter by Traffic Volume
```bash
# Only busy routes (5+ flights)
python fetch_flights.py -o busy.csv --min-flights 5

# Medium traffic (3+ flights)
python fetch_flights.py -o medium.csv --min-flights 3

# All routes (1+ flight, default)
python fetch_flights.py -o all.csv --min-flights 1
```

### Adjust Grid Resolution
```bash
# Fine-grained (0.5° cells)
python fetch_flights.py -o fine.csv --grid-resolution 0.5

# Coarse (2.0° cells, more aggregation)
python fetch_flights.py -o coarse.csv --grid-resolution 2.0
```

## 🎨 Visualization Options

### Basic Visualization
```bash
python plot_mpl.py -i realtime.csv -o output.png
```

### High Quality (Print)
```bash
python plot_mpl.py -i realtime.csv -o output.png --dpi 300 --color-mode print
```

### Custom Size
```bash
python plot_mpl.py -i realtime.csv -o output.png --width 40 --height 30 --dpi 200
```

### With Configuration
```bash
python plot_mpl.py -i realtime.csv -c config.yaml -o output.png
```

## 🔄 Common Workflows

### 1. Quick Snapshot
```bash
make fetch-realtime
python plot_mpl.py -i realtime.csv -o snapshot.png --dpi 200
```

### 2. Regional Analysis
```bash
# Define region
python fetch_flights.py -o region.csv --bounds 37 -123 38 -121

# Visualize with custom settings
python plot_mpl.py -i region.csv -o region_map.png --dpi 300 --width 20
```

### 3. Time Series (Manual)
```bash
# Capture multiple snapshots
for i in {1..10}; do
    timestamp=$(date +%Y%m%d_%H%M%S)
    python fetch_flights.py -o "snapshots/snap_${timestamp}.csv"
    echo "Snapshot ${i} captured"
    sleep 600  # Wait 10 minutes
done
```

### 4. Compare Real-Time vs Historical
```bash
# Fetch current
python fetch_flights.py -o realtime.csv

# Generate both maps
python plot_mpl.py -i realtime.csv -o rt_map.png
python plot_mpl.py -i data.csv -o historical_map.png

# Compare visually
open rt_map.png historical_map.png  # macOS
```

## 🐛 Troubleshooting

### No flights returned?
```bash
# Check API connectivity
curl https://globe.adsbexchange.com/data/aircraft.json

# Use verbose mode
python fetch_flights.py -o test.csv -v
```

### Too few routes?
```bash
# Reduce minimum flights threshold
python fetch_flights.py -o more.csv --min-flights 1

# Increase grid resolution (more aggregation)
python fetch_flights.py -o more.csv --grid-resolution 2.0
```

### Rate limit errors?
- Wait 5-10 minutes
- Use geographic filters to reduce data
- Consider getting RapidAPI key

### API key usage (optional, for higher limits)
```bash
python fetch_flights.py -o data.csv --api-key YOUR_RAPIDAPI_KEY
```

## 📊 Output Format

CSV with semicolon delimiter:
```csv
DepLat;DepLon;ArrLat;ArrLon;NbFlights;CO2Intensity
37.50000;-122.40000;40.70000;-74.00000;5;50.0
```

Compatible with all existing visualization scripts!

## 💡 Tips

### Best Practices
- **Use geographic filters** to reduce API load
- **Set min-flights > 1** for cleaner visualizations
- **Add -v flag** when debugging
- **Cache results** for repeated analysis
- **Respect rate limits** (~100 req/hour)

### Performance
- Smaller regions = faster processing
- Higher min-flights = fewer routes to plot
- Coarser grid = more aggregation

### Quality
- Higher DPI = larger file, better quality
- Print mode = better for printing
- Screen mode = better for digital display

## 📚 Documentation

- **Full Integration Guide**: `ADSBEXCHANGE_INTEGRATION.md`
- **Enhancement Summary**: `ADSBEXCHANGE_ENHANCEMENT.md`
- **Main README**: `README.md`
- **Configuration Guide**: `config.yaml`

## 🔗 Quick Links

### Major City Coordinates
```bash
# North America
SFO:  37.7749  -122.4194
NYC:  40.7128   -74.0060
LAX:  34.0522  -118.2437
ORD:  41.9742   -87.9073

# Europe
LHR:  51.5074    -0.1278
CDG:  48.8566     2.3522
FRA:  50.0379     8.5622
AMS:  52.3676     4.9041

# Asia
NRT:  35.7720   139.7590
PEK:  40.0799   116.6031
SIN:   1.3521   103.8198
DXB:  25.2532    55.3657
```

### Common Bounding Boxes
```bash
# US West Coast
--bounds 32 -125 49 -117

# US East Coast
--bounds 25 -80 45 -67

# UK & Ireland
--bounds 50 -10 60 2

# Western Europe
--bounds 40 -5 55 15
```

## ⚡ One-Liners

```bash
# Quick global snapshot
python fetch_flights.py -o snap.csv && python plot_mpl.py -i snap.csv

# SF Bay Area high-res
python fetch_flights.py -o sf.csv --center 37.7749 -122.4194 --radius 100 && python plot_mpl.py -i sf.csv -o sf.png --dpi 300

# Busy routes only
python fetch_flights.py -o busy.csv --min-flights 5 && python plot_mpl.py -i busy.csv

# Print-quality map
python fetch_flights.py -o data.csv && python plot_mpl.py -i data.csv -o print.png --dpi 600 --color-mode print
```

---

**Need more help?** Run `python fetch_flights.py --help` or read `ADSBEXCHANGE_INTEGRATION.md`
