#!/usr/bin/env python3
"""
Cleanup script to fix issues caused by the backfill process:
1. Restore Unicode characters (remove escapes)
2. Remove bad player entries
3. Fix venue names
"""

import json
import re
from pathlib import Path

def fix_unicode_escapes(text):
    """Convert Unicode escapes back to proper characters"""
    # Common Spanish characters
    unicode_map = {
        '\\u00e1': 'á',  # á
        '\\u00e9': 'é',  # é  
        '\\u00ed': 'í',  # í
        '\\u00f1': 'ñ',  # ñ
        '\\u00f3': 'ó',  # ó
        '\\u00fa': 'ú',  # ú
        '\\u00c1': 'Á',  # Á
        '\\u00c9': 'É',  # É
        '\\u00cd': 'Í',  # Í
        '\\u00d1': 'Ñ',  # Ñ
        '\\u00d3': 'Ó',  # Ó
        '\\u00da': 'Ú',  # Ú
    }
    
    for escape, char in unicode_map.items():
        text = text.replace(escape, char)
    
    return text

def cleanup_file(file_path):
    """Clean up a single JSON file"""
    print(f"🔧 Cleaning up {file_path}")
    
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix Unicode escapes
    original_content = content
    content = fix_unicode_escapes(content)
    
    if content != original_content:
        print(f"  ✅ Fixed Unicode escapes")
    
    # Parse JSON
    data = json.loads(content)
    
    # Remove bad player entries
    original_player_count = len(data.get('players', []))
    if 'players' in data:
        data['players'] = [
            player for player in data['players']
            if not (player.get('name') == '0' and player.get('team') == 'GAM')
        ]
    
    removed_count = original_player_count - len(data.get('players', []))
    if removed_count > 0:
        print(f"  ✅ Removed {removed_count} bad player entries")
    
    # Fix venue names that were changed incorrectly
    venue_fixes = {
        'Rate Field': 'Guaranteed Rate Field',  # Chicago White Sox correct name
        'Oriole Park at Camden Yards': 'Oriole Park at Camden Yards',  # This is correct
        'Bristol Motor Speedway': 'Bristol Motor Speedway',  # This is correct
    }
    
    fixed_venues = 0
    for game in data.get('games', []):
        if game.get('venue') in venue_fixes:
            old_venue = game['venue']
            game['venue'] = venue_fixes[old_venue]
            if old_venue != game['venue']:
                print(f"  ✅ Fixed venue: {old_venue} → {game['venue']}")
                fixed_venues += 1
    
    # Write back with proper encoding
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ File cleaned successfully")
    return True

def main():
    """Main cleanup function"""
    files_to_clean = [
        '/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballData/data/2025/july/july_29_2025.json',
        '/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballData/data/2025/july/july_11_2025.json',
        '/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballData/data/2025/august/august_02_2025.json'
    ]
    
    print("🚀 Starting cleanup of backfill issues...")
    
    for file_path in files_to_clean:
        if Path(file_path).exists():
            cleanup_file(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("✅ Cleanup completed!")

if __name__ == '__main__':
    main()