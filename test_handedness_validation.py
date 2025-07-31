#!/usr/bin/env python3
"""
Handedness Validation Test Script
Tests lineup data retrieval and handedness validation without making changes to roster data.
"""

import requests
import json
import datetime
import os
import sys
from typing import Dict, List, Optional, Any
import re
from enhanced_player_name_matcher import PlayerNameNormalizer, PlayerNameMatcher

class HandednessValidationTest:
    def __init__(self):
        self.api_base_url = "https://statsapi.mlb.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BaseballTracker-HandednessTest/1.0'
        })
        
        # Load roster data for comparison
        self.rosters_data = self.load_rosters_data()
        
        # Initialize enhanced name matcher
        self.name_matcher = PlayerNameMatcher()
        
        # Results tracking
        self.results = {
            'pitcher_validation': [],
            'batter_validation': [],
            'summary': {},
            'found_lineups': [],
            'roster_suggestions': []
        }
        
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

    def fetch_comprehensive_lineup_data(self, date_str: str = None) -> Optional[Dict]:
        """Fetch comprehensive lineup data including detailed player info"""
        try:
            if not date_str:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Use the standard schedule endpoint that gives us both pitcher and lineup data
            url = f"{self.api_base_url}/schedule"
            params = {
                'sportId': 1,
                'date': date_str,
                'hydrate': 'probablePitcher,lineups,venue,weather'
            }
            
            print(f"🔍 Fetching from: {url}")
            print(f"📋 Params: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            games_found = data.get('totalGames', 0)
            print(f"📊 API returned {games_found} games")
            
            return data
            
        except requests.RequestException as e:
            print(f"❌ Error fetching lineup data: {e}")
            return None

    def has_lineup_data(self, data: Dict) -> bool:
        """Check if API response contains actual lineup data"""
        try:
            for date_obj in data.get('dates', []):
                for game in date_obj.get('games', []):
                    lineups = game.get('lineups', {})
                    if lineups:
                        # Check if lineups have actual player data
                        for team_side in ['home', 'away']:
                            team_lineup = lineups.get(team_side, {})
                            if isinstance(team_lineup, dict) and team_lineup:
                                return True
            return False
        except:
            return False

    def extract_pitcher_handedness_data(self, api_data: Dict) -> List[Dict]:
        """Extract pitcher handedness from API data"""
        pitchers = []
        
        try:
            for date_obj in api_data.get('dates', []):
                for game in date_obj.get('games', []):
                    teams = game.get('teams', {})
                    
                    print(f"    🔍 Game {game.get('gamePk', 'No ID')}: {game.get('status', {}).get('detailedState', 'Unknown')}")
                    
                    for team_side in ['home', 'away']:
                        team_data = teams.get(team_side, {})
                        probable_pitcher = team_data.get('probablePitcher', {})
                        team_info = team_data.get('team', {})
                        
                        print(f"      {team_side} pitcher: {probable_pitcher}")
                        
                        if probable_pitcher and probable_pitcher.get('fullName'):
                            print(f"      ✅ Found pitcher: {probable_pitcher.get('fullName')}")
                            # Always get pitcher handedness from the person API endpoint for accuracy
                            throws_code, throws_desc = self.get_pitcher_handedness_from_api(
                                probable_pitcher.get('id')
                            )
                            
                            # Map team names to abbreviations
                            team_name = team_info.get('name', '')
                            team_abbr = self.map_team_name_to_abbr(team_name)
                            
                            pitcher_data = {
                                'name': probable_pitcher.get('fullName', ''),
                                'id': str(probable_pitcher.get('id', '')),
                                'team': team_abbr,
                                'api_throws': throws_code,
                                'api_throws_desc': throws_desc,
                                'team_side': team_side,
                                'game_id': str(game.get('gamePk', ''))
                            }
                            pitchers.append(pitcher_data)
                        else:
                            print(f"      ❌ No pitcher found for {team_side}")
                            
        except Exception as e:
            print(f"⚠️ Error extracting pitcher data: {e}")
            
        return pitchers

    def get_pitcher_handedness_from_lineups(self, game: Dict, pitcher_id: int) -> tuple:
        """Try to get pitcher handedness from lineup data"""
        try:
            # Use the same player API endpoint to get pitcher handedness
            return self.get_pitcher_handedness_from_api(pitcher_id)
            
        except Exception:
            pass
        
        return '', ''

    def get_pitcher_handedness_from_api(self, player_id: int) -> tuple:
        """Get pitcher handedness from person API endpoint"""
        try:
            if not player_id:
                return '', ''
            
            url = f"{self.api_base_url}/people/{player_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            people = data.get('people', [])
            
            if people:
                person = people[0]
                
                # Get pitching handedness
                pitch_hand = person.get('pitchHand', {})
                api_throws = pitch_hand.get('code', '')
                api_throws_desc = pitch_hand.get('description', '')
                
                return api_throws, api_throws_desc
                
        except Exception as e:
            print(f"⚠️ Error getting pitcher handedness for player {player_id}: {e}")
            
        return '', ''

    def map_team_name_to_abbr(self, team_name: str) -> str:
        """Map team name to abbreviation"""
        team_mapping = {
            'Seattle Mariners': 'SEA', 'Boston Red Sox': 'BOS', 'Miami Marlins': 'MIA',
            'Philadelphia Phillies': 'PHI', 'Washington Nationals': 'WSH', 'Colorado Rockies': 'COL',
            'New York Yankees': 'NYY', 'Los Angeles Angels': 'LAA', 'Toronto Blue Jays': 'TOR',
            'Arizona Diamondbacks': 'ARI', 'Cincinnati Reds': 'CIN', 'Minnesota Twins': 'MIN',
            'Atlanta Braves': 'ATL', 'New York Mets': 'NYM', 'Tampa Bay Rays': 'TB',
            'Baltimore Orioles': 'BAL', 'Texas Rangers': 'TEX', 'Kansas City Royals': 'KC',
            'San Francisco Giants': 'SF', 'Cleveland Guardians': 'CLE', 'Athletics': 'OAK',
            'Houston Astros': 'HOU', 'Los Angeles Dodgers': 'LAD', 'San Diego Padres': 'SD',
            'Detroit Tigers': 'DET', 'Pittsburgh Pirates': 'PIT', 'Chicago White Sox': 'CWS',
            'St. Louis Cardinals': 'STL', 'Chicago Cubs': 'CHC', 'Milwaukee Brewers': 'MIL'
        }
        return team_mapping.get(team_name, team_name)

    def extract_batter_handedness_data(self, api_data: Dict) -> List[Dict]:
        """Extract batter handedness from lineup data if available"""
        batters = []
        
        try:
            for date_obj in api_data.get('dates', []):
                for game in date_obj.get('games', []):
                    lineups = game.get('lineups', {})
                    teams = game.get('teams', {})
                    
                    # New format: homePlayers and awayPlayers arrays
                    for team_side in ['home', 'away']:
                        players_key = f'{team_side}Players'
                        team_players = lineups.get(players_key, [])
                        team_info = teams.get(team_side, {}).get('team', {})
                        team_name = team_info.get('name', '')
                        team_abbr = self.map_team_name_to_abbr(team_name)
                        
                        for i, player in enumerate(team_players):
                            if isinstance(player, dict) and player.get('fullName'):
                                # Get handedness data from player API endpoint
                                api_bats, api_bats_desc = self.get_player_handedness(player.get('id'))
                                
                                batter_data = {
                                    'name': player.get('fullName', ''),
                                    'id': str(player.get('id', '')),
                                    'team': team_abbr,
                                    'batting_order': i + 1,
                                    'position': player.get('primaryPosition', {}).get('abbreviation', ''),
                                    'api_bats': api_bats,
                                    'api_bats_desc': api_bats_desc,
                                    'team_side': team_side,
                                    'game_id': str(game.get('gamePk', ''))
                                }
                                batters.append(batter_data)
                                
        except Exception as e:
            print(f"⚠️ Error extracting batter data: {e}")
            
        return batters

    def get_player_handedness(self, player_id: int) -> tuple:
        """Get player handedness from person API endpoint"""
        try:
            if not player_id:
                return '', ''
            
            url = f"{self.api_base_url}/people/{player_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            people = data.get('people', [])
            
            if people:
                person = people[0]
                
                # Get batting handedness
                bat_side = person.get('batSide', {})
                api_bats = bat_side.get('code', '')
                api_bats_desc = bat_side.get('description', '')
                
                return api_bats, api_bats_desc
                
        except Exception as e:
            print(f"⚠️ Error getting handedness for player {player_id}: {e}")
            
        return '', ''

    def find_player_in_roster(self, player_name: str, player_type: str = 'any') -> Optional[Dict]:
        """Find player in roster data using enhanced name matching"""
        if not player_name:
            return None
        
        # Filter by player type
        candidates = self.rosters_data
        if player_type != 'any':
            candidates = [p for p in self.rosters_data if p.get('type') == player_type]
        
        # Use enhanced matcher
        match_result = self.name_matcher.find_best_match(player_name, candidates, threshold=0.7)
        
        if match_result:
            return match_result['player']
        
        # If no match found, generate suggestions for roster improvements
        suggestions = self.name_matcher.suggest_roster_improvements(player_name, candidates)
        if suggestions:
            self.results['roster_suggestions'].extend(suggestions)
        
        return None

    def validate_pitcher_handedness(self, pitchers: List[Dict]) -> List[Dict]:
        """Validate pitcher handedness against roster data"""
        results = []
        
        for pitcher in pitchers:
            roster_player = self.find_player_in_roster(pitcher['name'], 'pitcher')
            
            validation = {
                'name': pitcher['name'],
                'team': pitcher['team'],
                'api_handedness': pitcher['api_throws'],
                'api_description': pitcher['api_throws_desc'],
                'roster_found': roster_player is not None,
                'roster_handedness': roster_player.get('ph', 'MISSING') if roster_player else 'NOT_FOUND',
                'match_status': 'UNKNOWN',
                'needs_update': False,
                'action_needed': ''
            }
            
            if roster_player:
                roster_throws = roster_player.get('ph', '')
                api_throws = pitcher['api_throws']
                
                if not roster_throws:
                    validation['match_status'] = 'ROSTER_MISSING'
                    validation['needs_update'] = True
                    validation['action_needed'] = f'Add handedness: {api_throws}'
                elif roster_throws == api_throws:
                    validation['match_status'] = 'MATCH'
                    validation['action_needed'] = 'None - data matches'
                else:
                    validation['match_status'] = 'MISMATCH'
                    validation['needs_update'] = True
                    validation['action_needed'] = f'Update: {roster_throws} -> {api_throws}'
            else:
                validation['match_status'] = 'PLAYER_NOT_FOUND'
                validation['action_needed'] = 'Player not in roster database'
            
            results.append(validation)
            
        return results

    def validate_batter_handedness(self, batters: List[Dict]) -> List[Dict]:
        """Validate batter handedness against roster data"""
        results = []
        
        for batter in batters:
            roster_player = self.find_player_in_roster(batter['name'], 'hitter')
            
            # Convert API handedness to roster format
            api_bats = batter['api_bats']
            roster_format_map = {'L': 'L', 'R': 'R', 'S': 'B'}  # Switch -> Both
            expected_roster_bats = roster_format_map.get(api_bats, api_bats)
            
            validation = {
                'name': batter['name'],
                'team': batter['team'],
                'batting_order': batter['batting_order'],
                'position': batter['position'],
                'api_handedness': api_bats,
                'api_description': batter['api_bats_desc'],
                'expected_roster_format': expected_roster_bats,
                'roster_found': roster_player is not None,
                'roster_handedness': roster_player.get('bats', 'MISSING') if roster_player else 'NOT_FOUND',
                'match_status': 'UNKNOWN',
                'needs_update': False,
                'action_needed': ''
            }
            
            if roster_player:
                roster_bats = roster_player.get('bats', '')
                
                if not roster_bats:
                    validation['match_status'] = 'ROSTER_MISSING'
                    validation['needs_update'] = True
                    validation['action_needed'] = f'Add handedness: {expected_roster_bats}'
                elif roster_bats == expected_roster_bats:
                    validation['match_status'] = 'MATCH'
                    validation['action_needed'] = 'None - data matches'
                else:
                    validation['match_status'] = 'MISMATCH'
                    validation['needs_update'] = True
                    validation['action_needed'] = f'Update: {roster_bats} -> {expected_roster_bats}'
            else:
                validation['match_status'] = 'PLAYER_NOT_FOUND'
                validation['action_needed'] = 'Player not in roster database'
            
            results.append(validation)
            
        return results

    def print_results(self):
        """Print comprehensive validation results"""
        print("\n" + "="*80)
        print("🧪 HANDEDNESS VALIDATION TEST RESULTS")
        print("="*80)
        
        # Summary statistics
        pitcher_results = self.results['pitcher_validation']
        batter_results = self.results['batter_validation']
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Pitchers analyzed: {len(pitcher_results)}")
        print(f"   • Batters analyzed: {len(batter_results)}")
        
        # Pitcher results
        if pitcher_results:
            print(f"\n🥎 PITCHER HANDEDNESS VALIDATION:")
            print("-" * 60)
            
            matches = sum(1 for p in pitcher_results if p['match_status'] == 'MATCH')
            missing = sum(1 for p in pitcher_results if p['match_status'] == 'ROSTER_MISSING')
            mismatches = sum(1 for p in pitcher_results if p['match_status'] == 'MISMATCH')
            not_found = sum(1 for p in pitcher_results if p['match_status'] == 'PLAYER_NOT_FOUND')
            
            print(f"   ✅ Matches: {matches}")
            print(f"   ⚠️  Missing in roster: {missing}")
            print(f"   🔄 Mismatches: {mismatches}")
            print(f"   ❌ Players not found: {not_found}")
            
            print(f"\n📋 DETAILED PITCHER RESULTS:")
            for p in pitcher_results:
                status_icon = {'MATCH': '✅', 'ROSTER_MISSING': '⚠️', 'MISMATCH': '🔄', 'PLAYER_NOT_FOUND': '❌'}.get(p['match_status'], '❓')
                print(f"   {status_icon} {p['name']} ({p['team']})")
                print(f"      API: {p['api_handedness']} ({p['api_description']})")
                print(f"      Roster: {p['roster_handedness']}")
                print(f"      Action: {p['action_needed']}")
                print()
        
        # Batter results
        if batter_results:
            print(f"\n⚾ BATTER HANDEDNESS VALIDATION:")
            print("-" * 60)
            
            matches = sum(1 for b in batter_results if b['match_status'] == 'MATCH')
            missing = sum(1 for b in batter_results if b['match_status'] == 'ROSTER_MISSING')
            mismatches = sum(1 for b in batter_results if b['match_status'] == 'MISMATCH')
            not_found = sum(1 for b in batter_results if b['match_status'] == 'PLAYER_NOT_FOUND')
            
            print(f"   ✅ Matches: {matches}")
            print(f"   ⚠️  Missing in roster: {missing}")
            print(f"   🔄 Mismatches: {mismatches}")
            print(f"   ❌ Players not found: {not_found}")
            
            print(f"\n📋 DETAILED BATTER RESULTS:")
            for b in batter_results:
                status_icon = {'MATCH': '✅', 'ROSTER_MISSING': '⚠️', 'MISMATCH': '🔄', 'PLAYER_NOT_FOUND': '❌'}.get(b['match_status'], '❓')
                print(f"   {status_icon} {b['name']} ({b['team']}) - #{b['batting_order']} {b['position']}")
                print(f"      API: {b['api_handedness']} ({b['api_description']}) -> Roster format: {b['expected_roster_format']}")
                print(f"      Roster: {b['roster_handedness']}")
                print(f"      Action: {b['action_needed']}")
                print()
        
        # Implementation recommendations
        print(f"\n💡 IMPLEMENTATION RECOMMENDATIONS:")
        print("-" * 60)
        
        pitcher_needs_update = sum(1 for p in pitcher_results if p['needs_update'])
        batter_needs_update = sum(1 for b in batter_results if b['needs_update'])
        roster_suggestions = self.results.get('roster_suggestions', [])
        
        if pitcher_needs_update > 0:
            print(f"   🔧 {pitcher_needs_update} pitchers need roster updates")
        if batter_needs_update > 0:
            print(f"   🔧 {batter_needs_update} batters need roster updates")
        
        if roster_suggestions:
            print(f"   📝 {len(roster_suggestions)} roster enhancement suggestions available")
            
        if pitcher_needs_update == 0 and batter_needs_update == 0 and not roster_suggestions:
            print(f"   ✅ All handedness data is accurate - no updates needed!")
        else:
            print(f"   📝 Consider implementing automatic roster updates for missing/mismatched data")
        
        # Display roster suggestions
        if roster_suggestions:
            print(f"\n🔧 ROSTER ENHANCEMENT SUGGESTIONS:")
            print("-" * 60)
            
            for i, suggestion in enumerate(roster_suggestions[:5], 1):  # Show top 5
                print(f"   {i}. Player ID: {suggestion['player_id']} ({suggestion['team']})")
                print(f"      Current: name='{suggestion['current_name']}', fullName='{suggestion['current_fullName']}'")
                print(f"      Suggested: Add alternate name '{suggestion['suggested_value']}'")
                print(f"      Reason: {suggestion['reason']}")
                print(f"      Confidence: {suggestion['confidence']:.3f}")
                print()

    def run_test(self, date_str: str = None) -> Dict:
        """Run the complete handedness validation test"""
        print("🧪 Starting Handedness Validation Test...")
        print("=" * 50)
        
        # Fetch lineup data
        api_data = self.fetch_comprehensive_lineup_data(date_str)
        if not api_data:
            print("❌ Failed to fetch lineup data")
            return self.results
        
        # Extract pitcher data
        print("\n🔍 Extracting pitcher handedness data...")
        pitchers = self.extract_pitcher_handedness_data(api_data)
        print(f"   Found {len(pitchers)} pitchers")
        
        # Extract batter data
        print("\n🔍 Extracting batter handedness data...")
        batters = self.extract_batter_handedness_data(api_data)
        print(f"   Found {len(batters)} batters")
        
        # Validate data
        print("\n🔍 Validating against roster database...")
        self.results['pitcher_validation'] = self.validate_pitcher_handedness(pitchers)
        self.results['batter_validation'] = self.validate_batter_handedness(batters)
        
        # Print results
        self.print_results()
        
        return self.results

def main():
    """Main execution function"""
    tester = HandednessValidationTest()
    
    # Allow date specification via command line
    date_str = None
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
        print(f"🗓️ Testing handedness validation for date: {date_str}")
    else:
        print(f"🗓️ Testing handedness validation for today")
    
    results = tester.run_test(date_str)
    
    print("\n" + "="*80)
    print("🧪 TEST COMPLETE - NO CHANGES MADE TO ROSTER DATA")
    print("="*80)
    
    return results

if __name__ == "__main__":
    results = main()
    sys.exit(0)