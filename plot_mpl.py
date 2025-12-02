#!/usr/bin/env python3
"""Generate flight route visualization using Matplotlib and Cartopy.

This script creates beautiful flight route visualizations using modern mapping libraries.
Basemap has been deprecated, so this version uses Cartopy instead.
"""

import argparse
import logging
from pathlib import Path
from typing import Literal

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import pandas as pd
import yaml
from matplotlib.colors import LinearSegmentedColormap, PowerNorm


def load_config(config_path: Path | None = None) -> dict:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default config.yaml
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent / 'config.yaml'
    
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


def setup_logging(config: dict) -> None:
    """Configure logging based on config settings."""
    log_config = config.get('logging', {})
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(levelname)s: %(message)s')
    )


def plot_map(
    in_filename: str | Path,
    out_filename: str | Path,
    config: dict,
    color_mode: Literal['screen', 'print'] | None = None,
    absolute: bool | None = None
) -> None:
    """Plot flight routes on a world map and save as PNG.

    Args:
        in_filename: Path to CSV file containing flight data
        out_filename: Output image filename
        config: Configuration dictionary
        color_mode: 'screen' for on-screen display, 'print' for printer-friendly colors
        absolute: If True, color scale depends on dataset values (useful for comparison)
    """
    logger = logging.getLogger(__name__)
    
    # Get settings from config
    viz_config = config.get('visualization', {})
    output_config = config.get('output', {})
    data_config = config.get('data', {})
    color_schemes = config.get('color_schemes', {})
    
    # Use CLI args or fall back to config
    color_mode = color_mode or viz_config.get('color_mode', 'screen')
    absolute = absolute if absolute is not None else viz_config.get('absolute_scaling', False)
    
    # Get color scheme
    scheme = color_schemes.get(color_mode, {})
    bg_color = tuple(scheme.get('background', [0.0, 0.0, 0, 1.0]))
    coast_color = tuple(scheme.get('coastline', [204/255.0, 0, 153/255.0, 0.7]))
    color_list = [tuple(c) for c in scheme.get('gradient', [
        [0.0, 0.0, 0.0, 0.0],
        [204/255.0, 0, 153/255.0, 0.6],
        [255/255.0, 204/255.0, 230/255.0, 1.0]
    ])]

    # Define CSV columns
    csv_cols = data_config.get('columns', [
        'dep_lat', 'dep_lon', 'arr_lat', 'arr_lon', 'nb_flights', 'CO2'
    ])

    # Load data
    logger.info(f"Loading data from {in_filename}")
    routes = pd.read_csv(
        in_filename,
        names=csv_cols,
        na_values=['\\N'],
        sep=data_config.get('separator', ';'),
        skiprows=1
    )

    num_routes = len(routes)
    logger.info(f"Loaded {num_routes} flight routes")

    # Normalize dataset for color scale
    gamma = config.get('power_norm_gamma', 0.3)
    norm = PowerNorm(
        gamma=gamma,
        vmin=routes['nb_flights'].min(),
        vmax=routes['nb_flights'].max()
    )

    # Create linear color scale
    n = routes['nb_flights'].max() if absolute else num_routes
    cmap = LinearSegmentedColormap.from_list('cmap_flights', color_list, N=n)

    # Get figure settings
    fig_size = viz_config.get('figure_size', {})
    width = fig_size.get('width', 27)
    height = fig_size.get('height', 20)
    
    # Create figure with Cartopy projection
    logger.info("Creating map...")
    plt.figure(figsize=(width, height))
    ax = plt.axes(projection=ccrs.Miller())
    
    # Set map extent (global view)
    ax.set_global()
    
    # Add map features
    ax.add_feature(cfeature.COASTLINE, color=coast_color, linewidth=1.0)
    ax.add_feature(cfeature.LAND, facecolor=bg_color)
    ax.add_feature(cfeature.OCEAN, facecolor=bg_color)
    
    # Set background color
    ax.background_patch.set_facecolor(bg_color)

    # Get visualization settings
    line_width = viz_config.get('line_width', 0.5)
    alpha = viz_config.get('alpha', 0.8)

    # Plot each route
    logger.info("Drawing routes...")
    for i, (_, route) in enumerate(routes.sort_values(by='nb_flights', ascending=True).iterrows()):
        color = cmap(norm(int(route['nb_flights']))) if absolute else cmap(i * 1.0 / num_routes)
        
        # Draw great circle route
        ax.plot(
            [route['dep_lon'], route['arr_lon']],
            [route['dep_lat'], route['arr_lat']],
            color=color,
            linewidth=line_width,
            transform=ccrs.Geodetic(),
            alpha=alpha
        )

    # Save map
    dpi = output_config.get('dpi', 150)
    logger.info(f"Saving map to {out_filename}...")
    plt.savefig(out_filename, format='png', bbox_inches='tight', dpi=dpi)
    plt.close()
    logger.info("Map saved successfully!")


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Generate flight route visualization using Matplotlib and Cartopy'
    )
    parser.add_argument(
        '-i', '--input',
        type=Path,
        help='Input CSV file (default: data.csv)'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output PNG file (default: flights_map_mpl.png)'
    )
    parser.add_argument(
        '-c', '--config',
        type=Path,
        help='Configuration YAML file (default: config.yaml)'
    )
    parser.add_argument(
        '--color-mode',
        choices=['screen', 'print'],
        help='Color scheme: screen or print'
    )
    parser.add_argument(
        '--absolute',
        action='store_true',
        help='Use absolute color scaling based on flight counts'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        help='Output image DPI'
    )
    parser.add_argument(
        '--width',
        type=float,
        help='Figure width in inches'
    )
    parser.add_argument(
        '--height',
        type=float,
        help='Figure height in inches'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override log level if verbose
    if args.verbose:
        config.setdefault('logging', {})['level'] = 'DEBUG'
    
    setup_logging(config)
    
    # Determine input/output files
    if args.input:
        input_file = args.input
    else:
        input_file = Path(config.get('data', {}).get('filepath', 'data.csv'))
        if not input_file.is_absolute():
            input_file = Path(__file__).parent / input_file
    
    if args.output:
        output_file = args.output
    else:
        output_file = Path(
            config.get('output', {}).get('matplotlib_filename', 'flights_map_mpl.png')
        )
        if not output_file.is_absolute():
            output_file = Path(__file__).parent / output_file
    
    # Override config with CLI arguments
    if args.dpi:
        config.setdefault('output', {})['dpi'] = args.dpi
    if args.width:
        config.setdefault('visualization', {}).setdefault('figure_size', {})['width'] = args.width
    if args.height:
        config.setdefault('visualization', {}).setdefault('figure_size', {})['height'] = args.height
    
    # Generate the map
    plot_map(
        input_file,
        output_file,
        config,
        color_mode=args.color_mode,
        absolute=args.absolute
    )


if __name__ == '__main__':
    main()
