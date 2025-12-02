#!/usr/bin/env python3
"""
Visualize tracked flight data from CSV.

Usage:
    python visualize_track.py example_ual2212_track.csv
    python visualize_track.py my_track.csv -o my_plot.png
"""

import argparse
import sys
from pathlib import Path

try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Install with: pip install pandas matplotlib")
    sys.exit(1)


def plot_track(csv_file: Path, output_file: Path = None):
    """Create visualization plots for flight track."""

    # Read data
    df = pd.read_csv(csv_file)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    callsign = df["Callsign"].iloc[0]

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(f"Flight Track Analysis: {callsign}", fontsize=16, fontweight="bold")

    # 1. Flight Path (Map View)
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(df["Longitude"], df["Latitude"], "b-", linewidth=2, marker="o", markersize=6)
    ax1.plot(df["Longitude"].iloc[0], df["Latitude"].iloc[0], "go", markersize=12, label="Start")
    ax1.plot(df["Longitude"].iloc[-1], df["Latitude"].iloc[-1], "ro", markersize=12, label="End")
    ax1.set_xlabel("Longitude", fontsize=11)
    ax1.set_ylabel("Latitude", fontsize=11)
    ax1.set_title("Flight Path (Geographic)", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Add position labels for key points
    for i in [0, len(df) // 2, len(df) - 1]:
        ax1.annotate(
            f"{i+1}",
            xy=(df["Longitude"].iloc[i], df["Latitude"].iloc[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    # 2. Altitude Profile
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(df["Timestamp"], df["Altitude_ft"], "b-", linewidth=2, marker="o")
    ax2.set_xlabel("Time", fontsize=11)
    ax2.set_ylabel("Altitude (feet)", fontsize=11)
    ax2.set_title("Altitude Profile", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Add altitude labels
    for i in [0, -1]:
        ax2.annotate(
            f"{df['Altitude_ft'].iloc[i]:,.0f} ft",
            xy=(df["Timestamp"].iloc[i], df["Altitude_ft"].iloc[i]),
            xytext=(0, 10),
            textcoords="offset points",
            fontsize=9,
            ha="center",
        )

    # 3. Speed Profile
    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(df["Timestamp"], df["Velocity_kts"], "g-", linewidth=2, marker="o")
    ax3.set_xlabel("Time", fontsize=11)
    ax3.set_ylabel("Ground Speed (knots)", fontsize=11)
    ax3.set_title("Speed Profile", fontsize=12, fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 4. Vertical Rate
    ax4 = plt.subplot(2, 3, 4)
    vert_rate = df["VertRate_fpm"].dropna()
    if not vert_rate.empty:
        times = df.loc[vert_rate.index, "Timestamp"]
        colors = ["green" if v > 0 else "red" for v in vert_rate]
        ax4.bar(times, vert_rate, color=colors, alpha=0.7, width=0.0003)
        ax4.axhline(y=0, color="k", linestyle="-", linewidth=0.5)
        ax4.set_xlabel("Time", fontsize=11)
        ax4.set_ylabel("Vertical Rate (ft/min)", fontsize=11)
        ax4.set_title("Climb/Descent Rate", fontsize=12, fontweight="bold")
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha="right")
    else:
        ax4.text(
            0.5, 0.5, "No vertical rate data", ha="center", va="center", transform=ax4.transAxes
        )
        ax4.set_title("Climb/Descent Rate", fontsize=12, fontweight="bold")

    # 5. Speed vs Altitude
    ax5 = plt.subplot(2, 3, 5)
    sc = ax5.scatter(
        df["Altitude_ft"],
        df["Velocity_kts"],
        c=range(len(df)),
        cmap="viridis",
        s=100,
        alpha=0.6,
        edgecolors="black",
        linewidth=0.5,
    )
    ax5.set_xlabel("Altitude (feet)", fontsize=11)
    ax5.set_ylabel("Ground Speed (knots)", fontsize=11)
    ax5.set_title("Speed vs Altitude", fontsize=12, fontweight="bold")
    ax5.grid(True, alpha=0.3)
    plt.colorbar(sc, ax=ax5, label="Time Progress")

    # 6. Flight Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis("off")

    # Calculate statistics
    duration = (df["Timestamp"].iloc[-1] - df["Timestamp"].iloc[0]).total_seconds() / 60
    alt_gain = df["Altitude_ft"].iloc[-1] - df["Altitude_ft"].iloc[0]
    avg_climb = alt_gain / duration if duration > 0 else 0
    max_speed = df["Velocity_kts"].max()
    avg_speed = df["Velocity_kts"].mean()

    # Calculate distance
    from math import asin, cos, radians, sin, sqrt

    total_dist = 0
    for i in range(len(df) - 1):
        lat1, lon1 = radians(df["Latitude"].iloc[i]), radians(df["Longitude"].iloc[i])
        lat2, lon2 = radians(df["Latitude"].iloc[i + 1]), radians(df["Longitude"].iloc[i + 1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        total_dist += 6371 * c  # km

    stats_text = f"""
FLIGHT STATISTICS

Callsign: {callsign}
ICAO: {df['ICAO'].iloc[0]}

Duration: {duration:.1f} minutes
Data Points: {len(df)}

ALTITUDE
  Start: {df['Altitude_ft'].iloc[0]:,.0f} ft
  End: {df['Altitude_ft'].iloc[-1]:,.0f} ft
  Gain: {alt_gain:,.0f} ft
  Avg Climb: {avg_climb:.0f} ft/min

SPEED
  Max: {max_speed:.0f} kts
  Average: {avg_speed:.0f} kts

DISTANCE
  Total: {total_dist:.1f} km ({total_dist * 0.539957:.1f} nm)
  
POSITION
  Start: {df['Latitude'].iloc[0]:.4f}°, {df['Longitude'].iloc[0]:.4f}°
  End: {df['Latitude'].iloc[-1]:.4f}°, {df['Longitude'].iloc[-1]:.4f}°
    """

    ax6.text(
        0.1,
        0.95,
        stats_text,
        transform=ax6.transAxes,
        fontsize=10,
        verticalalignment="top",
        family="monospace",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.3},
    )

    plt.tight_layout()

    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"✅ Visualization saved to: {output_file}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize flight track data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize and display
  python visualize_track.py example_ual2212_track.csv
  
  # Save to file
  python visualize_track.py example_ual2212_track.csv -o flight_analysis.png
  
  # Visualize your own track
  python visualize_track.py my_track.csv -o my_analysis.png
        """,
    )

    parser.add_argument("csv_file", type=Path, help="Input CSV file with flight track data")
    parser.add_argument("-o", "--output", type=Path, help="Output PNG file (default: show plot)")

    args = parser.parse_args()

    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)

    plot_track(args.csv_file, args.output)


if __name__ == "__main__":
    main()
