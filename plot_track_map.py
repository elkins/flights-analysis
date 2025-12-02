#!/usr/bin/env python3
"""Visualize flight track on a map using Cartopy.

This script plots a single flight's path on a map, showing the geographic route
with altitude information color-coded along the path.
"""

import argparse
import csv
import logging
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def plot_track_on_map(
    track_file: Path, output_file: Path, title: str | None = None, zoom: bool = True
) -> None:
    """Plot flight track on a map.

    Args:
        track_file: CSV file with flight track data
        output_file: Output PNG filename
        title: Optional custom title
        zoom: If True, zoom to track bounds; if False, show full USA
    """
    logger = logging.getLogger(__name__)

    # Read track data
    logger.info(f"Loading track from {track_file}")
    lats, lons, alts, times, callsign = [], [], [], [], None

    with open(track_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not callsign:
                callsign = row.get("Callsign", "Unknown")

            lats.append(float(row["Latitude"]))
            lons.append(float(row["Longitude"]))

            # Prefer altitude in feet
            if "Altitude_ft" in row and row["Altitude_ft"]:
                alts.append(float(row["Altitude_ft"]))
            elif "Altitude_m" in row and row["Altitude_m"]:
                alts.append(float(row["Altitude_m"]) * 3.28084)
            else:
                alts.append(0)

            times.append(row["Timestamp"])

    logger.info(f"Loaded {len(lats)} track points for {callsign}")

    if len(lats) < 2:
        logger.error("Need at least 2 points to plot a track")
        return

    # Convert to numpy arrays
    lats = np.array(lats)
    lons = np.array(lons)
    alts = np.array(alts)

    # Create figure
    fig = plt.figure(figsize=(16, 12))

    # Use PlateCarree for USA-focused view
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Set map extent
    if zoom:
        # Zoom to track with padding
        lat_padding = (lats.max() - lats.min()) * 0.2 or 1
        lon_padding = (lons.max() - lons.min()) * 0.2 or 1
        ax.set_extent(
            [
                lons.min() - lon_padding,
                lons.max() + lon_padding,
                lats.min() - lat_padding,
                lats.max() + lat_padding,
            ]
        )
    else:
        # Show USA
        ax.set_extent([-125, -65, 24, 50])

    # Add map features
    ax.add_feature(cfeature.LAND, facecolor="#f0f0f0", zorder=0)
    ax.add_feature(cfeature.OCEAN, facecolor="#d0e8f0", zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="#666666", zorder=1)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="#999999", zorder=1)
    ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor="#aaaaaa", zorder=1)

    # Add gridlines
    gl = ax.gridlines(
        draw_labels=True, linewidth=0.5, color="gray", alpha=0.3, linestyle="--", zorder=2
    )
    gl.top_labels = False
    gl.right_labels = False

    # Color-code by altitude
    # Create colormap from blue (low) to red (high)
    colors = ["#0066cc", "#00ccff", "#00ff00", "#ffff00", "#ff6600", "#cc0000"]
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list("altitude", colors, N=n_bins)

    # Normalize altitude for colormap
    alt_min, alt_max = alts.min(), alts.max()
    if alt_max > alt_min:
        alt_norm = (alts - alt_min) / (alt_max - alt_min)
    else:
        alt_norm = np.zeros_like(alts)

    # Plot track segments with altitude coloring
    for i in range(len(lats) - 1):
        color = cmap(alt_norm[i])
        ax.plot(
            [lons[i], lons[i + 1]],
            [lats[i], lats[i + 1]],
            color=color,
            linewidth=2,
            transform=ccrs.Geodetic(),
            zorder=3,
        )

    # Mark start and end points
    ax.plot(
        lons[0],
        lats[0],
        marker="o",
        markersize=12,
        color="green",
        markeredgecolor="white",
        markeredgewidth=2,
        transform=ccrs.PlateCarree(),
        zorder=4,
        label="Start",
    )
    ax.plot(
        lons[-1],
        lats[-1],
        marker="o",
        markersize=12,
        color="red",
        markeredgecolor="white",
        markeredgewidth=2,
        transform=ccrs.PlateCarree(),
        zorder=4,
        label="End",
    )

    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=alt_min, vmax=alt_max))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("Altitude (feet)", fontsize=12, fontweight="bold")

    # Add legend
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)

    # Add title with flight info
    if title:
        title_text = title
    else:
        title_text = f"Flight Track: {callsign}"
        if alt_max > 0:
            title_text += f" | Altitude: {int(alt_min):,} - {int(alt_max):,} ft"
        title_text += f" | {len(lats)} points"

    ax.set_title(title_text, fontsize=14, fontweight="bold", pad=20)

    # Add timestamp info
    fig.text(
        0.5, 0.02, f"Time: {times[0]} to {times[-1]}", ha="center", fontsize=10, style="italic"
    )

    # Save figure
    logger.info(f"Saving map to {output_file}")
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Map saved successfully! ({output_file.stat().st_size // 1024} KB)")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Visualize flight track on a map")
    parser.add_argument("track_file", type=Path, help="Input CSV file with flight track data")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output PNG file (default: <trackfile>_map.png)"
    )
    parser.add_argument("--title", help="Custom title for the map")
    parser.add_argument(
        "--usa", action="store_true", help="Show full USA map instead of zooming to track"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        output_file = args.track_file.with_name(args.track_file.stem + "_map.png")

    plot_track_on_map(args.track_file, output_file, title=args.title, zoom=not args.usa)


if __name__ == "__main__":
    main()
