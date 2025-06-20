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
        self.api_base_url = "https://statsapi.mlb.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BaseballTracker-LineupFetcher/1.0'
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
    
    def fetch_lineup_data(self, date_str: str = None) -> Optional[Dict]:
        """Fetch lineup data from MLB Stats API"""
        try:
            if not date_str:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.api_base_url}/schedule"
            params = {
                'sportId': 1,  # MLB
                'date': date_str,
                'hydrate': 'probablePitcher,lineups,venue,weather'
            }
            
            print(f"Fetching lineup data from MLB Stats API for {date_str}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"API returned {data.get('totalGames', 0)} games")
            return data
            
        except requests.RequestException as e:
            print(f"Error fetching lineup data: {e}")
            return None
    
    def parse_game_data(self, api_data: Dict) -> List[Dict]:
        """Parse game data from MLB Stats API response"""
        games = []
        seen_game_ids = set()
        
        try:
            if not api_data or 'dates' not in api_data:
                return games
            
            for date_obj in api_data['dates']:
                for game in date_obj.get('games', []):
                    game_data = self.extract_game_info_from_api(game)
                    if game_data:
                        game_id = game_data.get('gameId', '')
                        matchup_key = game_data.get('matchupKey', '')
                        
                        # Use game ID for true duplicate detection, not team matchup
                        if game_id and game_id not in seen_game_ids:
                            games.append(game_data)
                            seen_game_ids.add(game_id)
                            print(f"✅ Added game: {matchup_key} (ID: {game_id}) at {game_data.get('gameTime', 'TBD')}")
                        elif game_id in seen_game_ids:
                            print(f"⚠️ Skipping true duplicate game ID: {game_id}")
                        else:
                            print(f"⚠️ Game missing ID: {matchup_key}")
                        
        except Exception as e:
            print(f"Error parsing game data: {e}")
            
        return games
    
    def extract_game_info_from_api(self, game: Dict) -> Optional[Dict]:
        """Extract game information from MLB Stats API response"""
        try:
            # Parse game date/time
            game_date = game.get('gameDate', '')
            if game_date:
                dt = datetime.datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")
            else:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                time_str = ""
            
            game_data = {
                "gameId": str(game.get('gamePk', '')),
                "date": date_str,
                "gameTime": time_str,
                "timezone": "UTC",
                "status": game.get('status', {}).get('detailedState', 'Scheduled'),
                "venue": self.extract_venue_info(game.get('venue', {})),
                "weather": {},
                "teams": self.extract_teams_info(game.get('teams', {})),
                "pitchers": self.extract_pitchers_info(game.get('teams', {})),
                "lineups": self.extract_lineups_info(game.get('lineups', {})),
                "updates": [],
                "matchupKey": "",
                "pitcherMatchup": ""
            }
            
            # Generate quick lookup keys
            home_abbr = game_data["teams"]["home"].get("abbr", "")
            away_abbr = game_data["teams"]["away"].get("abbr", "")
            
            if home_abbr and away_abbr:
                # For doubleheaders, include game time to make matchup key unique
                base_matchup = f"{away_abbr}@{home_abbr}"
                game_time = game_data.get("gameTime", "")
                
                # Create unique matchup key for doubleheaders
                if game_time:
                    game_data["matchupKey"] = f"{base_matchup}_{game_time}"
                else:
                    game_data["matchupKey"] = base_matchup
                
                home_pitcher = game_data["pitchers"]["home"].get("name", "TBD")
                away_pitcher = game_data["pitchers"]["away"].get("name", "TBD")
                game_data["pitcherMatchup"] = f"{away_pitcher} vs {home_pitcher}"
                
                return game_data
                
        except Exception as e:
            print(f"Error extracting game info from API: {e}")
            
        return None
    
    def map_team_name_to_abbr(self, team_name: str) -> str:
        """Map team name to abbreviation"""
        team_mapping = {
            'Seattle Mariners': 'SEA',
            'Boston Red Sox': 'BOS',
            'Miami Marlins': 'MIA',
            'Philadelphia Phillies': 'PHI',
            'Washington Nationals': 'WSH',
            'Colorado Rockies': 'COL',
            'New York Yankees': 'NYY',
            'Los Angeles Angels': 'LAA',
            'Toronto Blue Jays': 'TOR',
            'Arizona Diamondbacks': 'ARI',
            'Cincinnati Reds': 'CIN',
            'Minnesota Twins': 'MIN',
            'Atlanta Braves': 'ATL',
            'New York Mets': 'NYM',
            'Tampa Bay Rays': 'TB', 
            'Baltimore Orioles': 'BAL',
            'Texas Rangers': 'TEX',
            'Kansas City Royals': 'KC',
            'San Francisco Giants': 'SF',
            'Cleveland Guardians': 'CLE',
            'Athletics': 'OAK',
            'Houston Astros': 'HOU',
            'Los Angeles Dodgers': 'LAD',
            'San Diego Padres': 'SD',
            'Detroit Tigers': 'DET',
            'Pittsburgh Pirates': 'PIT',
            'Chicago White Sox': 'CWS',
            'St. Louis Cardinals': 'STL',
            'Chicago Cubs': 'CHC',
            'Milwaukee Brewers': 'MIL'
        }
        return team_mapping.get(team_name, team_name)
    
    def extract_venue_info(self, venue: Dict) -> Dict:
        """Extract venue information from API response"""
        return {
            "name": venue.get('name', ''),
            "city": venue.get('location', {}).get('city', ''),
            "state": venue.get('location', {}).get('stateAbbrev', '')
        }
    
    def extract_teams_info(self, teams: Dict) -> Dict:
        """Extract team information from API response"""
        home_team = teams.get('home', {}).get('team', {})
        away_team = teams.get('away', {}).get('team', {})
        
        # Try multiple possible abbreviation field names
        def get_team_abbr(team_data):
            for field in ['abbreviation', 'abbrev', 'teamCode', 'fileCode']:
                if team_data.get(field):
                    return team_data[field]
            # Fallback - try to map team names to abbreviations
            return self.map_team_name_to_abbr(team_data.get('name', ''))
        
        return {
            "home": {
                "abbr": get_team_abbr(home_team),
                "name": home_team.get('name', ''),
                "record": {
                    "wins": teams.get('home', {}).get('leagueRecord', {}).get('wins', 0),
                    "losses": teams.get('home', {}).get('leagueRecord', {}).get('losses', 0)
                }
            },
            "away": {
                "abbr": get_team_abbr(away_team),
                "name": away_team.get('name', ''),
                "record": {
                    "wins": teams.get('away', {}).get('leagueRecord', {}).get('wins', 0),
                    "losses": teams.get('away', {}).get('leagueRecord', {}).get('losses', 0)
                }
            }
        }
    
    def extract_pitchers_info(self, teams: Dict) -> Dict:
        """Extract pitcher information from API response"""
        home_pitcher = teams.get('home', {}).get('probablePitcher', {})
        away_pitcher = teams.get('away', {}).get('probablePitcher', {})
        
        return {
            "home": {
                "name": home_pitcher.get('fullName', 'TBD'),
                "id": str(home_pitcher.get('id', '')),
                "throws": home_pitcher.get('pitchHand', {}).get('code', ''),
                "era": home_pitcher.get('seasonStats', {}).get('era', 0.0),
                "record": {
                    "wins": home_pitcher.get('seasonStats', {}).get('wins', 0),
                    "losses": home_pitcher.get('seasonStats', {}).get('losses', 0)
                },
                "lastStart": "",
                "status": "probable" if home_pitcher.get('fullName') else "unknown",
                "confidence": 90 if home_pitcher.get('fullName') else 0
            },
            "away": {
                "name": away_pitcher.get('fullName', 'TBD'),
                "id": str(away_pitcher.get('id', '')),
                "throws": away_pitcher.get('pitchHand', {}).get('code', ''),
                "era": away_pitcher.get('seasonStats', {}).get('era', 0.0),
                "record": {
                    "wins": away_pitcher.get('seasonStats', {}).get('wins', 0),
                    "losses": away_pitcher.get('seasonStats', {}).get('losses', 0)
                },
                "lastStart": "",
                "status": "probable" if away_pitcher.get('fullName') else "unknown",
                "confidence": 90 if away_pitcher.get('fullName') else 0
            }
        }
    
    def extract_lineups_info(self, lineups: Dict) -> Dict:
        """Extract lineup information from API response"""
        # Lineups might not always be available from Stats API
        # Use enhanced_lineup_scraper.py to populate batting_order arrays
        return {
            "home": {
                "confirmed": bool(lineups.get('home')),
                "lastUpdated": datetime.datetime.now().isoformat(),
                "batting_order": []  # Populated by enhanced_lineup_scraper.py
            },
            "away": {
                "confirmed": bool(lineups.get('away')),
                "lastUpdated": datetime.datetime.now().isoformat(),
                "batting_order": []  # Populated by enhanced_lineup_scraper.py
            }
        }
    
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
    
    def update_roster_with_handedness(self, pitcher_name: str, throws: str, team_abbr: str):
        """Update roster data with pitcher handedness from MLB API when missing"""
        if not throws or not pitcher_name or throws == "":
            return False
            
        # Convert MLB API throws code to roster format
        handedness_map = {
            'L': 'L',  # Left-handed
            'R': 'R',  # Right-handed  
            'S': 'B'   # Switch (both) - rare for pitchers but possible
        }
        
        roster_handedness = handedness_map.get(throws, throws)
        updated = False
        
        for player in self.rosters_data:
            if (player.get("type") == "pitcher" and 
                player.get("fullName") == pitcher_name):
                
                # Check if handedness is missing or empty
                if not player.get("ph") or player.get("ph") == "":
                    player["ph"] = roster_handedness
                    updated = True
                    print(f"✅ Updated {pitcher_name} handedness: {roster_handedness} ({team_abbr})")
                break
        
        return updated
    
    def save_updated_roster_data(self):
        """Save updated roster data back to file"""
        try:
            rosters_path = "../BaseballTracker/public/data/rosters.json"
            with open(rosters_path, 'w', encoding='utf-8') as f:
                json.dump(self.rosters_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ Error saving updated roster data: {e}")
            return False
    
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
            
            # Include ALL pitchers in byPitcher lookup, including TBD
            if home_pitcher.get("name"):
                by_pitcher[home_pitcher["name"]] = {
                    "team": home_team.get("abbr", ""),
                    "opponent": away_team.get("abbr", ""),
                    "opponentPitcher": away_pitcher.get("name", "TBD"),
                    "gameTime": game["gameTime"],
                    "venue": game["venue"]["name"]
                }
                
            if away_pitcher.get("name"):
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
                "scrapedFrom": self.api_base_url,
                "dataQuality": "partial" if len(games) < 8 else "complete",
                "nextUpdateScheduled": (now + datetime.timedelta(minutes=30)).isoformat()
            },
            "games": games,
            "quickLookup": quick_lookup,
            "alerts": [],
            "statistics": {
                "totalPitchers": len([p for g in games for p in [g["pitchers"]["home"], g["pitchers"]["away"]] if p.get("name")]),
                "confirmedPitchers": len([p for g in games for p in [g["pitchers"]["home"], g["pitchers"]["away"]] if p.get("status") == "confirmed"]),
                "probablePitchers": len([p for g in games for p in [g["pitchers"]["home"], g["pitchers"]["away"]] if p.get("status") == "probable"]),
                "tbdPitchers": len([p for g in games for p in [g["pitchers"]["home"], g["pitchers"]["away"]] if p.get("name") == "TBD"]),
                "scratchedPitchers": 0,
                "postponedGames": 0,
                "lineupsPosted": 0,
                "lineupsToBePosted": len(games)
            }
        }
        
        return lineup_data
    
    def save_lineup_data(self, lineup_data: Dict, date_str: str = None) -> str:
        """Save lineup data to JSON files in both dev and production directories"""
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
        filename = f"starting_lineups_{date_str}.json"
        
        # Save to both dev (public) and production (build) directories
        directories = [
            "../BaseballTracker/public/data/lineups",   # Dev environment
            "../BaseballTracker/build/data/lineups"     # Production environment
        ]
        
        saved_files = []
        
        for lineups_dir in directories:
            try:
                # Ensure directory exists
                os.makedirs(lineups_dir, exist_ok=True)
                
                filepath = os.path.join(lineups_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(lineup_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Lineup data saved to {filepath}")
                saved_files.append(filepath)
                
            except Exception as e:
                print(f"❌ Error saving to {lineups_dir}: {e}")
        
        if saved_files:
            print(f"📊 Found {lineup_data['totalGames']} games with {lineup_data['gamesWithLineups']} having lineup info")
            print(f"💾 Saved to {len(saved_files)} locations: dev + production")
            return saved_files[0]  # Return first successful save path
        else:
            print("❌ Failed to save to any location")
            return ""
    
    def fetch_todays_lineups(self) -> Optional[Dict]:
        """Main method to fetch today's starting lineups"""
        print("🔄 Fetching MLB starting lineups...")
        
        # Fetch the API data
        api_data = self.fetch_lineup_data()
        if not api_data:
            return None
        
        # Parse games
        games = self.parse_game_data(api_data)
        if not games:
            print("⚠️ No games found in API response")
            return None
        
        # Enhance roster data with pitcher handedness from MLB API
        roster_updates = 0
        for game in games:
            for pitcher_type in ['home', 'away']:
                pitcher = game['pitchers'][pitcher_type]
                team_abbr = game['teams'][pitcher_type]['abbr']
                
                if (pitcher.get('name') and pitcher['name'] != 'TBD' and 
                    pitcher.get('throws') and pitcher['throws'] != ''):
                    if self.update_roster_with_handedness(
                        pitcher['name'], pitcher['throws'], team_abbr):
                        roster_updates += 1
        
        # Save updated roster data if any changes were made
        if roster_updates > 0:
            if self.save_updated_roster_data():
                print(f"💾 Updated roster data with {roster_updates} pitcher handedness entries")
            else:
                print(f"⚠️ Failed to save {roster_updates} roster updates")
        
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