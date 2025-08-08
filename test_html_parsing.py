#!/usr/bin/env python3
"""
Test the HTML parsing method for real player names
"""

from playbyplay_scraper import extract_playbyplay_data, get_page_content, transform_url_to_playbyplay
import json

def test_html_parsing():
    print("🧪 Testing HTML Play-by-Play Parsing")
    print("=" * 60)
    
    # Use a boxscore URL and transform it to playbyplay
    boxscore_url = "https://www.espn.com/mlb/game/_/gameId/401694974"
    playbyplay_url = transform_url_to_playbyplay(boxscore_url)
    
    print(f"🌐 Testing with URL: {playbyplay_url}")
    
    # Get the HTML content
    print("📡 Fetching HTML content...")
    html_content = get_page_content(playbyplay_url)
    
    if not html_content:
        print("❌ Failed to fetch HTML content")
        return
    
    # Extract play-by-play data using HTML method
    game_data, game_id, away_team, home_team = extract_playbyplay_data(html_content, playbyplay_url)
    
    if not game_data:
        print("❌ Failed to extract game data")
        return
    
    print(f"✅ Successfully extracted game data")
    print(f"📊 Teams: {away_team} @ {home_team}")
    print(f"🎭 Total plays: {len(game_data.get('plays', []))}")
    
    # Check the first few plays for real player names
    plays = game_data.get('plays', [])[:10]
    
    print(f"\n🔍 First 10 plays to check player names:")
    print("=" * 80)
    
    real_batters = 0
    real_pitchers = 0
    
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
        
        # Check for real names (not "Unknown" and not anonymous IDs)
        if batter != "Unknown" and not batter.startswith(('Batter_', 'Pitcher_')):
            real_batters += 1
            print(f"  ✅ Real batter name detected")
        else:
            print(f"  ❌ No real batter name")
            
        if pitcher != "Unknown" and not pitcher.startswith(('Batter_', 'Pitcher_')) and pitcher:
            real_pitchers += 1
            print(f"  ✅ Real pitcher name detected")
        else:
            print(f"  ❌ No real pitcher name")
        
        print()
    
    # Count all names
    all_plays = game_data.get('plays', [])
    total_real_batters = sum(1 for play in all_plays 
                           if play.get('batter', '') not in ['Unknown', ''] 
                           and not play.get('batter', '').startswith(('Batter_', 'Pitcher_')))
    total_real_pitchers = sum(1 for play in all_plays 
                            if play.get('pitcher', '') not in ['Unknown', ''] 
                            and not play.get('pitcher', '').startswith(('Batter_', 'Pitcher_')))
    
    print(f"📈 Name Resolution Summary:")
    print(f"  Batters with real names:  {total_real_batters}/{len(all_plays)} ({total_real_batters/len(all_plays)*100:.1f}%)")
    print(f"  Pitchers with real names: {total_real_pitchers}/{len(all_plays)} ({total_real_pitchers/len(all_plays)*100:.1f}%)")
    
    if total_real_batters > 0 or total_real_pitchers > 0:
        print("✅ SUCCESS: Real player names are being captured!")
    else:
        print("❌ FAILURE: Still not getting real player names")
    
    # Save a test file
    test_output = {
        'test_info': {
            'url': playbyplay_url,
            'game_id': game_id,
            'teams': f"{away_team} @ {home_team}",
            'total_plays': len(all_plays),
            'real_batter_names': total_real_batters,
            'real_pitcher_names': total_real_pitchers
        },
        'sample_plays': plays,
        'all_plays': all_plays[:20]  # First 20 for examination
    }
    
    with open('test_html_parsing_results.json', 'w') as f:
        json.dump(test_output, f, indent=2)
    
    print(f"💾 Test results saved to: test_html_parsing_results.json")

if __name__ == "__main__":
    test_html_parsing()