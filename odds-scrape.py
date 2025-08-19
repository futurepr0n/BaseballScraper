#!/usr/bin/env python3
"""
Legacy odds-scrape.py - Backwards compatibility wrapper
Calls the enhanced odds scraper for improved functionality
"""

import os
import sys

# For backwards compatibility, call the enhanced version
if __name__ == "__main__":
    print("🔄 Legacy odds-scrape.py called - forwarding to enhanced version...")
    
    # Import and run enhanced version
    try:
        from enhanced_odds_scrape import EnhancedOddsScraper
        scraper = EnhancedOddsScraper()
        success = scraper.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error running enhanced odds scraper: {e}")
        print("🔄 Falling back to original logic...")
        
        # Original import logic for fallback
        import json
        import csv
        import shutil
        from datetime import datetime
        
        # Use centralized configuration for data paths
        from config import PATHS, get_output_dirs
        
        # Load the JSON data from the file
        file_path = 'mlb-batter-hr-props.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found. Please download it first.")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{file_path}'. The file might be corrupted or not valid JSON.")
            exit(1)

# Use centralized odds directory
primary_dir = PATHS['odds']
primary_dir.mkdir(parents=True, exist_ok=True)
current_odds_file = os.path.join(primary_dir, 'mlb-hr-odds-only.csv')
tracking_file = os.path.join(primary_dir, 'mlb-hr-odds-tracking.csv')
historical_file = os.path.join(primary_dir, 'mlb-hr-odds-history.csv')

# Get output directories for file copying (supports dev/prod sync)
output_dirs = get_output_dirs('odds')

def load_tracking_data():
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
            print(f"Loaded tracking data for {len(tracking_data)} players")
        except Exception as e:
            print(f"Warning: Could not load tracking data: {e}")
    else:
        print("No existing tracking data found - starting fresh session")
    
    return tracking_data

def parse_odds_value(odds_str):
    """Convert odds string to numeric value for comparison"""
    if not odds_str:
        return 0
    
    try:
        return int(odds_str.replace('+', '').replace('-', ''))
    except ValueError:
        return 0

