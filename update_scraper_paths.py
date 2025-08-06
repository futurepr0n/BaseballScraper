#!/usr/bin/env python3
"""
Script to update BaseballScraper Python scripts to use centralized data configuration
"""

import os
import re
from pathlib import Path

# Import the new configuration
from config import DATA_PATH, PATHS, get_data_path, get_output_dirs

def update_python_file(file_path):
    """Update a Python file to use the new centralized configuration"""
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already using config
    if 'from config import' in content or 'import config' in content:
        print(f"  ✓ {file_path.name} - already using config")
        return False
    
    # Patterns to replace
    replacements = [
        # BaseballTracker paths
        (r'["\']\.\.\/BaseballTracker\/public\/data\/odds["\']', 'config.PATHS["odds"]'),
        (r'["\']\.\.\/BaseballTracker\/build\/data\/odds["\']', 'config.PATHS["odds"]'),
        (r'["\']\.\.\/BaseballTracker\/public\/data\/lineups["\']', 'config.PATHS["lineups"]'),
        (r'["\']\.\.\/BaseballTracker\/public\/data\/rosters\.json["\']', 'config.PATHS["rosters"]'),
        (r'["\']\.\.\/BaseballTracker\/public\/data\/hellraiser["\']', 'config.PATHS["hellraiser"]'),
        (r'["\']\.\.\/BaseballTracker\/public\/data\/injuries["\']', 'config.PATHS["injuries"]'),
        (r'["\']\.\.\/BaseballTracker\/public\/data["\']', 'str(config.DATA_PATH)'),
        (r'["\']\.\.\/BaseballTracker\/build\/data["\']', 'str(config.DATA_PATH)'),
        
        # For scripts that write to both directories
        (r'output_dirs\s*=\s*\[[^\]]+\]', 'output_dirs = config.get_output_dirs()'),
    ]
    
    # Track if we made changes
    modified = False
    original_content = content
    
    # Apply replacements
    for pattern, replacement in replacements:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    # If we made changes, add import at the top
    if modified:
        # Find the right place to add import (after other imports)
        import_lines = []
        other_lines = []
        
        for line in content.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                import_lines.append(line)
            else:
                other_lines.append(line)
        
        # Add our import
        import_lines.append('import config')
        
        # Reconstruct file
        content = '\n'.join(import_lines) + '\n' + '\n'.join(other_lines)
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"  ✓ {file_path.name} - updated with config imports")
        return True
    
    print(f"  - {file_path.name} - no hardcoded paths found")
    return False

def main():
    """Update all Python files in BaseballScraper"""
    print("Updating BaseballScraper Python scripts to use centralized configuration...")
    print()
    
    # Get all Python files
    scraper_dir = Path(__file__).parent
    python_files = list(scraper_dir.glob('*.py'))
    
    # Skip this script and config.py
    python_files = [f for f in python_files if f.name not in ['update_scraper_paths.py', 'config.py']]
    
    updated_count = 0
    
    # High priority files to update first
    priority_files = [
        'enhanced_comprehensive_hellraiser.py',
        'odds-scrape.py',
        'daily_hellraiser_scheduler.py',
        'lineup_scheduler.py',
        'fetch_starting_lineups.py',
        'enhanced_lineup_scraper.py',
        'roster_enhancement_tool.py',
        'injury_scrape.py',
    ]
    
    print("Updating high-priority files:")
    for filename in priority_files:
        file_path = scraper_dir / filename
        if file_path.exists():
            if update_python_file(file_path):
                updated_count += 1
    
    print("\nUpdating remaining files:")
    for file_path in python_files:
        if file_path.name not in priority_files:
            if update_python_file(file_path):
                updated_count += 1
    
    print(f"\nSummary: Updated {updated_count} files")
    
    # Show example usage
    if updated_count > 0:
        print("\nExample usage in updated files:")
        print("  from config import DATA_PATH, PATHS")
        print("  odds_dir = PATHS['odds']")
        print("  roster_path = PATHS['rosters']")
        print("  output_dirs = get_output_dirs('odds')")

if __name__ == "__main__":
    main()