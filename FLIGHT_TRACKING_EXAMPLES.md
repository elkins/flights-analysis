# Flight Tracking Examples

This document provides real-world examples of tracking specific flights using the OpenSky Network.

## Example: UAL2212 Departure from Newark (KEWR)

### Flight Information
- **Callsign**: UAL2212
- **Aircraft**: ICAO hex A2B8C5
- **Date**: December 1, 2025
- **Departure**: Newark Liberty International Airport (KEWR)
- **Phase**: Initial climb to cruise altitude

### Tracking Session
The flight was tracked for approximately 5 minutes during its initial climb phase, capturing 10 position updates at 30-second intervals.

### Data File
See `example_ual2212_track.csv` for the complete track data.

### Key Observations

**Altitude Profile:**
- Started at 8,775 ft (2,675 m)
- Climbed to 19,000 ft (5,791 m)
- Total climb: ~10,225 ft in 5 minutes
- Average climb rate: ~2,000 ft/min

**Speed Profile:**
- Initial: 257 knots
- Maximum: 340 knots
- Cruise: 338 knots

**Flight Path:**
- Consistent heading: ~257° (west-southwest)
- Departed Newark area (40.81°N, 74.16°W)
- Tracked to approximately (40.71°N, 74.92°W)
- Distance covered: ~35 nautical miles

**Climb Performance:**
- Peak climb rate: 3,904 ft/min (strong initial climb)
- Leveling off: Vertical rate dropped to 0 ft/min at cruise altitude
- Typical of modern jet aircraft departure procedures

## How to Reproduce

```bash
# Track any flight departing from Newark
python track_flight_opensky.py UAL2212 --follow --interval 30 --updates 10 -o my_track.csv

# Or track continuously until manually stopped
python track_flight_opensky.py UAL2212 --follow --interval 30
```

## CSV Data Format

The output CSV contains the following columns:

| Column | Description | Units |
|--------|-------------|-------|
| `Timestamp` | ISO 8601 timestamp | UTC |
| `Callsign` | Flight callsign | - |
| `ICAO` | Aircraft ICAO 24-bit address | Hex |
| `Latitude` | Latitude | Degrees |
| `Longitude` | Longitude | Degrees |
| `Altitude_m` | Altitude | Meters |
| `Altitude_ft` | Altitude | Feet |
| `Velocity_mps` | Ground speed | m/s |
| `Velocity_kts` | Ground speed | Knots |
| `Track` | Heading | Degrees (0-360) |
| `VertRate_mps` | Vertical rate | m/s |
| `VertRate_fpm` | Vertical rate | Feet per minute |
| `OnGround` | Ground status | Boolean |

### Example Row
```csv
2025-12-01T20:05:02,UAL2212,A2B8C5,40.804000,-74.389000,2674.6,8775,131.97,256.5,258.1,19.83,3904,False
```

This shows UAL2212 at 8,775 ft, traveling at 256.5 knots on heading 258°, climbing at 3,904 ft/min.

## Analysis Ideas

### 1. Altitude vs Time Plot
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('example_ual2212_track.csv')
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

plt.figure(figsize=(10, 6))
plt.plot(df['Timestamp'], df['Altitude_ft'])
plt.xlabel('Time')
plt.ylabel('Altitude (ft)')
plt.title('UAL2212 Climb Profile')
plt.grid(True)
plt.tight_layout()
plt.savefig('ual2212_altitude_profile.png', dpi=150)
```

### 2. Speed vs Altitude
```python
plt.figure(figsize=(10, 6))
plt.scatter(df['Altitude_ft'], df['Velocity_kts'])
plt.xlabel('Altitude (ft)')
plt.ylabel('Speed (knots)')
plt.title('UAL2212 Speed vs Altitude')
plt.grid(True)
plt.tight_layout()
plt.savefig('ual2212_speed_altitude.png', dpi=150)
```

### 3. Flight Path on Map
```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 8))
plt.plot(df['Longitude'], df['Latitude'], 'b-', marker='o', markersize=4)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('UAL2212 Flight Path')
plt.grid(True)

