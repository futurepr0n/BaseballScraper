#!/usr/bin/env python3
"""
Regenerate all play-by-play data with real player names
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

def regenerate_all_playbyplay():
    """Regenerate all play-by-play files with real player names"""
    
    playbyplay_dir = Path("../BaseballData/data/play-by-play")
    backup_dir = Path("../BaseballData/data/play-by-play_backup_anonymous")
    
    print("🧹 REGENERATING ALL PLAY-BY-PLAY DATA WITH REAL NAMES")
    print("=" * 70)
    
    if not playbyplay_dir.exists():
        print("❌ Play-by-play directory not found!")
        return
    
    # Get all existing files
    existing_files = list(playbyplay_dir.glob("*.json"))
    print(f"📊 Found {len(existing_files)} existing files to regenerate")
    
    # Create backup directory
    backup_dir.mkdir(exist_ok=True)
    print(f"📁 Backing up anonymous files to: {backup_dir}")
    
    # Track progress
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    print(f"\n🚀 Starting regeneration process...")
    print("=" * 70)
    
    for i, file_path in enumerate(existing_files, 1):
        filename = file_path.name
        game_id = extract_game_id_from_filename(filename)
        
        if not game_id:
            print(f"❌ [{i:4}/{len(existing_files)}] No game ID in {filename}")
            skipped_count += 1
            continue
        
        print(f"🔄 [{i:4}/{len(existing_files)}] Processing {filename} (Game ID: {game_id})")
        
        try:
            # Back up the old file
            backup_file = backup_dir / filename
            file_path.rename(backup_file)
            
            # Generate new data with real names
            game_data, extracted_game_id, away_team, home_team = extract_playbyplay_data_from_api(game_id)
            
            if game_data and game_data.get('plays'):
                # Count real names
                plays = game_data['plays']
                real_batters = sum(1 for play in plays if play.get('batter', '') not in ['Unknown', ''])
                real_pitchers = sum(1 for play in plays if play.get('pitcher', '') not in ['Unknown', ''])
                
                # Save new file
                with open(file_path, 'w') as f:
                    json.dump(game_data, f, indent=2)
                
                print(f"   ✅ Regenerated: {real_batters}/{len(plays)} batters, {real_pitchers}/{len(plays)} pitchers with real names")
                success_count += 1
                
            else:
                print(f"   ❌ Failed to extract data for game {game_id}")
                # Restore backup if generation failed
                backup_file.rename(file_path)
                failed_count += 1
        
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
            # Try to restore backup
            backup_file = backup_dir / filename
            if backup_file.exists():
                backup_file.rename(file_path)
            failed_count += 1
        
        # Rate limiting to avoid overwhelming ESPN
        if i % 10 == 0:
            delay = random.randint(15, 45)
            print(f"   ⏱️  Rate limiting: waiting {delay} seconds...")
            time.sleep(delay)
        else:
            time.sleep(random.randint(3, 8))
        
        # Progress update every 50 files
        if i % 50 == 0:
            print(f"\n📈 Progress Update:")
            print(f"   ✅ Successful: {success_count}")
            print(f"   ❌ Failed: {failed_count}")
            print(f"   ⏭️  Skipped: {skipped_count}")
            print(f"   📊 Completion: {i}/{len(existing_files)} ({i/len(existing_files)*100:.1f}%)")
            print("=" * 70)
    
    print(f"\n🏁 REGENERATION COMPLETE!")
    print("=" * 70)
    print(f"✅ Successfully regenerated: {success_count} files")
    print(f"❌ Failed to regenerate: {failed_count} files")  
    print(f"⏭️  Skipped (no game ID): {skipped_count} files")
    print(f"📁 Anonymous backups saved to: {backup_dir}")
    
    if success_count > 0:
        print(f"\n🎉 SUCCESS! {success_count} files now have real player names!")
        print("🎯 Ready for weakspot analysis with real names!")
        
        # Test a random regenerated file
        if existing_files:
            test_file = random.choice([f for f in playbyplay_dir.glob("*.json")])
            print(f"\n🔍 Testing random regenerated file: {test_file.name}")
            
            try:
                with open(test_file, 'r') as f:
                    test_data = json.load(f)
                
                plays = test_data.get('plays', [])[:3]
                print("Sample plays with real names:")
                for play in plays:
                    batter = play.get('batter', 'Unknown')
                    pitcher = play.get('pitcher', 'Unknown')
                    print(f"  👨‍💼 {batter} vs ⚾ {pitcher}")
                    
                # Check for anonymous IDs
                anonymous_count = sum(1 for play in test_data.get('plays', []) 
                                    if play.get('batter', '').startswith(('Batter_', 'Pitcher_'))
                                    or play.get('pitcher', '').startswith(('Batter_', 'Pitcher_')))
                
                if anonymous_count == 0:
                    print("✅ No anonymous IDs found!")
                else:
                    print(f"⚠️  Still found {anonymous_count} anonymous IDs")
                    
            except Exception as e:
                print(f"❌ Error testing file: {e}")
    
    else:
        print(f"\n⚠️  No files were successfully regenerated!")
        print("Check the error messages above for issues.")

if __name__ == "__main__":
    regenerate_all_playbyplay()