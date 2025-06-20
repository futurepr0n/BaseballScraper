#!/usr/bin/env python3
"""
Enhanced MLB Lineup Scraper
Fetches starting lineups from MLB.com with batting order, positions, and handedness
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import os

class MLBLineupScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://www.mlb.com/starting-lineups"
        
    def get_lineup_page(self, date_str):
        """Fetch the MLB starting lineups page for a specific date"""
        url = f"{self.base_url}/{date_str}"
        
        try:
            print(f"🔍 Fetching lineup data from: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching lineup page: {e}")
            return None
    
    def parse_handedness(self, handedness_text):
        """Convert MLB.com handedness format to standard format"""
        if not handedness_text:
            return None
            
        text = handedness_text.strip().upper()
        if 'LHP' in text or text == 'L':
            return 'L'
        elif 'RHP' in text or text == 'R':
            return 'R'
        elif 'B' in text or 'SWITCH' in text:
            return 'B'
        else:
            return None
    
    def parse_position(self, position_text):
        """Standardize position abbreviations"""
        if not position_text:
            return None
            
        position_map = {
            'C': 'C', 'CATCHER': 'C',
            '1B': '1B', 'FIRST': '1B', 'FIRST BASE': '1B',
            '2B': '2B', 'SECOND': '2B', 'SECOND BASE': '2B',
            '3B': '3B', 'THIRD': '3B', 'THIRD BASE': '3B',
            'SS': 'SS', 'SHORTSTOP': 'SS',
            'LF': 'LF', 'LEFT': 'LF', 'LEFT FIELD': 'LF',
            'CF': 'CF', 'CENTER': 'CF', 'CENTER FIELD': 'CF',
            'RF': 'RF', 'RIGHT': 'RF', 'RIGHT FIELD': 'RF',
            'DH': 'DH', 'DESIGNATED HITTER': 'DH'
        }
        
        pos = position_text.strip().upper()
        return position_map.get(pos, pos)
    
    def extract_team_lineup(self, team_section):
        """Extract lineup data from a team's section on the page"""
        lineup = []
        
        try:
            # Look for batting order list items
            batting_order_items = team_section.find_all(['li', 'div'], class_=re.compile(r'lineup|batter|player'))
            
            for i, item in enumerate(batting_order_items[:9]):  # Only first 9 batters
                player_data = {}
                
                # Extract player name
                name_element = item.find(['span', 'div', 'a'], class_=re.compile(r'name|player'))
                if name_element:
                    player_data['name'] = name_element.get_text(strip=True)
                
                # Extract position
                position_element = item.find(['span', 'div'], class_=re.compile(r'position|pos'))
                if position_element:
                    player_data['position'] = self.parse_position(position_element.get_text(strip=True))
                
                # Extract handedness (look for (L), (R), (B) patterns)
                handedness_match = re.search(r'\(([LRB])\)', item.get_text())
                if handedness_match:
                    player_data['bats'] = handedness_match.group(1)
                
                # Set batting order
                player_data['order'] = i + 1
                
                # Only add if we have essential data
                if player_data.get('name'):
                    lineup.append(player_data)
                    
        except Exception as e:
            print(f"⚠️ Error parsing team lineup: {e}")
            
        return lineup
    
    def scrape_lineups(self, date_str):
        """Scrape all lineups for a specific date"""
        html_content = self.get_lineup_page(date_str)
        if not html_content:
            return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        lineups = {}
        
        try:
            # Look for game containers
            game_containers = soup.find_all(['div', 'section'], class_=re.compile(r'game|matchup|lineup'))
            
            for container in game_containers:
                # Extract team information
                team_elements = container.find_all(['div', 'span'], class_=re.compile(r'team|club'))
                
                if len(team_elements) >= 2:
                    # Process both teams in the matchup
                    for team_element in team_elements[:2]:
                        team_name = team_element.get_text(strip=True)
                        team_abbr = self.get_team_abbreviation(team_name)
                        
                        if team_abbr:
                            # Find the lineup section for this team
                            team_lineup_section = team_element.find_parent().find_next(['div', 'ul'], class_=re.compile(r'lineup|batting'))
                            
                            if team_lineup_section:
                                lineup = self.extract_team_lineup(team_lineup_section)
                                if lineup:
                                    lineups[team_abbr] = {
                                        'confirmed': True,
                                        'lastUpdated': datetime.now().isoformat(),
                                        'batting_order': lineup
                                    }
                                    print(f"✅ Extracted lineup for {team_abbr}: {len(lineup)} players")
        
        except Exception as e:
            print(f"❌ Error scraping lineups: {e}")
        
        return lineups
    
    def get_team_abbreviation(self, team_name):
        """Convert team name to standard abbreviation"""
        team_map = {
            'ARIZONA': 'ARI', 'DIAMONDBACKS': 'ARI', 'D-BACKS': 'ARI',
            'ATLANTA': 'ATL', 'BRAVES': 'ATL',
            'BALTIMORE': 'BAL', 'ORIOLES': 'BAL',
            'BOSTON': 'BOS', 'RED SOX': 'BOS',
            'CHICAGO CUBS': 'CHC', 'CUBS': 'CHC',
            'CHICAGO WHITE SOX': 'CHW', 'WHITE SOX': 'CHW',
            'CINCINNATI': 'CIN', 'REDS': 'CIN',
            'CLEVELAND': 'CLE', 'GUARDIANS': 'CLE',
            'COLORADO': 'COL', 'ROCKIES': 'COL',
            'DETROIT': 'DET', 'TIGERS': 'DET',
            'HOUSTON': 'HOU', 'ASTROS': 'HOU',
            'KANSAS CITY': 'KC', 'ROYALS': 'KC',
            'LOS ANGELES ANGELS': 'LAA', 'ANGELS': 'LAA',
            'LOS ANGELES DODGERS': 'LAD', 'DODGERS': 'LAD',
            'MIAMI': 'MIA', 'MARLINS': 'MIA',
            'MILWAUKEE': 'MIL', 'BREWERS': 'MIL',
            'MINNESOTA': 'MIN', 'TWINS': 'MIN',
            'NEW YORK METS': 'NYM', 'METS': 'NYM',
            'NEW YORK YANKEES': 'NYY', 'YANKEES': 'NYY',
            'OAKLAND': 'OAK', 'ATHLETICS': 'OAK', "A'S": 'OAK',
            'PHILADELPHIA': 'PHI', 'PHILLIES': 'PHI',
            'PITTSBURGH': 'PIT', 'PIRATES': 'PIT',
            'SAN DIEGO': 'SD', 'PADRES': 'SD',
            'SAN FRANCISCO': 'SF', 'GIANTS': 'SF',
            'SEATTLE': 'SEA', 'MARINERS': 'SEA',
            'ST. LOUIS': 'STL', 'CARDINALS': 'STL',
            'TAMPA BAY': 'TB', 'RAYS': 'TB',
            'TEXAS': 'TEX', 'RANGERS': 'TEX',
            'TORONTO': 'TOR', 'BLUE JAYS': 'TOR',
            'WASHINGTON': 'WSH', 'NATIONALS': 'WSH'
        }
        
        name = team_name.upper().strip()
        return team_map.get(name)
    
    def update_lineup_file(self, date_str, scraped_lineups):
        """Update existing lineup JSON files with scraped data in both dev and production"""
        
        # Files to update in both dev and production directories
        lineup_files = [
            f"../BaseballTracker/public/data/lineups/starting_lineups_{date_str}.json",  # Dev
            f"../BaseballTracker/build/data/lineups/starting_lineups_{date_str}.json"   # Production
        ]
        
        updated_files = 0
        
        for lineup_file in lineup_files:
            try:
                # Load existing file
                if os.path.exists(lineup_file):
                    with open(lineup_file, 'r') as f:
                        lineup_data = json.load(f)
                else:
                    print(f"⚠️ Lineup file not found: {lineup_file}")
                    continue
            
                # Update lineups for each game
                updated_count = 0
                for game in lineup_data.get('games', []):
                    home_team = game['teams']['home']['abbr']
                    away_team = game['teams']['away']['abbr']
                    
                    # Update home team lineup
                    if home_team in scraped_lineups:
                        game['lineups']['home'] = scraped_lineups[home_team]
                        updated_count += 1
                    
                    # Update away team lineup
                    if away_team in scraped_lineups:
                        game['lineups']['away'] = scraped_lineups[away_team]
                        updated_count += 1
                
                # Update metadata
                lineup_data['lastUpdated'] = datetime.now().isoformat()
                lineup_data['gamesWithLineups'] = updated_count // 2  # Each game has 2 teams
                
                # Save updated file
                with open(lineup_file, 'w') as f:
                    json.dump(lineup_data, f, indent=2)
                
                print(f"✅ Updated {lineup_file}: {updated_count} lineups updated")
                updated_files += 1
                
            except Exception as e:
                print(f"❌ Error updating {lineup_file}: {e}")
        
        if updated_files > 0:
            print(f"💾 Successfully updated {updated_files} lineup files (dev + production)")
            return True
        else:
            print("❌ Failed to update any lineup files")
            return False

def main():
    """Main execution function"""
    scraper = MLBLineupScraper()
    
    # Get today's date
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    
    print(f"🏟️ Enhanced MLB Lineup Scraper")
    print(f"📅 Scraping lineups for: {date_str}")
    print("=" * 50)
    
    # Scrape lineups
    lineups = scraper.scrape_lineups(date_str)
    
    if lineups:
        print(f"\n📊 Successfully scraped {len(lineups)} team lineups")
        
        # Update the lineup file
        success = scraper.update_lineup_file(date_str, lineups)
        
        if success:
            print("✅ Lineup data successfully integrated!")
        else:
            print("❌ Failed to update lineup file")
    else:
        print("❌ No lineup data scraped")

if __name__ == "__main__":
    main()