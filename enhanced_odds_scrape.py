#!/usr/bin/env python3
"""
Enhanced Odds Scraper - Handles both HR and Hits props with better error handling
Uses centralized configuration and supports multiple data sources
"""

import json
import csv
import os
import shutil
from datetime import datetime

# Use centralized configuration for data paths
from config import PATHS, get_output_dirs

class EnhancedOddsScraper:
    def __init__(self):
        # Use centralized odds directory
        self.primary_dir = PATHS['odds']
        self.primary_dir.mkdir(parents=True, exist_ok=True)
        
        # Get output directories for file copying (supports dev/prod sync)
        self.output_dirs = get_output_dirs('odds')
        
        # Data source files
        self.hr_props_file = 'mlb-batter-hr-props.json'
        self.hits_props_file = 'mlb-batter-hits-props.json'
        
        print(f"🎯 Enhanced Odds Scraper initialized")
        print(f"   Primary directory: {self.primary_dir}")
        print(f"   Output directories: {len(self.output_dirs)}")
    
    def load_json_data(self, file_path, data_type):
        """Load and validate JSON data from file"""
        try:
            if not os.path.exists(file_path):
                print(f"⚠️ {data_type} file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data or 'markets' not in data:
                print(f"⚠️ Invalid {data_type} JSON structure - missing 'markets'")
                return None
            
            market_count = len(data.get('markets', []))
            selection_count = len(data.get('selections', []))
            print(f"✅ {data_type} data loaded: {market_count} markets, {selection_count} selections")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {data_type} file: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading {data_type} file: {e}")
            return None
    
    def load_tracking_data(self, tracking_file):
        """Load existing tracking data (opening odds, previous odds, etc.)"""
        tracking_data = {}
        
        if os.path.exists(tracking_file):
            try:
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        player_name = row['player_name'].strip()
                        tracking_data[player_name] = {
                            'opening_odds': row.get('opening_odds', '').strip(),
                            'previous_odds': row.get('previous_odds', '').strip(),
                            'opening_timestamp': row.get('opening_timestamp', ''),
                            'previous_timestamp': row.get('previous_timestamp', ''),
                            'total_runs': int(row.get('total_runs', 0)),
                            'session_high': row.get('session_high', '').strip(),
                            'session_low': row.get('session_low', '').strip()
                        }
                print(f"📊 Loaded tracking data for {len(tracking_data)} players")
            except Exception as e:
                print(f"⚠️ Warning: Could not load tracking data: {e}")
        else:
            print("📊 No existing tracking data found - starting fresh session")
        
        return tracking_data
    
    def parse_odds_value(self, odds_str):
        """Convert odds string to numeric value for comparison"""
        if not odds_str:
            return 0
        
        try:
            return int(odds_str.replace('+', '').replace('-', ''))
        except ValueError:
            return 0
    
    def calculate_movement_and_trends(self, player_name, current_odds, tracking_info, current_time):
        """Calculate comprehensive movement data for a player"""
        result = {
            'player_name': player_name,
            'opening_odds': '',
            'previous_odds': '', 
            'current_odds': current_odds,
            'opening_timestamp': current_time,
            'previous_timestamp': current_time,
            'current_timestamp': current_time,
            'total_runs': 1,
            'session_high': current_odds,
            'session_low': current_odds,
            'movement_from_previous': 'NEW',
            'movement_from_opening': 'NEW',
            'previous_delta': 0,
            'opening_delta': 0,
            'previous_delta_display': 'NEW',
            'opening_delta_display': 'NEW',
            'trend_direction': 'none',
            'favorable_vs_previous': 'neutral',
            'favorable_vs_opening': 'neutral'
        }
        
        if player_name in tracking_info:
            # Player exists in tracking
            existing = tracking_info[player_name]
            
            # Set opening odds (never changes during the day)
            result['opening_odds'] = existing['opening_odds'] or current_odds
            result['opening_timestamp'] = existing['opening_timestamp'] or current_time
            
            # Set previous odds (from last scrape)
            result['previous_odds'] = existing['previous_odds'] or existing['opening_odds'] or current_odds
            result['previous_timestamp'] = existing['previous_timestamp'] or existing['opening_timestamp'] or current_time
            
            # Increment run count
            result['total_runs'] = existing['total_runs'] + 1
            
            # Track session high/low
            curr_val = self.parse_odds_value(current_odds)
            high_val = self.parse_odds_value(existing['session_high']) if existing['session_high'] else curr_val
            low_val = self.parse_odds_value(existing['session_low']) if existing['session_low'] else curr_val
            
            result['session_high'] = existing['session_high'] if curr_val <= high_val else current_odds
            result['session_low'] = existing['session_low'] if curr_val >= low_val else current_odds
            
            # Calculate movement from previous and opening
            if result['previous_odds']:
                previous_movement = self.calculate_single_movement(result['previous_odds'], current_odds, 'previous')
                result.update({
                    'movement_from_previous': previous_movement['movement'],
                    'previous_delta': previous_movement['delta'],
                    'previous_delta_display': previous_movement['delta_display'],
                    'favorable_vs_previous': previous_movement['favorable']
                })
            
            if result['opening_odds']:
                opening_movement = self.calculate_single_movement(result['opening_odds'], current_odds, 'opening')
                result.update({
                    'movement_from_opening': opening_movement['movement'],
                    'opening_delta': opening_movement['delta'],
                    'opening_delta_display': opening_movement['delta_display'],
                    'favorable_vs_opening': opening_movement['favorable']
                })
                
                # Overall trend direction
                if abs(result['opening_delta']) < 25:
                    result['trend_direction'] = 'stable'
                elif result['opening_delta'] > 0:
                    result['trend_direction'] = 'bullish'  # Getting longer odds
                else:
                    result['trend_direction'] = 'bearish'  # Getting shorter odds
        else:
            # First time seeing this player today
            result['opening_odds'] = current_odds
            result['previous_odds'] = current_odds
            print(f"🆕 NEW PLAYER: {player_name} opening at {current_odds}")
        
        return result
    
    def calculate_single_movement(self, old_odds, new_odds, comparison_type):
        """Calculate movement between two odds values"""
        if not old_odds or not new_odds:
            return {
                'movement': 'ERROR',
                'delta': 0,
                'delta_display': 'ERROR',
                'favorable': 'neutral'
            }
        
        old_val = self.parse_odds_value(old_odds)
        new_val = self.parse_odds_value(new_odds)
        
        if old_val == 0 or new_val == 0:
            return {
                'movement': 'ERROR',
                'delta': 0,
                'delta_display': 'ERROR', 
                'favorable': 'neutral'
            }
        
        delta = new_val - old_val
        
        # Set movement threshold based on comparison type
        threshold = 10 if comparison_type == 'previous' else 25  # Larger threshold for opening comparison
        
        if abs(delta) < threshold:
            return {
                'movement': 'STABLE',
                'delta': delta,
                'delta_display': '→',
                'favorable': 'neutral'
            }
        elif delta > 0:  # Odds got longer (better for bettor)
            return {
                'movement': 'UP',
                'delta': delta,
                'delta_display': f'+{delta}',
                'favorable': 'good'
            }
        else:  # Odds got shorter (worse for bettor)
            return {
                'movement': 'DOWN',
                'delta': delta,
                'delta_display': str(delta),
                'favorable': 'bad'
            }
    
    def process_prop_data(self, data, prop_type, tracking_data):
        """Process prop data (HR or Hits) and return processed players"""
        if not data:
            return []
        
        current_time = datetime.now().isoformat()
        processed_players = []
        
        # Step 1: Process markets to identify prop types
        markets_info = {}
        if 'markets' not in data or not data['markets']:
            print(f"⚠️ No markets found in {prop_type} data")
            return []
        
        for market in data['markets']:
            market_id = market.get('id')
            market_name = market.get('name', '').lower()
            market_type_name = market.get('marketType', {}).get('name', '').lower()
            
            identified_prop = None
            if prop_type == "HR":
                if "home runs" in market_type_name or "home runs" in market_name:
                    identified_prop = "Home Runs"
            elif prop_type == "Hits":
                if "hits milestones" in market_type_name:
                    identified_prop = "Hits"
                elif ("hits" in market_name and 
                      "allowed" not in market_name and 
                      "vs" not in market_name):
                    identified_prop = "Hits"
            
            if market_id and identified_prop:
                markets_info[market_id] = {
                    "prop_type": identified_prop,
                    "original_market_name": market.get('name')
                }
        
        print(f"📊 Found {len(markets_info)} {prop_type} markets")
        
        # Step 2: Process selections
        if 'selections' not in data or not data['selections']:
            print(f"⚠️ No selections found in {prop_type} data")
            return []
        
        for selection in data['selections']:
            market_id = selection.get('marketId')
            selection_label = selection.get('label')
            
            if market_id in markets_info and selection_label == "1+":
                market_detail = markets_info[market_id]
                
                participants = selection.get('participants')
                if not participants or not isinstance(participants, list) or len(participants) == 0:
                    continue
                
                player_name = participants[0].get('name')
                
                if not player_name:
                    if market_detail["original_market_name"]:
                        name_parts = market_detail["original_market_name"].split(f" {market_detail['prop_type']}")
                        if name_parts:
                            player_name = name_parts[0].strip()
                
                if not player_name:
                    continue
                
                odds_american = selection.get('displayOdds', {}).get('american')
                if not odds_american:
                    continue
                
                # Calculate comprehensive movement and trends
                player_data = self.calculate_movement_and_trends(player_name, odds_american, tracking_data, current_time)
                processed_players.append(player_data)
                
                # Print status
                status_msg = f"{'⚾' if prop_type == 'HR' else '🥎'} {prop_type} {player_name}: {player_data['opening_odds']} → {player_data['previous_odds']} → {odds_american}"
                if player_data['movement_from_previous'] != 'NEW':
                    status_msg += f" ({player_data['previous_delta_display']})"
                if player_data['total_runs'] > 1:
                    status_msg += f" [Run #{player_data['total_runs']}, Trend: {player_data['trend_direction']}]"
                print(status_msg)
        
        return processed_players
    
    def write_output_files(self, hr_players, hits_players):
        """Write all output CSV files"""
        try:
            # Define all file paths
            hr_odds_file = os.path.join(self.primary_dir, 'mlb-hr-odds-only.csv')
            hr_tracking_file = os.path.join(self.primary_dir, 'mlb-hr-odds-tracking.csv')
            hr_historical_file = os.path.join(self.primary_dir, 'mlb-hr-odds-history.csv')
            
            hits_odds_file = os.path.join(self.primary_dir, 'mlb-hits-odds-only.csv')
            hits_tracking_file = os.path.join(self.primary_dir, 'mlb-hits-odds-tracking.csv')
            hits_historical_file = os.path.join(self.primary_dir, 'mlb-hits-odds-history.csv')
            
            files_written = []
            
            # Write HR files
            if hr_players:
                # Basic HR odds file
                with open(hr_odds_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['player_name', 'odds', 'last_updated'])
                    for player_data in hr_players:
                        writer.writerow([player_data['player_name'], player_data['current_odds'], player_data['current_timestamp']])
                files_written.append(('mlb-hr-odds-only.csv', len(hr_players)))
                
                # HR tracking file
                with open(hr_tracking_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['player_name', 'opening_odds', 'previous_odds', 'current_odds',
                                 'opening_timestamp', 'previous_timestamp', 'current_timestamp',
                                 'total_runs', 'session_high', 'session_low',
                                 'movement_from_previous', 'movement_from_opening', 
                                 'previous_delta', 'opening_delta',
                                 'previous_delta_display', 'opening_delta_display',
                                 'trend_direction', 'favorable_vs_previous', 'favorable_vs_opening']
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for player_data in hr_players:
                        # Update previous odds for next run
                        player_data['previous_odds'] = player_data['current_odds']
                        player_data['previous_timestamp'] = player_data['current_timestamp']
                        writer.writerow(player_data)
                files_written.append(('mlb-hr-odds-tracking.csv', len(hr_players)))
                
                # HR history (append)
                self.append_to_history(hr_players, hr_historical_file)
                files_written.append(('mlb-hr-odds-history.csv', len(hr_players)))
            
            # Write Hits files
            if hits_players:
                # Basic Hits odds file
                with open(hits_odds_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['player_name', 'odds', 'last_updated'])
                    for player_data in hits_players:
                        writer.writerow([player_data['player_name'], player_data['current_odds'], player_data['current_timestamp']])
                files_written.append(('mlb-hits-odds-only.csv', len(hits_players)))
                
                # Hits tracking file
                with open(hits_tracking_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['player_name', 'opening_odds', 'previous_odds', 'current_odds',
                                 'opening_timestamp', 'previous_timestamp', 'current_timestamp',
                                 'total_runs', 'session_high', 'session_low',
                                 'movement_from_previous', 'movement_from_opening', 
                                 'previous_delta', 'opening_delta',
                                 'previous_delta_display', 'opening_delta_display',
                                 'trend_direction', 'favorable_vs_previous', 'favorable_vs_opening']
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for player_data in hits_players:
                        # Update previous odds for next run
                        player_data['previous_odds'] = player_data['current_odds']
                        player_data['previous_timestamp'] = player_data['current_timestamp']
                        writer.writerow(player_data)
                files_written.append(('mlb-hits-odds-tracking.csv', len(hits_players)))
                
                # Hits history (append)
                self.append_to_history(hits_players, hits_historical_file)
                files_written.append(('mlb-hits-odds-history.csv', len(hits_players)))
            
            # Copy files to all output directories
            self.copy_files_to_all_directories(files_written)
            
            return files_written
            
        except Exception as e:
            print(f"❌ Error writing output files: {e}")
            return []
    
    def append_to_history(self, player_data_list, historical_file):
        """Append current state to historical tracking"""
        try:
            file_exists = os.path.exists(historical_file)
            
            with open(historical_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'player_name', 'current_odds', 'previous_odds', 'opening_odds', 
                             'movement_from_previous', 'previous_delta', 'total_runs', 'trend_direction']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                for player_data in player_data_list:
                    writer.writerow({
                        'timestamp': player_data['current_timestamp'],
                        'player_name': player_data['player_name'],
                        'current_odds': player_data['current_odds'],
                        'previous_odds': player_data['previous_odds'], 
                        'opening_odds': player_data['opening_odds'],
                        'movement_from_previous': player_data['movement_from_previous'],
                        'previous_delta': player_data['previous_delta'],
                        'total_runs': player_data['total_runs'],
                        'trend_direction': player_data['trend_direction']
                    })
        except Exception as e:
            print(f"⚠️ Warning: Could not append to history file {historical_file}: {e}")
    
    def copy_files_to_all_directories(self, files_written):
        """Copy generated files to all output directories"""
        for i, output_dir in enumerate(self.output_dirs):
            if i == 0:  # Skip primary directory (already written)
                continue
                
            try:
                for file_name, count in files_written:
                    source_file = os.path.join(self.primary_dir, file_name)
                    target_file = os.path.join(output_dir, file_name)
                    shutil.copy2(source_file, target_file)
                    print(f"  ✓ Synced {file_name} to {output_dir}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not sync to {output_dir}: {e}")
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting Enhanced Odds Scraping...")
        print("=" * 50)
        
        # Load data sources
        hr_data = self.load_json_data(self.hr_props_file, "HR Props")
        hits_data = self.load_json_data(self.hits_props_file, "Hits Props")
        
        if not hr_data and not hits_data:
            print("❌ No valid data sources found - cannot proceed")
            return False
        
        # Load tracking data
        hr_tracking_file = os.path.join(self.primary_dir, 'mlb-hr-odds-tracking.csv')
        hits_tracking_file = os.path.join(self.primary_dir, 'mlb-hits-odds-tracking.csv')
        
        hr_tracking_data = self.load_tracking_data(hr_tracking_file)
        hits_tracking_data = self.load_tracking_data(hits_tracking_file)
        
        # Process data
        hr_players = []
        hits_players = []
        
        if hr_data:
            print(f"\n📊 Processing HR Props data...")
            hr_players = self.process_prop_data(hr_data, "HR", hr_tracking_data)
            print(f"✅ Processed {len(hr_players)} HR players")
        
        if hits_data:
            print(f"\n📊 Processing Hits Props data...")
            hits_players = self.process_prop_data(hits_data, "Hits", hits_tracking_data)
            print(f"✅ Processed {len(hits_players)} Hits players")
        
        # Write output files
        if hr_players or hits_players:
            print(f"\n💾 Writing output files...")
            files_written = self.write_output_files(hr_players, hits_players)
            
            if files_written:
                print(f"\n🎯 SUCCESS: Enhanced odds scraping completed!")
                print(f"📊 Files updated in {len(self.output_dirs)} directories:")
                
                for output_dir in self.output_dirs:
                    print(f"  📂 {output_dir}/")
                    for file_name, count in files_written:
                        print(f"    📄 {file_name} ({count} players)")
                
                # Print session summary
                if hr_players:
                    new_hr = len([p for p in hr_players if p['total_runs'] == 1])
                    existing_hr = len(hr_players) - new_hr
                    print(f"\n⚾ HR SESSION SUMMARY:")
                    print(f"  New players: {new_hr}, Existing players: {existing_hr}")
                
                if hits_players:
                    new_hits = len([p for p in hits_players if p['total_runs'] == 1])
                    existing_hits = len(hits_players) - new_hits
                    print(f"\n🥎 HITS SESSION SUMMARY:")
                    print(f"  New players: {new_hits}, Existing players: {existing_hits}")
                
                return True
            else:
                print("❌ Failed to write output files")
                return False
        else:
            print("❌ No players processed from available data")
            return False

def main():
    """Main entry point for backwards compatibility with original odds-scrape.py"""
    scraper = EnhancedOddsScraper()
    success = scraper.run()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()