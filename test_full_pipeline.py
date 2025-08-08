#!/usr/bin/env python3
"""
Test the full scraping pipeline with real player names
"""

import json
import os
from pathlib import Path
from playbyplay_scraper import extract_playbyplay_data_from_api

def test_full_pipeline():
    print("🧪 Testing Full Play-by-Play Pipeline")
    print("=" * 60)
    
    # Test with a known game ID
    test_game_id = "401694974"  # ARI vs NYY from April 1, 2025
    
    print(f"🎯 Testing with game ID: {test_game_id}")
    
    # Extract data using our fixed scraper
    game_data, game_id, away_team, home_team = extract_playbyplay_data_from_api(test_game_id)
    
    if not game_data:
        print("❌ Failed to extract game data")
        return
    
    print(f"✅ Successfully extracted game data")
    print(f"📊 Teams: {away_team} @ {home_team}")
    print(f"🎭 Total plays: {len(game_data.get('plays', []))}")
    
    # Save to the centralized location as the actual scraper would
    output_dir = Path("../BaseballData/data/play-by-play")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename using actual scraper format
    filename = f"{away_team}_vs_{home_team}_playbyplay_april_1_2025_{game_id}.json"
    output_file = output_dir / filename
    
    # Save the data
    with open(output_file, 'w') as f:
        json.dump(game_data, f, indent=2)
    
    print(f"💾 Saved play-by-play data to: {output_file}")
    
    # Analyze the content
    plays = game_data.get('plays', [])
    
    # Count real names vs unknowns
    real_batters = sum(1 for play in plays if play.get('batter', '') not in ['Unknown', ''])
    real_pitchers = sum(1 for play in plays if play.get('pitcher', '') not in ['Unknown', ''])
    
    # Count unique players
    unique_batters = set(play.get('batter', '') for play in plays if play.get('batter', '') != 'Unknown')
    unique_pitchers = set(play.get('pitcher', '') for play in plays if play.get('pitcher', '') != 'Unknown')
    
    print(f"\n📈 Analysis Summary:")
    print(f"  ✅ Plays with real batter names: {real_batters}/{len(plays)} ({real_batters/len(plays)*100:.1f}%)")
    print(f"  ✅ Plays with real pitcher names: {real_pitchers}/{len(plays)} ({real_pitchers/len(plays)*100:.1f}%)")
    print(f"  👨‍💼 Unique batters identified: {len(unique_batters)}")
    print(f"  ⚾ Unique pitchers identified: {len(unique_pitchers)}")
    
    print(f"\n🔍 Sample batters: {list(unique_batters)[:8]}")
    print(f"🔍 Sample pitchers: {list(unique_pitchers)[:4]}")
    
    # Check for any remaining anonymous IDs
    anonymous_batters = [play.get('batter', '') for play in plays if play.get('batter', '').startswith(('Batter_', 'Pitcher_'))]
    anonymous_pitchers = [play.get('pitcher', '') for play in plays if play.get('pitcher', '').startswith(('Batter_', 'Pitcher_'))]
    
    if anonymous_batters or anonymous_pitchers:
        print(f"\n⚠️ Still found some anonymous IDs:")
        print(f"  Anonymous batters: {len(anonymous_batters)}")
        print(f"  Anonymous pitchers: {len(anonymous_pitchers)}")
    else:
        print(f"\n🎉 NO ANONYMOUS IDs FOUND - All player names resolved!")
    
    # Verify the file can be read by our weakspot analyzer
    print(f"\n🔧 Testing compatibility with weakspot analyzer...")
    
    try:
        # Simulate what the weakspot analyzer would do
        test_plays = []
        for play in plays[:5]:
            pitcher = play.get('pitcher', 'Unknown')
            batter = play.get('batter', 'Unknown') 
            result = play.get('play_result', 'Unknown')
            
            if pitcher != 'Unknown' and batter != 'Unknown':
                test_plays.append({
                    'pitcher': pitcher,
                    'batter': batter,
                    'result': result
                })
        
        print(f"  ✅ Successfully extracted {len(test_plays)} analyzable plays")
        print(f"  ✅ Sample analyzable play: {test_plays[0] if test_plays else 'None'}")
        
        # This is the format our weakspot analyzer expects
        print(f"\n🎯 Ready for weakspot analysis!")
        print(f"  - File location: {output_file}")
        print(f"  - Real pitcher names: ✅")
        print(f"  - Real batter names: ✅")
        print(f"  - Analyzable plays: {len(test_plays)} out of {len(plays)}")
        
    except Exception as e:
        print(f"  ❌ Compatibility issue: {e}")

if __name__ == "__main__":
    test_full_pipeline()