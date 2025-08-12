#!/usr/bin/env python3
"""
Test the fixed play-by-play scraper to verify real player names are captured
"""

from playbyplay_scraper import extract_playbyplay_data_from_api
import json

def test_fixed_scraper():
    print("🧪 Testing Fixed Play-by-Play Scraper")
    print("=" * 60)
    
    # Test with a known game ID from our existing data
    test_game_id = "401694974"  # ARI vs NYY from April 1, 2025
    
    print(f"🎯 Testing with game ID: {test_game_id}")
    
    # Extract data using the fixed API method
    game_data, game_id, away_team, home_team = extract_playbyplay_data_from_api(test_game_id)
    
    if not game_data:
        print("❌ Failed to extract game data")
        return
    
    print(f"✅ Successfully extracted game data")
    print(f"📊 Teams: {away_team} @ {home_team}")
    print(f"🎭 Total plays: {len(game_data.get('plays', []))}")
    
    # Check the first few plays for real player names
    plays = game_data.get('plays', [])[:5]
    
    print(f"\n🔍 First 5 plays to check player names:")
    print("=" * 80)
    
    for i, play in enumerate(plays, 1):
        batter = play.get('batter', 'Unknown')
        pitcher = play.get('pitcher', 'Unknown') 
        inning = play.get('inning', 0)
        inning_half = play.get('inning_half', '')
        result = play.get('play_result', '')
        
        print(f"Play {i}: {inning} {inning_half}")
        print(f"  👨‍💼 Batter:  {batter}")
        print(f"  ⚾ Pitcher: {pitcher}")
        print(f"  📋 Result:  {result}")
        
        # Check if we still have anonymous IDs
        if batter.startswith(('Batter_', 'Pitcher_')):
            print(f"  ⚠️  Still has anonymous batter ID!")
        if pitcher.startswith(('Batter_', 'Pitcher_')):
            print(f"  ⚠️  Still has anonymous pitcher ID!")
        
        print()
    
    # Count anonymous vs real names
    all_plays = game_data.get('plays', [])
    anonymous_batters = sum(1 for play in all_plays if play.get('batter', '').startswith(('Batter_', 'Pitcher_')))
    anonymous_pitchers = sum(1 for play in all_plays if play.get('pitcher', '').startswith(('Batter_', 'Pitcher_')))
    real_batters = len(all_plays) - anonymous_batters
    real_pitchers = len(all_plays) - anonymous_pitchers
    
    print(f"📈 Name Resolution Summary:")
    print(f"  Batters with real names:  {real_batters}/{len(all_plays)} ({real_batters/len(all_plays)*100:.1f}%)")
    print(f"  Pitchers with real names: {real_pitchers}/{len(all_plays)} ({real_pitchers/len(all_plays)*100:.1f}%)")
    
    if real_batters > 0 and real_pitchers > 0:
        print("✅ SUCCESS: Real player names are being captured!")
    else:
        print("❌ FAILURE: Still getting anonymous IDs")
    
    # Save a test file to examine
    test_output = {
        'test_info': {
            'game_id': test_game_id,
            'teams': f"{away_team} @ {home_team}",
            'total_plays': len(all_plays),
            'real_batter_names': real_batters,
            'real_pitcher_names': real_pitchers
        },
        'sample_plays': plays,
        'full_game_data': game_data
    }
    
    with open('test_playbyplay_fixed.json', 'w') as f:
        json.dump(test_output, f, indent=2)
    
    print(f"💾 Test results saved to: test_playbyplay_fixed.json")

if __name__ == "__main__":
    test_fixed_scraper()