#!/usr/bin/env python3
"""
Debug API Response Script
Shows what data is actually available from the MLB Stats API
"""

import requests
import json
import datetime
import sys

def debug_mlb_api():
    api_base_url = "https://statsapi.mlb.com/api/v1"
    session = requests.Session()
    session.headers.update({'User-Agent': 'BaseballTracker-Debug/1.0'})
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    print(f"🔍 Debugging MLB Stats API for {date_str}")
    print("=" * 60)
    
    # Basic schedule endpoint
    url = f"{api_base_url}/schedule"
    params = {
        'sportId': 1,
        'date': date_str,
        'hydrate': 'probablePitcher,lineups,venue,weather'
    }
    
    try:
        print(f"📡 Fetching: {url}")
        print(f"📋 Params: {params}")
        
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📊 Total Games: {data.get('totalGames', 0)}")
        print(f"📊 Total Items: {data.get('totalItems', 0)}")
        
        # Analyze structure
        if 'dates' in data:
            print(f"\n📅 Dates found: {len(data['dates'])}")
            
            for date_obj in data['dates']:
                date_val = date_obj.get('date', '')
                games = date_obj.get('games', [])
                print(f"\n📅 Date: {date_val} - {len(games)} games")
                
                for i, game in enumerate(games):
                    print(f"\n  🎯 Game {i+1}: {game.get('gamePk', 'No ID')}")
                    print(f"     Status: {game.get('status', {}).get('detailedState', 'Unknown')}")
                    
                    # Teams
                    teams = game.get('teams', {})
                    home_team = teams.get('home', {}).get('team', {})
                    away_team = teams.get('away', {}).get('team', {})
                    print(f"     Teams: {away_team.get('name', 'Unknown')} @ {home_team.get('name', 'Unknown')}")
                    
                    # Pitchers
                    home_pitcher = teams.get('home', {}).get('probablePitcher', {})
                    away_pitcher = teams.get('away', {}).get('probablePitcher', {})
                    
                    if home_pitcher.get('fullName'):
                        print(f"     Home Pitcher: {home_pitcher.get('fullName', 'TBD')}")
                        print(f"       ID: {home_pitcher.get('id', 'No ID')}")
                        print(f"       Throws: {home_pitcher.get('pitchHand', {}).get('code', 'Unknown')}")
                        print(f"       Throws Desc: {home_pitcher.get('pitchHand', {}).get('description', 'Unknown')}")
                    
                    if away_pitcher.get('fullName'):
                        print(f"     Away Pitcher: {away_pitcher.get('fullName', 'TBD')}")
                        print(f"       ID: {away_pitcher.get('id', 'No ID')}")
                        print(f"       Throws: {away_pitcher.get('pitchHand', {}).get('code', 'Unknown')}")
                        print(f"       Throws Desc: {away_pitcher.get('pitchHand', {}).get('description', 'Unknown')}")
                    
                    # Lineups
                    lineups = game.get('lineups', {})
                    print(f"     Lineups: {type(lineups)} - {lineups}")
                    
                    if lineups:
                        for team_side in ['home', 'away']:
                            team_lineup = lineups.get(team_side, {})
                            print(f"       {team_side} lineup: {type(team_lineup)} - {team_lineup}")
                    
                    print(f"     Raw game keys: {list(game.keys())}")
        
        # Save raw response for analysis
        with open('debug_api_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Raw API response saved to debug_api_response.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_mlb_api()