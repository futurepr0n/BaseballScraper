import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import shutil
import hashlib
import os

# File paths
ROSTERS_FILE = "/app/BaseballTracker/public/data/rosters.json"
INJURIES_DIR = "/app/BaseballTracker/public/data/injuries"

# Team name mapping from full names to abbreviations
TEAM_MAPPING = {
    "Arizona Diamondbacks": "ARI",
    "Athletics": "OAK", 
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH"
}

def ensure_directories_exist():
    """Ensure the necessary directories exist."""
    os.makedirs(INJURIES_DIR, exist_ok=True)
    # Make sure the rosters directory exists too
    rosters_dir = os.path.dirname(ROSTERS_FILE)
    os.makedirs(rosters_dir, exist_ok=True)

def generate_injury_id(player_name, injury_info, first_reported_date):
    """Generate a unique ID for an injury based on player, type, and timeframe."""
    # Extract injury type from comment or status
    injury_type = ""
    comment = injury_info.get("COMMENT", "").lower()
    status = injury_info.get("STATUS", "").lower()
    
    # Common injury keywords
    injury_keywords = ["elbow", "shoulder", "knee", "back", "hamstring", "oblique", 
                      "wrist", "ankle", "finger", "thumb", "calf", "groin", 
                      "hip", "lat", "forearm", "biceps", "triceps", "quad"]
    
    for keyword in injury_keywords:
        if keyword in comment or keyword in status:
            injury_type = keyword
            break
    
    if not injury_type:
        injury_type = "general"
    
    # Create a hash based on player name, injury type, and rough timeframe (week)
    date_obj = datetime.strptime(first_reported_date, "%Y-%m-%d")
    week_start = date_obj - timedelta(days=date_obj.weekday())
    week_str = week_start.strftime("%Y-%U")
    
    injury_string = f"{player_name.lower()}_{injury_type}_{week_str}"
    injury_hash = hashlib.md5(injury_string.encode()).hexdigest()[:8]
    
    return f"{first_reported_date}_{injury_type}_{injury_hash}"

def parse_estimated_return_date(date_str):
    """Parse estimated return date and convert to a comparable format."""
    if not date_str or date_str.lower() in ['', 'n/a', 'unknown']:
        return None
    
    try:
        # Handle various date formats
        current_year = datetime.now().year
        
        # Try "Month Day" format
        if re.match(r'^[A-Za-z]+ \d+$', date_str):
            date_obj = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")
            return date_obj.strftime("%Y-%m-%d")
        
        # Try full date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        return date_str  # Return as-is if can't parse
    except:
        return date_str

def compare_return_dates(old_date, new_date):
    """Compare return dates to determine progression."""
    if not old_date or not new_date:
        return "unknown"
    
    try:
        old_parsed = parse_estimated_return_date(old_date)
        new_parsed = parse_estimated_return_date(new_date)
        
        if not old_parsed or not new_parsed:
            return "unknown"
        
        if old_parsed == new_parsed:
            return "on_track"
        elif new_parsed > old_parsed:
            return "pushed_back"
        else:
            return "moved_up"
    except:
        return "unknown"

def scrape_injuries():
    """Scrape injury data from ESPN."""
    url = "https://www.espn.com/mlb/injuries"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.espn.com/',
        'Connection': 'keep-alive'
    }
    
    response = requests.get(url, headers=headers)
    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')
    data = []
    team_sections = soup.find_all('div', class_='ResponsiveTable Table__league-injuries')

    for section in team_sections:
        team_name_element = section.find('span', class_='injuries__teamName ml2')
        
        if team_name_element:
            team_name = team_name_element.text.strip()
            table = section.find('table')
            
            if table:
                rows = table.find_all('tr', class_='Table__TR Table__TR--sm Table__even')
                
                for row in rows:
                    name_cell = row.find('td', class_='col-name Table__TD')
                    pos_cell = row.find('td', class_='col-pos Table__TD')
                    date_cell = row.find('td', class_='col-date Table__TD')
                    status_cell = row.find('td', class_='col-stat Table__TD')
                    comment_cell = row.find('td', class_='col-desc Table__TD')
                    
                    if all([name_cell, pos_cell, date_cell, status_cell, comment_cell]):
                        name_link = name_cell.find('a')
                        name = name_link.text.strip() if name_link else name_cell.text.strip()
                        
                        status_span = status_cell.find('span')
                        status = status_span.text.strip() if status_span else status_cell.text.strip()
                        
                        player_data = {
                            "TEAM NAME": team_name,
                            "NAME": name,
                            "POS": pos_cell.text.strip(),
                            "EST. RETURN DATE": date_cell.text.strip(),
                            "STATUS": status,
                            "COMMENT": comment_cell.text.strip()
                        }
                        data.append(player_data)

    return data

