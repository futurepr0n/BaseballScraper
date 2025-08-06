"""
Centralized data path configuration for BaseballScraper
This configuration enables all scraper scripts to use centralized data storage in BaseballData
instead of referencing BaseballTracker's directories
"""

import os
from pathlib import Path

# Determine environment
IS_PRODUCTION = os.environ.get('NODE_ENV') == 'production' or os.path.exists('/app')

# Get the base directory of BaseballScraper
SCRAPER_DIR = Path(__file__).parent

# Environment-aware data path resolution
def get_data_path():
    """Get the centralized data path from environment or defaults"""
    # First check for explicit environment variable
    if env_path := os.environ.get('BASEBALL_DATA_PATH'):
        return Path(env_path).resolve()
    
    # Fallback to defaults based on environment
    if IS_PRODUCTION:
        return Path('/app/BaseballData/data')
    else:
        # Development fallback - relative to BaseballScraper
        return SCRAPER_DIR.parent / 'BaseballData' / 'data'

# Base data path using environment-aware resolution
DATA_PATH = get_data_path()

# Ensure data path exists
DATA_PATH.mkdir(parents=True, exist_ok=True)

# Define specific data subdirectories
PATHS = {
    'data': DATA_PATH,
    'predictions': DATA_PATH / 'predictions',
    'stats': DATA_PATH / 'stats',
    'rolling_stats': DATA_PATH / 'rolling_stats',
    'team_stats': DATA_PATH / 'team_stats',
    'rosters': DATA_PATH / 'rosters.json',
    'odds': DATA_PATH / 'odds',
    'lineups': DATA_PATH / 'lineups',
    'hellraiser': DATA_PATH / 'hellraiser',
    'injuries': DATA_PATH / 'injuries',
    'handedness': DATA_PATH / 'handedness',
    'stadium': DATA_PATH / 'stadium',
    'multi_hit_stats': DATA_PATH / 'multi_hit_stats',
    'scanned': DATA_PATH.parent / 'SCANNED',  # Centralized processed schedule files
    'csv_backups': DATA_PATH.parent / 'CSV_BACKUPS',  # Centralized CSV backup files
}

# Legacy paths for backward compatibility (will be removed after migration)
LEGACY_PATHS = {
    'tracker_public': SCRAPER_DIR.parent / 'BaseballTracker' / 'public' / 'data',
    'tracker_build': SCRAPER_DIR.parent / 'BaseballTracker' / 'build' / 'data',
}

# Utility functions
def get_data_path(*segments):
    """Get a path within the data directory"""
    return DATA_PATH.joinpath(*segments)

def get_game_data_path(year, month=None, day=None):
    """Get path for game data files"""
    if month and day:
        month_name = month if isinstance(month, str) else get_month_name(month)
        filename = f"{month_name}_{day:02d}_{year}.json"
        return DATA_PATH / str(year) / month_name / filename
    elif month:
        month_name = month if isinstance(month, str) else get_month_name(month)
        return DATA_PATH / str(year) / month_name
    else:
        return DATA_PATH / str(year)

def get_month_name(month_num):
    """Convert month number to name"""
    months = ['', 'january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december']
    return months[month_num] if 1 <= month_num <= 12 else ''

def ensure_dir(path):
    """Ensure a directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

# For scripts that write to multiple locations (dev/prod sync)
def get_output_dirs(subpath=''):
    """
    Get both development and production output directories
    During migration, this returns the centralized path twice
    After migration, scripts can be updated to use single path
    """
    base_path = DATA_PATH / subpath if subpath else DATA_PATH
    return [str(base_path), str(base_path)]  # Same path for both

# Debug information
if __name__ == "__main__":
    print(f"BaseballScraper Configuration:")
    print(f"  Environment: {'Production' if IS_PRODUCTION else 'Development'}")
    print(f"  Data Path: {DATA_PATH}")
    print(f"  Data Path Exists: {DATA_PATH.exists()}")
    print(f"  Key Paths:")
    for name, path in PATHS.items():
        print(f"    {name}: {path}")