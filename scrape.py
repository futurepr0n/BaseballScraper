import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import random
import time
from urllib.parse import urlparse
import os
import glob  # Added for finding files matching pattern

# --- (Keep TEAM_ABBREVIATIONS dictionary and get_team_abbr function) ---
TEAM_ABBREVIATIONS = {
    "Arizona Diamondbacks": "ARI", "D-backs": "ARI", "Diamondbacks": "ARI",
    "Atlanta Braves": "ATL", "Braves": "ATL",
    "Baltimore Orioles": "BAL", "Orioles": "BAL",
    "Boston Red Sox": "BOS", "Red Sox": "BOS",
    "Chicago Cubs": "CHC", "Cubs": "CHC",
    "Chicago White Sox": "CHW", "White Sox": "CHW",
    "Cincinnati Reds": "CIN", "Reds": "CIN",
    "Cleveland Guardians": "CLE", "Guardians": "CLE",
    "Colorado Rockies": "COL", "Rockies": "COL",
    "Detroit Tigers": "DET", "Tigers": "DET",
    "Houston Astros": "HOU", "Astros": "HOU",
    "Kansas City Royals": "KC", "Royals": "KC",
    "Los Angeles Angels": "LAA", "Angels": "LAA",
    "Los Angeles Dodgers": "LAD", "Dodgers": "LAD",
    "Miami Marlins": "MIA", "Marlins": "MIA",
    "Milwaukee Brewers": "MIL", "Brewers": "MIL",
    "Minnesota Twins": "MIN", "Twins": "MIN",
    "New York Mets": "NYM", "Mets": "NYM",
    "New York Yankees": "NYY", "Yankees": "NYY",
    "Oakland Athletics": "OAK", "Athletics": "OAK", "A's": "OAK",
    "Philadelphia Phillies": "PHI", "Phillies": "PHI",
    "Pittsburgh Pirates": "PIT", "Pirates": "PIT",
    "San Diego Padres": "SD", "Padres": "SD",
    "San Francisco Giants": "SF", "Giants": "SF",
    "Seattle Mariners": "SEA", "Mariners": "SEA",
    "St. Louis Cardinals": "STL", "Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Rays": "TB",
    "Texas Rangers": "TEX", "Rangers": "TEX",
    "Toronto Blue Jays": "TOR", "Blue Jays": "TOR",
    "Washington Nationals": "WSH", "Nationals": "WSH",
}

def get_team_abbr(full_name):
    cleaned_name = re.sub(r'\s+(Hitting|Pitching|Batting)$', '', full_name, flags=re.I).strip()
    abbr = TEAM_ABBREVIATIONS.get(cleaned_name)
    if abbr: return abbr
    nickname = cleaned_name.split()[-1]
    abbr = TEAM_ABBREVIATIONS.get(nickname)
    if abbr: return abbr
    for name, abbr_val in TEAM_ABBREVIATIONS.items():
        if cleaned_name in name or name in cleaned_name:
             if len(cleaned_name) > 2 and (cleaned_name in name.split() or cleaned_name == name.split()[-1]):
                return abbr_val
    print(f"Warning: Abbreviation not found for team name: '{full_name}' (cleaned: '{cleaned_name}')")
    return cleaned_name[:3].upper()

