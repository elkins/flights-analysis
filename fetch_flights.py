#!/usr/bin/env python3
"""
Fetch flight data from ADS-B Exchange and convert to flights-analysis format.

This module provides tools to fetch real-time flight data from ADS-B Exchange
and convert it into the CSV format expected by plot_mpl.py and plot_gcmap.py.

Usage:
    # Fetch all current flights and save to CSV
    python fetch_flights.py -o flights_realtime.csv

    # Filter by geographic area (lat/lon bounds)
    python fetch_flights.py -o flights_sf.csv --bounds 37.0 -123.0 38.5 -121.5

    # Filter by radius around a point
    python fetch_flights.py -o flights_nyc.csv --center 40.7128 -74.0060 --radius 100

    # With minimum flight count threshold
    python fetch_flights.py -o flights.csv --min-flights 5
"""

import argparse
import csv
import logging
import math
import sys
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
EARTH_RADIUS_KM = 6371.0
CONV_FT_TO_M = 0.3048
CONV_KT_TO_MPS = 0.514444444


@dataclass
class FlightRoute:
    """Represents an aggregated flight route between two points."""

    dep_lat: float
    dep_lon: float
    arr_lat: float
    arr_lon: float
    nb_flights: int
    co2_intensity: float = 0.0  # Placeholder for compatibility


class ADSBExchangeFetcher:
    """Fetch flight data from ADS-B Exchange public API."""

    # Public API endpoint (no key required, but rate limited)
    BASE_URL = "https://globe.adsbexchange.com/data/aircraft.json"

    def __init__(self, api_key: str | None = None):
        """
        Initialize ADS-B Exchange fetcher.

        Args:
            api_key: Optional RapidAPI key for higher rate limits
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "FlightsAnalysis/1.0"})

    def fetch_current_flights(self) -> list[dict]:
        """
        Fetch all currently tracked flights.

        Returns:
            List of flight dictionaries
        """
        try:
            logger.info("Fetching current flights from ADS-B Exchange...")
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()

            data = response.json()
            aircraft = data.get("aircraft", [])

            logger.info(f"Received {len(aircraft)} aircraft")
            return aircraft

        except requests.RequestException as e:
            logger.error(f"Failed to fetch flight data: {e}")
            return []

    def parse_flights(
        self,
        aircraft_data: list[dict],
        bounds: tuple[float, float, float, float] | None = None,
        center: tuple[float, float] | None = None,
        radius_km: float | None = None,
    ) -> Iterator[dict]:
        """
        Parse and filter flight data.

        Args:
            aircraft_data: Raw aircraft data from API
            bounds: Optional (min_lat, min_lon, max_lat, max_lon) filter
            center: Optional (lat, lon) center point for radius filter
            radius_km: Radius in kilometers for center-based filtering

        Yields:
            Filtered flight dictionaries with standardized fields
        """
        for aircraft in aircraft_data:
            # Extract position
            lat = aircraft.get("lat")
            lon = aircraft.get("lon")

            if lat is None or lon is None:
                continue

            # Apply geographic filters
            if bounds:
                min_lat, min_lon, max_lat, max_lon = bounds
                if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                    continue

            if center and radius_km:
                distance = self._calculate_distance(center, (lat, lon))
                if distance > radius_km:
                    continue

            # Extract altitude
            altitude = aircraft.get("alt_baro") or aircraft.get("alt_geom")
            if altitude and altitude != "ground":
                try:
                    altitude = float(altitude) * CONV_FT_TO_M
                except (ValueError, TypeError):
                    altitude = None
            else:
                altitude = None

            # Extract other fields
            yield {
                "icao": aircraft.get("hex", "").upper(),
                "callsign": (aircraft.get("flight") or "").strip() or None,
                "registration": aircraft.get("r"),
                "type": aircraft.get("t"),
                "lat": lat,
                "lon": lon,
                "altitude": altitude,
                "speed": aircraft.get("gs"),  # ground speed in knots
                "track": aircraft.get("track"),
                "timestamp": datetime.now(),
            }

    @staticmethod
    def _calculate_distance(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
        """
        Calculate great circle distance between two coordinates (Haversine formula).

        Args:
            coord1: (latitude, longitude) in degrees
            coord2: (latitude, longitude) in degrees

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        # Convert to radians
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return EARTH_RADIUS_KM * c


