#!/usr/bin/env python3
"""
Test script for the game backfill functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backfill_missing_games import GameBackfiller

def test_scrape_single_game():
    """Test scraping a single game"""
    backfiller = GameBackfiller()
    
    # Test with the July 29 Blue Jays game
    print("Testing game scraping for 401696518...")
    result = backfiller.scrape_game_data('401696518')
    
    if result:
        print("✅ Successfully scraped game data")
        print(f"Game: {result['game']}")
        print(f"Players found: {len(result['players'])}")
        return True
    else:
        print("❌ Failed to scrape game data")
        return False

def test_team_name_normalization():
    """Test team name normalization"""
    backfiller = GameBackfiller()
    
    test_cases = [
        ('Blue Jays', 'TOR'),
        ('Orioles', 'BAL'),
        ('Braves', 'ATL'),
        ('Reds', 'CIN'),
        ('Guardians', 'CLE'),
        ('White Sox', 'CHW')
    ]
    
    print("\nTesting team name normalization...")
    all_passed = True
    for input_name, expected in test_cases:
        result = backfiller._normalize_team_name(input_name)
        if result == expected:
            print(f"✅ {input_name} -> {result}")
        else:
            print(f"❌ {input_name} -> {result} (expected {expected})")
            all_passed = False
    
    return all_passed

if __name__ == '__main__':
    print("🧪 Running backfill tests...")
    
    success = True
    
    # Test team normalization
    if not test_team_name_normalization():
        success = False
    
    # Test game scraping
    if not test_scrape_single_game():
        success = False
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)