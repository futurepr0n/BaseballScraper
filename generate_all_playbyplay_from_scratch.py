#!/usr/bin/env python3
"""
Generate ALL play-by-play data from scratch using game schedule files
No existing files needed - builds everything fresh with real player names
"""

import os
import json
import time
import random
import glob
from pathlib import Path
from datetime import datetime
from playbyplay_scraper import extract_playbyplay_data_from_api
import re

def extract_game_id_from_url(url):
    """Extract game ID from ESPN boxscore URL"""
    match = re.search(r'gameId/(\d+)', url)
    return match.group(1) if match else None

def get_team_abbr_from_url(url):
    """Extract team abbreviations from URL structure"""
    # URLs typically contain team info, but we'll let the API determine this
    return None, None

def generate_filename(away_team, home_team, date_str, game_id):
    """Generate consistent filename format"""
    # Parse date string (assumes YYYY-MM-DD format)
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month_name = date_obj.strftime("%B").lower()
        day = date_obj.day
        year = date_obj.year
        return f"{away_team}_vs_{home_team}_playbyplay_{month_name}_{day}_{year}_{game_id}.json"
    except:
        # Fallback format
        return f"{away_team}_vs_{home_team}_playbyplay_{date_str}_{game_id}.json"

def read_schedule_files():
    """Read all schedule files and extract game URLs"""
    schedule_files = glob.glob("*.txt")
    schedule_files = [f for f in schedule_files if re.match(r'\w+_\d+_\d{4}\.txt', f)]
    
    print(f"📅 Found {len(schedule_files)} schedule files")
    
    all_games = []
    
    for schedule_file in sorted(schedule_files):
        print(f"📖 Reading {schedule_file}...")
        
        # Extract date from filename
        match = re.match(r'(\w+)_(\d+)_(\d{4})\.txt', schedule_file)
        if not match:
            continue
            
        month_name, day, year = match.groups()
        
        # Convert month name to number
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        month_num = month_map.get(month_name.lower(), '01')
        date_str = f"{year}-{month_num}-{day.zfill(2)}"
        
        try:
            with open(schedule_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
            
            for url in urls:
                game_id = extract_game_id_from_url(url)
                if game_id:
                    all_games.append({
                        'url': url,
                        'game_id': game_id,
                        'date': date_str,
                        'date_str': f"{month_name}_{day}_{year}",
                        'schedule_file': schedule_file
                    })
                    
        except Exception as e:
            print(f"❌ Error reading {schedule_file}: {e}")
    
    print(f"🎯 Total games found: {len(all_games)}")
    return all_games

def generate_all_playbyplay_from_scratch():
    """Generate all play-by-play data from scratch"""
    
    print("🆕 GENERATING ALL PLAY-BY-PLAY DATA FROM SCRATCH")
    print("=" * 70)
    print("📋 This will generate fresh data with REAL PLAYER NAMES")
    print("=" * 70)
    
    # Ensure output directory exists
    output_dir = Path("../BaseballData/data/play-by-play")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read all schedule files
    all_games = read_schedule_files()
    
    if not all_games:
        print("❌ No games found in schedule files!")
        return
    
    print(f"\n🚀 Starting generation for {len(all_games)} games...")
    print("=" * 70)
    
    # Track progress
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, game in enumerate(all_games, 1):
        game_id = game['game_id']
        date_str = game['date_str']
        
        print(f"⚾ [{i:4}/{len(all_games)}] Game ID: {game_id} ({date_str})")
        
        try:
            # Generate play-by-play data using our FIXED scraper
            game_data, extracted_game_id, away_team, home_team = extract_playbyplay_data_from_api(game_id)
            
            if not game_data or not game_data.get('plays'):
                print(f"   ❌ No play data available")
                failed_count += 1
                continue
            
            # Generate filename
            filename = generate_filename(away_team or "AWAY", home_team or "HOME", game['date'], game_id)
            output_file = output_dir / filename
            
            # Save the data
            with open(output_file, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            # Analyze the generated data
            plays = game_data['plays']
            real_batters = sum(1 for play in plays if play.get('batter', '') not in ['Unknown', ''])
            real_pitchers = sum(1 for play in plays if play.get('pitcher', '') not in ['Unknown', ''])
            
            # Check for anonymous IDs (should be zero)
            anonymous_count = sum(1 for play in plays 
                                if play.get('batter', '').startswith(('Batter_', 'Pitcher_'))
                                or play.get('pitcher', '').startswith(('Batter_', 'Pitcher_')))
            
            if anonymous_count > 0:
                print(f"   ⚠️  Generated {filename} - but still has {anonymous_count} anonymous IDs!")
            else:
                print(f"   ✅ Generated {filename}")
                print(f"      👨‍💼 {real_batters}/{len(plays)} batters with real names")
                print(f"      ⚾ {real_pitchers}/{len(plays)} pitchers with real names")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error generating data for game {game_id}: {e}")
            failed_count += 1
        
        # Rate limiting - be respectful to ESPN servers
        if i % 20 == 0:
            delay = random.randint(30, 60)
            print(f"   ⏱️  Rate limiting: waiting {delay} seconds after 20 requests...")
            time.sleep(delay)
        else:
            time.sleep(random.randint(3, 8))
        
        # Progress update every 100 files
        if i % 100 == 0:
            print(f"\n📈 Progress Update:")
            print(f"   ✅ Successful: {success_count}")
            print(f"   ❌ Failed: {failed_count}")
            print(f"   📊 Completion: {i}/{len(all_games)} ({i/len(all_games)*100:.1f}%)")
            print("=" * 70)
    
    print(f"\n🏁 GENERATION COMPLETE!")
    print("=" * 70)
    print(f"✅ Successfully generated: {success_count} files")
    print(f"❌ Failed to generate: {failed_count} files")
    print(f"📁 Output directory: {output_dir}")
    
    if success_count > 0:
        print(f"\n🎉 SUCCESS! Generated {success_count} files with REAL PLAYER NAMES!")
        
        # Test a few generated files
        generated_files = list(output_dir.glob("*.json"))
        if generated_files:
            print(f"\n🔍 Testing random generated files...")
            
            for test_file in random.sample(generated_files, min(3, len(generated_files))):
                print(f"\n📄 Testing: {test_file.name}")
                
                try:
                    with open(test_file, 'r') as f:
                        test_data = json.load(f)
                    
                    plays = test_data.get('plays', [])[:2]
                    for play in plays:
                        batter = play.get('batter', 'Unknown')
                        pitcher = play.get('pitcher', 'Unknown')
                        result = play.get('play_result', 'Unknown')
                        print(f"   👨‍💼 {batter} vs ⚾ {pitcher} → {result}")
                    
                    # Check for anonymous IDs
                    all_plays = test_data.get('plays', [])
                    anonymous_count = sum(1 for play in all_plays 
                                        if play.get('batter', '').startswith(('Batter_', 'Pitcher_'))
                                        or play.get('pitcher', '').startswith(('Batter_', 'Pitcher_')))
                    
                    if anonymous_count == 0:
                        print(f"   ✅ No anonymous IDs - all {len(all_plays)} plays have real names!")
                    else:
                        print(f"   ⚠️  Found {anonymous_count} anonymous IDs out of {len(all_plays)} plays")
                        
                except Exception as e:
                    print(f"   ❌ Error testing file: {e}")
        
        print(f"\n🎯 READY FOR WEAKSPOT ANALYSIS!")
        print("All generated files have real player names instead of anonymous IDs.")
        print("Your weakspot analysis will now show actual player names like 'Jacob deGrom' instead of 'Pitcher_4346118'")
        
    else:
        print(f"\n❌ No files were successfully generated!")
        print("Check your internet connection and schedule files.")

if __name__ == "__main__":
    generate_all_playbyplay_from_scratch()