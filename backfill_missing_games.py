#!/usr/bin/env python3
"""
MLB Game Backfill Script
========================
Handles missing or incorrect game data by scraping specific ESPN game URLs
and updating the corresponding JSON files and CSV backups.

Usage:
    python backfill_missing_games.py --config games_to_backfill.json
    python backfill_missing_games.py --game-id 401696518 --date 2025-07-29
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import sys
import os

# Add BaseballScraper to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from config import PATHS, DATA_PATH
    CENTRALIZED_DATA = True
    print("✅ Using centralized data configuration")
except ImportError:
    # Fallback to relative paths
    CENTRALIZED_DATA = False
    DATA_PATH = Path("../BaseballData")
    print("⚠️  Using fallback data paths")

class GameBackfiller:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if CENTRALIZED_DATA:
            self.data_path = DATA_PATH
            self.csv_backup_path = PATHS["csv_backups"]
        else:
            self.data_path = DATA_PATH / "data"
            self.csv_backup_path = DATA_PATH / "CSV_BACKUPS"
    
    def scrape_game_data(self, game_id):
        """Scrape game data from ESPN game URL"""
        url = f"https://www.espn.com/mlb/game/_/gameId/{game_id}/"
        print(f"🔄 Scraping game {game_id} from {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract game data
            game_data = self._extract_game_info(soup, game_id)
            player_data = self._extract_player_stats(soup, game_id)
            
            return {
                'game': game_data,
                'players': player_data
            }
            
        except Exception as e:
            print(f"❌ Error scraping game {game_id}: {e}")
            return None
    
    def _extract_game_info(self, soup, game_id):
        """Extract basic game information"""
        try:
            # Use known results first for the specific games we're fixing
            known_results = {
                '401696518': ('TOR', 2, 'BAL', 3),  # TOR@BAL Game 2
                '401696561': ('ATL', 4, 'CIN', 2),  # ATL@CIN suspended 
                '401800822': ('CLE', 4, 'CHW', 2),  # CLE@CHW Game 1 - July 11 doubleheader
                '401696319': ('CLE', 4, 'CHW', 5),  # CLE@CHW Game 2 - July 11 doubleheader (11 innings)
            }
            
            if game_id in known_results:
                away_team, away_score, home_team, home_score = known_results[game_id]
                print(f"🎯 Using known result for {game_id}: {away_team} {away_score}, {home_team} {home_score}")
                
                # Extract venue and other details
                venue = self._extract_venue(soup)
                date_time = self._extract_datetime(soup)
                
                return {
                    'homeTeam': home_team,
                    'awayTeam': away_team,
                    'homeScore': home_score,
                    'awayScore': away_score,
                    'status': 'Final',
                    'venue': venue,
                    'attendance': 0,
                    'originalId': int(game_id),
                    'dateTime': date_time,
                    'round': 18
                }
            
            # Fallback to scraping for other games
            teams = soup.find_all('div', class_='ScoreCell__TeamName')
            scores = soup.find_all('div', class_='ScoreCell__Score')
            
            if len(teams) >= 2 and len(scores) >= 2:
                away_team = self._normalize_team_name(teams[0].text.strip())
                home_team = self._normalize_team_name(teams[1].text.strip()) 
                
                away_score = int(scores[0].text.strip()) if scores[0].text.strip().isdigit() else 0
                home_score = int(scores[1].text.strip()) if scores[1].text.strip().isdigit() else 0
                
                # Extract venue and other details
                venue = self._extract_venue(soup)
                date_time = self._extract_datetime(soup)
                
                return {
                    'homeTeam': home_team,
                    'awayTeam': away_team,
                    'homeScore': home_score,
                    'awayScore': away_score,
                    'status': 'Final',
                    'venue': venue,
                    'attendance': 0,
                    'originalId': int(game_id),
                    'dateTime': date_time,
                    'round': 18
                }
            else:
                raise ValueError("Could not find team names and scores via scraping")
                
        except Exception as e:
            print(f"⚠️  Error extracting game info: {e}")
            return None
    
    def _extract_player_stats(self, soup, game_id):
        """Extract player statistics"""
        players = []
        
        try:
            # Look for batting tables
            batting_tables = soup.find_all('table', class_='Table')
            
            for table in batting_tables:
                team_header = table.find_previous('h3')
                if team_header:
                    team_name = self._normalize_team_name(team_header.text)
                    
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 8:  # Minimum for batting stats
                            player_name = cells[0].text.strip()
                            if player_name and not any(x in player_name.lower() for x in ['total', 'team']):
                                player_stats = {
                                    'name': player_name,
                                    'team': team_name,
                                    'gameId': game_id,
                                    'playerType': 'hitter',
                                    'AB': int(cells[1].text.strip() or 0),
                                    'R': int(cells[2].text.strip() or 0),
                                    'H': int(cells[3].text.strip() or 0),
                                    'RBI': int(cells[4].text.strip() or 0),
                                    'HR': int(cells[5].text.strip() or 0),
                                    'BB': int(cells[6].text.strip() or 0)
                                }
                                players.append(player_stats)
            
            # Look for pitching tables (simplified)
            pitching_sections = soup.find_all('section', class_='Pitching')
            for section in pitching_sections:
                # Extract pitching stats (basic implementation)
                pass
                
        except Exception as e:
            print(f"⚠️  Error extracting player stats: {e}")
        
        return players
    
    def _normalize_team_name(self, name):
        """Convert team names to standard 3-letter codes"""
        team_map = {
            'Blue Jays': 'TOR', 'Toronto': 'TOR',
            'Orioles': 'BAL', 'Baltimore': 'BAL',
            'Braves': 'ATL', 'Atlanta': 'ATL',
            'Reds': 'CIN', 'Cincinnati': 'CIN',
            'Guardians': 'CLE', 'Cleveland': 'CLE',
            'White Sox': 'CHW', 'Chicago': 'CHW',
            'Padres': 'SD', 'San Diego': 'SD',
            'Phillies': 'PHI', 'Philadelphia': 'PHI',
            'Tigers': 'DET', 'Detroit': 'DET',
            'Nationals': 'WSH', 'Washington': 'WSH',
            'Brewers': 'MIL', 'Milwaukee': 'MIL',
            'Mets': 'NYM', 'New York': 'NYM'
        }
        
        for key, code in team_map.items():
            if key.lower() in name.lower():
                return code
        return name[:3].upper()  # Fallback
    
    def _extract_venue(self, soup):
        """Extract venue information"""
        venue_elem = soup.find('div', class_='GameInfo__Location')
        return venue_elem.text.strip() if venue_elem else "Unknown Venue"
    
    def _extract_datetime(self, soup):
        """Extract game datetime"""
        # This is simplified - ESPN datetime extraction can be complex
        return f"{datetime.now().strftime('%Y-%m-%d')} 19:00:00Z"
    
    def update_json_file(self, date_str, game_data, player_data):
        """Update the JSON file for the specified date"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month_name = date_obj.strftime('%B').lower()
        
        json_path = self.data_path / "2025" / month_name / f"{month_name}_{date_obj.day:02d}_2025.json"
        
        if not json_path.exists():
            print(f"❌ JSON file not found: {json_path}")
            return False
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Update or add game
            game_updated = False
            for i, game in enumerate(data['games']):
                if game['originalId'] == game_data['originalId']:
                    # Update existing game, preserving important fields
                    data['games'][i]['homeScore'] = game_data['homeScore']
                    data['games'][i]['awayScore'] = game_data['awayScore']
                    data['games'][i]['status'] = game_data['status']
                    if game_data.get('venue'):
                        data['games'][i]['venue'] = game_data['venue']
                    game_updated = True
                    print(f"✅ Updated existing game {game_data['originalId']} with final scores")
                    break
                # Also check for games with originalId 1607 (placeholder) for the same teams
                elif (game.get('originalId') == 1607 and 
                      game.get('homeTeam') == game_data.get('homeTeam') and
                      game.get('awayTeam') == game_data.get('awayTeam')):
                    # Replace placeholder game with real data
                    data['games'][i].update(game_data)
                    game_updated = True
                    print(f"✅ Replaced placeholder game with {game_data['originalId']}")
                    break
            
            if not game_updated:
                # Add new game
                data['games'].append(game_data)
                print(f"✅ Added new game {game_data['originalId']}")
            
            # Update or add players
            existing_player_ids = {p.get('gameId') for p in data.get('players', [])}
            if str(game_data['originalId']) not in existing_player_ids:
                if 'players' not in data:
                    data['players'] = []
                data['players'].extend(player_data)
                print(f"✅ Added {len(player_data)} player records")
            
            # Write back to file, preserving Unicode characters
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated {json_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating JSON file: {e}")
            return False
    
    def create_csv_backup(self, date_str, game_data, player_data):
        """Create/update CSV backup file"""
        csv_filename = f"mlb_games_{date_str.replace('-', '_')}.csv"
        csv_path = self.csv_backup_path / csv_filename
        
        try:
            # Prepare CSV data
            csv_data = []
            
            # Add game row
            csv_data.append({
                'Date': date_str,
                'Away Team': game_data['awayTeam'],
                'Home Team': game_data['homeTeam'],
                'Away Score': game_data['awayScore'],
                'Home Score': game_data['homeScore'],
                'Game ID': game_data['originalId'],
                'Status': game_data['status'],
                'Venue': game_data['venue']
            })
            
            df = pd.DataFrame(csv_data)
            
            if csv_path.exists():
                # Append to existing
                existing_df = pd.read_csv(csv_path)
                # Remove duplicates based on Game ID
                existing_df = existing_df[existing_df['Game ID'] != game_data['originalId']]
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_csv(csv_path, index=False)
            print(f"✅ Updated CSV backup: {csv_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating CSV backup: {e}")
            return False
    
    def backfill_game(self, game_id, date_str):
        """Backfill a specific game"""
        print(f"\n🎯 Backfilling game {game_id} for {date_str}")
        
        # Scrape game data
        scraped_data = self.scrape_game_data(game_id)
        if not scraped_data:
            print(f"❌ Failed to scrape game {game_id}")
            return False
        
        game_data = scraped_data['game']
        player_data = scraped_data['players']
        
        if not game_data:
            print(f"❌ No game data extracted for {game_id}")
            return False
        
        # Update JSON file
        json_success = self.update_json_file(date_str, game_data, player_data)
        
        # Create CSV backup
        csv_success = self.create_csv_backup(date_str, game_data, player_data)
        
        if json_success and csv_success:
            print(f"✅ Successfully backfilled game {game_id}")
            return True
        else:
            print(f"⚠️  Partial success for game {game_id}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Backfill missing MLB games')
    parser.add_argument('--config', help='JSON config file with games to backfill')
    parser.add_argument('--game-id', help='Single game ID to backfill')
    parser.add_argument('--date', help='Date in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    backfiller = GameBackfiller()
    
    if args.config:
        # Load config file
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        for game in config['games']:
            backfiller.backfill_game(game['game_id'], game['date'])
    
    elif args.game_id and args.date:
        # Single game backfill
        backfiller.backfill_game(args.game_id, args.date)
    
    else:
        # Default: process known issues
        known_issues = [
            {'game_id': '401696518', 'date': '2025-07-29'},  # TOR@BAL Game 2
            {'game_id': '401696561', 'date': '2025-08-02'},  # ATL@CIN suspended
            {'game_id': '401800822', 'date': '2025-07-12'},  # CLE@CHW Game 1
            {'game_id': '401696319', 'date': '2025-07-12'},  # CLE@CHW Game 2 (makeup)
        ]
        
        print("🚀 Starting backfill for known issues...")
        for issue in known_issues:
            backfiller.backfill_game(issue['game_id'], issue['date'])

if __name__ == '__main__':
    main()