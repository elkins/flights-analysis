#!/usr/bin/env python3
"""Generate flight route visualization using GCMapper."""

import argparse
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from gcmap import GCMapper, Gradient


def load_config(config_path: Optional[Path] = None) -> dict:
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


def generate_map(
    input_file: Path,
    output_file: Path,
    config: dict
) -> None:
    """Generate flight map visualization from CSV data.
    
    Args:
        input_file: Path to CSV data file
        output_file: Path for output image
        config: Configuration dictionary
    """
    logger = logging.getLogger(__name__)
    
    # Get settings from config
    data_config = config.get('data', {})
    gcmap_config = config.get('gcmap', {})
    
    csv_cols = data_config.get('columns', [
        'dep_lat', 'dep_lon', 'arr_lat', 'arr_lon', 'nb_flights', 'CO2'
    ])
    
    # Load data
    logger.info(f"Loading data from {input_file}")
    routes = pd.read_csv(
        input_file,
        names=csv_cols,
        na_values=['\\N'],
        sep=data_config.get('separator', ';'),
        skiprows=1
    )
    
    logger.info(f"Loaded {len(routes)} flight routes")
    
    # Create gradient from config
    gradient_config = gcmap_config.get('gradient', [
        {'position': 0, 'color': [0, 0, 0, 0]},
        {'position': 0.5, 'color': [204, 0, 153, 0.6]},
        {'position': 1, 'color': [255, 204, 230, 1.0]}
    ])
    
    gradient_tuples = tuple(
        (g['position'], *g['color']) for g in gradient_config
    )
    grad = Gradient(gradient_tuples)
    
    # Initialize GCMapper
    height = gcmap_config.get('height', 2000)
    width = gcmap_config.get('width', 4000)
    gcm = GCMapper(cols=grad, height=height, width=width)
    
    gcm.set_data(
        routes['dep_lon'],
        routes['dep_lat'],
        routes['arr_lon'],
        routes['arr_lat'],
        routes['nb_flights']
    )
    
    # Generate and save map
    logger.info("Generating map...")
    img = gcm.draw()
    img.save(output_file)
    logger.info(f"Map saved to {output_file}")


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Generate flight route visualization using GCMapper'
    )
    parser.add_argument(
        '-i', '--input',
        type=Path,
        help='Input CSV file (default: data.csv)'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output PNG file (default: flights_map_gcmap.png)'
    )
    parser.add_argument(
        '-c', '--config',
        type=Path,
        help='Configuration YAML file (default: config.yaml)'
    )
    parser.add_argument(
        '--width',
        type=int,
        help='Map width in pixels'
    )
    parser.add_argument(
        '--height',
        type=int,
        help='Map height in pixels'
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
        output_file = Path(config.get('output', {}).get('gcmap_filename', 'flights_map_gcmap.png'))
        if not output_file.is_absolute():
            output_file = Path(__file__).parent / output_file
    
    # Override config with CLI arguments
    if args.width:
        config.setdefault('gcmap', {})['width'] = args.width
    if args.height:
        config.setdefault('gcmap', {})['height'] = args.height
    
    # Generate the map
    generate_map(input_file, output_file, config)


if __name__ == '__main__':
    main()