def normalize_string(s):
    """Normalize string for comparison."""
    if not s:
        return ''
    return re.sub(r'[.,]', '', s.lower().strip())

def extract_first_initial_last_name(full_name):
    """Extract first initial and last name from full name."""
    if not full_name:
        return ''
    
    name_parts = full_name.strip().split()
    if len(name_parts) < 2:
        return normalize_string(full_name)
    
    first_initial = name_parts[0][0]
    last_name = name_parts[-1]
    return normalize_string(f"{first_initial}. {last_name}")

def find_player_match(injured_player, roster_players):
    """Find matching player in roster for injured player."""
    injured_team = TEAM_MAPPING.get(injured_player["TEAM NAME"])
    injured_name = injured_player["NAME"]
    normalized_injured_name = normalize_string(injured_name)
    injured_initial_last_name = extract_first_initial_last_name(injured_name)
    
    team_players = [p for p in roster_players if not injured_team or p.get("team") == injured_team]
    players_to_search = team_players if team_players else roster_players
    
    # Try exact full name match first
    for player in players_to_search:
        if player.get("fullName") and normalize_string(player["fullName"]) == normalized_injured_name:
            return player
    
    # Try first initial + last name match
    for player in players_to_search:
        if normalize_string(player.get("name", "")) == injured_initial_last_name:
            return player
    
    # Try partial matches (last name only)
    injured_last_name = normalize_string(injured_name.split()[-1])
    for player in players_to_search:
        player_last_name = normalize_string(player.get("name", "").split()[-1].replace('.', ''))
        if player_last_name == injured_last_name and len(player_last_name) > 2:
            return player
    
    return None

