#!/usr/bin/env python3
"""
Test script for the lineup fetcher functionality
"""

import sys
import json
from fetch_starting_lineups import StartingLineupFetcher

def test_fetcher():
    """Test the lineup fetcher"""
    print("🧪 Testing MLB Lineup Fetcher...")
    
    # Create fetcher instance
    fetcher = StartingLineupFetcher()
    
    # Test data loading
    print(f"📊 Loaded {len(fetcher.teams_data)} teams")
    print(f"👥 Loaded {len(fetcher.rosters_data)} roster entries")
    
    # Test page fetching
    print("\n🌐 Testing page fetch...")
    html_content = fetcher.fetch_lineup_page()
    
    if html_content:
        print(f"✅ Successfully fetched page ({len(html_content)} chars)")
        
        # Test parsing
        print("\n🔍 Testing game parsing...")
        games = fetcher.parse_game_data(html_content)
        print(f"🎮 Found {len(games)} games")
        
        if games:
            # Show sample game data
            print("\n📋 Sample game data:")
            sample_game = games[0]
            print(f"  Game ID: {sample_game.get('gameId', 'N/A')}")
            print(f"  Matchup: {sample_game.get('matchupKey', 'N/A')}")
            print(f"  Pitchers: {sample_game.get('pitcherMatchup', 'N/A')}")
            
            # Test full data generation
            print("\n📊 Testing full data generation...")
            lineup_data = fetcher.generate_lineup_data(games)
            
            print(f"✅ Generated complete lineup data:")
            print(f"  Total games: {lineup_data['totalGames']}")
            print(f"  Games with lineups: {lineup_data['gamesWithLineups']}")
            print(f"  Data quality: {lineup_data['metadata']['dataQuality']}")
            
            # Show quick lookup examples
            print(f"\n🔍 Quick lookup examples:")
            by_team = lineup_data['quickLookup']['byTeam']
            for team, data in list(by_team.items())[:3]:  # Show first 3
                print(f"  {team}: {data['pitcher']} vs {data['opponent']}")
            
            return True
        else:
            print("⚠️ No games found in parsing")
            return False
    else:
        print("❌ Failed to fetch page")
        return False

def test_scheduler():
    """Test the scheduler functionality"""
    print("\n🧪 Testing Lineup Scheduler...")
    
    from lineup_scheduler import LineupScheduler
    
    scheduler = LineupScheduler()
    
    # Test basic functionality
    lineup_file = scheduler.get_todays_lineup_file()
    print(f"📁 Today's file path: {lineup_file}")
    
    # Test should_update logic
    should_update = scheduler.should_update(None)
    print(f"🔄 Should update (no existing data): {should_update}")
    
    print("✅ Scheduler tests completed")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting lineup fetcher tests...\n")
    
    try:
        # Test fetcher
        fetcher_success = test_fetcher()
        
        # Test scheduler
        scheduler_success = test_scheduler()
        
        if fetcher_success and scheduler_success:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)