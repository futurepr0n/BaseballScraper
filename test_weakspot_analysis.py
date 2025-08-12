#!/usr/bin/env python3
"""
Test script for the weakspot analysis engine
"""

from weakspot_analysis_engine import WeakspotAnalysisEngine
import json

def test_analysis_engine():
    """Test the analysis engine with a limited dataset"""
    print("🧪 TESTING WEAKSPOT ANALYSIS ENGINE")
    print("="*50)
    
    # Initialize with limited data for testing
    engine = WeakspotAnalysisEngine()
    
    # Load limited data for testing
    print("📊 Loading test dataset (first 100 files)...")
    engine.load_playbyplay_data(limit_files=100)
    
    if engine.games_processed == 0:
        print("❌ No games processed - check data directory")
        return
    
    print(f"\n✅ Test data loaded successfully!")
    print(f"   Games processed: {engine.games_processed}")
    print(f"   Pitchers found: {len(engine.pitchers_data)}")
    print(f"   Batters found: {len(engine.batters_data)}")
    
    # Test individual analysis functions
    print(f"\n🔍 Running analysis tests...")
    
    # Test inning vulnerabilities
    print("   Testing inning vulnerability analysis...")
    inning_vulns = engine.analyze_pitcher_inning_vulnerabilities(min_appearances=3)
    print(f"   ✅ Found {len(inning_vulns)} pitchers with inning vulnerabilities")
    
    # Test pitch predictability 
    print("   Testing pitch predictability analysis...")
    predictable = engine.analyze_pitch_predictability(min_sequences=2)
    print(f"   ✅ Found {len(predictable)} pitchers with predictable patterns")
    
    # Test count vulnerabilities
    print("   Testing count vulnerability analysis...")
    count_vulns = engine.analyze_count_vulnerabilities(min_counts=3)
    print(f"   ✅ Found {len(count_vulns)} pitchers with count weaknesses")
    
    # Show sample results
    print(f"\n📋 SAMPLE RESULTS:")
    print("="*50)
    
    if inning_vulns:
        sample_pitcher = inning_vulns[0]
        print(f"🎯 TOP INNING VULNERABILITY:")
        print(f"   Pitcher: {sample_pitcher['pitcher']}")
        print(f"   Appearances: {sample_pitcher['total_appearances']}")
        print(f"   Vulnerable innings: {list(sample_pitcher['vulnerable_innings'].keys())}")
        
        # Show specific inning stats
        for inning, stats in list(sample_pitcher['vulnerable_innings'].items())[:2]:
            print(f"      {inning}: {stats['avg_outcome_score']:.2f} avg score ({stats['total_plays']} plays)")
    
    if predictable:
        sample_predictable = predictable[0]
        print(f"\n🔮 TOP PREDICTABLE PITCHER:")
        print(f"   Pitcher: {sample_predictable['pitcher']}")
        print(f"   Total sequences: {sample_predictable['total_sequences']}")
        
        # Show predictable sequences
        for sequence, stats in list(sample_predictable['predictable_sequences'].items())[:2]:
            print(f"      Pattern: {sequence}")
            print(f"         Frequency: {stats['frequency']}, Avg score: {stats['avg_outcome_score']:.2f}")
    
    if count_vulns:
        sample_count = count_vulns[0]
        print(f"\n📊 TOP COUNT VULNERABILITY:")
        print(f"   Pitcher: {sample_count['pitcher']}")
        print(f"   Total pitches: {sample_count['total_pitches']}")
        
        # Show weak counts
        for count, stats in list(sample_count['weak_counts'].items())[:2]:
            print(f"      Count {count}: {stats['avg_outcome_score']:.2f} avg score ({stats['pitch_count']} pitches)")
            print(f"         Most common pitch: {stats['most_common_pitch'][0]} ({stats['most_common_pitch'][1]} times)")
    
    # Test report generation
    print(f"\n📝 Testing report generation...")
    try:
        reports = engine.generate_analysis_report()
        print(f"   ✅ Generated comprehensive analysis reports")
        print(f"   📁 Check ../BaseballData/data/weakspot_analysis/ for JSON files")
        
        # Show report summary
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   🎯 Inning vulnerabilities: {len(reports['inning_vulnerabilities'])} pitchers")
        print(f"   🔮 Predictable patterns: {len(reports['pitch_predictability'])} pitchers") 
        print(f"   📊 Count weaknesses: {len(reports['count_vulnerabilities'])} pitchers")
        
    except Exception as e:
        print(f"   ❌ Report generation failed: {e}")
    
    print(f"\n🎉 Testing complete!")
    
    # Show next steps
    print(f"\n🚀 NEXT STEPS:")
    print("   1. Review generated JSON files in ../BaseballData/data/weakspot_analysis/")
    print("   2. Run full analysis with engine.load_playbyplay_data() (no limit)")
    print("   3. Integrate with daily processing pipeline") 
    print("   4. Add lineup position analysis")
    print("   5. Create frontend filtering interface")

if __name__ == "__main__":
    test_analysis_engine()