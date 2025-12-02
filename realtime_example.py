#!/usr/bin/env python3
"""
Real-Time Flight Visualization Example

This script demonstrates a complete workflow:
1. Fetch current flights from ADS-B Exchange
2. Filter and aggregate into routes
3. Generate visualization
4. Compare with historical data

Usage:
    python realtime_example.py
"""

import subprocess
import sys
from pathlib import Path


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_command(cmd: list[str], description: str) -> bool:
    """
    Run a command and report results.

    Args:
        cmd: Command and arguments as list
        description: Human-readable description

    Returns:
        True if successful, False otherwise
    """
    print(f"▶ {description}")
    print(f"  Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print("✓ Success!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        if e.stderr:
            print(f"  {e.stderr}")
        return False


def main():
    """Main example workflow."""
    print_header("Real-Time Flight Visualization Demo")

    print("This example demonstrates fetching and visualizing current air traffic.\n")
    print("Steps:")
    print("  1. Fetch current flights from ADS-B Exchange")
    print("  2. Filter by geographic region (optional)")
    print("  3. Aggregate into routes")
    print("  4. Generate visualization")
    print("  5. Compare with historical data")

    # Define output paths
    realtime_csv = Path("realtime_flights.csv")
    realtime_map = Path("realtime_map.png")
    historical_map = Path("historical_map.png")

    # Step 1: Fetch all current flights
    print_header("Step 1: Fetch Current Flights")

    success = run_command(
        ["python", "fetch_flights.py", "-o", str(realtime_csv), "--min-flights", "2", "-v"],
        "Fetching current flights worldwide...",
    )

    if not success:
        print("Failed to fetch flight data. Please check your internet connection.")
        print("\nNote: The ADS-B Exchange public API may have rate limits.")
        print("If you're getting errors, try again in a few minutes.")
        sys.exit(1)

    if not realtime_csv.exists():
        print(f"Error: Expected output file {realtime_csv} was not created.")
        sys.exit(1)

    # Step 2: Generate real-time visualization
    print_header("Step 2: Visualize Real-Time Data")

    success = run_command(
        [
            "python",
            "plot_mpl.py",
            "-i",
            str(realtime_csv),
            "-o",
            str(realtime_map),
            "--dpi",
            "200",
            "--color-mode",
            "screen",
            "-v",
        ],
        "Generating real-time flight map...",
    )

    if not success or not realtime_map.exists():
        print("Failed to generate real-time visualization.")
        sys.exit(1)

    # Step 3: Generate historical comparison
    print_header("Step 3: Generate Historical Comparison")

    historical_csv = Path("data.csv")
    if historical_csv.exists():
        success = run_command(
            [
                "python",
                "plot_mpl.py",
                "-i",
                str(historical_csv),
                "-o",
                str(historical_map),
                "--dpi",
                "200",
                "--color-mode",
                "screen",
                "-v",
            ],
            "Generating historical flight map for comparison...",
        )

        if success and historical_map.exists():
            print("\n📊 Comparison:")
            print(f"  Real-time map:   {realtime_map}")
            print(f"  Historical map:  {historical_map}")
            print("\nNotice the differences:")
            print("  - Real-time: Current air traffic patterns (changes constantly)")
            print("  - Historical: Aggregated patterns over time (stable)")
    else:
        print("No historical data.csv found for comparison.")

    # Summary
    print_header("Summary")

    print("✓ Successfully generated real-time flight visualization!")
    print("\nOutput files:")
    print(f"  Data:  {realtime_csv}")
    print(f"  Map:   {realtime_map}")

    if historical_map.exists():
        print(f"  Comparison: {historical_map}")

    print("\n💡 Next Steps:")
    print("  1. Open the PNG files to view the maps")
    print("  2. Run this script again to see how patterns change")
    print("  3. Try geographic filtering:")
    print("     python fetch_flights.py -o sf.csv --center 37.7749 -122.4194 --radius 100")
    print("  4. Read ADSBEXCHANGE_INTEGRATION.md for advanced usage")
    print("  5. Explore interactively:")
    print("     jupyter notebook notebooks/flight_analysis_tutorial.ipynb")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