def calculate_movement_and_trends(player_name, current_odds, tracking_info, current_time):
    """Calculate comprehensive movement data for a player"""
    result = {
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
        curr_val = parse_odds_value(current_odds)
        high_val = parse_odds_value(existing['session_high']) if existing['session_high'] else curr_val
        low_val = parse_odds_value(existing['session_low']) if existing['session_low'] else curr_val
        
        result['session_high'] = existing['session_high'] if curr_val <= high_val else current_odds
        result['session_low'] = existing['session_low'] if curr_val >= low_val else current_odds
        
        # Calculate movement from previous odds
        if result['previous_odds']:
            previous_movement = calculate_single_movement(result['previous_odds'], current_odds, 'previous')
            result['movement_from_previous'] = previous_movement['movement']
            result['previous_delta'] = previous_movement['delta']
            result['previous_delta_display'] = previous_movement['delta_display']
            result['favorable_vs_previous'] = previous_movement['favorable']
        
        # Calculate movement from opening odds  
        if result['opening_odds']:
            opening_movement = calculate_single_movement(result['opening_odds'], current_odds, 'opening')
            result['movement_from_opening'] = opening_movement['movement']
            result['opening_delta'] = opening_movement['delta']
            result['opening_delta_display'] = opening_movement['delta_display']
            result['favorable_vs_opening'] = opening_movement['favorable']
            
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
        print(f"NEW PLAYER: {player_name} opening at {current_odds}")
    
    return result

def calculate_single_movement(old_odds, new_odds, comparison_type):
    """Calculate movement between two odds values"""
    if not old_odds or not new_odds:
        return {
            'movement': 'ERROR',
            'delta': 0,
            'delta_display': 'ERROR',
            'favorable': 'neutral'
        }
    
    old_val = parse_odds_value(old_odds)
    new_val = parse_odds_value(new_odds)
    
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

def append_to_history(player_data):
    """Append current state to historical tracking"""
    file_exists = os.path.exists(historical_file)
    
    with open(historical_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'player_name', 'current_odds', 'previous_odds', 'opening_odds', 
                     'movement_from_previous', 'previous_delta', 'total_runs', 'trend_direction']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
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

# --- Step 1: Load existing tracking data ---
print("Loading existing tracking data...")
tracking_data = load_tracking_data()

# --- Step 2: Process markets ---
markets_info = {}
if 'markets' not in data or not data['markets']:
    print("Error: 'markets' key not found or is empty in the JSON data.")
    exit()

for market in data['markets']:
    market_id = market.get('id')
    market_name = market.get('name', '').lower()
    market_type_name = market.get('marketType', {}).get('name', '').lower()

    prop_type = None
    if "home runs" in market_type_name:
        prop_type = "Home Runs"
    elif "hits milestones" in market_type_name:
        prop_type = "Hits"
    elif prop_type is None:
        if "home runs" in market_name:
            prop_type = "Home Runs"
        elif "hits" in market_name and "allowed" not in market_name and "vs" not in market_name:
            prop_type = "Hits"

    if market_id and prop_type:
        markets_info[market_id] = {
            "prop_type": prop_type,
            "original_market_name": market.get('name')
        }

# --- Step 3: Process selections and calculate comprehensive tracking ---
current_time = datetime.now().isoformat()
processed_hr_players = []
processed_hits_players = []

# Load tracking data for both prop types
hits_tracking_file = os.path.join(primary_dir, 'mlb-hits-odds-tracking.csv')
hits_historical_file = os.path.join(primary_dir, 'mlb-hits-odds-history.csv')

def load_hits_tracking_data():
    """Load existing tracking data for hits props"""
    tracking_data = {}
    
    if os.path.exists(hits_tracking_file):
        try:
            with open(hits_tracking_file, 'r', encoding='utf-8') as f:
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
            print(f"Loaded hits tracking data for {len(tracking_data)} players")
        except Exception as e:
            print(f"Warning: Could not load hits tracking data: {e}")
    else:
        print("No existing hits tracking data found - starting fresh session")
    
    return tracking_data

hits_tracking_data = load_hits_tracking_data()

def append_to_hits_history(player_data):
    """Append current state to historical hits tracking"""
    file_exists = os.path.exists(hits_historical_file)
    
    with open(hits_historical_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'player_name', 'current_odds', 'previous_odds', 'opening_odds', 
                     'movement_from_previous', 'previous_delta', 'total_runs', 'trend_direction']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
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

if 'selections' not in data or not data['selections']:
    print("Error: 'selections' key not found or is empty in the JSON data.")
    exit()

for selection in data['selections']:
    market_id = selection.get('marketId')
    selection_label = selection.get('label')

    if market_id in markets_info and selection_label == "1+":
        market_detail = markets_info[market_id]
        prop_type = market_detail["prop_type"]

        participants = selection.get('participants')
        if not participants or not isinstance(participants, list) or len(participants) == 0:
            continue
        
        player_name = participants[0].get('name')
        
        if not player_name:
            if market_detail["original_market_name"]:
                name_parts = market_detail["original_market_name"].split(f" {prop_type}")
                if name_parts:
                    player_name = name_parts[0].strip()

        if not player_name:
            continue

        odds_american = selection.get('displayOdds', {}).get('american')
        if not odds_american:
            continue

        if prop_type == "Home Runs":
            # Calculate comprehensive movement and trends for HR
            player_data = calculate_movement_and_trends(player_name, odds_american, tracking_data, current_time)
            player_data['player_name'] = player_name
            
            processed_hr_players.append(player_data)
            
            # Append to historical tracking
            append_to_history(player_data)
            
            # Print comprehensive status
            status_msg = f"⚾ HR {player_name}: {player_data['opening_odds']} → {player_data['previous_odds']} → {odds_american}"
            if player_data['movement_from_previous'] != 'NEW':
                status_msg += f" ({player_data['previous_delta_display']})"
            if player_data['total_runs'] > 1:
                status_msg += f" [Run #{player_data['total_runs']}, Trend: {player_data['trend_direction']}]"
            print(status_msg)
            
        elif prop_type == "Hits":
            # Calculate comprehensive movement and trends for Hits
            player_data = calculate_movement_and_trends(player_name, odds_american, hits_tracking_data, current_time)
            player_data['player_name'] = player_name
            
            processed_hits_players.append(player_data)
            
            # Append to hits historical tracking
            append_to_hits_history(player_data)
            
            # Print comprehensive status
            status_msg = f"🥎 Hits {player_name}: {player_data['opening_odds']} → {player_data['previous_odds']} → {odds_american}"
            if player_data['movement_from_previous'] != 'NEW':
                status_msg += f" ({player_data['previous_delta_display']})"
            if player_data['total_runs'] > 1:
                status_msg += f" [Run #{player_data['total_runs']}, Trend: {player_data['trend_direction']}]"
            print(status_msg)

def copy_files_to_all_directories(files_to_copy):
    """Copy generated files to all output directories"""
    for i, output_dir in enumerate(output_dirs):
        if i == 0:  # Skip primary directory (already written)
            continue
            
        try:
            for source_file, target_name in files_to_copy:
                target_file = os.path.join(output_dir, target_name)
                import shutil
                shutil.copy2(source_file, target_file)
                print(f"  ✓ Synced {target_name} to {output_dir}")
        except Exception as e:
            print(f"  ⚠ Warning: Could not sync to {output_dir}: {e}")

# --- Step 4: Write comprehensive tracking files ---
try:
    # Define file paths for hits props
    hits_odds_file = os.path.join(primary_dir, 'mlb-hits-odds-only.csv')
    
    # Write basic HR odds file (for compatibility)
    with open(current_odds_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['player_name', 'odds', 'last_updated'])
        
        for player_data in processed_hr_players:
            writer.writerow([player_data['player_name'], player_data['current_odds'], player_data['current_timestamp']])
    
    # Write basic Hits odds file
    with open(hits_odds_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['player_name', 'odds', 'last_updated'])
        
        for player_data in processed_hits_players:
            writer.writerow([player_data['player_name'], player_data['current_odds'], player_data['current_timestamp']])
    
    # Write comprehensive HR tracking file
    with open(tracking_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['player_name', 'opening_odds', 'previous_odds', 'current_odds',
                     'opening_timestamp', 'previous_timestamp', 'current_timestamp',
                     'total_runs', 'session_high', 'session_low',
                     'movement_from_previous', 'movement_from_opening', 
                     'previous_delta', 'opening_delta',
                     'previous_delta_display', 'opening_delta_display',
                     'trend_direction', 'favorable_vs_previous', 'favorable_vs_opening']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for player_data in processed_hr_players:
            # Update previous odds for next run
            player_data['previous_odds'] = player_data['current_odds']
            player_data['previous_timestamp'] = player_data['current_timestamp']
            writer.writerow(player_data)
    
    # Write comprehensive Hits tracking file
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
        
        for player_data in processed_hits_players:
            # Update previous odds for next run
            player_data['previous_odds'] = player_data['current_odds']
            player_data['previous_timestamp'] = player_data['current_timestamp']
            writer.writerow(player_data)
    
    # Copy files to all directories (development + production)
    files_to_copy = [
        (current_odds_file, 'mlb-hr-odds-only.csv'),
        (tracking_file, 'mlb-hr-odds-tracking.csv'),
        (historical_file, 'mlb-hr-odds-history.csv'),
        (hits_odds_file, 'mlb-hits-odds-only.csv'),
        (hits_tracking_file, 'mlb-hits-odds-tracking.csv'),
        (hits_historical_file, 'mlb-hits-odds-history.csv')
    ]
    copy_files_to_all_directories(files_to_copy)

    print(f"\n🎯 SUCCESS: Processed {len(processed_hr_players)} HR players, {len(processed_hits_players)} Hits players")
    print(f"Files updated in {len(output_dirs)} directories:")
    for output_dir in output_dirs:
        print(f"  📂 {output_dir}/")
        print(f"    🏠 mlb-hr-odds-only.csv (basic HR odds)")
        print(f"    🏠 mlb-hr-odds-tracking.csv (HR movement tracking)")
        print(f"    🏠 mlb-hr-odds-history.csv (HR historical log)")
        print(f"    🥎 mlb-hits-odds-only.csv (basic Hits odds)")
        print(f"    🥎 mlb-hits-odds-tracking.csv (Hits movement tracking)")
        print(f"    🥎 mlb-hits-odds-history.csv (Hits historical log)")
    
    # Print HR session summary
    if processed_hr_players:
        new_hr_players = len([p for p in processed_hr_players if p['total_runs'] == 1])
        existing_hr_players = len(processed_hr_players) - new_hr_players
        hr_movements = {}
        hr_trends = {}
        
        for player_data in processed_hr_players:
            if player_data['total_runs'] > 1:  # Only count movement for existing players
                movement = player_data['movement_from_previous']
                hr_movements[movement] = hr_movements.get(movement, 0) + 1
                
                trend = player_data['trend_direction']
                hr_trends[trend] = hr_trends.get(trend, 0) + 1
        
        print(f"\n⚾ HR SESSION SUMMARY:")
        print(f"  New HR players: {new_hr_players}")
        print(f"  Existing HR players: {existing_hr_players}")
        
        if hr_movements:
            print(f"  HR Movement from previous:")
            for movement, count in hr_movements.items():
                print(f"    {movement}: {count}")
        
        if hr_trends:
            print(f"  HR Daily trends (vs opening):")
            for trend, count in hr_trends.items():
                print(f"    {trend}: {count}")
    
    # Print Hits session summary
    if processed_hits_players:
        new_hits_players = len([p for p in processed_hits_players if p['total_runs'] == 1])
        existing_hits_players = len(processed_hits_players) - new_hits_players
        hits_movements = {}
        hits_trends = {}
        
        for player_data in processed_hits_players:
            if player_data['total_runs'] > 1:  # Only count movement for existing players
                movement = player_data['movement_from_previous']
                hits_movements[movement] = hits_movements.get(movement, 0) + 1
                
                trend = player_data['trend_direction']
                hits_trends[trend] = hits_trends.get(trend, 0) + 1
        
        print(f"\n🥎 HITS SESSION SUMMARY:")
        print(f"  New Hits players: {new_hits_players}")
        print(f"  Existing Hits players: {existing_hits_players}")
        
        if hits_movements:
            print(f"  Hits Movement from previous:")
            for movement, count in hits_movements.items():
                print(f"    {movement}: {count}")
        
        if hits_trends:
            print(f"  Hits Daily trends (vs opening):")
            for trend, count in hits_trends.items():
                print(f"    {trend}: {count}")
        
except Exception as e:
    print(f"Error writing tracking files: {e}")
    exit(1)