# Mark start and end
plt.plot(df['Longitude'].iloc[0], df['Latitude'].iloc[0], 
         'go', markersize=10, label='Start')
plt.plot(df['Longitude'].iloc[-1], df['Latitude'].iloc[-1], 
         'ro', markersize=10, label='End')
plt.legend()
plt.tight_layout()
plt.savefig('ual2212_path.png', dpi=150)
```

### 4. Calculate Distance Traveled
```python
from math import radians, sin, cos, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """Calculate great circle distance in km."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # Earth radius in km

# Calculate total distance
total_distance = 0
for i in range(len(df) - 1):
    d = haversine(
        df['Latitude'].iloc[i], df['Longitude'].iloc[i],
        df['Latitude'].iloc[i+1], df['Longitude'].iloc[i+1]
    )
    total_distance += d

print(f"Total distance traveled: {total_distance:.2f} km")
print(f"Total distance traveled: {total_distance * 0.539957:.2f} nm")
```

## Finding Other Flights to Track

### Active United Flights
```bash
# Search for all United flights currently in the air
python -c "
import requests
r = requests.get('https://opensky-network.org/api/states/all', timeout=30)
data = r.json()
united = [s[1].strip() for s in data['states'] if s[1] and 'UAL' in s[1]]
print(f'Found {len(united)} United flights:')
for flight in sorted(set(united))[:20]:
    print(f'  {flight}')
"
```

### Flights Near Specific Airports
```bash
# Newark area (40.69°N, 74.17°W)
python track_flight_opensky.py UAL1234 --bounds 40.5 -74.5 41.0 -73.5

# San Francisco area
python track_flight_opensky.py UAL456 --bounds 37.3 -122.8 37.9 -122.0
```

## Tips for Effective Tracking

### 1. Timing
- Track departures within 5-10 minutes of scheduled takeoff
- Best data during climb and cruise phases
- Landings can be tracked but position updates may be less frequent near ground

### 2. Update Intervals
- **30 seconds**: Good balance for most tracking
- **10-15 seconds**: Detailed tracking (but watch rate limits)
- **60 seconds**: Long-term tracking, less data volume

### 3. Session Length
- **Short (5-10 updates)**: Departure/arrival analysis
- **Medium (20-50 updates)**: Regional flight tracking
- **Long (100+ updates)**: Cross-country flights

### 4. Data Quality
- OpenSky data is crowd-sourced; coverage varies by region
- Best coverage: North America, Europe, parts of Asia
- Updates may be sparse over oceans or remote areas

## Common Use Cases

### Flight Monitoring
Track a specific flight you're interested in (e.g., meeting someone at airport):
```bash
python track_flight_opensky.py UAL123 --follow --interval 60
```

### Performance Analysis
Collect data for analyzing aircraft performance:
```bash
python track_flight_opensky.py UAL456 --follow --updates 50 -o performance_data.csv
```

### Route Analysis
Track the same flight number on multiple days to compare routes:
```bash
# Day 1
python track_flight_opensky.py UAL789 --follow -o ua789_day1.csv

# Day 2
python track_flight_opensky.py UAL789 --follow -o ua789_day2.csv

# Compare the routes
```

### Educational Purposes
Demonstrate aviation concepts like climb rates, flight levels, etc.:
```bash
python track_flight_opensky.py UAL999 --follow --updates 30 -o educational_example.csv
```

## Additional Resources

- **OpenSky Network**: https://opensky-network.org/
- **Flight tracking visualization**: Use `plot_mpl.py` with tracked data
- **Real-time analysis**: Combine with pandas/matplotlib for live visualization
- **API documentation**: https://opensky-network.org/apidoc/

## Next Steps

1. **Track more flights**: Try different airlines, airports, or flight phases
2. **Analyze patterns**: Compare departure procedures, climb rates, cruise speeds
3. **Visualize data**: Create plots and maps from tracked data
4. **Build datasets**: Collect multiple tracks for statistical analysis
5. **Integrate with other tools**: Combine with weather data, airport info, etc.

---

**Want to contribute your own tracking example?** Save your interesting tracks and document them!
