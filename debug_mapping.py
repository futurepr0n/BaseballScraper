#!/usr/bin/env python3
"""
Debug the pitcher name mapping system
"""

from pathlib import Path
from pitcher_name_mapper import PitcherNameMapper
import json

def debug_mapping():
    # Initialize mapper
    mapper = PitcherNameMapper("../BaseballData/data")
    mapper.load_all_data_sources()
    
    print("=== DEBUGGING PITCHER MAPPING ===\n")
    
    print(f"Total game contexts loaded: {len(mapper.game_context_map)}")
    print("\nSample game contexts:")
    for i, (key, value) in enumerate(mapper.game_context_map.items()):
        if i >= 10:
            break
        print(f"  {key}: {value}")
    
    # Focus on a specific play-by-play file
    test_file = "../BaseballData/data/play-by-play/ARI_vs_NYY_playbyplay_april_1_2025_401694974.json"
    with open(test_file, 'r') as f:
        game_data = json.load(f)
    
    print(f"\n=== ANALYZING SPECIFIC GAME: {test_file} ===")
    print(f"Game ID: {game_data['metadata']['game_id']}")
    print(f"Away Team: {game_data['metadata']['away_team']}")
    print(f"Home Team: {game_data['metadata']['home_team']}")
    
    # Find unique pitcher IDs in this game
    pitcher_ids = set()
    for play in game_data.get('plays', []):
        pitcher_id = play.get('pitcher')
        if pitcher_id:
            pitcher_ids.add(pitcher_id)
    
    print(f"Unique pitcher IDs: {list(pitcher_ids)[:5]}...")
    
    # Check if we have CSV data for this game
    game_id = game_data['metadata']['game_id']
    csv_matches = []
    for key, value in mapper.game_context_map.items():
        if value.get('source') == 'csv' and game_id in key:
            csv_matches.append((key, value))
    
    print(f"\nCSV matches for game {game_id}:")
    for key, value in csv_matches:
        print(f"  {key}: {value}")
    
    # Test the mapping for one pitcher
    test_pitcher = list(pitcher_ids)[0] if pitcher_ids else None
    if test_pitcher:
        print(f"\n=== TESTING MAPPING FOR {test_pitcher} ===")
        
        # Extract contexts for this pitcher
        contexts = []
        for play in game_data.get('plays', []):
            if play.get('pitcher') == test_pitcher:
                context = {
                    'game_id': game_data['metadata']['game_id'],
                    'home_team': game_data['metadata']['home_team'],
                    'away_team': game_data['metadata']['away_team'],
                    'date': '2025-04-01',  # Known from filename
                    'inning': play.get('inning', 1),
                    'inning_half': play.get('inning_half', '')
                }
                contexts.append(context)
        
        print(f"Found {len(contexts)} contexts for {test_pitcher}")
        if contexts:
            print("Sample contexts:")
            for ctx in contexts[:3]:
                print(f"  {ctx}")
            
            # Try the mapping
            result = mapper._resolve_anonymous_id(test_pitcher, contexts)
            print(f"\nMapping result: {result}")

if __name__ == "__main__":
    debug_mapping()