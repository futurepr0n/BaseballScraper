#!/usr/bin/env python3
"""
Test the enhanced scraper to verify rich ESPN descriptions
"""

import json
from playbyplay_scraper import extract_playbyplay_data_from_api

def test_enhanced_scraper():
    print("🧪 TESTING ENHANCED SCRAPER")
    print("=" * 50)
    
    # Test with the same game we used before
    test_game_id = "401694974"  # ARI vs NYY from April 1, 2025
    
    print(f"🎯 Testing enhanced scraper with game ID: {test_game_id}")
    
    # Extract data using our enhanced scraper
    game_data, game_id, away_team, home_team = extract_playbyplay_data_from_api(test_game_id)
    
    if not game_data:
        print("❌ Failed to extract game data")
        return
    
    print(f"✅ Successfully extracted game data")
    print(f"📊 Teams: {away_team} @ {home_team}")
    
    plays = game_data.get('plays', [])
    print(f"🎭 Total plays: {len(plays)}")
    
    print(f"\n🔍 Testing first 5 plays for enhanced descriptions:")
    print("=" * 80)
    
    enhanced_count = 0
    basic_count = 0
    
    for i, play in enumerate(plays[:5], 1):
        batter = play.get('batter', 'Unknown')
        pitcher = play.get('pitcher', 'Unknown')
        raw_text = play.get('raw_text', '')
        all_texts = play.get('all_play_texts', [])
        
        print(f"\nPlay {i}:")
        print(f"  👨‍💼 Batter:    {batter}")
        print(f"  ⚾ Pitcher:   {pitcher}")
        print(f"  📝 Raw Text:  {raw_text}")
        
        if all_texts:
            print(f"  🎭 All Texts: {all_texts[:3]}")  # Show first 3
        
        # Check if we got enhanced descriptions
        if (not raw_text.startswith('Pitch ') and 
            not raw_text.startswith('At-bat ') and 
            any(word in raw_text.lower() for word in [
                'singles', 'doubles', 'homers', 'strikes out', 'walks', 'flies out',
                'grounds out', 'pitches to', 'safe', 'error'
            ])):
            print(f"  ✅ Enhanced ESPN description!")
            enhanced_count += 1
        else:
            print(f"  ⚠️  Basic description")
            basic_count += 1
    
    print(f"\n📈 Enhancement Analysis:")
    print(f"  ✅ Enhanced descriptions: {enhanced_count}/5")
    print(f"  ⚠️  Basic descriptions:    {basic_count}/5")
    
    # Analyze all plays
    all_enhanced = 0
    all_basic = 0
    
    for play in plays:
        raw_text = play.get('raw_text', '')
        if (not raw_text.startswith('Pitch ') and 
            not raw_text.startswith('At-bat ') and 
            any(word in raw_text.lower() for word in [
                'singles', 'doubles', 'homers', 'strikes out', 'walks', 'flies out',
                'grounds out', 'pitches to', 'safe', 'error', 'reaches'
            ])):
            all_enhanced += 1
        else:
            all_basic += 1
    
    print(f"\n📊 Full Game Analysis:")
    print(f"  ✅ Enhanced descriptions: {all_enhanced}/{len(plays)} ({all_enhanced/len(plays)*100:.1f}%)")
    print(f"  ⚠️  Basic descriptions:    {all_basic}/{len(plays)} ({all_basic/len(plays)*100:.1f}%)")
    
    # Save test results
    test_output = {
        'test_info': {
            'game_id': test_game_id,
            'teams': f"{away_team} @ {home_team}",
            'total_plays': len(plays),
            'enhanced_descriptions': all_enhanced,
            'basic_descriptions': all_basic,
            'enhancement_rate': all_enhanced/len(plays)*100
        },
        'sample_plays': plays[:5]
    }
    
    with open('test_enhanced_scraper_results.json', 'w') as f:
        json.dump(test_output, f, indent=2)
    
    if all_enhanced > all_basic:
        print(f"\n🎉 SUCCESS! Enhanced scraper is working!")
        print(f"   🏆 {all_enhanced/len(plays)*100:.1f}% of plays have rich ESPN descriptions")
        print(f"   ✅ Ready for full regeneration with enhanced descriptions")
    elif all_enhanced > 0:
        print(f"\n✅ PARTIAL SUCCESS! Some enhanced descriptions captured")
        print(f"   📈 {all_enhanced/len(plays)*100:.1f}% enhancement rate")
        print(f"   🔧 Good enough for full regeneration")
    else:
        print(f"\n⚠️  NO ENHANCEMENT DETECTED")
        print(f"   🔍 All descriptions are still basic - may need API structure investigation")
    
    print(f"\n💾 Test results saved to: test_enhanced_scraper_results.json")

if __name__ == "__main__":
    test_enhanced_scraper()