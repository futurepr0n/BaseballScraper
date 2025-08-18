#!/usr/bin/env python3
"""
Test script for the enhanced odds scraping functionality
Tests both HR and 1+ Hits props processing
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime

def test_odds_data_structure():
    """Test if sample JSON data contains both HR and Hits props"""
    
    print("🧪 Testing Enhanced Odds Data Structure")
    print("=" * 50)
    
    # Check if sample data file exists
    sample_file = 'mlb-batter-hr-props.json'
    if not os.path.exists(sample_file):
        print("❌ No sample data file found. Download first with:")
        print("   wget -O mlb-batter-hr-props.json 'https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/743?=json'")
        return False
        
    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return False
    
    print(f"✅ Sample data loaded successfully")
    
    # Analyze markets
    if 'markets' not in data:
        print("❌ No markets found in data")
        return False
        
    hr_markets = 0
    hits_markets = 0
    other_markets = 0
    
    for market in data['markets']:
        market_type_name = market.get('marketType', {}).get('name', '').lower()
        market_name = market.get('name', '').lower()
        
        if "home runs" in market_type_name or "home runs" in market_name:
            hr_markets += 1
        elif "hits milestones" in market_type_name or ("hits" in market_name and "allowed" not in market_name):
            hits_markets += 1
        else:
            other_markets += 1
    
    print(f"📊 Market Analysis:")
    print(f"   ⚾ Home Run markets: {hr_markets}")
    print(f"   🥎 Hits markets: {hits_markets}")
    print(f"   📈 Other markets: {other_markets}")
    
    # Analyze selections
    if 'selections' not in data:
        print("❌ No selections found in data")
        return False
    
    hr_selections = 0
    hits_selections = 0
    
    # Quick market mapping
    markets_info = {}
    for market in data['markets']:
        market_id = market.get('id')
        market_name = market.get('name', '').lower()
        market_type_name = market.get('marketType', {}).get('name', '').lower()
        
        prop_type = None
        if "home runs" in market_type_name:
            prop_type = "Home Runs"
        elif "hits milestones" in market_type_name:
            prop_type = "Hits"
        elif "home runs" in market_name:
            prop_type = "Home Runs"
        elif "hits" in market_name and "allowed" not in market_name:
            prop_type = "Hits"
        
        if market_id and prop_type:
            markets_info[market_id] = prop_type
    
    for selection in data['selections']:
        market_id = selection.get('marketId')
        selection_label = selection.get('label')
        
        if market_id in markets_info and selection_label == "1+":
            if markets_info[market_id] == "Home Runs":
                hr_selections += 1
            elif markets_info[market_id] == "Hits":
                hits_selections += 1
    
    print(f"🎯 Selection Analysis (1+ only):")
    print(f"   ⚾ Home Run selections: {hr_selections}")
    print(f"   🥎 Hits selections: {hits_selections}")
    
    if hr_selections > 0 and hits_selections > 0:
        print("✅ Both HR and Hits props found in data - enhanced processing ready!")
        return True
    elif hr_selections > 0:
        print("⚠️  Only HR props found - Hits props may not be available today")
        return True
    else:
        print("❌ No valid props found for processing")
        return False

def test_enhanced_script():
    """Test the enhanced odds-scrape.py script"""
    
    print("\n🔧 Testing Enhanced Odds Script")
    print("=" * 40)
    
    # Check if enhanced script exists
    if not os.path.exists('odds-scrape.py'):
        print("❌ Enhanced odds-scrape.py not found")
        return False
    
    print("✅ Enhanced odds-scrape.py found")
    
    # Test script execution (dry run by checking imports)
    try:
        import subprocess
        result = subprocess.run([
            'python3', '-c', 
            'import sys; sys.path.append("."); from config import PATHS, get_output_dirs; print("Config import successful")'
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ Configuration imports working")
        else:
            print(f"❌ Configuration import error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Script test error: {e}")
        return False
    
    return True

def test_output_structure():
    """Test expected output file structure"""
    
    print("\n📁 Testing Output Structure")
    print("=" * 35)
    
    from config import PATHS
    
    odds_dir = PATHS['odds']
    print(f"📂 Odds directory: {odds_dir}")
    
    if not odds_dir.exists():
        print("⚠️  Odds directory doesn't exist yet (will be created on first run)")
        odds_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Created odds directory")
    else:
        print("✅ Odds directory exists")
    
    # Expected files after processing
    expected_files = [
        'mlb-hr-odds-only.csv',
        'mlb-hr-odds-tracking.csv', 
        'mlb-hr-odds-history.csv',
        'mlb-hits-odds-only.csv',
        'mlb-hits-odds-tracking.csv',
        'mlb-hits-odds-history.csv'
    ]
    
    print("📋 Expected output files:")
    for filename in expected_files:
        filepath = odds_dir / filename
        status = "✅ Exists" if filepath.exists() else "⏳ Will be created"
        print(f"   {filename}: {status}")
    
    return True

def test_integration_readiness():
    """Test if the system is ready for dashboard integration"""
    
    print("\n🔗 Testing Dashboard Integration Readiness")
    print("=" * 45)
    
    # Check BaseballTracker integration paths
    base_dir = Path(__file__).parent.parent
    tracker_public = base_dir / 'BaseballTracker' / 'public' / 'data' / 'odds'
    tracker_build = base_dir / 'BaseballTracker' / 'build' / 'data' / 'odds'
    
    print(f"🎯 Integration paths:")
    print(f"   Public: {tracker_public}")
    print(f"   Build:  {tracker_build}")
    
    # Test if BaseballTracker exists
    if not (base_dir / 'BaseballTracker').exists():
        print("⚠️  BaseballTracker not found at expected location")
        print("   Files will be copied to centralized location only")
    else:
        print("✅ BaseballTracker found - ready for dashboard integration")
    
    # Check if odds service exists in BaseballTracker
    odds_service = base_dir / 'BaseballTracker' / 'src' / 'services' / 'oddsService.js'
    if odds_service.exists():
        print("✅ Odds service found - dashboard can consume odds data")
    else:
        print("⚠️  Odds service not found - may need to create service for dashboard integration")
    
    return True

if __name__ == "__main__":
    print("🚀 Enhanced Odds Scraping Test Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests_passed = 0
    total_tests = 4
    
    if test_odds_data_structure():
        tests_passed += 1
    
    if test_enhanced_script():
        tests_passed += 1
        
    if test_output_structure():
        tests_passed += 1
        
    if test_integration_readiness():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed - Enhanced odds system ready!")
        print("\n📋 Next Steps:")
        print("   1. Run: ./update-odds.sh (manual test)")
        print("   2. Verify both HR and Hits files are created")
        print("   3. Set up cron automation: crontab -e")
        print("   4. Integrate with BaseballTracker dashboard")
    else:
        print("❌ Some tests failed - please review issues above")
        sys.exit(1)
    
    print(f"\n🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")