class RouteAggregator:
    """Aggregate individual flights into routes for visualization."""

    def __init__(self, min_flights: int = 1, grid_resolution: float = 1.0):
        """
        Initialize route aggregator.

        Args:
            min_flights: Minimum number of flights required for a route
            grid_resolution: Grid cell size in degrees for grouping nearby positions
        """
        self.min_flights = min_flights
        self.grid_resolution = grid_resolution
        self.routes: dict[tuple[tuple[float, float], tuple[float, float]], int] = defaultdict(int)

    def add_flight(self, lat: float, lon: float, track: float | None, speed: float | None):
        """
        Add a flight observation to route aggregation.

        Args:
            lat: Current latitude
            lon: Current longitude
            track: Heading in degrees (if available)
            speed: Ground speed in knots (if available)
        """
        # Snap to grid
        grid_lat = round(lat / self.grid_resolution) * self.grid_resolution
        grid_lon = round(lon / self.grid_resolution) * self.grid_resolution

        # Estimate departure and arrival based on track
        # This is a simple heuristic - real route detection would be more complex
        if track is not None and speed is not None and speed > 50:  # Moving aircraft
            # Project backwards and forwards along track
            # Simple approximation: assume 500km route
            distance_deg = 5.0  # ~500km at equator

            track_rad = math.radians(track)
            dlat = distance_deg * math.cos(track_rad)
            dlon = distance_deg * math.sin(track_rad) / math.cos(math.radians(lat))

            dep_lat = grid_lat - dlat / 2
            dep_lon = grid_lon - dlon / 2
            arr_lat = grid_lat + dlat / 2
            arr_lon = grid_lon + dlon / 2

            # Store route
            dep_point = (round(dep_lat, 1), round(dep_lon, 1))
            arr_point = (round(arr_lat, 1), round(arr_lon, 1))

            self.routes[(dep_point, arr_point)] += 1

    def get_routes(self) -> list[FlightRoute]:
        """
        Get aggregated routes meeting minimum flight threshold.

        Returns:
            List of FlightRoute objects
        """
        routes = []
        for (dep, arr), count in self.routes.items():
            if count >= self.min_flights:
                dep_lat, dep_lon = dep
                arr_lat, arr_lon = arr
                routes.append(
                    FlightRoute(
                        dep_lat=dep_lat,
                        dep_lon=dep_lon,
                        arr_lat=arr_lat,
                        arr_lon=arr_lon,
                        nb_flights=count,
                        co2_intensity=50.0,  # Placeholder value
                    )
                )

        logger.info(f"Aggregated {len(routes)} routes from {len(self.routes)} observations")
        return routes


def save_to_csv(routes: list[FlightRoute], output_path: Path) -> None:
    """
    Save routes to CSV file in flights-analysis format.

    Args:
        routes: List of FlightRoute objects
        output_path: Output CSV file path
    """
    logger.info(f"Saving {len(routes)} routes to {output_path}")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")

        # Write header
        writer.writerow(["DepLat", "DepLon", "ArrLat", "ArrLon", "NbFlights", "CO2Intensity"])

        # Write routes
        for route in routes:
            writer.writerow(
                [
                    f"{route.dep_lat:.5f}",
                    f"{route.dep_lon:.5f}",
                    f"{route.arr_lat:.5f}",
                    f"{route.arr_lon:.5f}",
                    route.nb_flights,
                    f"{route.co2_intensity:.5f}",
                ]
            )

    logger.info(f"Successfully saved to {output_path}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Fetch real-time flight data from ADS-B Exchange",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all flights
  python fetch_flights.py -o realtime.csv

  # Filter by geographic bounds
  python fetch_flights.py -o sf_bay.csv --bounds 37.0 -123.0 38.5 -121.5

  # Filter by radius around a point
  python fetch_flights.py -o nyc.csv --center 40.7128 -74.0060 --radius 200

  # Require minimum flight count per route
  python fetch_flights.py -o busy_routes.csv --min-flights 3
        """,
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("flights_realtime.csv"),
        help="Output CSV file path (default: flights_realtime.csv)",
    )

    parser.add_argument(
        "--bounds",
        nargs=4,
        type=float,
        metavar=("MIN_LAT", "MIN_LON", "MAX_LAT", "MAX_LON"),
        help="Filter by geographic bounding box",
    )

    parser.add_argument(
        "--center",
        nargs=2,
        type=float,
        metavar=("LAT", "LON"),
        help="Center point for radius filter",
    )

    parser.add_argument(
        "--radius", type=float, metavar="KM", help="Radius in kilometers (requires --center)"
    )

    parser.add_argument(
        "--min-flights",
        type=int,
        default=1,
        help="Minimum number of flights per route (default: 1)",
    )

    parser.add_argument(
        "--grid-resolution",
        type=float,
        default=1.0,
        help="Grid resolution in degrees for grouping (default: 1.0)",
    )

    parser.add_argument("--api-key", type=str, help="ADS-B Exchange RapidAPI key (optional)")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if args.radius and not args.center:
        parser.error("--radius requires --center")

    # Initialize fetcher
    fetcher = ADSBExchangeFetcher(api_key=args.api_key)

    # Fetch flights
    aircraft_data = fetcher.fetch_current_flights()

    if not aircraft_data:
        logger.error("No flight data retrieved")
        sys.exit(1)

    # Parse and filter flights
    bounds = tuple(args.bounds) if args.bounds else None
    center = tuple(args.center) if args.center else None

    flights = list(
        fetcher.parse_flights(aircraft_data, bounds=bounds, center=center, radius_km=args.radius)
    )

    logger.info(f"Filtered to {len(flights)} flights")

    if not flights:
        logger.warning("No flights match the specified filters")
        sys.exit(1)

    # Aggregate into routes
    aggregator = RouteAggregator(min_flights=args.min_flights, grid_resolution=args.grid_resolution)

    for flight in flights:
        aggregator.add_flight(
            flight["lat"], flight["lon"], flight.get("track"), flight.get("speed")
        )

    routes = aggregator.get_routes()

    if not routes:
        logger.warning(f"No routes with at least {args.min_flights} flights")
        sys.exit(1)

    # Save to CSV
    save_to_csv(routes, args.output)

    logger.info(f"Done! Generated {len(routes)} routes from {len(flights)} flights")
    logger.info(f"Visualize with: python plot_mpl.py -i {args.output}")


if __name__ == "__main__":
    main()
