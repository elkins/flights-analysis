#!/usr/bin/env python3
"""
Track a specific flight by callsign (e.g., UA262, UAL262).

This script fetches real-time data from ADS-B Exchange and tracks a specific
flight, showing its current position, altitude, speed, and flight path.

Usage:
    # Track United Airlines flight 262
    python track_flight.py UA262
    python track_flight.py UAL262
    
    # Track and save path to CSV
    python track_flight.py UA262 -o ua262_path.csv
    
    # Track with updates every 30 seconds
    python track_flight.py UA262 --follow --interval 30
    
    # Plot the flight path
    python track_flight.py UA262 --plot
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging
import csv
import sys
import time
import json

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FlightPosition:
    """Represents a single position record for a flight."""
    timestamp: datetime
    icao: str
    callsign: str
    lat: float
    lon: float
    altitude: Optional[float] = None  # meters
    speed: Optional[float] = None  # m/s
    track: Optional[float] = None  # degrees
    vert_rate: Optional[float] = None  # m/s
    registration: Optional[str] = None
    aircraft_type: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None


class FlightTracker:
    """Track specific flights from ADS-B Exchange."""
    
    BASE_URL = "https://globe.adsbexchange.com/data/aircraft.json"
    
    # Conversion constants
    CONV_FT_TO_M = 0.3048
    CONV_KT_TO_MPS = 0.514444444
    CONV_FPM_TO_MPS = 5.08e-3
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize flight tracker."""
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FlightTracker/1.0'
        })
        self.flight_history: List[FlightPosition] = []
    
    def normalize_callsign(self, callsign: str) -> List[str]:
        """
        Generate possible callsign variations.
        
        United Airlines uses both UA and UAL prefixes.
        
        Args:
            callsign: Input callsign (e.g., 'UA262', 'UAL262', '262')
            
        Returns:
            List of possible callsign variations
        """
        callsign = callsign.upper().strip()
        
        variations = [callsign]
        
        # If just numbers, add airline codes
        if callsign.isdigit():
            variations.extend([
                f"UA{callsign}",
                f"UAL{callsign}",
                f"UA {callsign}",
                f"UAL {callsign}"
            ])
        # If starts with UA, also try UAL
        elif callsign.startswith('UA') and not callsign.startswith('UAL'):
            number = callsign[2:].strip()
            variations.extend([
                f"UAL{number}",
                f"UA {number}",
                f"UAL {number}"
            ])
        # If starts with UAL, also try UA
        elif callsign.startswith('UAL'):
            number = callsign[3:].strip()
            variations.extend([
                f"UA{number}",
                f"UA {number}",
                f"UAL {number}"
            ])
        
        return variations
    
    def find_flight(self, callsign: str) -> Optional[FlightPosition]:
        """
        Find a specific flight by callsign in current data.
        
        Args:
            callsign: Flight callsign to search for
            
        Returns:
            FlightPosition if found, None otherwise
        """
        variations = self.normalize_callsign(callsign)
        logger.debug(f"Searching for callsign variations: {variations}")
        
        try:
            logger.info("Fetching current flight data from ADS-B Exchange...")
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            aircraft_list = data.get('aircraft', [])
            
            logger.info(f"Received data for {len(aircraft_list)} aircraft")
            
            # Search for matching callsign
            for aircraft in aircraft_list:
                flight_callsign = (aircraft.get('flight') or '').strip().upper()
                
                if flight_callsign in variations:
                    return self._parse_aircraft(aircraft)
            
            # If not found, show similar callsigns
            similar = [
                a.get('flight', '').strip() 
                for a in aircraft_list 
                if a.get('flight') and any(v[:2] in a.get('flight', '') for v in variations)
            ]
            
            if similar:
                logger.info(f"Flight not found. Similar callsigns currently tracked: {similar[:10]}")
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch flight data: {e}")
            return None
    
    def _parse_aircraft(self, aircraft: Dict[str, Any]) -> Optional[FlightPosition]:
        """Parse aircraft data into FlightPosition."""
        # Parse position
        lat = aircraft.get('lat')
        lon = aircraft.get('lon')
        
        # Require valid coordinates
        if lat is None or lon is None:
            return None
        
        # Parse altitude
        altitude = aircraft.get('alt_baro') or aircraft.get('alt_geom')
        if altitude and altitude != "ground":
            try:
                altitude = float(altitude) * self.CONV_FT_TO_M
            except (ValueError, TypeError):
                altitude = None
        else:
            altitude = None
        
        # Parse speed
        speed = aircraft.get('gs')
        if speed:
            speed = float(speed) * self.CONV_KT_TO_MPS
        
        # Parse vertical rate
        vert_rate = aircraft.get('baro_rate') or aircraft.get('geom_rate')
        if vert_rate:
            vert_rate = float(vert_rate) * self.CONV_FPM_TO_MPS
        
        return FlightPosition(
            timestamp=datetime.now(),
            icao=aircraft.get('hex', '').upper(),
            callsign=(aircraft.get('flight') or '').strip(),
            lat=lat,
            lon=lon,
            altitude=altitude,
            speed=speed,
            track=aircraft.get('track'),
            vert_rate=vert_rate,
            registration=aircraft.get('r'),
            aircraft_type=aircraft.get('t'),
            origin=aircraft.get('from'),
            destination=aircraft.get('to')
        )
    
    def track_continuous(
        self,
        callsign: str,
        interval_seconds: int = 30,
        max_updates: Optional[int] = None
    ) -> List[FlightPosition]:
        """
        Track a flight continuously with periodic updates.
        
        Args:
            callsign: Flight callsign to track
            interval_seconds: Time between updates
            max_updates: Maximum number of updates (None for unlimited)
            
        Returns:
            List of FlightPosition records
        """
        update_count = 0
        
        print(f"\n🛫 Tracking {callsign} (updates every {interval_seconds}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while max_updates is None or update_count < max_updates:
                position = self.find_flight(callsign)
                
                if position:
                    self.flight_history.append(position)
                    self._print_position(position, update_count)
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Flight {callsign} not found")
                
                update_count += 1
                
                if max_updates is None or update_count < max_updates:
                    time.sleep(interval_seconds)
                    
        except KeyboardInterrupt:
            print("\n\n⏹️  Tracking stopped by user")
        
        return self.flight_history
    
    def _print_position(self, pos: FlightPosition, update_num: int) -> None:
        """Print formatted position information."""
        print(f"[{pos.timestamp.strftime('%H:%M:%S')}] Update #{update_num + 1}: {pos.callsign}")
        print(f"  📍 Position: {pos.lat:.4f}°, {pos.lon:.4f}°")
        
        if pos.altitude:
            alt_ft = pos.altitude * 3.28084
            print(f"  ✈️  Altitude: {alt_ft:,.0f} ft ({pos.altitude:,.0f} m)")
        
        if pos.speed:
            speed_kts = pos.speed * 1.94384
            print(f"  🚀 Speed: {speed_kts:.0f} kts ({pos.speed:.1f} m/s)")
        
        if pos.track:
            print(f"  🧭 Heading: {pos.track:.0f}°")
        
        if pos.vert_rate:
            vr_fpm = pos.vert_rate * 196.85
            direction = "↗️ " if pos.vert_rate > 0 else "↘️ "
            print(f"  {direction}Vert Rate: {vr_fpm:+.0f} ft/min")
        
        if pos.aircraft_type:
            print(f"  ✈️  Aircraft: {pos.aircraft_type}")
        
        if pos.registration:
            print(f"  🔖 Registration: {pos.registration}")
        
        if pos.origin or pos.destination:
            route = f"{pos.origin or '???'} → {pos.destination or '???'}"
            print(f"  🛫→🛬 Route: {route}")
        
        print()
    
    def save_to_csv(self, output_path: Path) -> None:
        """Save flight history to CSV."""
        if not self.flight_history:
            logger.warning("No flight history to save")
            return
        
        logger.info(f"Saving {len(self.flight_history)} position records to {output_path}")
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Timestamp', 'Callsign', 'ICAO', 'Latitude', 'Longitude',
                'Altitude_m', 'Altitude_ft', 'Speed_mps', 'Speed_kts',
                'Track', 'VertRate_mps', 'VertRate_fpm',
                'Registration', 'AircraftType', 'Origin', 'Destination'
            ])
            
            # Data
            for pos in self.flight_history:
                writer.writerow([
                    pos.timestamp.isoformat(),
                    pos.callsign,
                    pos.icao,
                    f"{pos.lat:.6f}" if pos.lat else '',
                    f"{pos.lon:.6f}" if pos.lon else '',
                    f"{pos.altitude:.1f}" if pos.altitude else '',
                    f"{pos.altitude * 3.28084:.0f}" if pos.altitude else '',
                    f"{pos.speed:.2f}" if pos.speed else '',
                    f"{pos.speed * 1.94384:.1f}" if pos.speed else '',
                    f"{pos.track:.1f}" if pos.track else '',
                    f"{pos.vert_rate:.2f}" if pos.vert_rate else '',
                    f"{pos.vert_rate * 196.85:.0f}" if pos.vert_rate else '',
                    pos.registration or '',
                    pos.aircraft_type or '',
                    pos.origin or '',
                    pos.destination or ''
                ])
        
        logger.info(f"Saved to {output_path}")
    
    def plot_flight_path(self, output_path: Optional[Path] = None) -> None:
        """Plot the flight path on a map."""
        if not self.flight_history:
            logger.warning("No flight history to plot")
            return
        
        positions_with_coords = [
            p for p in self.flight_history 
            if p.lat is not None and p.lon is not None
        ]
        
        if not positions_with_coords:
            logger.warning("No positions with coordinates to plot")
            return
        
        logger.info(f"Plotting {len(positions_with_coords)} position records...")
        
        # Create a simple CSV for plotting
        temp_csv = Path("temp_flight_path.csv")
        
        with open(temp_csv, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['DepLat', 'DepLon', 'ArrLat', 'ArrLon', 'NbFlights', 'CO2Intensity'])
            
            # Connect consecutive positions
            for i in range(len(positions_with_coords) - 1):
                p1 = positions_with_coords[i]
                p2 = positions_with_coords[i + 1]
                
                writer.writerow([
                    f"{p1.lat:.5f}",
                    f"{p1.lon:.5f}",
                    f"{p2.lat:.5f}",
                    f"{p2.lon:.5f}",
                    1,
                    50.0
                ])
        
        # Use plot_mpl.py to visualize
        import subprocess
        
        out_file = output_path or Path(f"{self.flight_history[0].callsign}_path.png")
        
        try:
            subprocess.run([
                'python', 'plot_mpl.py',
                '-i', str(temp_csv),
                '-o', str(out_file),
                '--dpi', '200',
                '-v'
            ], check=True)
            
            logger.info(f"Flight path plotted to {out_file}")
            
        finally:
            # Cleanup temp file
            if temp_csv.exists():
                temp_csv.unlink()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Track specific flight by callsign',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find current position of UA262
  python track_flight.py UA262
  
  # Track with continuous updates every 30 seconds
  python track_flight.py UA262 --follow --interval 30
  
  # Save track to CSV
  python track_flight.py UA262 -o ua262_track.csv --follow --updates 10
  
  # Track and plot the path
  python track_flight.py UA262 --follow --updates 20 --plot
        """
    )
    
    parser.add_argument(
        'callsign',
        help='Flight callsign (e.g., UA262, UAL262)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output CSV file for flight track'
    )
    
    parser.add_argument(
        '--follow',
        action='store_true',
        help='Continuously track the flight'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Update interval in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--updates',
        type=int,
        help='Maximum number of updates (default: unlimited)'
    )
    
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Plot the flight path'
    )
    
    parser.add_argument(
        '--api-key',
        help='ADS-B Exchange RapidAPI key (optional)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize tracker
    tracker = FlightTracker(api_key=args.api_key)
    
    if args.follow:
        # Continuous tracking
        tracker.track_continuous(
            args.callsign,
            interval_seconds=args.interval,
            max_updates=args.updates
        )
    else:
        # Single lookup
        print(f"\n🔍 Looking for flight {args.callsign}...\n")
        position = tracker.find_flight(args.callsign)
        
        if position:
            tracker.flight_history.append(position)
            tracker._print_position(position, 0)
        else:
            print(f"❌ Flight {args.callsign} not currently tracked")
            print("\nTips:")
            print("  - Try variations: UA262, UAL262, UAL 262")
            print("  - The flight might not be airborne right now")
            print("  - Check ADS-B Exchange directly: https://globe.adsbexchange.com/")
            sys.exit(1)
    
    # Save to CSV if requested
    if args.output:
        tracker.save_to_csv(args.output)
    
    # Plot if requested
    if args.plot:
        tracker.plot_flight_path()
    
    # Summary
    if tracker.flight_history:
        print(f"\n✅ Tracked {len(tracker.flight_history)} position(s)")
        
        if args.output:
            print(f"📄 Data saved to: {args.output}")
        
        if args.plot:
            print(f"🗺️  Map saved to: {tracker.flight_history[0].callsign}_path.png")


if __name__ == '__main__':
    main()
