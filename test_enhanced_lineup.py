#!/usr/bin/env python3
"""
Test script for the enhanced lineup scraper
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_lineup_scraper import MLBLineupScraper

def test_scraper():
    """Test the enhanced lineup scraper"""
    print("🧪 Testing Enhanced MLB Lineup Scraper")
    print("=" * 50)
    
    scraper = MLBLineupScraper()
    
    # Test with today's date
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    
    print(f"📅 Testing with date: {date_str}")
    
    # Test page fetching
    print("\n1. Testing page fetch...")
    html = scraper.get_lineup_page(date_str)
    if html:
        print(f"✅ Successfully fetched page ({len(html)} characters)")
    else:
        print("❌ Failed to fetch page")
        return
    
    # Test lineup scraping
    print("\n2. Testing lineup extraction...")
    lineups = scraper.scrape_lineups(date_str)
    
    if lineups:
        print(f"✅ Extracted lineups for {len(lineups)} teams:")
        for team_abbr, lineup_data in lineups.items():
            players = len(lineup_data.get('batting_order', []))
            print(f"   {team_abbr}: {players} players")
            
            # Show first few players for verification
            if players > 0:
                batting_order = lineup_data.get('batting_order', [])
                for i, player in enumerate(batting_order[:3]):
                    print(f"     {i+1}. {player.get('name', 'Unknown')} ({player.get('position', '?')}) - {player.get('bats', '?')}")
                if players > 3:
                    print(f"     ... and {players - 3} more")
    else:
        print("❌ No lineups extracted")
        print("\n📋 This might be expected if:")
        print("   - Lineups haven't been posted yet")
        print("   - It's an off day")
        print("   - MLB.com changed their page structure")
    
    # Test file update (only if lineups were found)
    if lineups:
        print(f"\n3. Testing file update...")
        success = scraper.update_lineup_file(date_str, lineups)
        if success:
            print("✅ Successfully updated lineup file")
        else:
            print("❌ Failed to update lineup file")
    
    print(f"\n{'='*50}")
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_scraper()