#!/usr/bin/env python3
"""
Hellraiser HR Analysis Generator (v4.0 - Advanced Metrics Edition)

Generates comprehensive home run analysis for MLB players using:
- Current HR odds data from CSV files
- Today's lineup information with confirmed starting pitchers
- Advanced hitting metrics (exit velocity, barrel rate, hard contact %)
- Advanced pitcher metrics (exit velocity allowed, barrel rate allowed)
- Historical player statistics for validation
- The three-pathway Hellraiser methodology (Perfect Storm, Batter-Driven, Pitcher-Driven)

Data Sources:
- public/data/odds/mlb-hr-odds-only.csv (current odds)
- public/data/lineups/starting_lineups_YYYY-MM-DD.json (confirmed lineups/pitchers)
- public/data/injuries/rosters_backup_*.json (player-team mapping)
- public/data/stats/hitter_exit_velocity_2025.csv (advanced hitting metrics)
- public/data/stats/custom_pitcher_2025.csv (advanced pitcher metrics)

Output: JSON files in public/data/hellraiser/ for HellraiserCard component

Advanced Scoring Methodology:
- Odds Analysis (25%): Market value assessment
- Advanced Hitter Analysis (35%): Exit velocity, barrel rate, hard contact %
- Advanced Pitcher Analysis (25%): Exit velocity allowed, barrel vulnerability
- Venue Analysis (10%): Park factors and conditions
- Home Field Advantage (5%): Home vs away performance boost

Usage:
python3 generate_hellraiser_analysis.py                    # All teams
python3 generate_hellraiser_analysis.py --teams NYY        # Yankees only
python3 generate_hellraiser_analysis.py --teams SEA CHC    # Mariners vs Cubs
"""

