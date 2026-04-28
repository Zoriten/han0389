"""
Configuration module for the landscape retention estimation tool.

This file defines all global parameters:
- project paths
- coordinate reference system
- raster resolution
- rainfall input for the SCS Curve Number method
"""

from dataclasses import dataclass
from pathlib import Path

# The configuration structure is implemented as a dataclass.
# It stores:
# - base project directory
# - paths to raw, processed and result data folders
# - CRS (EPSG code)
# - raster resolution in meters
# - rainfall depth in millimeters


@dataclass
class Config:
	base_dir: Path
	data_raw_dir: Path
	data_processed_dir: Path
	data_results_dir: Path
	crs_epsg: int
	raster_resolution: int
	rainfall_mm: float


def load_default_config() -> Config:
	base_dir = Path(__file__).resolve().parent

	return Config(
		base_dir=base_dir,
		data_raw_dir=base_dir / "data" / "raw",
		data_processed_dir=base_dir / "data" / "processed",
		data_results_dir=base_dir / "data" / "results",
		crs_epsg=5514,
		raster_resolution=10,
		rainfall_mm=30.0,
	)