def update_rosters_with_injuries(injury_data, create_backup=True):
    """Update rosters with enhanced injury tracking."""
    try:
        with open(ROSTERS_FILE, 'r', encoding='utf-8') as f:
            roster_data = json.load(f)
        
        print(f"Loaded {len(injury_data)} injury records and {len(roster_data)} roster players")
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        currently_injured_players = set()
        
        matched_count = 0
        new_injuries_count = 0
        updated_injuries_count = 0
        unmatched_injuries = []
        
        # Process each injured player from current scrape
        for injury in injury_data:
            matched_player = find_player_match(injury, roster_data)
            
            if matched_player:
                currently_injured_players.add(matched_player['name'])
                
                # Initialize injuries list if it doesn't exist
                if 'injuries' not in matched_player:
                    matched_player['injuries'] = []
                
                # Generate injury ID
                injury_id = generate_injury_id(matched_player['name'], injury, current_date)
                
                # Check if this injury already exists (by looking for similar recent injuries)
                existing_injury = None
                for existing in matched_player['injuries']:
                    if (existing.get('active', False) and 
                        existing.get('position') == injury['POS'] and
                        abs((datetime.strptime(current_date, "%Y-%m-%d") - 
                             datetime.strptime(existing.get('firstReported', current_date), "%Y-%m-%d")).days) <= 30):
                        existing_injury = existing
                        break
                
                if existing_injury:
                    # Update existing injury
                    old_return_date = existing_injury.get('estimatedReturn')
                    new_return_date = parse_estimated_return_date(injury["EST. RETURN DATE"])
                    
                    # Determine progression
                    progression = compare_return_dates(old_return_date, new_return_date)
                    
                    # Update the injury
                    existing_injury.update({
                        "status": injury["STATUS"],
                        "estimatedReturn": new_return_date or injury["EST. RETURN DATE"],
                        "comment": injury["COMMENT"],
                        "lastUpdated": current_date,
                        "progression": progression
                    })
                    
                    # Add to progression history
                    if 'progressionHistory' not in existing_injury:
                        existing_injury['progressionHistory'] = []
                    
                    # Only add if it's a change
                    last_entry = existing_injury['progressionHistory'][-1] if existing_injury['progressionHistory'] else {}
                    if (last_entry.get('estimatedReturn') != new_return_date or 
                        last_entry.get('status') != injury["STATUS"]):
                        existing_injury['progressionHistory'].append({
                            "date": current_date,
                            "estimatedReturn": new_return_date or injury["EST. RETURN DATE"],
                            "status": injury["STATUS"],
                            "progression": progression
                        })
                    
                    updated_injuries_count += 1
                    print(f"📝 Updated: {matched_player['name']} - {progression}")
                    
                else:
                    # Create new injury
                    new_injury = {
                        "id": injury_id,
                        "status": injury["STATUS"],
                        "estimatedReturn": parse_estimated_return_date(injury["EST. RETURN DATE"]) or injury["EST. RETURN DATE"],
                        "originalEstimatedReturn": parse_estimated_return_date(injury["EST. RETURN DATE"]) or injury["EST. RETURN DATE"],
                        "position": injury["POS"],
                        "comment": injury["COMMENT"],
                        "firstReported": current_date,
                        "lastUpdated": current_date,
                        "active": True,
                        "progression": "initial",
                        "progressionHistory": [{
                            "date": current_date,
                            "estimatedReturn": parse_estimated_return_date(injury["EST. RETURN DATE"]) or injury["EST. RETURN DATE"],
                            "status": injury["STATUS"],
                            "progression": "initial"
                        }]
                    }
                    
                    matched_player['injuries'].append(new_injury)
                    new_injuries_count += 1
                    team_abbr = TEAM_MAPPING.get(injury["TEAM NAME"], injury["TEAM NAME"])
                    print(f"🆕 New injury: {matched_player['name']} ({team_abbr}) - {injury['STATUS']}")
                
                matched_count += 1
                
            else:
                unmatched_injuries.append({
                    "name": injury["NAME"],
                    "team": injury["TEAM NAME"],
                    "status": injury["STATUS"]
                })
        
        # Mark injuries as inactive for players no longer on injury report
        inactive_count = 0
        for player in roster_data:
            if 'injuries' in player:
                for injury in player['injuries']:
                    if (injury.get('active', False) and 
                        player['name'] not in currently_injured_players):
                        injury['active'] = False
                        injury['resolvedDate'] = current_date
                        inactive_count += 1
                        print(f"✅ Resolved: {player['name']} - injury marked as inactive")
        
        # Create backup
        if create_backup:
            backup_filename = os.path.join(INJURIES_DIR, f"rosters_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json")
            shutil.copy2(ROSTERS_FILE, backup_filename)
            print(f"\nBackup created: {backup_filename}")
        
        # Write updated roster data
        with open(ROSTERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(roster_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== INJURY TRACKING SUMMARY ===")
        print(f"Total injuries processed: {len(injury_data)}")
        print(f"Successfully matched: {matched_count}")
        print(f"New injuries: {new_injuries_count}")
        print(f"Updated injuries: {updated_injuries_count}")
        print(f"Resolved injuries: {inactive_count}")
        print(f"Unmatched: {len(unmatched_injuries)}")
        
        if unmatched_injuries:
            print(f"\n=== UNMATCHED INJURIES (showing first 10) ===")
            for injury in unmatched_injuries[:10]:
                team_abbr = TEAM_MAPPING.get(injury["team"], injury["team"])
                print(f"- {injury['name']} ({team_abbr}) - {injury['status']}")
            
            if len(unmatched_injuries) > 10:
                print(f"... and {len(unmatched_injuries) - 10} more")
        
        return {
            "total_injuries": len(injury_data),
            "matched": matched_count,
            "new_injuries": new_injuries_count,
            "updated_injuries": updated_injuries_count,
            "resolved_injuries": inactive_count,
            "unmatched": len(unmatched_injuries),
            "unmatched_list": unmatched_injuries
        }
        
    except FileNotFoundError as e:
        print(f"Error: Could not find rosters.json file at {ROSTERS_FILE} - {e}")
        return None
    except Exception as e:
        print(f"Error updating rosters: {e}")
        return None

def main():
    """Main function to scrape injuries and update rosters."""
    print("Starting enhanced MLB injury tracking...")
    
    try:
        # Ensure directories exist
        ensure_directories_exist()
        
        # Scrape injury data
        print("1. Scraping injury data from ESPN...")
        injury_data = scrape_injuries()
        
        if not injury_data:
            print("No injury data found. Exiting.")
            return
        
        # Save injury data to the injuries directory
        injury_filename = os.path.join(INJURIES_DIR, f"mlb_injuries_{datetime.now().strftime('%Y-%m-%d')}.json")
        with open(injury_filename, 'w', encoding='utf-8') as f:
            json.dump(injury_data, f, indent=4, ensure_ascii=False)
        print(f"Injury data saved to {injury_filename} ({len(injury_data)} entries)")
        
        # Update rosters with enhanced tracking
        print("\n2. Updating rosters with enhanced injury tracking...")
        result = update_rosters_with_injuries(injury_data)
        
        if result:
            print(f"\n✅ Enhanced injury tracking completed!")
            print(f"📊 {result['new_injuries']} new injuries, {result['updated_injuries']} updated, {result['resolved_injuries']} resolved")
        else:
            print("❌ Failed to update rosters")
            
    except Exception as e:
        print(f"❌ Error in main process: {e}")

if __name__ == "__main__":
    main()