# --- (Other functions remain the same) ---
def get_page_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def extract_boxscore_data(html_content, url):
    if not html_content:
        return None # Return None for data

    soup = BeautifulSoup(html_content, 'html.parser')
    # --- Date extraction removed ---

    all_teams_data = {} # Nested structure: {team_abbr: {'hitting': df, 'pitching': df}}

    # Find all Team Title divs
    team_title_divs = soup.find_all('div', class_='TeamTitle', attrs={'data-testid': 'teamTitle'})

    if not team_title_divs:
        print(f"Error: Could not find any 'div.TeamTitle' elements on {url}. Cannot extract H/P data.")
        return None

    print(f"Debug: Found {len(team_title_divs)} TeamTitle divs. Processing...")

    for title_div in team_title_divs:
        # 1. Extract Team Name and Determine Data Type (Hitting/Pitching)
        team_name_tag = title_div.find('div', class_='TeamTitle__Name')
        if not team_name_tag:
            print(f"Warning: Found TeamTitle div but no TeamTitle__Name inside. Skipping section. URL: {url}")
            continue
        team_name_full = team_name_tag.get_text(strip=True)
        team_abbr = get_team_abbr(team_name_full)

        data_type = 'unknown'
        if 'Hitting' in team_name_full or 'Batting' in team_name_full: data_type = 'hitting'
        elif 'Pitching' in team_name_full: data_type = 'pitching'
        else:
            print(f"Warning: Could not determine data type (hitting/pitching) from title: '{team_name_full}'. Skipping section.")
            continue
        print(f"Debug: Processing team: {team_name_full} ({team_abbr}), type: {data_type}")

        # 2. Find ResponsiveTable div
        responsive_table_div = title_div.find_next_sibling('div', class_='ResponsiveTable')
        if not responsive_table_div:
            print(f"Warning: Could not find 'div.ResponsiveTable' immediately after TeamTitle for {team_name_full}. Skipping. URL: {url}")
            continue

        # 3. Find the TWO tables
        player_name_table = responsive_table_div.find('table', class_='Table--fixed-left')
        stats_scroller_div = responsive_table_div.find('div', class_='Table__Scroller')
        stats_table = stats_scroller_div.find('table') if stats_scroller_div else None
        if not player_name_table or not stats_table:
            print(f"Warning: Could not find both player name table and stats table for {team_name_full}. Skipping. URL: {url}")
            continue

        # 4. Extract Stat Headers
        stat_headers = []
        stats_head = stats_table.find('thead')
        if stats_head:
            header_tags = stats_head.find_all('th')
            stat_headers = [th.get_text(strip=True).lower().replace('.', '').replace('-', '_') for th in header_tags]
        if not stat_headers:
             print(f"Warning: Could not extract stat headers for {team_name_full} ({data_type}). Skipping. URL: {url}")
             continue
        # Use generic player column name temporarily
        all_headers = ['player_temp'] + stat_headers
        print(f"Debug: Headers for {data_type}: {all_headers}")

        # 5. Extract Player Names and Stats using data-idx
        player_names_map = {}
        player_stats_map = {}
        name_body = player_name_table.find('tbody')
        if name_body:
            name_rows = name_body.find_all('tr', attrs={'data-idx': True})
            for row in name_rows:
                idx = row['data-idx']
                name_cell = row.find('td')
                if name_cell:
                    name_link = name_cell.find('a', class_='Boxscore__Athlete_Name')
                    player_name = name_link.get_text(strip=True) if name_link else name_cell.get_text(strip=True)
                    player_name = re.sub(r'^[a-z]-', '', player_name).strip()
                    player_name = re.sub(r'\s*\([^)]+\)$', '', player_name).strip() # Pitching notes
                    if player_name and player_name.lower() != 'team':
                        player_names_map[idx] = player_name
        stats_body = stats_table.find('tbody')
        if stats_body:
             stats_rows = stats_body.find_all('tr', attrs={'data-idx': True})
             for row in stats_rows:
                 idx = row['data-idx']
                 stat_cells = row.find_all('td')
                 stats_list = [cell.get_text(strip=True) for cell in stat_cells]
                 if len(stats_list) == len(stat_headers):
                    player_stats_map[idx] = stats_list

        # 6. Combine into final list of dictionaries
        combined_player_data = []
        processed_indices = set(player_names_map.keys()) & set(player_stats_map.keys())
        sorted_indices = sorted(list(processed_indices), key=int)
        print(f"Debug: Combining data for {len(sorted_indices)} players for {team_abbr} {data_type}.")
        for idx in sorted_indices:
            player_data = {}
            player_name = player_names_map[idx]
            player_name = re.sub(r'\s+[A-Z1-3]{1,3}$', '', player_name).strip() # Hitting positions
            player_data[all_headers[0]] = player_name
            stats = player_stats_map[idx]
            for i, header in enumerate(stat_headers): player_data[header] = stats[i]
            valid = False
            if data_type == 'hitting' and 'ab' in player_data: valid = True
            if data_type == 'pitching' and 'ip' in player_data: valid = True
            if valid: combined_player_data.append(player_data)

        # 7. Create DataFrame and store
        if combined_player_data:
            df = pd.DataFrame(combined_player_data)
            df = df.rename(columns={all_headers[0]: 'player'}) # Rename first col to 'player'
            if team_abbr not in all_teams_data: all_teams_data[team_abbr] = {}
            all_teams_data[team_abbr][data_type] = df
            print(f"Successfully processed and stored {data_type} data for {team_abbr}.")
        else:
            print(f"Warning: No combined player data could be generated for {team_name_full} ({data_type}).")

    # Final check
    processed_teams = len(all_teams_data)
    expected_teams = len(set(get_team_abbr(t.find('div', class_='TeamTitle__Name').get_text(strip=True)) for t in team_title_divs if t.find('div', class_='TeamTitle__Name')))
    if processed_teams < expected_teams:
        print(f"Warning: Found {expected_teams} unique teams in titles but only successfully processed data for {processed_teams} teams.")

    return all_teams_data # Only return the data dictionary

