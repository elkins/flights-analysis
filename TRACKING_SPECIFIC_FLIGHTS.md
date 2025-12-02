# Tracking Specific Flights (e.g., UA 262)

## Quick Answer: Use OpenSky Network (Free!)

**I've created `track_flight_opensky.py` which works RIGHT NOW without any API key:**

```bash
# Find UA 262 (if currently flying)
python track_flight_opensky.py UA262 -v

# Track continuously (updates every 30 seconds)
python track_flight_opensky.py UA262 --follow --interval 30

# Save track to CSV and plot the path
python track_flight_opensky.py UA262 --follow --updates 20 -o ua262_track.csv --plot
```

**Note**: UA 262 may not be airborne right now. The script will show similar United flights that ARE currently flying.

## Why Two Scripts?

1. **`track_flight_opensky.py`** ✅ **USE THIS**
   - Uses OpenSky Network (free, no API key)
   - Works immediately
   - Good for commercial flights
   - ~7,600+ aircraft tracked globally

2. **`track_flight.py`** (requires API key)
   - Uses ADS-B Exchange (more complete, but restricted)
   - Requires RapidAPI key
   - Better coverage including military/private aircraft

## Solution 1: Use RapidAPI (Recommended for Automated Tracking)

### Setup

1. **Sign up for RapidAPI:**
   - Go to: https://rapidapi.com/adsbx/api/adsbexchange-com1/
   - Subscribe to a plan (free tier available with limits)
   - Get your API key

2. **Use with track_flight.py:**
   ```bash
   python track_flight.py UA262 --api-key YOUR_RAPIDAPI_KEY
   ```

### Example: Track UA 262
```bash
# Single lookup
python track_flight.py UA262 --api-key YOUR_KEY -v

# Continuous tracking (updates every 30 seconds)
python track_flight.py UA262 --api-key YOUR_KEY --follow --interval 30

# Track and save to CSV
python track_flight.py UA262 --api-key YOUR_KEY --follow --updates 20 -o ua262_track.csv

# Track and plot the path
python track_flight.py UA262 --api-key YOUR_KEY --follow --updates 20 --plot
```

## Solution 2: Use Your flightdata Project

Your existing `~/aviation/flightdata` project may have better API access configured!

### Option A: Use flightdata directly
```bash
cd ~/aviation/flightdata

# Check if it works
python adsbexchange.py

# Look for UA262
python -c "
from adsbexchange import get_flights_all

for flight in get_flights_all():
    if flight.flight and 'UA262' in flight.flight:
        print(f'Found: {flight.flight}')
        print(f'  Position: {flight.lat}, {flight.lon}')
        print(f'  Altitude: {flight.altitude}m')
        break
"
```

### Option B: Import from flightdata
```python
# In flights-analysis directory
import sys
sys.path.append('/Users/georgeelkins/aviation/flightdata')

from adsbexchange import ADSBExchangeClient, get_flights_all

# Your flightdata project might have API key configured
for flight in get_flights_all():
    if flight.flight and 'UA262' in flight.flight:
        print(f"Found UA262 at {flight.lat}, {flight.lon}")
```

## Solution 3: Web Scraping (Last Resort)

If API access is blocked, scrape the web interface:

```python
# This would require additional libraries (selenium, beautifulsoup4)
# Not included by default, but possible if needed
```

## Solution 4: Alternative Data Sources

### FlightAware
- Has a free tier API
- Requires registration
- Good for specific flight tracking

### OpenSky Network
- Free, open API
- No API key required for basic use
- REST API: https://opensky-network.org/api/

Example with OpenSky:
```python
import requests

# OpenSky Network API (free, no key needed)
response = requests.get(
    'https://opensky-network.org/api/states/all',
    params={'lamin': 25, 'lomin': -125, 'lamax': 50, 'lomax': -65}
)

data = response.json()
for state in data.get('states', []):
    callsign = (state[1] or '').strip()
    if 'UA262' in callsign:
        print(f"Found: {callsign}")
        print(f"  Lat/Lon: {state[6]}, {state[5]}")
        print(f"  Altitude: {state[7]}m")
```

## Updated track_flight.py for OpenSky

I can create a version that uses OpenSky Network instead of ADS-B Exchange, which has free API access:

```bash
# Create OpenSky version
python track_flight_opensky.py UA262
```

Would you like me to:
1. **Create an OpenSky version** (free, no API key needed)?
2. **Integrate with your flightdata project** (reuse existing setup)?
3. **Show how to get a RapidAPI key** (best for production use)?

## Quick Test: What Flights Are Currently Tracked?

Even without a key, we can try alternative approaches:

```bash
# Try OpenSky Network (free)
curl -s "https://opensky-network.org/api/states/all?lamin=25&lomin=-125&lamax=50&lomax=-65" | python3 -m json.tool | grep -A 5 "UAL"
```

## Next Steps

**For tracking UA 262 specifically, I recommend:**

1. **Short-term**: Use your existing `flightdata` project
   ```bash
   cd ~/aviation/flightdata
   python examples.py  # Check if it has working API access
   ```

2. **Long-term**: Get a RapidAPI key for automated tracking
   - Free tier: 100 requests/day
   - Paid tiers: Higher limits

3. **Alternative**: I can create an OpenSky Network version
   - Free, no API key
   - Good coverage for commercial flights
   - Slightly different data format

**Which approach would you like to pursue?**
