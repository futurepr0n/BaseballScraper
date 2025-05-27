import json
import csv
from datetime import datetime
import os

# Load the JSON data from the file
file_path = 'mlb-batter-hr-props.json'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Error: File '{file_path}' not found. Please download it first.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{file_path}'. The file might be corrupted or not valid JSON.")
    exit()

# --- Step 1: Pre-process markets to easily get market type by ID ---
markets_info = {}
if 'markets' not in data or not data['markets']:
    print("Error: 'markets' key not found or is empty in the JSON data.")
    exit()

for market in data['markets']:
    market_id = market.get('id')
    market_name = market.get('name', '').lower() # Market name like "Shohei Ohtani Home Runs"
    market_type_name = market.get('marketType', {}).get('name', '').lower() # e.g., "home runs milestones"

    prop_type = None
    # Prioritize marketType.name if available and specific
    if "home runs" in market_type_name:
        prop_type = "Home Runs"
    elif "hits milestones" in market_type_name: # More specific than just "hits"
        prop_type = "Hits"
    # Fallback to checking market.name if marketType.name wasn't specific enough
    elif prop_type is None:
        if "home runs" in market_name:
            prop_type = "Home Runs"
        # Be careful with "Hits" to not confuse with "Hits Allowed" (pitcher prop)
        elif "hits" in market_name and "allowed" not in market_name and "vs" not in market_name:
            prop_type = "Hits"

    if market_id and prop_type:
        markets_info[market_id] = {
            "prop_type": prop_type,
            "original_market_name": market.get('name') # Store original for potential player name extraction
        }

# --- Step 2: Process selections to extract odds ---
home_run_odds_1plus = []
hits_odds_1plus = []

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
        
        # Player name is usually in the selection's participant list
        player_name = participants[0].get('name')
        
        if not player_name:
            # Fallback: try to parse from market name if desperate, though less reliable
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
            home_run_odds_1plus.append((player_name, odds_american))
        elif prop_type == "Hits":
            hits_odds_1plus.append((player_name, odds_american))

# --- Step 3: Write to CSV ---
# Hardcoded directory path
output_dir = '/app/BaseballTracker/public/data/odds'
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, 'mlb-hr-odds.csv')
current_time = datetime.now().isoformat()

try:
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['player_name', 'prop_type', 'odds', 'last_updated'])
        
        # Write home run odds (remove duplicates and sort)
        unique_hr_odds = list(set(home_run_odds_1plus))
        for player_name, odds in sorted(unique_hr_odds):
            writer.writerow([player_name, 'Home Runs', odds, current_time])
        
        # Write hits odds (remove duplicates and sort)
        unique_hits_odds = list(set(hits_odds_1plus))
        for player_name, odds in sorted(unique_hits_odds):
            writer.writerow([player_name, 'Hits', odds, current_time])

    print(f"Successfully wrote {len(unique_hr_odds)} home run odds and {len(unique_hits_odds)} hits odds to {output_file}")
    
except Exception as e:
    print(f"Error writing to CSV file: {e}")
    exit(1)

# Also create a separate HR-only file for easier processing
hr_only_file = os.path.join(output_dir, 'mlb-hr-odds-only.csv')
try:
    with open(hr_only_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['player_name', 'odds', 'last_updated'])
        
        # Write only home run odds
        unique_hr_odds = list(set(home_run_odds_1plus))
        for player_name, odds in sorted(unique_hr_odds):
            writer.writerow([player_name, odds, current_time])
            
    print(f"Also wrote HR-only odds to {hr_only_file}")
    
except Exception as e:
    print(f"Error writing HR-only CSV file: {e}")