def save_data_to_csv(all_teams_data, date_identifier): # Now expects date string from filename
    if not all_teams_data:
        print(f"No data extracted to save for date: {date_identifier}.")
        return
    if not date_identifier: # Should not happen with new logic, but safety check
         date_identifier = "unknown_date"
         print("Warning: Using 'unknown_date' as filename identifier.")

    hitting_headers = ['player', 'ab', 'r', 'h', 'rbi', 'hr', 'bb', 'k', 'avg', 'obp', 'slg']
    pitching_headers = ['player', 'ip', 'h', 'r', 'er', 'bb', 'k', 'hr', 'pc_st', 'era']

    for team_abbr, data_dict in all_teams_data.items():
        for data_type, df in data_dict.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                if data_type == 'hitting': desired_headers = hitting_headers
                elif data_type == 'pitching': desired_headers = pitching_headers
                else:
                    print(f"Warning: Unknown data type '{data_type}' for team {team_abbr}. Skipping save.")
                    continue

                df.columns = df.columns.str.lower()
                output_columns = [h for h in desired_headers if h in df.columns]

                if not output_columns or 'player' not in output_columns:
                     print(f"Warning: Essential columns missing for {team_abbr} {data_type}. Available: {list(df.columns)}. Skipping save.")
                     continue

                df_output = df[output_columns]
                # Construct filename using the passed date_identifier
                filename = f"{team_abbr.lower()}_{data_type}_{date_identifier}.csv"
                try:
                    df_output.to_csv(filename, index=False, encoding='utf-8')
                    print(f"Successfully saved data to {filename}")
                except Exception as e:
                    print(f"Error saving {filename}: {e}")
            else:
                print(f"No valid DataFrame found or empty for {team_abbr} {data_type}.")


def read_urls_from_file(filepath):
    urls = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                url = line.strip()
                if url and url.startswith('http'):
                    urls.append(url)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    return urls

def extract_game_id_from_url(url):
    try:
        match = re.search(r'/gameId/(\d+)', url)
        if match: return match.group(1)
        else:
            path_parts = urlparse(url).path.split('/')
            if 'gameId' in path_parts:
                game_id_index = path_parts.index('gameId')
                if game_id_index + 1 < len(path_parts): return path_parts[game_id_index + 1]
    except Exception as e: print(f"Error parsing gameId from URL {url}: {e}")
    return None


# --- REVISED: Main execution block ---
if __name__ == "__main__":
    # Find all files matching the month_day_year.txt pattern
    date_files = glob.glob("*_*_*.txt")
    valid_files = []
    
    # Validate files follow expected naming convention
    for file in date_files:
        base_name = os.path.basename(file)
        date_identifier, extension = os.path.splitext(base_name)
        
        # Simple validation that it looks like month_day_year format
        if re.match(r'^[a-z]+_\d+_\d+$', date_identifier, re.IGNORECASE):
            valid_files.append(file)
        else:
            print(f"Skipping file '{file}' as it doesn't match expected naming format month_day_year.txt")
    
    if not valid_files:
        print("No valid date files found. Please ensure files are named like 'month_day_year.txt'")
        exit()
    
    print(f"Found {len(valid_files)} date files to process: {', '.join(valid_files)}")
    
    # Process each valid file
    for url_file in valid_files:
        base_name = os.path.basename(url_file)
        date_identifier, extension = os.path.splitext(base_name)
        
        print(f"\n=== Processing file: {url_file} with date identifier: {date_identifier} ===\n")
        
        # Read URLs from this file
        urls_to_process = read_urls_from_file(url_file)
        
        if not urls_to_process:
            print(f"No valid URLs found in {url_file}. Skipping.")
            continue
        
        print(f"Found {len(urls_to_process)} URLs to process from {url_file}.")
        for i, game_url in enumerate(urls_to_process):
            print(f"\n--- Processing URL {i+1}/{len(urls_to_process)}: {game_url} ---")
            
            # Fetch content
            html = get_page_content(game_url)
            
            if html:
                # Extract data
                extracted_data = extract_boxscore_data(html, game_url)
                
                # Save data using the date identifier from this filename
                save_data_to_csv(extracted_data, date_identifier)
            else:
                print(f"Skipping data extraction and saving due to fetch error for {game_url}")
            
            sleep_time = random.uniform(10, 35)
            print(f"Waiting for {sleep_time:.2f} seconds before next request...")
            time.sleep(sleep_time)
        
        print(f"\n--- Finished processing all URLs from {url_file}. ---")
    
    print("\n=== Completed processing all input files. ===")