#!/usr/bin/env python3
"""
Debug the ESPN API structure to understand why player names aren't being extracted
"""

import requests
import json

def debug_api_structure():
    game_id = "401694974"  # ARI vs NYY from April 1, 2025
    api_url = f'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?event={game_id}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"🔍 Debugging API structure for game {game_id}")
    print(f"📡 API URL: {api_url}")
    print("=" * 80)
    
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        api_data = response.json()
        
        # Check what top-level keys exist
        print(f"🔑 Top-level keys: {list(api_data.keys())}")
        
        # Check if boxscore data exists and its structure
        if 'boxscore' in api_data:
            boxscore = api_data['boxscore']
            print(f"\n📊 Boxscore keys: {list(boxscore.keys())}")
            
            if 'teams' in boxscore:
                teams = boxscore['teams']
                print(f"🏟️ Found {len(teams)} teams in boxscore")
                
                for i, team in enumerate(teams):
                    print(f"\nTeam {i+1}:")
                    print(f"  Keys: {list(team.keys())}")
                    
                    if 'team' in team:
                        team_info = team['team']
                        print(f"  Team info: {team_info.get('abbreviation', 'Unknown')} - {team_info.get('displayName', 'Unknown')}")
                    
                    if 'statistics' in team:
                        stats = team['statistics']
                        print(f"  Statistics groups: {len(stats)}")
                        
                        for j, stat_group in enumerate(stats):
                            print(f"    Group {j+1} keys: {list(stat_group.keys())}")
                            
                            if 'athletes' in stat_group:
                                athletes = stat_group['athletes']
                                print(f"    Athletes: {len(athletes)}")
                                
                                # Show first few athletes
                                for k, athlete_data in enumerate(athletes[:3]):
                                    print(f"      Athlete {k+1} keys: {list(athlete_data.keys())}")
                                    
                                    if 'athlete' in athlete_data:
                                        athlete = athlete_data['athlete']
                                        print(f"        ID: {athlete.get('id')}")
                                        print(f"        Name: {athlete.get('displayName', 'No displayName')}")
                                        print(f"        Full Name: {athlete.get('fullName', 'No fullName')}")
                                        print(f"        Short Name: {athlete.get('shortName', 'No shortName')}")
                                        print(f"        All athlete keys: {list(athlete.keys())}")
                        
        else:
            print("❌ No boxscore data found in API response")
        
        # Check plays structure
        if 'plays' in api_data:
            plays = api_data['plays']
            print(f"\n⚾ Found {len(plays)} plays")
            
            # Examine first few plays
            for i, play in enumerate(plays[:3]):
                print(f"\nPlay {i+1}:")
                print(f"  Keys: {list(play.keys())}")
                
                # Check for participants
                if 'participants' in play:
                    participants = play['participants']
                    print(f"  Participants: {len(participants)}")
                    for j, participant in enumerate(participants):
                        print(f"    Participant {j+1}: {list(participant.keys())}")
                        if 'athlete' in participant:
                            athlete = participant['athlete']
                            print(f"      Athlete ID: {athlete.get('id')}")
                            print(f"      Type: {participant.get('type', 'Unknown')}")
                else:
                    print("  No participants in play")
                
                # Check text description for names
                if 'text' in play:
                    text = play['text']
                    if len(text) < 100:
                        print(f"  Text: {text}")
                    else:
                        print(f"  Text (truncated): {text[:100]}...")
        
        else:
            print("❌ No plays data found in API response")
            
        # Save full response for detailed analysis
        with open('api_debug_response.json', 'w') as f:
            json.dump(api_data, f, indent=2)
        print(f"\n💾 Full API response saved to: api_debug_response.json")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_api_structure()