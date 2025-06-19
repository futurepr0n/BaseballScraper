#!/usr/bin/env python3
"""
MLB Starting Lineup Fetcher
Fetches starting lineups from MLB.com and generates comprehensive lineup data
for use in BaseballTracker Pinheads-Playhouse component.
"""

import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import sys
from typing import Dict, List, Optional, Any
import time
import re

# Add BaseballTracker path for access to team/roster data
sys.path.append('../BaseballTracker/src/services')

class StartingLineupFetcher:
    def __init__(self):
        self.base_url = "https://www.mlb.com/starting-lineups"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load team and roster data for validation
        self.teams_data = self.load_teams_data()
        self.rosters_data = self.load_rosters_data()
        
    def load_teams_data(self) -> Dict:
        """Load team data from BaseballTracker"""
        try:
            teams_path = "../BaseballTracker/public/data/teams.json"
            if os.path.exists(teams_path):
                with open(teams_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load teams data: {e}")
        return {}
    
    def load_rosters_data(self) -> List:
        """Load roster data from BaseballTracker"""
        try:
            rosters_path = "../BaseballTracker/public/data/rosters.json"
            if os.path.exists(rosters_path):
                with open(rosters_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load rosters data: {e}")
        return []
    
    def fetch_lineup_page(self) -> Optional[str]:
        """Fetch the MLB starting lineups page"""
        try:
            print(f"Fetching lineup data from {self.base_url}")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching lineup page: {e}")
            return None
    
    def parse_game_data(self, html_content: str) -> List[Dict]:
        """Parse game data from MLB lineup page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        games = []
        
        try:
            # Look for game containers - MLB.com structure may vary
            game_containers = soup.find_all(['div', 'article'], class_=re.compile(r'game|lineup|matchup', re.I))
            
            if not game_containers:
                # Try alternative selectors
                game_containers = soup.find_all(['div'], attrs={'data-game-pk': True})
            
            for container in game_containers:
                game_data = self.extract_game_info(container)
                if game_data:
                    games.append(game_data)
                    
        except Exception as e:
            print(f"Error parsing game data: {e}")
            
        return games
    
    def extract_game_info(self, container) -> Optional[Dict]:
        """Extract game information from a game container"""
        try:
            game_data = {
                "gameId": "",
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "gameTime": "",
                "timezone": "ET",
                "status": "scheduled",
                "venue": {"name": "", "city": "", "state": ""},
                "weather": {},
                "teams": {"home": {}, "away": {}},
                "pitchers": {"home": {}, "away": {}},
                "lineups": {"home": {"confirmed": False, "batting_order": []}, 
                           "away": {"confirmed": False, "batting_order": []}},
                "updates": [],
                "matchupKey": "",
                "pitcherMatchup": ""
            }
            
            # Extract game ID
            game_id = container.get('data-game-pk') or container.get('data-gameid')
            if game_id:
                game_data["gameId"] = str(game_id)
            
            # Extract team information
            self.extract_team_info(container, game_data)
            
            # Extract pitcher information
            self.extract_pitcher_info(container, game_data)
            
            # Extract game time and venue
            self.extract_game_details(container, game_data)
            
            # Generate quick lookup keys
            if game_data["teams"]["home"].get("abbr") and game_data["teams"]["away"].get("abbr"):
                away_abbr = game_data["teams"]["away"]["abbr"]
                home_abbr = game_data["teams"]["home"]["abbr"]
                game_data["matchupKey"] = f"{away_abbr}@{home_abbr}"
                
                home_pitcher = game_data["pitchers"]["home"].get("name", "TBD")
                away_pitcher = game_data["pitchers"]["away"].get("name", "TBD")
                game_data["pitcherMatchup"] = f"{away_pitcher} vs {home_pitcher}"
                
                return game_data
                
        except Exception as e:
            print(f"Error extracting game info: {e}")
            
        return None
    
    def extract_team_info(self, container, game_data: Dict):
        """Extract team information from container"""
        # Look for team elements
        team_elements = container.find_all(['div', 'span'], class_=re.compile(r'team|club', re.I))
        
        for element in team_elements:
            # Try to identify team abbreviations
            text = element.get_text(strip=True)
            if len(text) == 3 and text.upper() in self.teams_data:
                abbr = text.upper()
                team_info = {
                    "abbr": abbr,
                    "name": self.teams_data[abbr].get("name", abbr),
                    "record": {"wins": 0, "losses": 0}  # Placeholder
                }
                
                # Determine if home or away (rough heuristic)
                if not game_data["teams"]["away"].get("abbr"):
                    game_data["teams"]["away"] = team_info
                elif not game_data["teams"]["home"].get("abbr"):
                    game_data["teams"]["home"] = team_info
    
    def extract_pitcher_info(self, container, game_data: Dict):
        """Extract pitcher information from container"""
        pitcher_elements = container.find_all(['div', 'span'], string=re.compile(r'pitcher|starting', re.I))
        
        for element in pitcher_elements:
            # Look for pitcher names in nearby elements
            pitcher_name = self.find_pitcher_name(element)
            if pitcher_name:
                pitcher_info = {
                    "name": pitcher_name,
                    "id": "",
                    "throws": "",
                    "era": 0.0,
                    "record": {"wins": 0, "losses": 0},
                    "lastStart": "",
                    "status": "probable",
                    "confidence": 75
                }
                
                # Try to match with roster data
                self.enrich_pitcher_data(pitcher_info)
                
                # Assign to home or away
                if not game_data["pitchers"]["away"].get("name"):
                    game_data["pitchers"]["away"] = pitcher_info
                elif not game_data["pitchers"]["home"].get("name"):
                    game_data["pitchers"]["home"] = pitcher_info
    
    def find_pitcher_name(self, element) -> Optional[str]:
        """Find pitcher name near the given element"""
        # Look in siblings and parent elements for names
        for sibling in element.find_next_siblings():
            text = sibling.get_text(strip=True)
            if self.looks_like_player_name(text):
                return text
                
        # Look in parent container
        parent = element.parent
        if parent:
            names = parent.find_all(string=lambda text: self.looks_like_player_name(text) if text else False)
            if names:
                return names[0].strip()
                
        return None
    
    def looks_like_player_name(self, text: str) -> bool:
        """Check if text looks like a player name"""
        if not text or len(text) < 5:
            return False
            
        # Simple heuristics for player names
        words = text.split()
        if len(words) >= 2:
            # Check if it contains common name patterns
            if all(word.isalpha() for word in words):
                return True
                
        return False
    
    def enrich_pitcher_data(self, pitcher_info: Dict):
        """Enrich pitcher data with roster information"""
        name = pitcher_info["name"]
        for player in self.rosters_data:
            if (player.get("type") == "pitcher" and 
                player.get("fullName") == name):
                pitcher_info["id"] = player.get("id", "")
                pitcher_info["throws"] = player.get("throws", "")
                break
    
    def extract_game_details(self, container, game_data: Dict):
        """Extract game time and venue information"""
        # Look for time elements
        time_elements = container.find_all(['div', 'span'], string=re.compile(r'\d{1,2}:\d{2}', re.I))
        if time_elements:
            game_data["gameTime"] = time_elements[0].get_text(strip=True)
        
        # Look for venue information
        venue_elements = container.find_all(['div', 'span'], class_=re.compile(r'venue|stadium|ballpark', re.I))
        if venue_elements:
            venue_text = venue_elements[0].get_text(strip=True)
            game_data["venue"]["name"] = venue_text
    
    def build_quick_lookup_tables(self, games: List[Dict]) -> Dict:
        """Build quick lookup tables for teams and pitchers"""
        by_team = {}
        by_pitcher = {}
        
        for game in games:
            home_team = game["teams"]["home"]
            away_team = game["teams"]["away"]
            home_pitcher = game["pitchers"]["home"]
            away_pitcher = game["pitchers"]["away"]
            
            if home_team.get("abbr"):
                by_team[home_team["abbr"]] = {
                    "pitcher": home_pitcher.get("name", "TBD"),
                    "opponent": away_team.get("abbr", ""),
                    "opponentPitcher": away_pitcher.get("name", "TBD"),
                    "gameTime": game["gameTime"],
                    "homeAway": "home"
                }
                
            if away_team.get("abbr"):
                by_team[away_team["abbr"]] = {
                    "pitcher": away_pitcher.get("name", "TBD"),
                    "opponent": home_team.get("abbr", ""),
                    "opponentPitcher": home_pitcher.get("name", "TBD"),
                    "gameTime": game["gameTime"],
                    "homeAway": "away"
                }
            
            if home_pitcher.get("name") and home_pitcher["name"] != "TBD":
                by_pitcher[home_pitcher["name"]] = {
                    "team": home_team.get("abbr", ""),
                    "opponent": away_team.get("abbr", ""),
                    "opponentPitcher": away_pitcher.get("name", "TBD"),
                    "gameTime": game["gameTime"],
                    "venue": game["venue"]["name"]
                }
                
            if away_pitcher.get("name") and away_pitcher["name"] != "TBD":
                by_pitcher[away_pitcher["name"]] = {
                    "team": away_team.get("abbr", ""),
                    "opponent": home_team.get("abbr", ""),
                    "opponentPitcher": home_pitcher.get("name", "TBD"),
                    "gameTime": game["gameTime"],
                    "venue": game["venue"]["name"]
                }
        
        return {"byTeam": by_team, "byPitcher": by_pitcher}
    
    def generate_lineup_data(self, games: List[Dict]) -> Dict:
        """Generate complete lineup data structure"""
        now = datetime.datetime.now()
        quick_lookup = self.build_quick_lookup_tables(games)
        
        lineup_data = {
            "date": now.strftime("%Y-%m-%d"),
            "lastUpdated": now.isoformat(),
            "updateCount": 1,
            "totalGames": len(games),
            "gamesWithLineups": len([g for g in games if g["pitchers"]["home"].get("name") != "TBD"]),
            "metadata": {
                "scrapedFrom": self.base_url,
                "dataQuality": "partial" if len(games) < 8 else "complete",
                "nextUpdateScheduled": (now + datetime.timedelta(minutes=30)).isoformat()
            },
            "games": games,
            "quickLookup": quick_lookup,
            "alerts": [],
            "statistics": {
                "confirmedPitchers": len([g for g in games if 
                                        g["pitchers"]["home"].get("status") == "confirmed" or
                                        g["pitchers"]["away"].get("status") == "confirmed"]),
                "probablePitchers": len([g for g in games if 
                                       g["pitchers"]["home"].get("status") == "probable" or
                                       g["pitchers"]["away"].get("status") == "probable"]),
                "scratchedPitchers": 0,
                "postponedGames": 0,
                "lineupsPosted": 0,
                "lineupsToBePosted": len(games)
            }
        }
        
        return lineup_data
    
    def save_lineup_data(self, lineup_data: Dict, date_str: str = None) -> str:
        """Save lineup data to JSON file"""
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
        # Ensure lineups directory exists
        lineups_dir = "../BaseballTracker/public/data/lineups"
        os.makedirs(lineups_dir, exist_ok=True)
        
        filename = f"starting_lineups_{date_str}.json"
        filepath = os.path.join(lineups_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(lineup_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Lineup data saved to {filepath}")
            print(f"📊 Found {lineup_data['totalGames']} games with {lineup_data['gamesWithLineups']} having lineup info")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving lineup data: {e}")
            return ""
    
    def fetch_todays_lineups(self) -> Optional[Dict]:
        """Main method to fetch today's starting lineups"""
        print("🔄 Fetching MLB starting lineups...")
        
        # Fetch the page
        html_content = self.fetch_lineup_page()
        if not html_content:
            return None
        
        # Parse games
        games = self.parse_game_data(html_content)
        if not games:
            print("⚠️ No games found on lineup page")
            return None
        
        # Generate complete data structure
        lineup_data = self.generate_lineup_data(games)
        
        # Save to file
        filepath = self.save_lineup_data(lineup_data)
        if filepath:
            return lineup_data
            
        return None

def main():
    """Main execution function"""
    fetcher = StartingLineupFetcher()
    lineup_data = fetcher.fetch_todays_lineups()
    
    if lineup_data:
        print(f"✅ Successfully fetched lineup data for {lineup_data['totalGames']} games")
        
        # Print summary
        print("\n📋 Today's Matchups:")
        for team, data in lineup_data['quickLookup']['byTeam'].items():
            print(f"  {team}: {data['pitcher']} vs {data['opponent']} ({data['opponentPitcher']})")
            
        return True
    else:
        print("❌ Failed to fetch lineup data")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)