#!/usr/bin/env python3
"""
Track specific flights using OpenSky Network API (free, no key required).

OpenSky Network provides free access to real-time flight data without requiring
an API key. This is a good alternative to ADS-B Exchange for tracking specific flights.

Usage:
    # Track United Airlines flight 262
    python track_flight_opensky.py UA262
    
    # Track with updates every 30 seconds
    python track_flight_opensky.py UA262 --follow --interval 30
    
    # Save and plot
    python track_flight_opensky.py UA262 --follow --updates 20 -o ua262.csv --plot
"""

import argparse
import csv
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FlightPosition:
    """Flight position from OpenSky Network."""
    timestamp: datetime
    icao: str
    callsign: str
    lat: float
    lon: float
    altitude: float  # meters (already in meters from OpenSky)
    velocity: float | None  # m/s
    track: float | None  # degrees
    vert_rate: float | None  # m/s
    on_ground: bool = False


class OpenSkyTracker:
    """Track flights using OpenSky Network API."""
    
    BASE_URL = "https://opensky-network.org/api/states/all"
    
    def __init__(self, username: str | None = None, password: str | None = None):
        """
        Initialize OpenSky tracker.
        
        Args:
            username: OpenSky username (optional, increases rate limits)
            password: OpenSky password (optional)
        """
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
        self.flight_history: list[FlightPosition] = []
    
    def normalize_callsign(self, callsign: str) -> list[str]:
        """Generate callsign variations."""
        callsign = callsign.upper().strip()
        variations = [callsign]
        
        if callsign.isdigit():
            variations.extend([
                f"UA{callsign}", f"UAL{callsign}", f"UA {callsign}", f"UAL {callsign}"
            ])
        elif callsign.startswith('UA') and not callsign.startswith('UAL'):
            number = callsign[2:].strip()
            variations.extend([f"UAL{number}", f"UA {number}", f"UAL {number}"])
        elif callsign.startswith('UAL'):
            number = callsign[3:].strip()
            variations.extend([f"UA{number}", f"UA {number}", f"UAL {number}"])
        
        return variations
    
    def find_flight(
        self,
        callsign: str,
        bounds: tuple[float, float, float, float] | None = None
    ) -> FlightPosition | None:
        """
        Find flight by callsign.
        
        Args:
            callsign: Flight callsign
            bounds: Optional (lamin, lomin, lamax, lomax) to filter region
            
        Returns:
            FlightPosition if found
        """
        variations = self.normalize_callsign(callsign)
        logger.debug(f"Searching for: {variations}")
        
        try:
            params = {}
            if bounds:
                params = {
                    'lamin': bounds[0],
                    'lomin': bounds[1],
                    'lamax': bounds[2],
                    'lomax': bounds[3]
                }
            
            logger.info("Fetching flight data from OpenSky Network...")
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            states = data.get('states', [])
            
            logger.info(f"Received {len(states)} aircraft states")
            
            # Search for matching callsign
            for state in states:
                flight_callsign = (state[1] or '').strip().upper()
                
                if flight_callsign in variations:
                    return self._parse_state(state, data.get('time', time.time()))
            
            # Show similar callsigns
            similar = [
                (s[1] or '').strip()
                for s in states
                if s[1] and any(v[:2] in (s[1] or '') for v in variations)
            ][:10]
            
            if similar:
                logger.info(f"Similar callsigns: {similar}")
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data: {e}")
            return None
    
    def _parse_state(self, state: list, timestamp: float) -> FlightPosition:
        """
        Parse OpenSky state vector.
        
        State vector format:
        [0] icao24, [1] callsign, [2] origin_country, [3] time_position,
        [4] last_contact, [5] longitude, [6] latitude, [7] baro_altitude,
        [8] on_ground, [9] velocity, [10] true_track, [11] vertical_rate
        """
        return FlightPosition(
            timestamp=datetime.fromtimestamp(timestamp),
            icao=state[0].upper() if state[0] else '',
            callsign=(state[1] or '').strip(),
            lon=state[5],
            lat=state[6],
            altitude=state[7] if state[7] is not None else 0.0,
            velocity=state[9],
            track=state[10],
            vert_rate=state[11],
            on_ground=state[8]
        )
    
    def track_continuous(
        self,
        callsign: str,
        interval_seconds: int = 30,
        max_updates: int | None = None,
        bounds: tuple[float, float, float, float] | None = None
    ) -> list[FlightPosition]:
        """Track flight continuously."""
        update_count = 0
        
        print(f"\n🛫 Tracking {callsign} with OpenSky Network")
        print(f"   Updates every {interval_seconds}s (Press Ctrl+C to stop)\n")
        
        try:
            while max_updates is None or update_count < max_updates:
                position = self.find_flight(callsign, bounds)
                
                if position:
                    self.flight_history.append(position)
                    self._print_position(position, update_count)
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {callsign} not found")
                
                update_count += 1
                
                if max_updates is None or update_count < max_updates:
                    time.sleep(interval_seconds)
                    
        except KeyboardInterrupt:
            print("\n\n⏹️  Tracking stopped")
        
        return self.flight_history
    
    def _print_position(self, pos: FlightPosition, update_num: int) -> None:
        """Print position info."""
        print(f"[{pos.timestamp.strftime('%H:%M:%S')}] Update #{update_num + 1}: {pos.callsign}")
        print(f"  📍 Position: {pos.lat:.4f}°, {pos.lon:.4f}°")
        print(f"  ✈️  Altitude: {pos.altitude:,.0f} m ({pos.altitude * 3.28084:,.0f} ft)")
        
        if pos.velocity:
            print(f"  🚀 Speed: {pos.velocity * 1.94384:.0f} kts ({pos.velocity:.1f} m/s)")
        
        if pos.track:
            print(f"  🧭 Heading: {pos.track:.0f}°")
        
        if pos.vert_rate:
            direction = "↗️ " if pos.vert_rate > 0 else "↘️ "
            print(f"  {direction}Vert Rate: {pos.vert_rate * 196.85:+.0f} ft/min")
        
        if pos.on_ground:
            print("  🛬 Status: On Ground")
        
        print()
    
    def save_to_csv(self, output_path: Path) -> None:
        """Save track to CSV."""
        if not self.flight_history:
            logger.warning("No data to save")
            return
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 'Callsign', 'ICAO', 'Latitude', 'Longitude',
                'Altitude_m', 'Altitude_ft', 'Velocity_mps', 'Velocity_kts',
                'Track', 'VertRate_mps', 'VertRate_fpm', 'OnGround'
            ])
            
            for pos in self.flight_history:
                writer.writerow([
                    pos.timestamp.isoformat(),
                    pos.callsign,
                    pos.icao,
                    f"{pos.lat:.6f}",
                    f"{pos.lon:.6f}",
                    f"{pos.altitude:.1f}",
                    f"{pos.altitude * 3.28084:.0f}",
                    f"{pos.velocity:.2f}" if pos.velocity else '',
                    f"{pos.velocity * 1.94384:.1f}" if pos.velocity else '',
                    f"{pos.track:.1f}" if pos.track else '',
                    f"{pos.vert_rate:.2f}" if pos.vert_rate else '',
                    f"{pos.vert_rate * 196.85:.0f}" if pos.vert_rate else '',
                    pos.on_ground
                ])
        
        logger.info(f"Saved to {output_path}")
    
    def plot_flight_path(self, output_path: Path | None = None) -> None:
        """Plot flight path."""
        if len(self.flight_history) < 2:
            logger.warning("Need at least 2 positions to plot")
            return
        
        temp_csv = Path("temp_flight_path.csv")
        
        with open(temp_csv, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['DepLat', 'DepLon', 'ArrLat', 'ArrLon', 'NbFlights', 'CO2Intensity'])
            
            for i in range(len(self.flight_history) - 1):
                p1 = self.flight_history[i]
                p2 = self.flight_history[i + 1]
                writer.writerow([
                    f"{p1.lat:.5f}", f"{p1.lon:.5f}",
                    f"{p2.lat:.5f}", f"{p2.lon:.5f}",
                    1, 50.0
                ])
        
        import subprocess
        out_file = output_path or Path(f"{self.flight_history[0].callsign.strip()}_path.png")
        
        try:
            subprocess.run([
                'python', 'plot_mpl.py', '-i', str(temp_csv),
                '-o', str(out_file), '--dpi', '200', '-v'
            ], check=True)
            logger.info(f"Plotted to {out_file}")
        finally:
            temp_csv.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description='Track flights using OpenSky Network (free)',
        epilog="""
Examples:
  # Find UA262
  python track_flight_opensky.py UA262
  
  # Track continuously
  python track_flight_opensky.py UA262 --follow --interval 30
  
  # Save and plot
  python track_flight_opensky.py UA262 --follow --updates 20 -o track.csv --plot
  
  # Search in specific region (North America)
  python track_flight_opensky.py UA262 --bounds 25 -125 50 -65
        """
    )
    
    parser.add_argument('callsign', help='Flight callsign (e.g., UA262)')
    parser.add_argument('-o', '--output', type=Path, help='Output CSV file')
    parser.add_argument('--follow', action='store_true', help='Track continuously')
    parser.add_argument('--interval', type=int, default=30, help='Update interval (seconds)')
    parser.add_argument('--updates', type=int, help='Max updates')
    parser.add_argument('--plot', action='store_true', help='Plot the path')
    parser.add_argument(
        '--bounds', nargs=4, type=float,
        metavar=('LAMIN', 'LOMIN', 'LAMAX', 'LOMAX'),
        help='Geographic bounds to search'
    )
    parser.add_argument('--username', help='OpenSky username (for higher limits)')
    parser.add_argument('--password', help='OpenSky password')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tracker = OpenSkyTracker(username=args.username, password=args.password)
    
    bounds = tuple(args.bounds) if args.bounds else None
    
    if args.follow:
        tracker.track_continuous(args.callsign, args.interval, args.updates, bounds)
    else:
        print(f"\n🔍 Looking for {args.callsign}...\n")
        position = tracker.find_flight(args.callsign, bounds)
        
        if position:
            tracker.flight_history.append(position)
            tracker._print_position(position, 0)
        else:
            print(f"❌ {args.callsign} not found")
            print("\nTips:")
            print("  - Try: UA262, UAL262, UAL 262")
            print("  - Flight might not be airborne")
            print("  - Add --bounds to search specific region")
            print("  - Check: https://opensky-network.org/")
            sys.exit(1)
    
    if args.output:
        tracker.save_to_csv(args.output)
    
    if args.plot:
        tracker.plot_flight_path()
    
    if tracker.flight_history:
        print(f"\n✅ Tracked {len(tracker.flight_history)} position(s)")


if __name__ == '__main__':
    main()
