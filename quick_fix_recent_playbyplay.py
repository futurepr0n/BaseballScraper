#!/usr/bin/env python3
"""
Quick fix: Update only recent play-by-play files needed for current analysis
"""

import os
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from playbyplay_scraper import extract_playbyplay_data_from_api
import re

def extract_game_id_from_filename(filename):
    """Extract game ID from filename"""
    match = re.search(r'_(\d+)\.json$', filename)
    return match.group(1) if match else None

def is_recent_file(filename, days=30):
    """Check if file is from recent games (last N days)"""
    try:
        # Extract date from filename
        date_match = re.search(r'(\w+)_(\d{1,2})_(\d{4})', filename)
        if not date_match:
            return False
        
        month_name, day, year = date_match.groups()
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month = month_map.get(month_name.lower())
        if not month:
            return False
        
        file_date = datetime(int(year), month, int(day))
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return file_date >= cutoff_date
        
    except:
        return False

def quick_fix_recent_playbyplay():
    """Update only recent play-by-play files that are actively used"""
    
    playbyplay_dir = Path("../BaseballData/data/play-by-play")
    
    print("⚡ QUICK FIX: UPDATING RECENT PLAY-BY-PLAY DATA")
    print("=" * 60)
    
    if not playbyplay_dir.exists():
        print("❌ Play-by-play directory not found!")
        return
    
    # Get recent files (last 30 days)
    all_files = list(playbyplay_dir.glob("*.json"))
    recent_files = [f for f in all_files if is_recent_file(f.name, days=30)]
    
    print(f"📊 Total files: {len(all_files)}")
    print(f"🎯 Recent files to update: {len(recent_files)}")
    
    if not recent_files:
        print("ℹ️  No recent files found to update")
        return
    
    # Track progress
    success_count = 0
    failed_count = 0
    
    print(f"\n🚀 Updating recent files...")
    print("=" * 60)
    
    for i, file_path in enumerate(recent_files, 1):
        filename = file_path.name
        game_id = extract_game_id_from_filename(filename)
        
        if not game_id:
            print(f"❌ [{i:3}/{len(recent_files)}] No game ID in {filename}")
            failed_count += 1
            continue
        
        print(f"🔄 [{i:3}/{len(recent_files)}] {filename} (Game ID: {game_id})")
        
        try:
            # Check if file already has real names
            with open(file_path, 'r') as f:
                current_data = json.load(f)
            
            plays = current_data.get('plays', [])
            anonymous_count = sum(1 for play in plays 
                                if play.get('batter', '').startswith(('Batter_', 'Pitcher_'))
                                or play.get('pitcher', '').startswith(('Batter_', 'Pitcher_')))
            
            if anonymous_count == 0:
                print(f"   ✅ Already has real names, skipping...")
                success_count += 1
                continue
            
            # Generate new data with real names
            game_data, extracted_game_id, away_team, home_team = extract_playbyplay_data_from_api(game_id)
            
            if game_data and game_data.get('plays'):
                # Save updated file
                with open(file_path, 'w') as f:
                    json.dump(game_data, f, indent=2)
                
                new_plays = game_data['plays']
                real_batters = sum(1 for play in new_plays if play.get('batter', '') not in ['Unknown', ''])
                real_pitchers = sum(1 for play in new_plays if play.get('pitcher', '') not in ['Unknown', ''])
                
                print(f"   ✅ Updated: {real_batters}/{len(new_plays)} batters, {real_pitchers}/{len(new_plays)} pitchers")
                success_count += 1
                
            else:
                print(f"   ❌ Failed to extract new data")
                failed_count += 1
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed_count += 1
        
        # Rate limiting
        time.sleep(random.randint(2, 5))
    
    print(f"\n🏁 QUICK FIX COMPLETE!")
    print("=" * 60)
    print(f"✅ Successfully updated: {success_count} files")
    print(f"❌ Failed to update: {failed_count} files")
    
    if success_count > 0:
        print(f"\n🎯 Recent play-by-play data now has real player names!")
        print("🔧 Now run the weakspot analyzer to see the improvement!")

if __name__ == "__main__":
    quick_fix_recent_playbyplay()