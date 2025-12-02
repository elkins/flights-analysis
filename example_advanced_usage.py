"""
Example script demonstrating advanced usage of the flights analysis tools.

This script shows how to:
1. Load and customize configurations programmatically
2. Use the plotting functions as library imports
3. Create custom visualizations
4. Batch process multiple configurations
"""

from pathlib import Path
from typing import Literal

import yaml

# Import the plotting functions
from plot_gcmap import generate_map as generate_gcmap
from plot_mpl import plot_map


def create_custom_config(output_name: str, color_mode: str = "screen") -> dict:
    """Create a custom configuration dictionary.
    
    Args:
        output_name: Base name for output files
        color_mode: Color scheme to use
        
    Returns:
        Configuration dictionary
    """
    return {
        "output": {
            "directory": "outputs",
            "dpi": 300,
            "gcmap_filename": f"{output_name}_gcmap.png",
            "matplotlib_filename": f"{output_name}_mpl.png",
        },
        "data": {
            "filepath": "data.csv",
            "separator": ";",
        },
        "visualization": {
            "color_mode": color_mode,
            "figure_size": {"width": 30, "height": 20},
            "line_width": 0.5,
            "alpha": 0.8,
        },
        "logging": {
            "level": "INFO",
        },
    }


def batch_generate_maps():
    """Generate multiple map variants with different settings."""
    # Create output directory
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    data_file = Path(__file__).parent / "data.csv"
    
    # Define configurations
    configs: list[tuple[str, Literal["screen", "print"], bool]] = [
        ("screen_normal", "screen", False),
        ("screen_absolute", "screen", True),
        ("print_normal", "print", False),
        ("print_absolute", "print", True),
    ]
    
    print("Generating multiple map variants...")
    print("=" * 60)
    
    for name, color_mode, absolute in configs:
        print(f"\nGenerating {name} variant...")
        
        # Create config
        config = create_custom_config(name, color_mode)
        
        # Update paths
        output_file = output_dir / f"{name}_mpl.png"
        
        # Generate map
        plot_map(
            data_file,
            output_file,
            config,
            color_mode=color_mode,
            absolute=absolute
        )
        
        print(f"  ✓ Saved to {output_file}")
    
    print("\n" + "=" * 60)
    print(f"All maps generated successfully in {output_dir}")


def save_custom_config_example():
    """Save an example custom configuration file."""
    config = {
        "output": {
            "directory": ".",
            "dpi": 300,
            "format": "png",
        },
        "data": {
            "filepath": "data.csv",
            "separator": ";",
        },
        "visualization": {
            "color_mode": "screen",
            "absolute_scaling": False,
            "figure_size": {"width": 40, "height": 25},
            "line_width": 0.3,
            "alpha": 0.9,
        },
        "color_schemes": {
            "custom": {
                "background": [0.05, 0.05, 0.1, 1.0],
                "coastline": [0.0, 0.8, 1.0, 0.8],
                "gradient": [
                    [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.8, 1.0, 0.6],
                    [0.0, 1.0, 1.0, 1.0],
                ],
            }
        },
        "power_norm_gamma": 0.5,
        "logging": {
            "level": "DEBUG",
        },
    }
    
    output_file = Path(__file__).parent / "custom_config_example.yaml"
    
    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Custom configuration example saved to {output_file}")


def main():
    """Main demonstration function."""
    print("Flights Analysis - Advanced Usage Examples")
    print("=" * 60)
    
    # Example 1: Save custom config
    print("\n1. Creating custom configuration file...")
    save_custom_config_example()
    
    # Example 2: Batch generate maps
    print("\n2. Batch generating maps with different settings...")
    batch_generate_maps()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nTo use the custom config:")
    print("  python plot_mpl.py -c custom_config_example.yaml")


if __name__ == "__main__":
    main()
