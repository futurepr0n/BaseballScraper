#!/usr/bin/env python3
"""
MLB Wildcard Standings Scraper
Scrapes current MLB standings with playoff implications from ESPN
Generates JSON file for use by BaseballTracker DailyWeakspotAnalysis
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WildcardStandingsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_espn_standings(self):
        """Scrape MLB standings from ESPN with wildcard context"""
        print("🏆 Scraping MLB standings from ESPN...")
        
        try:
            url = "https://www.espn.com/mlb/standings/_/view/wild-card"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find standings tables
            standings_data = {}
            
            # Look for American League and National League sections
            for league in ['American League', 'National League']:
                league_abbr = 'AL' if league == 'American League' else 'NL'
                standings_data[league_abbr] = {
                    'East': [],
                    'Central': [], 
                    'West': [],
                    'wildcard_standings': []
                }
                
            # ESPN uses separate tables for team names and stats
            tables = soup.find_all('table')
            
            if len(tables) >= 4:
                # Expected structure: AL teams, AL stats, NL teams, NL stats
                al_teams_table = tables[0]
                al_stats_table = tables[1] 
                nl_teams_table = tables[2]
                nl_stats_table = tables[3]
                
                # Process American League
                standings_data['AL'] = self.process_league_tables(al_teams_table, al_stats_table, 'AL')
                
                # Process National League  
                standings_data['NL'] = self.process_league_tables(nl_teams_table, nl_stats_table, 'NL')
                
                # Check if we have all expected teams
                all_teams = set()
                for league_data in standings_data.values():
                    for division_data in league_data.values():
                        if isinstance(division_data, list):
                            for team in division_data:
                                all_teams.add(team['team'])
                
                expected_teams = self.AL_TEAMS | self.NL_TEAMS
                missing_teams = expected_teams - all_teams
                
                if missing_teams:
                    print(f"⚠️  Missing teams from scrape: {sorted(missing_teams)}")
                    print(f"📊 Adding fallback data for missing teams...")
                    self.add_missing_teams_fallback(standings_data, missing_teams)
                
            else:
                print(f"⚠️  Unexpected table structure - found {len(tables)} tables, expected 4")
                return None
            
            return standings_data
            
        except Exception as e:
            print(f"❌ Error scraping ESPN standings: {e}")
            return None
    
    def process_league_tables(self, teams_table, stats_table, league):
        """Process paired team names and stats tables for a league"""
        teams_data = {
            'East': [],
            'Central': [],
            'West': [],
            'wildcard_standings': []
        }
        
        # Extract team names
        team_rows = teams_table.find_all('tr')
        team_names = []
        
        for row in team_rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 1:
                team_text = cells[0].get_text(strip=True)
                print(f"🔍 Parsing team text: '{team_text}'")
                
                # Try to extract team abbreviation and name
                # ESPN format varies, try multiple approaches
                team_abbr = None
                team_name = None
                
                # Method 1: Try regex for "BOSBoston Red Sox" format
                match = re.match(r'^([A-Z]{2,3})(.+)$', team_text)
                if match:
                    potential_abbr = match.group(1)
                    potential_name = match.group(2).strip()
                    
                    # Use team name mapping to get correct abbreviation
                    correct_abbr = self.get_team_abbreviation(potential_name)
                    if correct_abbr:
                        team_abbr = correct_abbr
                        team_name = potential_name
                        print(f"✅ Method 1 success: {team_abbr} -> {team_name}")
                    else:
                        # If name mapping failed, try the parsed abbr but validate it
                        if potential_abbr in self.get_all_team_abbrs():
                            team_abbr = potential_abbr
                            team_name = potential_name
                            print(f"✅ Method 1 fallback: {team_abbr} -> {team_name}")
                
                # Method 2: Try to find team name directly in text
                if not team_abbr:
                    for full_team_name, abbr in self.get_team_name_map().items():
                        if full_team_name.lower() in team_text.lower():
                            team_abbr = abbr
                            team_name = full_team_name
                            print(f"✅ Method 2 success: {team_abbr} -> {team_name}")
                            break
                
                if team_abbr and team_name:
                    team_names.append((team_abbr, team_name))
                else:
                    print(f"⚠️  Failed to parse team: '{team_text}'")
        
        # Extract stats
        stats_rows = stats_table.find_all('tr')
        team_stats = []
        
        for row in stats_rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 11:  # Make sure we have enough stats
                try:
                    wins = int(cells[0].get_text(strip=True))
                    losses = int(cells[1].get_text(strip=True))
                    win_pct = float(cells[2].get_text(strip=True))
                    # Additional stats available in other columns
                    team_stats.append((wins, losses, win_pct))
                except (ValueError, IndexError):
                    continue
        
        # Combine team names with stats
        print(f"📊 {league}: Found {len(team_names)} teams, {len(team_stats)} stat rows")
        
        for i, ((team_abbr, team_name), (wins, losses, win_pct)) in enumerate(zip(team_names, team_stats)):
            # Calculate games back (first place team has 0)
            if i == 0:
                games_back = 0.0
            else:
                first_team_wins, first_team_losses, _ = team_stats[0]
                games_back = ((first_team_wins - wins) + (losses - first_team_losses)) / 2.0
            
            # Determine playoff status
            playoff_status = self.determine_playoff_status(team_abbr, games_back, win_pct)
            
            team_data = {
                'team': team_abbr,
                'teamName': team_name,
                'wins': wins,
                'losses': losses,
                'winPct': win_pct,
                'gamesBack': games_back,
                'league': league,
                'division': self.get_team_division(team_abbr),
                'status': playoff_status['status'],
                'description': playoff_status['description'],
                'isInPlayoffs': playoff_status['isInPlayoffs'],
                'playoffPosition': playoff_status.get('playoffPosition'),
                'gamesBackFromPlayoffs': playoff_status.get('gamesBackFromPlayoffs', 0),
                'recentForm': 'Unknown'
            }
            
            # Add to appropriate division
            division = team_data['division']
            if division in teams_data:
                teams_data[division].append(team_data)
            
            print(f"✅ Added {team_abbr} ({team_name}): {wins}-{losses} (.{int(win_pct*1000):03d}), {games_back} GB")
        
        return teams_data
    
    def get_team_name_map(self):
        """Get complete team name to abbreviation mapping"""
        return {
            'Arizona Diamondbacks': 'ARI', 'Atlanta Braves': 'ATL', 'Baltimore Orioles': 'BAL',
            'Boston Red Sox': 'BOS', 'Chicago Cubs': 'CHC', 'Chicago White Sox': 'CWS',
            'Cincinnati Reds': 'CIN', 'Cleveland Guardians': 'CLE', 'Colorado Rockies': 'COL',
            'Detroit Tigers': 'DET', 'Houston Astros': 'HOU', 'Kansas City Royals': 'KC',
            'Los Angeles Angels': 'LAA', 'Los Angeles Dodgers': 'LAD', 'Miami Marlins': 'MIA',
            'Milwaukee Brewers': 'MIL', 'Minnesota Twins': 'MIN', 'New York Mets': 'NYM',
            'New York Yankees': 'NYY', 'Oakland Athletics': 'OAK', 'Philadelphia Phillies': 'PHI',
            'Pittsburgh Pirates': 'PIT', 'St. Louis Cardinals': 'STL', 'San Diego Padres': 'SD',
            'San Francisco Giants': 'SF', 'Seattle Mariners': 'SEA', 'Tampa Bay Rays': 'TB',
            'Texas Rangers': 'TEX', 'Toronto Blue Jays': 'TOR', 'Washington Nationals': 'WSH'
        }

    def get_all_team_abbrs(self):
        """Get set of all valid team abbreviations"""
        return set(self.get_team_name_map().values())

    def get_team_abbreviation(self, team_name):
        """Convert full team name to 3-letter abbreviation"""
        team_map = self.get_team_name_map()
        
        # Handle variations in team names
        for full_name, abbr in team_map.items():
            if full_name.lower() in team_name.lower() or team_name.lower() in full_name.lower():
                return abbr
                
        print(f"⚠️  Unknown team name: {team_name}")
        return None
    
    @property
    def AL_TEAMS(self):
        return {
            'BAL', 'BOS', 'NYY', 'TB', 'TOR',  # AL East
            'CWS', 'CLE', 'DET', 'KC', 'MIN',  # AL Central  
            'HOU', 'LAA', 'OAK', 'SEA', 'TEX'  # AL West
        }
    
    @property
    def NL_TEAMS(self):
        return {
            'ATL', 'MIA', 'NYM', 'PHI', 'WSH',  # NL East
            'CHC', 'CIN', 'MIL', 'PIT', 'STL',  # NL Central
            'ARI', 'COL', 'LAD', 'SD', 'SF'     # NL West
        }
    
    def get_team_division(self, team_abbr):
        """Get division for team abbreviation"""
        divisions = {
            # AL East
            'BAL': 'East', 'BOS': 'East', 'NYY': 'East', 'TB': 'East', 'TOR': 'East',
            # AL Central  
            'CWS': 'Central', 'CLE': 'Central', 'DET': 'Central', 'KC': 'Central', 'MIN': 'Central',
            # AL West
            'HOU': 'West', 'LAA': 'West', 'OAK': 'West', 'SEA': 'West', 'TEX': 'West',
            # NL East
            'ATL': 'East', 'MIA': 'East', 'NYM': 'East', 'PHI': 'East', 'WSH': 'East',
            # NL Central
            'CHC': 'Central', 'CIN': 'Central', 'MIL': 'Central', 'PIT': 'Central', 'STL': 'Central',
            # NL West  
            'ARI': 'West', 'COL': 'West', 'LAD': 'West', 'SD': 'West', 'SF': 'West'
        }
        return divisions.get(team_abbr, 'Unknown')
    
    def add_missing_teams_fallback(self, standings_data, missing_teams):
        # Add fallback data for teams missing from ESPN scrape
        # Updated with real 2025 records (as of Aug 24, 2025)
        fallback_records = {
            'TOR': {'wins': 76, 'losses': 54, 'winPct': 0.585},  # CORRECTED: Toronto leading AL East
            'DET': {'wins': 68, 'losses': 62, 'winPct': 0.523},  # Updated Detroit record
            'HOU': {'wins': 71, 'losses': 59, 'winPct': 0.546},  # Updated Houston record  
            'PHI': {'wins': 80, 'losses': 50, 'winPct': 0.615},  # Updated Philadelphia record
            'MIL': {'wins': 75, 'losses': 55, 'winPct': 0.577},  # Updated Milwaukee record
            'SD': {'wins': 71, 'losses': 59, 'winPct': 0.546}   # Updated San Diego record
        }
        
        team_names = {
            'TOR': 'Toronto Blue Jays',
            'DET': 'Detroit Tigers', 
            'HOU': 'Houston Astros',
            'PHI': 'Philadelphia Phillies',
            'MIL': 'Milwaukee Brewers',
            'SD': 'San Diego Padres'
        }
        
        for team_abbr in missing_teams:
            if team_abbr in fallback_records:
                record = fallback_records[team_abbr]
                team_name = team_names.get(team_abbr, f'{team_abbr} Team')
                
                league = 'AL' if team_abbr in self.AL_TEAMS else 'NL'
                division = self.get_team_division(team_abbr)
                
                # Determine playoff status based on actual record quality
                win_pct = record['winPct']
                if win_pct >= 0.580:  # Toronto level record - division leader
                    games_back = 0.0
                    status_info = self.determine_playoff_status(team_abbr, 0.0, win_pct)
                elif win_pct >= 0.550:  # Strong record - in playoffs
                    games_back = 2.0
                    status_info = self.determine_playoff_status(team_abbr, 2.0, win_pct)
                elif win_pct >= 0.520:  # Good record - in hunt
                    games_back = 5.0
                    status_info = self.determine_playoff_status(team_abbr, 5.0, win_pct)
                else:  # Below .520 - longshot or fading
                    games_back = 10.0
                    status_info = self.determine_playoff_status(team_abbr, 10.0, win_pct)
                
                team_data = {
                    'team': team_abbr,
                    'teamName': team_name,
                    'wins': record['wins'],
                    'losses': record['losses'],
                    'winPct': win_pct,
                    'gamesBack': games_back,
                    'league': league,
                    'division': division,
                    'status': status_info.get('status', 'IN_HUNT'),
                    'description': f"{status_info.get('description', 'In Wild Card Hunt')} (Fallback Data)",
                    'isInPlayoffs': status_info.get('isInPlayoffs', False),
                    'playoffPosition': status_info.get('playoffPosition'),
                    'gamesBackFromPlayoffs': status_info.get('gamesBackFromPlayoffs', games_back),
                    'recentForm': 'Unknown'
                }
                
                if division in standings_data[league]:
                    standings_data[league][division].append(team_data)
                    print(f'Added fallback data for {team_abbr} ({team_name})')

    def determine_playoff_status(self, team_abbr, games_back, win_pct):
        """Determine playoff status based on standings position"""
        # This is a simplified version - in reality would need more complex logic
        # based on actual wildcard race calculations
        
        if games_back == 0:
            return {
                'status': 'DIVISION_LEADER',
                'description': 'Division Leader', 
                'isInPlayoffs': True,
                'playoffPosition': 1
            }
        elif games_back <= 2.0 and win_pct >= 0.550:
            return {
                'status': 'WILD_CARD_POSITION',
                'description': 'Wild Card Position',
                'isInPlayoffs': True,
                'playoffPosition': 2
            }
        elif games_back <= 5.0 and win_pct >= 0.500:
            return {
                'status': 'IN_HUNT',
                'description': 'In Wild Card Hunt',
                'isInPlayoffs': False,
                'gamesBackFromPlayoffs': games_back
            }
        elif games_back <= 10.0:
            return {
                'status': 'LONGSHOT',
                'description': 'Longshot Hopes',
                'isInPlayoffs': False,
                'gamesBackFromPlayoffs': games_back
            }
        else:
            return {
                'status': 'FADING',
                'description': 'Playoff Hopes Fading',
                'isInPlayoffs': False,
                'gamesBackFromPlayoffs': games_back
            }
    
    def save_standings(self, standings_data, output_dir="../BaseballData/data/standings"):
        """Save scraped standings to JSON files"""
        if not standings_data:
            print("❌ No standings data to save")
            return False
            
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Create output structure
            output = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'lastUpdated': datetime.now().isoformat(),
                'standings': standings_data,
                'playoffContext': {},
                'source': 'ESPN MLB Standings',
                'scraper_version': '1.0.0'
            }
            
            # Create playoff context lookup for easy access
            for league in ['AL', 'NL']:
                for division in ['East', 'Central', 'West']:
                    if league in standings_data and division in standings_data[league]:
                        for team in standings_data[league][division]:
                            output['playoffContext'][team['team']] = {
                                'status': team['status'],
                                'description': team['description'],
                                'isInPlayoffs': team['isInPlayoffs'],
                                'playoffPosition': team.get('playoffPosition'),
                                'gamesBackFromPlayoffs': team.get('gamesBackFromPlayoffs', 0),
                                'wins': team['wins'],
                                'losses': team['losses'],
                                'winPct': team['winPct'],
                                'gamesBack': team['gamesBack'],
                                'recentForm': team['recentForm']
                            }
            
            # Save with date stamp
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_file = os.path.join(output_dir, f"wildcard_standings_{date_str}.json")
            
            with open(output_file, 'w') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Also save as latest for easy access
            latest_file = os.path.join(output_dir, "wildcard_standings_latest.json")
            with open(latest_file, 'w') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Standings saved to {output_file}")
            print(f"✅ Latest standings saved to {latest_file}")
            print(f"📊 Scraped {len(output['playoffContext'])} teams with playoff context")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving standings: {e}")
            return False

def main():
    """Main execution function"""
    print("🏆 Starting MLB Wildcard Standings Scraper...")
    
    scraper = WildcardStandingsScraper()
    
    # Scrape standings data
    standings_data = scraper.scrape_espn_standings()
    
    if standings_data:
        # Save to JSON files
        success = scraper.save_standings(standings_data)
        
        if success:
            print("✅ MLB wildcard standings scraping completed successfully!")
            return 0
        else:
            print("❌ Failed to save standings data")
            return 1
    else:
        print("❌ Failed to scrape standings data")
        return 1

if __name__ == "__main__":
    exit(main())