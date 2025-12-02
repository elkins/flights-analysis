#!/usr/bin/env python3
"""
Visualize tracked flight data - Simple version using only matplotlib.

Usage:
    python visualize_track_simple.py example_ual2212_track.csv
    python visualize_track_simple.py my_track.csv -o my_plot.png
"""

import argparse
import sys
import csv
from pathlib import Path
from datetime import datetime
from math import radians, sin, cos, asin, sqrt

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    print("Error: matplotlib not found. Install with: pip install matplotlib")
    sys.exit(1)


def plot_track(csv_file: Path, output_file=None):
    """Create visualization plots for flight track."""
    
    # Read CSV manually
    data = {
        'Timestamp': [],
        'Callsign': [],
        'ICAO': [],
        'Latitude': [],
        'Longitude': [],
        'Altitude_ft': [],
        'Velocity_kts': [],
        'VertRate_fpm': []
    }
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['Timestamp'].append(datetime.fromisoformat(row['Timestamp']))
            data['Callsign'].append(row['Callsign'])
            data['ICAO'].append(row['ICAO'])
            data['Latitude'].append(float(row['Latitude']))
            data['Longitude'].append(float(row['Longitude']))
            data['Altitude_ft'].append(float(row['Altitude_ft']))
            data['Velocity_kts'].append(float(row['Velocity_kts']) if row['Velocity_kts'] else 0)
            data['VertRate_fpm'].append(float(row['VertRate_fpm']) if row['VertRate_fpm'] else 0)
    
    callsign = data['Callsign'][0]
    n_points = len(data['Timestamp'])
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(f'Flight Track Analysis: {callsign}', fontsize=16, fontweight='bold')
    
    # 1. Flight Path (Map View)
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(data['Longitude'], data['Latitude'], 'b-', linewidth=2, marker='o', markersize=6)
    ax1.plot(data['Longitude'][0], data['Latitude'][0], 'go', markersize=12, label='Start')
    ax1.plot(data['Longitude'][-1], data['Latitude'][-1], 'ro', markersize=12, label='End')
    ax1.set_xlabel('Longitude', fontsize=11)
    ax1.set_ylabel('Latitude', fontsize=11)
    ax1.set_title('Flight Path (Geographic)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. Altitude Profile
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(data['Timestamp'], data['Altitude_ft'], 'b-', linewidth=2, marker='o')
    ax2.set_xlabel('Time', fontsize=11)
    ax2.set_ylabel('Altitude (feet)', fontsize=11)
    ax2.set_title('Altitude Profile', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Speed Profile
    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(data['Timestamp'], data['Velocity_kts'], 'g-', linewidth=2, marker='o')
    ax3.set_xlabel('Time', fontsize=11)
    ax3.set_ylabel('Ground Speed (knots)', fontsize=11)
    ax3.set_title('Speed Profile', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Vertical Rate
    ax4 = plt.subplot(2, 3, 4)
    vert_rates = [v for v in data['VertRate_fpm'] if v != 0]
    if vert_rates:
        colors = ['green' if v > 0 else 'red' for v in data['VertRate_fpm']]
        ax4.bar(data['Timestamp'], data['VertRate_fpm'], color=colors, alpha=0.7, width=0.0003)
        ax4.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax4.set_xlabel('Time', fontsize=11)
        ax4.set_ylabel('Vertical Rate (ft/min)', fontsize=11)
        ax4.set_title('Climb/Descent Rate', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        ax4.text(0.5, 0.5, 'No vertical rate data', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Climb/Descent Rate', fontsize=12, fontweight='bold')
    
    # 5. Speed vs Altitude
    ax5 = plt.subplot(2, 3, 5)
    colors = plt.cm.viridis([i/n_points for i in range(n_points)])
    ax5.scatter(data['Altitude_ft'], data['Velocity_kts'], c=colors, s=100, alpha=0.6, 
                edgecolors='black', linewidth=0.5)
    ax5.set_xlabel('Altitude (feet)', fontsize=11)
    ax5.set_ylabel('Ground Speed (knots)', fontsize=11)
    ax5.set_title('Speed vs Altitude (colored by time)', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # 6. Flight Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    # Calculate statistics
    duration = (data['Timestamp'][-1] - data['Timestamp'][0]).total_seconds() / 60
    alt_gain = data['Altitude_ft'][-1] - data['Altitude_ft'][0]
    avg_climb = alt_gain / duration if duration > 0 else 0
    max_speed = max(data['Velocity_kts'])
    avg_speed = sum(data['Velocity_kts']) / len(data['Velocity_kts'])
    
    # Calculate distance
    total_dist = 0
    for i in range(len(data['Latitude']) - 1):
        lat1, lon1 = radians(data['Latitude'][i]), radians(data['Longitude'][i])
        lat2, lon2 = radians(data['Latitude'][i+1]), radians(data['Longitude'][i+1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        total_dist += 6371 * c  # km
    
    stats_text = f"""FLIGHT STATISTICS

Callsign: {callsign}
ICAO: {data['ICAO'][0]}

Duration: {duration:.1f} minutes
Data Points: {n_points}

ALTITUDE
  Start: {data['Altitude_ft'][0]:,.0f} ft
  End: {data['Altitude_ft'][-1]:,.0f} ft
  Gain: {alt_gain:,.0f} ft
  Avg Climb: {avg_climb:.0f} ft/min

SPEED
  Max: {max_speed:.0f} kts
  Average: {avg_speed:.0f} kts

DISTANCE
  Total: {total_dist:.1f} km
         {total_dist * 0.539957:.1f} nm

POSITION
  Start: {data['Latitude'][0]:.4f}°
         {data['Longitude'][0]:.4f}°
  End:   {data['Latitude'][-1]:.4f}°
         {data['Longitude'][-1]:.4f}°
    """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes, 
             fontsize=9, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✅ Visualization saved to: {output_file}")
        print(f"\n📊 Quick Stats:")
        print(f"   Duration: {duration:.1f} min")
        print(f"   Altitude: {data['Altitude_ft'][0]:,.0f} → {data['Altitude_ft'][-1]:,.0f} ft")
        print(f"   Distance: {total_dist:.1f} km ({total_dist * 0.539957:.1f} nm)")
        print(f"   Avg Speed: {avg_speed:.0f} kts")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Visualize flight track data (simple version)',
        epilog='Examples:\n'
               '  python visualize_track_simple.py example_ual2212_track.csv\n'
               '  python visualize_track_simple.py my_track.csv -o analysis.png',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('csv_file', type=Path, help='Input CSV file with flight track data')
    parser.add_argument('-o', '--output', type=Path, help='Output PNG file (default: show plot)')
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    plot_track(args.csv_file, args.output)


if __name__ == '__main__':
    main()