import json
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class HellraiserAnalysisGenerator:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # Default to BaseballTracker directory
            script_dir = Path(__file__).parent.absolute()
            self.base_dir = script_dir.parent / "BaseballTracker"
        else:
            self.base_dir = Path(base_dir)
        
        self.output_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.today = datetime.now().strftime("%Y-%m-%d")
        print(f"🔥 Hellraiser Analysis Generator - {self.today}")
        
        # Accent normalization map
        self.accent_map = {
            'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ā': 'a', 'ą': 'a', 'å': 'a', 'ã': 'a',
            'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e', 'ē': 'e', 'ę': 'e',
            'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ī': 'i', 'į': 'i',
            'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ō': 'o', 'ø': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u', 'ų': 'u',
            'ñ': 'n', 'ń': 'n', 'ç': 'c', 'č': 'c', 'ć': 'c',
            'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ā': 'A', 'Ą': 'A', 'Å': 'A', 'Ã': 'A',
            'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E', 'Ē': 'E', 'Ę': 'E',
            'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I', 'Ī': 'I', 'Į': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Ō': 'O', 'Ø': 'O', 'Õ': 'O',
            'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U', 'Ū': 'U', 'Ų': 'U',
            'Ñ': 'N', 'Ń': 'N', 'Ç': 'C', 'Č': 'C', 'Ć': 'C'
        }
    
    def normalize_accents(self, text: str) -> str:
        """Normalize accented characters to plain English"""
        if not text:
            return ''
        return ''.join(self.accent_map.get(char, char) for char in text)

    def load_current_odds(self) -> List[Dict]:
        """Load current HR odds data"""
        odds_file = self.base_dir / "public" / "data" / "odds" / "mlb-hr-odds-only.csv"
        odds_data = []
        
        try:
            with open(odds_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    odds_data.append({
                        'player_name': row['player_name'],
                        'odds': row['odds'],
                        'last_updated': row['last_updated']
                    })
            
            print(f"✅ Loaded {len(odds_data)} players with HR odds")
            return odds_data
            
        except FileNotFoundError:
            print("❌ HR odds file not found")
            return []

    def load_lineup_data(self, date: str = None) -> Optional[Dict]:
        """Load today's lineup data with confirmed pitchers"""
        if date is None:
            date = self.today
            
        lineup_file = self.base_dir / "public" / "data" / "lineups" / f"starting_lineups_{date}.json"
        
        try:
            with open(lineup_file, 'r') as f:
                lineup_data = json.load(f)
            
            print(f"✅ Loaded lineup data for {len(lineup_data.get('games', []))} games")
            return lineup_data
            
        except FileNotFoundError:
            print(f"❌ Lineup file not found for {date}")
            return None

    def load_roster_data(self) -> List[Dict]:
        """Load current roster data for player-team mapping"""
        # Find the most recent roster backup file
        roster_dir = self.base_dir / "public" / "data" / "injuries"
        roster_files = list(roster_dir.glob("rosters_backup_*.json"))
        
        if not roster_files:
            print("❌ No roster files found")
            return []
        
        # Get the most recent roster file
        latest_roster = max(roster_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_roster, 'r') as f:
                roster_data = json.load(f)
            
            print(f"✅ Loaded roster data for {len(roster_data)} players from {latest_roster.name}")
            return roster_data
            
        except Exception as e:
            print(f"❌ Error loading roster data: {e}")
            return []

    def load_historical_stats(self, date: str = None) -> List[Dict]:
        """Load historical player statistics"""
        if date is None:
            date = self.today
        
        # Try to load player stats from recent dates
        for days_back in range(5):
            try_date = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=days_back)
            try_date_str = try_date.strftime("%Y-%m-%d")
            
            # Construct file path
            year = try_date.year
            month_name = try_date.strftime("%B").lower()
            day = try_date.strftime("%d")
            
            stats_file = self.base_dir / "public" / "data" / str(year) / month_name / f"{month_name}_{day}_{year}.json"
            
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    if 'players' in data:
                        print(f"✅ Loaded historical stats for {len(data['players'])} players from {try_date_str}")
                        return data['players']
            except FileNotFoundError:
                continue
        
        print("❌ No historical player stats found")
        return []

    def load_advanced_hitter_stats(self) -> Dict[str, Dict]:
        """Load advanced hitting metrics (exit velocity, barrels, etc.)"""
        hitter_stats = {}
        
        # Load exit velocity data
        exit_velo_file = self.base_dir / "public" / "data" / "stats" / "hitter_exit_velocity_2025.csv"
        try:
            with open(exit_velo_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean the name format
                    name_parts = row['last_name, first_name'].split(', ')
                    if len(name_parts) == 2:
                        full_name = f"{name_parts[1]} {name_parts[0]}"
                        hitter_stats[full_name] = {
                            'exit_velocity_avg': float(row['avg_hit_speed']) if row['avg_hit_speed'] else 0,
                            'max_exit_velocity': float(row['max_hit_speed']) if row['max_hit_speed'] else 0,
                            'barrel_percent': float(row['brl_percent']) if row['brl_percent'] else 0,
                            'barrels': int(row['barrels']) if row['barrels'] else 0,
                            'ev95_percent': float(row['ev95percent']) if row['ev95percent'] else 0,
                            'avg_distance': float(row['avg_distance']) if row['avg_distance'] else 0,
                            'avg_hr_distance': float(row['avg_hr_distance']) if row['avg_hr_distance'] else 0,
                            'sweet_spot_percent': float(row['anglesweetspotpercent']) if row['anglesweetspotpercent'] else 0
                        }
            
            print(f"✅ Loaded advanced hitting stats for {len(hitter_stats)} players")
        except FileNotFoundError:
            print("❌ Advanced hitting stats file not found")
        except Exception as e:
            print(f"❌ Error loading advanced hitting stats: {e}")
        
        return hitter_stats

    def load_advanced_pitcher_stats(self) -> Dict[str, Dict]:
        """Load advanced pitcher metrics (arsenal, exit velocity allowed, etc.)"""
        pitcher_stats = {}
        
        # Load custom pitcher data
        pitcher_file = self.base_dir / "public" / "data" / "stats" / "custom_pitcher_2025.csv"
        try:
            with open(pitcher_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean the name format
                    name_parts = row['last_name, first_name'].split(', ')
                    if len(name_parts) == 2:
                        full_name = f"{name_parts[1]} {name_parts[0]}"
                        pitcher_stats[full_name] = {
                            'era': float(row['p_era']) if row['p_era'] else 0,
                            'whip': float(row['p_opp_on_base_avg']) if row['p_opp_on_base_avg'] else 0,
                            'exit_velocity_allowed': float(row['exit_velocity_avg']) if row['exit_velocity_avg'] else 0,
                            'barrel_percent_allowed': float(row['barrel_batted_rate']) if row['barrel_batted_rate'] else 0,
                            'hard_hit_percent_allowed': float(row['hard_hit_percent']) if row['hard_hit_percent'] else 0,
                            'whiff_percent': float(row['whiff_percent']) if row['whiff_percent'] else 0,
                            'fastball_velocity': float(row['fastball_avg_speed']) if row['fastball_avg_speed'] else 0,
                            'spin_rate': float(row['fastball_avg_spin']) if row['fastball_avg_spin'] else 0,
                            'k_percent': float(row['k_percent']) if row['k_percent'] else 0,
                            'bb_percent': float(row['bb_percent']) if row['bb_percent'] else 0,
                            'home_runs_allowed': int(row['home_run']) if row['home_run'] else 0,
                            'games': int(row['p_game']) if row['p_game'] else 1
                        }
            
            print(f"✅ Loaded advanced pitcher stats for {len(pitcher_stats)} players")
        except FileNotFoundError:
            print("❌ Advanced pitcher stats file not found")
        except Exception as e:
            print(f"❌ Error loading advanced pitcher stats: {e}")
        
        return pitcher_stats

    def load_swing_path_data(self) -> Dict[str, Dict]:
        """Load swing path data from CSV files for both RHP and LHP"""
        swing_path_data = {}
        
        # Load RHP data
        rhp_file = self.base_dir / "public" / "data" / "stats" / "batters-swing-path-RHP.csv"
        lhp_file = self.base_dir / "public" / "data" / "stats" / "batters-swing-path-LHP.csv"
        
        try:
            # Load RHP data
            with open(rhp_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Handle "Lastname, Firstname" format
                    player_name = row['name'].strip().strip('"')
                    if ', ' in player_name:
                        name_parts = player_name.split(', ')
                        if len(name_parts) == 2:
                            full_name = f"{name_parts[1].strip()} {name_parts[0].strip()}"
                        else:
                            full_name = player_name
                    else:
                        full_name = player_name
                    
                    # Initialize player entry if not exists
                    if full_name not in swing_path_data:
                        swing_path_data[full_name] = {'rhp': {}, 'lhp': {}}
                    
                    # Parse RHP data
                    swing_path_data[full_name]['rhp'] = {
                        'handedness': row['side'].strip().strip('"') if row['side'] else 'R',
                        'avg_bat_speed': float(row['avg_bat_speed']) if row['avg_bat_speed'] else 0.0,
                        'attack_angle': float(row['attack_angle']) if row['attack_angle'] else 0.0,
                        'ideal_attack_angle_rate': float(row['ideal_attack_angle_rate']) if row['ideal_attack_angle_rate'] else 0.0,
                        'swing_tilt': float(row['swing_tilt']) if row['swing_tilt'] else 0.0,
                        'attack_direction': float(row['attack_direction']) if row['attack_direction'] else 0.0
                    }
            
            print(f"✅ Loaded RHP swing path data for {len(swing_path_data)} players")
            
        except FileNotFoundError:
            print("❌ RHP swing path file not found")
        except Exception as e:
            print(f"❌ Error loading RHP swing path data: {e}")
        
        try:
            # Load LHP data
            with open(lhp_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Handle "Lastname, Firstname" format
                    player_name = row['name'].strip().strip('"')
                    if ', ' in player_name:
                        name_parts = player_name.split(', ')
                        if len(name_parts) == 2:
                            full_name = f"{name_parts[1].strip()} {name_parts[0].strip()}"
                        else:
                            full_name = player_name
                    else:
                        full_name = player_name
                    
                    # Initialize player entry if not exists
                    if full_name not in swing_path_data:
                        swing_path_data[full_name] = {'rhp': {}, 'lhp': {}}
                    
                    # Parse LHP data
                    swing_path_data[full_name]['lhp'] = {
                        'handedness': row['side'].strip().strip('"') if row['side'] else 'R',
                        'avg_bat_speed': float(row['avg_bat_speed']) if row['avg_bat_speed'] else 0.0,
                        'attack_angle': float(row['attack_angle']) if row['attack_angle'] else 0.0,
                        'ideal_attack_angle_rate': float(row['ideal_attack_angle_rate']) if row['ideal_attack_angle_rate'] else 0.0,
                        'swing_tilt': float(row['swing_tilt']) if row['swing_tilt'] else 0.0,
                        'attack_direction': float(row['attack_direction']) if row['attack_direction'] else 0.0
                    }
            
            print(f"✅ Loaded LHP swing path data for {len([p for p in swing_path_data.values() if p.get('lhp')])} players")
            
        except FileNotFoundError:
            print("❌ LHP swing path file not found")
        except Exception as e:
            print(f"❌ Error loading LHP swing path data: {e}")
        
        return swing_path_data

    def create_player_team_mapping(self, roster_data: List[Dict]) -> Dict[str, str]:
        """Create comprehensive player name to team mapping"""
        player_team_map = {}
        
        for player in roster_data:
            name = player.get('name', '').strip()
            full_name = player.get('fullName', '').strip()
            team = player.get('team', '').strip()
            
            if team:  # Only need team to be valid
                # Map abbreviated name
                if name:
                    player_team_map[name] = team
                    player_team_map[name.lower()] = team
                
                # Map full name (most important for odds matching)
                if full_name:
                    player_team_map[full_name] = team
                    player_team_map[full_name.lower()] = team
                    
                    # Handle "Last, First" format
                    if ', ' in full_name:
                        first_last = ' '.join(reversed(full_name.split(', ')))
                        player_team_map[first_last] = team
                        player_team_map[first_last.lower()] = team
                    
                    # Create additional variations for common mismatches
                    # Handle Jr./Sr. suffixes
                    clean_full = full_name.replace(' Jr.', '').replace(' Sr.', '').replace(' III', '').replace(' II', '')
                    if clean_full != full_name:
                        player_team_map[clean_full] = team
                        player_team_map[clean_full.lower()] = team
        
        print(f"✅ Created player-team mapping for {len(player_team_map)} name variations")
        return player_team_map

    def find_player_team(self, player_name: str, player_team_map: Dict[str, str]) -> Optional[str]:
        """Find team for a player using enhanced fuzzy matching with accent normalization"""
        # Direct match
        if player_name in player_team_map:
            return player_team_map[player_name]
        
        # Lowercase match
        if player_name.lower() in player_team_map:
            return player_team_map[player_name.lower()]
        
        # Normalize accents for enhanced matching
        normalized_player_name = self.normalize_accents(player_name)
        
        # Try normalized matching
        for map_name, team in player_team_map.items():
            normalized_map_name = self.normalize_accents(map_name)
            if normalized_player_name.lower() == normalized_map_name.lower():
                print(f"🔍 Found accent-normalized match: '{player_name}' -> '{map_name}' ({team})")
                return team
        
        # Handle common name variations
        player_parts = player_name.split()
        if len(player_parts) >= 2:
            first_name = player_parts[0]
            last_name = player_parts[-1]
            
            # Try "F. Lastname" format (common in rosters) with accent normalization
            abbreviated = f"{first_name[0]}. {last_name}"
            abbreviated_normalized = self.normalize_accents(abbreviated)
            
            for map_name, team in player_team_map.items():
                normalized_map_name = self.normalize_accents(map_name)
                if abbreviated_normalized.lower() == normalized_map_name.lower():
                    print(f"🔍 Found abbreviated + accent match: '{player_name}' -> '{abbreviated}' -> '{map_name}' ({team})")
                    return team
            
            # Try just last name matching with accent normalization
            normalized_last_name = self.normalize_accents(last_name)
            for map_name, team in player_team_map.items():
                normalized_map_name = self.normalize_accents(map_name)
                if normalized_last_name.lower() in normalized_map_name.lower() and len(last_name) > 4:
                    # Additional check: make sure it's not a super common last name
                    if normalized_last_name.lower() not in ['rodriguez', 'martinez', 'garcia', 'lopez', 'hernandez']:
                        print(f"🔍 Found last name + accent match: '{player_name}' -> '{map_name}' ({team})")
                        return team
                    # For common names, need first name match too
                    elif self.normalize_accents(first_name[0]).lower() in normalized_map_name.lower():
                        print(f"🔍 Found common name + accent match: '{player_name}' -> '{map_name}' ({team})")
                        return team
        
        # Fuzzy matching for full names with accent normalization
        normalized_player_name = self.normalize_accents(player_name)
        for map_name, team in player_team_map.items():
            normalized_map_name = self.normalize_accents(map_name)
            if (normalized_player_name.lower() in normalized_map_name.lower() or 
                normalized_map_name.lower() in normalized_player_name.lower()):
                print(f"🔍 Found fuzzy + accent match: '{player_name}' -> '{map_name}' ({team})")
                return team
        
        print(f"❌ No team found for player: '{player_name}'")
        return None

    def get_pitcher_matchup(self, team: str, lineup_data: Dict) -> Optional[Dict]:
        """Get opposing pitcher for a team"""
        if not lineup_data or 'games' not in lineup_data:
            return None
        
        # Handle team abbreviation variations
        team_variations = {
            'CHW': 'CWS',  # Chicago White Sox
            'CWS': 'CHW'
        }
        
        # Check both the original team and any variations
        teams_to_check = [team]
        if team in team_variations:
            teams_to_check.append(team_variations[team])
        
        for game in lineup_data['games']:
            teams = game.get('teams', {})
            pitchers = game.get('pitchers', {})
            
            home_team = teams.get('home', {}).get('abbr')
            away_team = teams.get('away', {}).get('abbr')
            
            # Check if team is home (including variations)
            if any(t in [home_team] for t in teams_to_check):
                # Team is home, opposing pitcher is away
                away_pitcher = pitchers.get('away', {})
                if away_pitcher.get('name'):
                    return {
                        'pitcher_name': away_pitcher['name'],
                        'opponent_team': away_team,
                        'venue': game.get('venue', {}).get('name', 'Unknown'),
                        'game_time': game.get('gameTime', ''),
                        'is_home': True
                    }
            # Check if team is away (including variations)
            elif any(t in [away_team] for t in teams_to_check):
                # Team is away, opposing pitcher is home
                home_pitcher = pitchers.get('home', {})
                if home_pitcher.get('name'):
                    return {
                        'pitcher_name': home_pitcher['name'],
                        'opponent_team': home_team,
                        'venue': game.get('venue', {}).get('name', 'Unknown'),
                        'game_time': game.get('gameTime', ''),
                        'is_home': False
                    }
        
        return None

    def load_historical_odds(self) -> Dict[str, Dict]:
        """Load historical odds data for market analysis"""
        odds_history = {}
        odds_file = self.base_dir / "public" / "data" / "odds" / "mlb-hr-odds-history.csv"
        
        try:
            with open(odds_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_name = row['player_name']
                    if player_name not in odds_history:
                        odds_history[player_name] = {
                            'opening_odds': row['opening_odds'],
                            'previous_odds': row['previous_odds'],
                            'total_runs': int(row['total_runs']) if row['total_runs'] else 0,
                            'trend_direction': row['trend_direction']
                        }
                        
            print(f"✅ Loaded historical odds for {len(odds_history)} players")
            return odds_history
            
        except FileNotFoundError:
            print("⚠️ Historical odds file not found")
            return {}

    def calculate_hellraiser_score(self, player: Dict, pitcher_matchup: Dict, historical_stats: List[Dict], 
                                 advanced_hitter_stats: Dict = None, advanced_pitcher_stats: Dict = None, 
                                 swing_path_data: Dict = None, historical_odds: Dict = None) -> Tuple[int, str, List[str], List[str]]:
        """Calculate Hellraiser confidence score using the three-pathway methodology with advanced metrics"""
        base_score = 50  # Lower base score for more realistic range
        reasoning = []
        risk_factors = []
        
        player_name = player['player_name']
        pitcher_name = pitcher_matchup['pitcher_name']
        
        # Historical odds analysis (5% weight)
        historical_context = historical_odds.get(player_name) if historical_odds else None
        if historical_context:
            current_odds_num = int(player['odds'][1:]) if player['odds'].startswith('+') else int(player['odds'])
            
            if historical_context.get('opening_odds'):
                try:
                    opening_odds_num = int(historical_context['opening_odds'][1:]) if historical_context['opening_odds'].startswith('+') else int(historical_context['opening_odds'])
                    
                    # Better odds than opening = positive movement
                    if current_odds_num < opening_odds_num:
                        base_score += 8
                        reasoning.append(f"Improved odds from opening ({historical_context['opening_odds']} → {player['odds']})")
                    elif current_odds_num > opening_odds_num * 1.15:  # Significantly worse
                        base_score -= 5
                        risk_factors.append(f"Worsened odds from opening ({historical_context['opening_odds']} → {player['odds']})")
                except (ValueError, TypeError):
                    pass
            
            # Trend analysis
            if historical_context.get('trend_direction') == 'bullish':
                base_score += 5
                reasoning.append("Bullish odds trend")
            elif historical_context.get('trend_direction') == 'bearish':
                base_score -= 3
                risk_factors.append("Bearish odds trend")
        
        # Odds analysis (25% weight)
        odds_str = player['odds']
        try:
            if odds_str.startswith('+'):
                odds_value = int(odds_str[1:])
            else:
                odds_value = int(odds_str)
                
            if odds_value <= 150:
                base_score += 12
                reasoning.append(f"Excellent odds ({odds_str})")
            elif odds_value <= 250:
                base_score += 8
                reasoning.append(f"Good odds ({odds_str})")
            elif odds_value <= 400:
                base_score += 4
                reasoning.append(f"Decent odds ({odds_str})")
            elif odds_value <= 600:
                base_score += 1
                reasoning.append(f"Fair odds ({odds_str})")
            else:
                base_score -= 3
                risk_factors.append("Long shot odds")
                
        except ValueError:
            risk_factors.append("Invalid odds data")
        
        # Advanced Hitter Analysis (35% weight)
        if advanced_hitter_stats and player_name in advanced_hitter_stats:
            hitter_data = advanced_hitter_stats[player_name]
            
            # Exit velocity analysis (15% weight) - more conservative
            exit_velo = hitter_data.get('exit_velocity_avg', 0)
            if exit_velo >= 94:  # Truly elite
                base_score += 10
                reasoning.append(f"Elite exit velocity ({exit_velo:.1f} mph)")
            elif exit_velo >= 90:  # Good
                base_score += 6
                reasoning.append(f"Strong exit velocity ({exit_velo:.1f} mph)")
            elif exit_velo >= 86:  # Average
                base_score += 2
                reasoning.append(f"Solid exit velocity ({exit_velo:.1f} mph)")
            elif exit_velo < 83 and exit_velo > 0:  # Below average
                base_score -= 2
                risk_factors.append(f"Below average exit velocity ({exit_velo:.1f} mph)")
            
            # Barrel rate analysis (10% weight)
            barrel_pct = hitter_data.get('barrel_percent', 0)
            if barrel_pct >= 10:  # Elite barrel rate
                base_score += 10
                reasoning.append(f"Elite barrel rate ({barrel_pct:.1f}%)")
            elif barrel_pct >= 6:  # Good barrel rate
                base_score += 6
                reasoning.append(f"Strong barrel rate ({barrel_pct:.1f}%)")
            elif barrel_pct >= 3:  # Average
                base_score += 3
                reasoning.append(f"Solid barrel rate ({barrel_pct:.1f}%)")
            elif barrel_pct < 2 and barrel_pct > 0:
                risk_factors.append(f"Low barrel rate ({barrel_pct:.1f}%)")
            
            # Hard contact analysis (10% weight)
            ev95_pct = hitter_data.get('ev95_percent', 0)
            if ev95_pct >= 35:  # Elite hard contact
                base_score += 8
                reasoning.append(f"Elite hard contact ({ev95_pct:.1f}%)")
            elif ev95_pct >= 25:  # Good hard contact
                base_score += 5
                reasoning.append(f"Strong hard contact ({ev95_pct:.1f}%)")
            elif ev95_pct < 15 and ev95_pct > 0:
                risk_factors.append(f"Low hard contact rate ({ev95_pct:.1f}%)")
        
        # Swing Path Analysis (15% weight)
        if swing_path_data and player_name in swing_path_data:
            # Determine pitcher handedness - for now assume RHP unless specified
            # This could be enhanced by determining actual pitcher handedness from pitcher data
            pitcher_hand = 'rhp'  # Default to RHP for now
            
            swing_data = swing_path_data[player_name].get(pitcher_hand, {})
            if swing_data:
                # Bat speed analysis (5% weight)
                bat_speed = swing_data.get('avg_bat_speed', 0)
                if bat_speed >= 75:  # Elite bat speed
                    base_score += 6
                    reasoning.append(f"Elite bat speed ({bat_speed:.1f} mph)")
                elif bat_speed >= 72:  # Above average
                    base_score += 4
                    reasoning.append(f"Strong bat speed ({bat_speed:.1f} mph)")
                elif bat_speed >= 69:  # Average
                    base_score += 2
                    reasoning.append(f"Solid bat speed ({bat_speed:.1f} mph)")
                elif bat_speed < 67 and bat_speed > 0:
                    risk_factors.append(f"Below average bat speed ({bat_speed:.1f} mph)")
                
                # Attack angle analysis (5% weight) - ideal range is 5-20 degrees
                attack_angle = swing_data.get('attack_angle', 0)
                if 5 <= attack_angle <= 20:  # Ideal range for home runs
                    base_score += 6
                    reasoning.append(f"Optimal attack angle ({attack_angle:.1f}°)")
                elif 3 <= attack_angle <= 25:  # Good range
                    base_score += 3
                    reasoning.append(f"Good attack angle ({attack_angle:.1f}°)")
                elif attack_angle < 0 or attack_angle > 30:  # Poor range
                    risk_factors.append(f"Poor attack angle ({attack_angle:.1f}°)")
                
                # Ideal attack angle rate (5% weight)
                ideal_rate = swing_data.get('ideal_attack_angle_rate', 0)
                if ideal_rate >= 0.5:  # High consistency
                    base_score += 5
                    reasoning.append(f"High ideal angle rate ({ideal_rate*100:.0f}%)")
                elif ideal_rate >= 0.3:  # Good consistency
                    base_score += 3
                    reasoning.append(f"Good ideal angle rate ({ideal_rate*100:.0f}%)")
                elif ideal_rate < 0.2 and ideal_rate > 0:
                    risk_factors.append(f"Low ideal angle rate ({ideal_rate*100:.0f}%)")
                
                # Create comprehensive swing optimization score
                swing_optimization_score = 0
                if bat_speed > 0 and attack_angle > 0 and ideal_rate > 0:
                    # Normalize bat speed (67-79 mph range to 0-100)
                    bat_speed_norm = min(100, max(0, (bat_speed - 67) / 12 * 100))
                    
                    # Attack angle score (5-20 degrees is optimal)
                    if 5 <= attack_angle <= 20:
                        angle_score = 100
                    elif 3 <= attack_angle <= 25:
                        angle_score = 75
                    elif 0 <= attack_angle <= 30:
                        angle_score = 50
                    else:
                        angle_score = 25
                    
                    # Ideal rate score
                    rate_score = min(100, ideal_rate * 200)  # 0.5 rate = 100 score
                    
                    # Weighted average
                    swing_optimization_score = int((bat_speed_norm * 0.4) + (angle_score * 0.3) + (rate_score * 0.3))
        
        # Advanced Pitcher Analysis (25% weight)  
        if advanced_pitcher_stats and pitcher_name in advanced_pitcher_stats:
            pitcher_data = advanced_pitcher_stats[pitcher_name]
            
            # Pitcher vulnerability analysis (15% weight)
            exit_velo_allowed = pitcher_data.get('exit_velocity_allowed', 0)
            if exit_velo_allowed >= 90:  # Vulnerable pitcher
                base_score += 10
                reasoning.append(f"Pitcher allows hard contact ({exit_velo_allowed:.1f} mph)")
            elif exit_velo_allowed >= 87:
                base_score += 6
                reasoning.append(f"Pitcher allows solid contact ({exit_velo_allowed:.1f} mph)")
            elif exit_velo_allowed <= 83 and exit_velo_allowed > 0:
                risk_factors.append(f"Pitcher limits contact quality ({exit_velo_allowed:.1f} mph)")
            
            # Barrel rate allowed (10% weight)
            barrel_allowed = pitcher_data.get('barrel_percent_allowed', 0)
            if barrel_allowed >= 8:  # Vulnerable to barrels
                base_score += 8
                reasoning.append(f"Pitcher vulnerable to barrels ({barrel_allowed:.1f}%)")
            elif barrel_allowed >= 5:
                base_score += 4
                reasoning.append(f"Pitcher allows barrels ({barrel_allowed:.1f}%)")
            elif barrel_allowed <= 3 and barrel_allowed > 0:
                risk_factors.append(f"Pitcher limits barrels ({barrel_allowed:.1f}%)")
            
            # Home run rate
            hr_rate = pitcher_data.get('home_runs_allowed', 0) / max(pitcher_data.get('games', 1), 1)
            if hr_rate >= 1.5:  # Very vulnerable
                base_score += 6
                reasoning.append(f"High HR rate allowed ({hr_rate:.2f}/game)")
            elif hr_rate >= 1.0:
                base_score += 3
                reasoning.append(f"Moderate HR rate allowed ({hr_rate:.2f}/game)")
            elif hr_rate <= 0.5:
                risk_factors.append(f"Low HR rate allowed ({hr_rate:.2f}/game)")
        
        # Venue analysis (10% weight)
        venue = pitcher_matchup.get('venue', '')
        hitter_friendly_parks = ['Yankee Stadium', 'Coors Field', 'Fenway Park', 'Camden Yards', 'Minute Maid Park']
        pitcher_friendly_parks = ['Petco Park', 'Marlins Park', 'Tropicana Field']
        
        if any(park in venue for park in hitter_friendly_parks):
            base_score += 8
            reasoning.append(f"Hitter-friendly venue ({venue})")
        elif any(park in venue for park in pitcher_friendly_parks):
            base_score -= 5
            risk_factors.append(f"Pitcher-friendly venue ({venue})")
        
        # Home field advantage (5% weight)
        if pitcher_matchup.get('is_home'):
            base_score += 5
            reasoning.append("Home field advantage")
        
        # Historical performance lookup (backup data)
        historical_match = None
        for hist_player in historical_stats:
            hist_name = hist_player.get('name', hist_player.get('Name', ''))
            if (hist_name.lower() == player_name.lower() or 
                player_name.lower() in hist_name.lower() or
                hist_name.lower() in player_name.lower()):
                historical_match = hist_player
                break
        
        if historical_match:
            # Analyze recent HR performance (backup/confirmation)
            hr_total = historical_match.get('homeRuns', historical_match.get('HR', 0))
            if hr_total > 15:  # Good power numbers
                base_score += 4
                reasoning.append(f"Strong power profile ({hr_total} HRs)")
            elif hr_total > 8:
                base_score += 2
                reasoning.append(f"Decent power ({hr_total} HRs)")
        
        # Determine pathway based on score and analysis type
        if base_score >= 80:
            pathway = "perfectStorm"
            reasoning.append("Perfect Storm: Elite combination of factors")
        elif base_score >= 70:
            # Determine if batter-driven or pitcher-driven based on primary factors
            hitter_factors = len([r for r in reasoning if any(word in r.lower() for word in ['exit velocity', 'barrel', 'contact', 'power'])])
            pitcher_factors = len([r for r in reasoning if any(word in r.lower() for word in ['pitcher', 'allows', 'vulnerable'])])
            
            if hitter_factors >= pitcher_factors:
                pathway = "batterDriven"
                reasoning.append("Batter-Driven: Strong offensive profile with advanced metrics")
            else:
                pathway = "pitcherDriven"
                reasoning.append("Pitcher-Driven: Exploiting pitcher vulnerabilities")
        else:
            pathway = "pitcherDriven"
            reasoning.append("Pitcher-Driven: Exploiting pitcher weakness")
        
        return min(95, max(45, base_score)), pathway, reasoning, risk_factors

    def generate_analysis(self, team_filter: List[str] = None) -> Dict:
        """Generate complete Hellraiser analysis"""
        print(f"\n🔥 Generating Hellraiser Analysis for {self.today}")
        
        # Load all data sources
        odds_data = self.load_current_odds()
        lineup_data = self.load_lineup_data()
        roster_data = self.load_roster_data()
        historical_stats = self.load_historical_stats()
        advanced_hitter_stats = self.load_advanced_hitter_stats()
        advanced_pitcher_stats = self.load_advanced_pitcher_stats()
        swing_path_data = self.load_swing_path_data()
        historical_odds = self.load_historical_odds()
        
        if not odds_data:
            return self.create_error_response("No odds data available")
        
        if not lineup_data:
            return self.create_error_response("No lineup data available")
        
        # Create player-team mapping
        player_team_map = self.create_player_team_mapping(roster_data)
        
        # Process each player with odds
        analysis_picks = []
        processed_count = 0
        
        for odds_player in odds_data:
            player_name = odds_player['player_name']
            
            # Find player's team
            team = self.find_player_team(player_name, player_team_map)
            if not team:
                print(f"⚠️ Could not find team for {player_name}")
                continue
            
            # Apply team filter if specified
            if team_filter and team not in team_filter:
                continue
            
            # Get pitcher matchup
            pitcher_matchup = self.get_pitcher_matchup(team, lineup_data)
            if not pitcher_matchup:
                print(f"⚠️ No pitcher matchup found for {player_name} ({team})")
                continue
            
            # Calculate Hellraiser score with advanced metrics
            score, pathway, reasoning, risk_factors = self.calculate_hellraiser_score(
                odds_player, pitcher_matchup, historical_stats, 
                advanced_hitter_stats, advanced_pitcher_stats, swing_path_data, historical_odds
            )
            
            # Create analysis pick
            pick = {
                'playerName': player_name,
                'team': team,
                'pitcher': f"vs {pitcher_matchup['pitcher_name']}",
                'confidenceScore': score,
                'classification': self.get_classification(score),
                'pathway': pathway,
                'reasoning': '; '.join(reasoning),
                'riskFactors': risk_factors,
                'game': f"{pitcher_matchup.get('opponent_team', 'TBD')} @ {team if pitcher_matchup.get('is_home') else pitcher_matchup.get('opponent_team', 'TBD')}",
                'venue': pitcher_matchup.get('venue', 'Unknown'),
                'gameTime': pitcher_matchup.get('game_time', ''),
                'odds': {
                    'american': odds_player['odds'],
                    'decimal': self.american_to_decimal(odds_player['odds']),
                    'source': 'current'
                },
                'marketEfficiency': self.evaluate_market_efficiency(odds_player['odds'], score)
            }
            
            # Add swing path data if available
            if swing_path_data and player_name in swing_path_data:
                # Default to RHP for now - could be enhanced with actual pitcher handedness
                pitcher_hand = 'rhp'
                swing_data = swing_path_data[player_name].get(pitcher_hand, {})
                
                if swing_data:
                    # Calculate swing optimization score
                    bat_speed = swing_data.get('avg_bat_speed', 0)
                    attack_angle = swing_data.get('attack_angle', 0)
                    ideal_rate = swing_data.get('ideal_attack_angle_rate', 0)
                    
                    swing_optimization_score = 0
                    if bat_speed > 0 and attack_angle > 0 and ideal_rate > 0:
                        # Normalize bat speed (67-79 mph range to 0-100)
                        bat_speed_norm = min(100, max(0, (bat_speed - 67) / 12 * 100))
                        
                        # Attack angle score (5-20 degrees is optimal)
                        if 5 <= attack_angle <= 20:
                            angle_score = 100
                        elif 3 <= attack_angle <= 25:
                            angle_score = 75
                        elif 0 <= attack_angle <= 30:
                            angle_score = 50
                        else:
                            angle_score = 25
                        
                        # Ideal rate score
                        rate_score = min(100, ideal_rate * 200)  # 0.5 rate = 100 score
                        
                        # Weighted average
                        swing_optimization_score = int((bat_speed_norm * 0.4) + (angle_score * 0.3) + (rate_score * 0.3))
                    
                    # Add swing path fields to the pick
                    pick['swing_bat_speed'] = bat_speed
                    pick['swing_attack_angle'] = attack_angle
                    pick['swing_optimization_score'] = swing_optimization_score
                    pick['swing_ideal_rate'] = ideal_rate
            
            analysis_picks.append(pick)
            processed_count += 1
            
            # Uncomment for debugging: print(f"✅ {player_name} ({team}) vs {pitcher_matchup['pitcher_name']} - Score: {score}")
        
        # Sort picks by confidence score
        analysis_picks.sort(key=lambda x: x['confidenceScore'], reverse=True)
        
        # Categorize by pathway
        pathway_breakdown = {
            'perfectStorm': [p for p in analysis_picks if p['pathway'] == 'perfectStorm'],
            'batterDriven': [p for p in analysis_picks if p['pathway'] == 'batterDriven'],
            'pitcherDriven': [p for p in analysis_picks if p['pathway'] == 'pitcherDriven']
        }
        
        # Calculate summary statistics
        total_picks = len(analysis_picks)
        personal_straight = len([p for p in analysis_picks if p['classification'] == 'Personal Straight'])
        longshots = len([p for p in analysis_picks if p['classification'] == 'Longshot'])
        
        if total_picks > 0:
            avg_odds = sum([self.american_to_decimal(p['odds']['american']) for p in analysis_picks]) / total_picks
        else:
            avg_odds = 0
        
        # Create final analysis
        analysis = {
            'date': self.today,
            'updatedAt': datetime.now().isoformat(),
            'generatedBy': 'python_hellraiser_generator',
            'teamFilter': team_filter,
            'picks': analysis_picks,
            'pathwayBreakdown': pathway_breakdown,
            'summary': {
                'totalPicks': total_picks,
                'personalStraight': personal_straight,
                'longshots': longshots,
                'averageOdds': round(avg_odds, 2)
            },
            'dataQuality': {
                'playersWithOdds': len(odds_data),
                'playersProcessed': processed_count,
                'gamesAvailable': len(lineup_data.get('games', [])),
                'historicalDataAvailable': len(historical_stats) > 0
            }
        }
        
        print(f"\n🔥 Analysis Complete:")
        print(f"   Total Picks: {total_picks}")
        print(f"   Perfect Storm: {len(pathway_breakdown['perfectStorm'])}")
        print(f"   Batter-Driven: {len(pathway_breakdown['batterDriven'])}")
        print(f"   Pitcher-Driven: {len(pathway_breakdown['pitcherDriven'])}")
        
        return analysis

    def create_error_response(self, error_message: str) -> Dict:
        """Create error response with basic structure"""
        return {
            'date': self.today,
            'error': error_message,
            'picks': [],
            'pathwayBreakdown': {'perfectStorm': [], 'batterDriven': [], 'pitcherDriven': []},
            'summary': {'totalPicks': 0, 'personalStraight': 0, 'longshots': 0, 'averageOdds': 0}
        }

    def get_classification(self, score: int) -> str:
        """Get classification based on confidence score"""
        if score >= 80:
            return 'Personal Straight'
        elif score >= 70:
            return 'Straight'
        elif score >= 60:
            return 'Value Play'
        else:
            return 'Longshot'

    def american_to_decimal(self, american_odds: str) -> float:
        """Convert American odds to decimal"""
        try:
            if american_odds.startswith('+'):
                value = int(american_odds[1:])
                return round((value / 100) + 1, 2)
            else:
                value = int(american_odds)
                return round((100 / abs(value)) + 1, 2)
        except ValueError:
            return 1.0

    def evaluate_market_efficiency(self, odds: str, confidence: int) -> dict:
        """Evaluate market efficiency based on odds vs confidence with detailed breakdown"""
        decimal_odds = self.american_to_decimal(odds)
        implied_prob = 1 / decimal_odds
        
        # Convert confidence score to realistic probability using a scaling function
        # High confidence (90+) = ~15-25% actual probability
        # Medium confidence (70-89) = ~8-15% actual probability  
        # Low confidence (50-69) = ~3-8% actual probability
        if confidence >= 90:
            confidence_prob = 0.15 + (confidence - 90) * 0.01  # 15-25%
        elif confidence >= 70:
            confidence_prob = 0.08 + (confidence - 70) * 0.0035  # 8-15%
        elif confidence >= 50:
            confidence_prob = 0.03 + (confidence - 50) * 0.0025  # 3-8%
        else:
            confidence_prob = 0.01 + confidence * 0.0004  # 1-3%
        
        # Calculate edge (positive = good value, negative = poor value)
        edge = confidence_prob - implied_prob
        edge_pct = edge * 100
        
        # Realistic thresholds for sports betting analysis with reasoning
        if confidence_prob > implied_prob * 1.5:  # 50%+ edge required (very rare)
            value = 'positive'
            assessment = 'Exceptional Value'
            reasoning = f"Model confidence significantly exceeds market expectations (+{edge_pct:.1f}% edge) - rare opportunity"
        elif confidence_prob > implied_prob * 1.25:  # 25%+ edge
            value = 'positive'
            assessment = 'Strong Value'
            reasoning = f"Model shows strong edge over market price (+{edge_pct:.1f}% advantage)"
        elif confidence_prob > implied_prob * 1.1:  # 10%+ edge
            value = 'positive'
            assessment = 'Undervalued'
            reasoning = f"Market appears to undervalue this opportunity (+{edge_pct:.1f}% model edge)"
        elif confidence_prob > implied_prob * 1.03:  # 3%+ edge (slight value)
            value = 'slight_positive'
            assessment = 'Slight Value'
            reasoning = f"Minor positive edge detected (+{edge_pct:.1f}%) - marginal value play"
        elif confidence_prob < implied_prob * 0.85:  # 15%+ negative edge
            value = 'negative'
            assessment = 'Overvalued'
            reasoning = f"Market price appears inflated ({edge_pct:.1f}% negative edge) - avoid"
        elif confidence_prob < implied_prob * 0.97:  # 3%+ negative edge
            value = 'slight_negative'
            assessment = 'Slight Overvalued'
            reasoning = f"Slightly overpriced by market ({edge_pct:.1f}% negative edge)"
        else:
            value = 'neutral'
            assessment = 'Fair Value'
            reasoning = f"Market price aligns well with model assessment ({edge_pct:+.1f}% edge)"
        
        return {
            'modelProbability': confidence_prob,
            'impliedProbability': implied_prob,
            'edge': edge,
            'value': value,
            'assessment': assessment,
            'reasoning': reasoning
        }

    def save_analysis(self, analysis: Dict, team_filter: List[str] = None, archive: bool = True) -> str:
        """Save analysis to JSON file with optional archiving"""
        timestamp = datetime.now().strftime("%H%M")  # HHMM format
        
        if team_filter:
            filename = f"hellraiser_analysis_{self.today}_{'_'.join(team_filter)}.json"
            archive_filename = f"hellraiser_analysis_{self.today}_{timestamp}_{'_'.join(team_filter)}.json"
        else:
            filename = f"hellraiser_analysis_{self.today}.json"
            archive_filename = f"hellraiser_analysis_{self.today}_{timestamp}.json"
        
        # Save current version (for React app)
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Archive timestamped version
        if archive:
            archive_dir = self.output_dir / "archive" / self.today
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = archive_dir / archive_filename
            
            # Add run metadata to archived version
            archived_analysis = {
                **analysis,
                'runMetadata': {
                    'timestamp': datetime.now().isoformat(),
                    'runTime': timestamp,
                    'dayOfWeek': datetime.now().strftime('%A'),
                    'hoursToFirstGame': self.calculate_hours_to_first_game(),
                    'totalOddsChanges': self.count_odds_changes_since_opening()
                }
            }
            
            with open(archive_path, 'w') as f:
                json.dump(archived_analysis, f, indent=2)
            
            print(f"✅ Analysis saved to {output_path}")
            print(f"📁 Archived to {archive_path}")
            return str(output_path)
        
        print(f"✅ Analysis saved to {output_path}")
        return str(output_path)

    def calculate_hours_to_first_game(self) -> float:
        """Calculate hours until first game starts"""
        try:
            lineup_file = self.base_dir / "public" / "data" / "lineups" / f"starting_lineups_{self.today}.json"
            with open(lineup_file, 'r') as f:
                lineup_data = json.load(f)
            
            earliest_time = None
            for game in lineup_data.get('games', []):
                game_time_str = game.get('gameTime', '')
                if game_time_str:
                    # Parse game time and find earliest
                    try:
                        game_time = datetime.strptime(f"{self.today} {game_time_str}", "%Y-%m-%d %H:%M")
                        if earliest_time is None or game_time < earliest_time:
                            earliest_time = game_time
                    except:
                        continue
            
            if earliest_time:
                now = datetime.now()
                hours_diff = (earliest_time - now).total_seconds() / 3600
                return round(hours_diff, 1)
        except:
            pass
        
        return 0.0

    def count_odds_changes_since_opening(self) -> int:
        """Count how many players have odds different from opening"""
        try:
            odds_file = self.base_dir / "public" / "data" / "odds" / "mlb-hr-odds-tracking.csv"
            if not odds_file.exists():
                return 0
            
            changes = 0
            with open(odds_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    current = row.get('current_odds', '')
                    opening = row.get('opening_odds', '')
                    if current and opening and current != opening:
                        changes += 1
            
            return changes
        except:
            return 0

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Hellraiser HR Analysis')
    parser.add_argument('--teams', nargs='*', help='Filter by specific teams (e.g., NYY BAL)')
    parser.add_argument('--date', help='Analysis date (YYYY-MM-DD, default: today)')
    parser.add_argument('--output-dir', help='Output directory for analysis files')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = HellraiserAnalysisGenerator()
    
    if args.date:
        generator.today = args.date
    
    # Generate analysis
    team_filter = args.teams if args.teams else None
    analysis = generator.generate_analysis(team_filter)
    
    # Save analysis
    output_path = generator.save_analysis(analysis, team_filter)
    
    if analysis.get('error'):
        print(f"❌ Analysis failed: {analysis['error']}")
        sys.exit(1)
    else:
        print(f"🔥 Hellraiser Analysis completed successfully!")
        print(f"📁 Output: {output_path}")

if __name__ == "__main__":
    main()