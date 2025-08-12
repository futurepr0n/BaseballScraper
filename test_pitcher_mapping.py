#!/usr/bin/env python3
"""
Test the pitcher name mapping system
"""

from pathlib import Path
from pitcher_name_mapper import PitcherNameMapper
import json

def test_pitcher_mapping():
    # Initialize mapper
    mapper = PitcherNameMapper("../BaseballData/data")
    
    # Load all data sources
    mapper.load_all_data_sources()
    
    # Test with sample play-by-play files
    playbyplay_dir = Path("../BaseballData/data/play-by-play")
    pbp_files = list(playbyplay_dir.glob("*_vs_*_playbyplay_*.json"))[:10]
    
    print(f"Testing with {len(pbp_files)} play-by-play files...")
    
    # Build mapping
    mapping_results = mapper.build_anonymous_mapping(pbp_files)
    
    print(f"\nFound {len(mapping_results)} pitcher mappings")
    print("\nSample Results:")
    print("=" * 80)
    
    for i, (anon_id, mapping) in enumerate(mapping_results.items()):
        if i >= 15:
            break
        real_name = mapping.get('real_name', 'Unknown')
        confidence = mapping.get('confidence', 0)
        method = mapping.get('method', 'unknown')
        
        print(f"{anon_id:18} -> {real_name:25} (conf: {confidence:.2f}, method: {method})")
    
    # Generate report
    report = mapper.generate_mapping_report()
    print(f"\nMapping Report:")
    print("=" * 80)
    print(json.dumps(report, indent=2))
    
    # Test specific pitcher retrieval
    print(f"\nTesting specific pitcher resolution:")
    print("=" * 80)
    
    sample_ids = list(mapping_results.keys())[:5]
    for pitcher_id in sample_ids:
        resolved_name = mapper.get_pitcher_name(pitcher_id)
        print(f"{pitcher_id} -> {resolved_name}")

if __name__ == "__main__":
    test_pitcher_mapping()