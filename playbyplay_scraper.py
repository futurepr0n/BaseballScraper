#!/usr/bin/env python3
"""
MLB Play-by-Play Scraper
Extends existing scraper functionality to collect comprehensive play-by-play data
Uses same approach as enhanced_scrape.py - transforms boxscore URLs to playbyplay URLs

Usage:
  python playbyplay_scraper.py                    # Process yesterday's games (automatic)
  python playbyplay_scraper.py july_12_2025.txt  # Process specific file
  python playbyplay_scraper.py --days-ago 8      # Process games from 8 days ago
"""

import json
import os
import glob
import argparse
import sys
import random
import time
import re
from typing import List, Dict
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Import centralized configuration
from config import DATA_PATH

# Import helper functions from existing scraper
from enhanced_scrape import (
    get_team_abbr, 
    get_date_filename, 
    get_yesterday_filename,
    extract_game_id_from_url,
    read_urls_from_file,
    get_page_content,
    move_file_to_scanned
)

# Import player name enhancement (optional)
try:
    from enhance_player_names import enhance_play_data_with_rosters
    ENHANCE_PLAYER_NAMES_AVAILABLE = True
except ImportError:
    print("⚠️ enhance_player_names module not available - using basic player name handling")
    ENHANCE_PLAYER_NAMES_AVAILABLE = False

try:
    from boxscore_name_matcher import enhance_play_data_with_boxscore_names
    BOXSCORE_NAME_MATCHER_AVAILABLE = True
except ImportError:
    print("⚠️ boxscore_name_matcher module not available - using basic player name handling")
    BOXSCORE_NAME_MATCHER_AVAILABLE = False

def transform_url_to_playbyplay(boxscore_url: str) -> str:
    """Transform boxscore URL to play-by-play URL"""
    return boxscore_url.replace('/boxscore/', '/playbyplay/')

def extract_playbyplay_data_from_api(game_id: str) -> tuple:
    """Extract comprehensive play-by-play data from ESPN API"""
    api_url = f'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?event={game_id}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"📡 Fetching comprehensive data from ESPN API...")
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        api_data = response.json()
        
        if 'plays' not in api_data:
            print(f"❌ No plays data found in API response")
            return None, game_id, None, None
        
        plays = api_data['plays']
        print(f"✅ Found {len(plays)} total plays in API data")
        
        # Build player ID to name mapping from boxscore players data
        player_id_to_name = {}
        if 'boxscore' in api_data and 'players' in api_data['boxscore']:
            print(f"📋 Building player name mapping from boxscore players...")
            teams = api_data['boxscore']['players']
            
            for team in teams:
                team_abbr = team.get('team', {}).get('abbreviation', 'Unknown')
                statistics = team.get('statistics', [])
                
                for stat_group in statistics:
                    if 'athletes' in stat_group:
                        athletes = stat_group['athletes']
                        for athlete_data in athletes:
                            athlete = athlete_data.get('athlete', {})
                            player_id = athlete.get('id')
                            player_name = (athlete.get('displayName') or 
                                         athlete.get('fullName') or 
                                         athlete.get('shortName'))
                            if player_id and player_name:
                                player_id_to_name[str(player_id)] = player_name
            
            print(f"✅ Mapped {len(player_id_to_name)} player IDs to names")
        else:
            print(f"⚠️ No boxscore data available for player name mapping")
        
        # Initialize game data structure
        game_data = {
            'metadata': {
                'game_id': game_id,
                'api_url': api_url,
                'scraped_at': datetime.now().isoformat()
            },
            'plays': []
        }
        
        # Extract team information from plays
        away_team_abbr = None
        home_team_abbr = None
        
        # Try to get team info from header if available
        if 'header' in api_data and 'competitions' in api_data['header']:
            competitions = api_data['header']['competitions']
            if competitions and 'competitors' in competitions[0]:
                competitors = competitions[0]['competitors']
                for competitor in competitors:
                    if competitor.get('homeAway') == 'away':
                        away_team_abbr = competitor.get('team', {}).get('abbreviation', 'AWAY')
                    elif competitor.get('homeAway') == 'home':
                        home_team_abbr = competitor.get('team', {}).get('abbreviation', 'HOME')
        
        if not away_team_abbr or not home_team_abbr:
            away_team_abbr = "AWAY"
            home_team_abbr = "HOME"
        
        game_data['metadata']['away_team'] = away_team_abbr
        game_data['metadata']['home_team'] = home_team_abbr
        print(f"🏟️ Teams from API: {away_team_abbr} @ {home_team_abbr}")
        
        # Group plays by at-bat
        at_bats = {}
        current_at_bat = None
        
        for play in plays:
            at_bat_id = play.get('atBatId')
            if not at_bat_id:
                continue
            
            # Initialize new at-bat if needed
            if at_bat_id not in at_bats:
                at_bats[at_bat_id] = {
                    'at_bat_id': at_bat_id,
                    'batter': None,
                    'pitcher': None,
                    'inning': None,
                    'inning_half': None,
                    'play_description': None,
                    'play_result': None,
                    'pitches': [],
                    'final_play': None,
                    'play_texts': [],  # Store all play descriptions
                    'result_description': None  # Best description for this at-bat
                }
            
            current_ab = at_bats[at_bat_id]
            
            # Extract inning information
            if 'period' in play:
                current_ab['inning'] = play['period'].get('number')
                current_ab['inning_half'] = play['period'].get('type')
            
            # Extract participant information (batter and pitcher)
            participants = play.get('participants', [])
            for participant in participants:
                athlete_id = participant.get('athlete', {}).get('id')
                if participant.get('type') == 'batter' and athlete_id:
                    # Resolve batter name from our mapping
                    batter_name = player_id_to_name.get(str(athlete_id))
                    if batter_name:
                        current_ab['batter'] = batter_name
                elif participant.get('type') == 'pitcher' and athlete_id:
                    # Resolve pitcher name from our mapping
                    pitcher_name = player_id_to_name.get(str(athlete_id))
                    if pitcher_name:
                        current_ab['pitcher'] = pitcher_name
            
            # Collect play descriptions - ESPN provides rich text descriptions
            play_text = play.get('text', '').strip()
            if play_text and play_text not in current_ab['play_texts']:
                current_ab['play_texts'].append(play_text)
                
                # Identify result descriptions (non-pitch descriptions)
                if not play_text.startswith('Pitch ') and not play_text.startswith('Top of') and not play_text.startswith('Bottom of'):
                    # This looks like a meaningful play description, not just pitch tracking
                    if (any(word in play_text.lower() for word in [
                        'singles', 'doubles', 'triples', 'homers', 'strikes out', 'walks', 'flies out',
                        'grounds out', 'lines out', 'pops out', 'reaches', 'safe', 'error', 'fielder',
                        'pitches to', 'batting', 'intentional walk'
                    ]) or 'out' in play_text.lower()):
                        current_ab['result_description'] = play_text
            
            # Process pitch data
            play_type = play.get('type', {}).get('type', '')
            if 'pitchType' in play and 'pitchVelocity' in play:
                # This is a pitch
                pitch_data = {
                    'pitch_number': play.get('atBatPitchNumber', 0),
                    'result': play.get('type', {}).get('text', 'Unknown'),
                    'pitch_type': play.get('pitchType', {}).get('text', 'Unknown'),
                    'velocity': play.get('pitchVelocity', None),
                    'balls': play.get('resultCount', {}).get('balls', 0),
                    'strikes': play.get('resultCount', {}).get('strikes', 0)
                }
                current_ab['pitches'].append(pitch_data)
            
            # Check for final at-bat result
            if play_type in ['single', 'double', 'triple', 'home-run', 'strikeout', 'walk', 'fly-out', 'ground-out', 'line-out', 'pop-out']:
                current_ab['play_description'] = play.get('text', '')
                current_ab['play_result'] = play.get('type', {}).get('text', 'Other')
                current_ab['final_play'] = play
        
        print(f"🎯 Processed {len(at_bats)} at-bats from API data")
        
        # Convert at-bats to play format
        play_sequence = 0
        for at_bat_id, at_bat in at_bats.items():
            if not at_bat['pitches'] and not at_bat['play_description']:
                continue  # Skip empty at-bats
            
            play_sequence += 1
            
            # Determine play result category
            play_result = "Other"
            description = at_bat['play_description'] or ''
            lower_desc = description.lower()
            
            if at_bat['play_result']:
                result_text = at_bat['play_result'].lower()
                if 'home run' in result_text or 'home-run' in result_text:
                    play_result = "Home Run"
                elif 'triple' in result_text:
                    play_result = "Triple"
                elif 'double' in result_text:
                    play_result = "Double"
                elif 'single' in result_text:
                    play_result = "Single"
                elif 'walk' in result_text:
                    play_result = "Walk"
                elif 'strikeout' in result_text or 'struck out' in lower_desc:
                    play_result = "Strikeout"
                elif 'ground' in result_text and 'out' in result_text:
                    play_result = "Groundout"
                elif 'fly' in result_text and 'out' in result_text:
                    play_result = "Flyout"
                elif 'line' in result_text and 'out' in result_text:
                    play_result = "Lineout"
                elif 'pop' in result_text and 'out' in result_text:
                    play_result = "Popout"
            
            # Choose the best description to use
            enhanced_description = (
                at_bat['result_description'] or  # Rich ESPN description (preferred)
                description or                    # Fallback to basic description
                f"At-bat {at_bat_id}: {play_result}"  # Last resort
            )
            
            play_data = {
                'play_sequence': play_sequence,
                'game_id': game_id,
                'inning': at_bat['inning'] or 1,
                'inning_half': at_bat['inning_half'] or 'Unknown',
                'batter': at_bat['batter'] or "Unknown",  # Now contains actual names
                'pitcher': at_bat['pitcher'] or "Unknown",
                'play_description': description,
                'play_result': play_result,
                'pitch_sequence': at_bat['pitches'],
                'raw_text': enhanced_description,  # Enhanced ESPN descriptions!
                'all_play_texts': at_bat['play_texts']  # For debugging/analysis
            }
            
            game_data['plays'].append(play_data)
        
        print(f"✅ Extracted {len(game_data['plays'])} plays with comprehensive pitch data")
        total_pitches = sum(len(play.get('pitch_sequence', [])) for play in game_data['plays'])
        print(f"⚾ Total individual pitches: {total_pitches}")
        
        return game_data, game_id, away_team_abbr, home_team_abbr
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return None, game_id, None, None
    except Exception as e:
        print(f"❌ Error processing API data: {e}")
        return None, game_id, None, None


def extract_playbyplay_data(html_content: str, url: str) -> tuple:
    """Extract detailed play-by-play data from ESPN pages with real player names"""
    if not html_content:
        return None, None, None, None
    
    # Extract game ID but use HTML parsing since API doesn't have player names
    game_id = extract_game_id_from_url(url)
    print(f"⚾ Using HTML parsing to extract real player names...")
    
    # Fallback to HTML parsing if game ID extraction fails
    soup = BeautifulSoup(html_content, 'html.parser')
    game_id = extract_game_id_from_url(url)
    
    # Initialize game data structure
    game_data = {
        'metadata': {
            'game_id': game_id,
            'url': url,
            'scraped_at': datetime.now().isoformat()
        },
        'plays': []
    }
    
    # Extract team information for filename
    away_team_abbr = None
    home_team_abbr = None
    
    try:
        # First, try to find team abbreviations in Table__TD elements (most reliable)
        table_cells = soup.select('td.Table__TD')
        team_abbrs = []
        for cell in table_cells:
            text = cell.get_text(strip=True)
            # Team abbreviations are typically 2-3 uppercase letters
            if text and len(text) <= 3 and text.isupper() and text.isalpha():
                if text not in team_abbrs:
                    team_abbrs.append(text)
                    if len(team_abbrs) >= 2:
                        break
        
        if len(team_abbrs) >= 2:
            away_team_abbr = team_abbrs[0]
            home_team_abbr = team_abbrs[1]
            game_data['metadata']['away_team'] = away_team_abbr
            game_data['metadata']['home_team'] = home_team_abbr
            print(f"🏟️ Teams from Table__TD: {away_team_abbr} @ {home_team_abbr}")
        else:
            # Fallback to header selectors
            header_selectors = [
                '.ScoreCell__TeamName',  # Main team name selector
                '.Gamestrip__Team__Name',  # Alternative team name
                'h2.ScoreCell__TeamName',  # Header team names
                '.team-name',  # Generic team name
                '.competitor-name'  # Competitor name
            ]
            
            team_names = []
            for selector in header_selectors:
                elements = soup.select(selector)
                if elements:
                    team_names = [elem.get_text(strip=True) for elem in elements[:2]]
                    if len(team_names) >= 2:
                        print(f"✅ Found team names using selector: {selector}")
                        break
            
            # Convert team names to abbreviations if we found any
            if len(team_names) >= 2:
                away_team_abbr = get_team_abbr(team_names[0])
                home_team_abbr = get_team_abbr(team_names[1])
                game_data['metadata']['away_team'] = away_team_abbr
                game_data['metadata']['home_team'] = home_team_abbr
                print(f"🏟️ Teams from headers: {away_team_abbr} @ {home_team_abbr}")
            else:
                print(f"⚠️ Could not extract team names from {url}, using generic naming")
                away_team_abbr = "AWAY"
                home_team_abbr = "HOME"
        
        # Extract play-by-play data from AtBatAccordion elements
        at_bat_elements = soup.select('div.AtBatAccordion')
        if not at_bat_elements:
            # Try alternative selectors
            at_bat_elements = soup.select('div[class*="AtBat"]')
        
        if not at_bat_elements:
            print(f"⚠️ Could not find AtBat elements in {url}")
            return game_data, game_id, away_team_abbr, home_team_abbr
        
        print(f"✅ Found {len(at_bat_elements)} at-bat elements")
        
        # Also look for half-inning sections to get inning context
        half_inning_sections = soup.select('div[class*="HalfInning"]')
        print(f"✅ Found {len(half_inning_sections)} half-inning sections")
        
        # Build inning context map by analyzing the DOM structure
        inning_context_map = {}
        
        # Find all inning headers and map them to positions
        inning_headers = soup.select('h3, .inning-header, [class*="Inning"], [class*="inning"]')
        for header in inning_headers:
            header_text = header.get_text(strip=True)
            inning_match = re.search(r'(Top|Bottom)\s+(\d+)(?:st|nd|rd|th)?', header_text, re.IGNORECASE)
            if inning_match:
                half = inning_match.group(1).title()
                inning_num = int(inning_match.group(2))
                print(f"🔍 Found inning context: {half} {inning_num}")
                
                # Find subsequent AtBat elements until next inning header
                next_elements = []
                current_element = header.next_sibling
                while current_element:
                    if hasattr(current_element, 'name') and current_element.name:
                        if 'AtBatAccordion' in str(current_element.get('class', [])):
                            next_elements.append(current_element)
                        elif current_element.name in ['h3'] or 'Inning' in str(current_element.get('class', [])):
                            break
                    current_element = current_element.next_sibling
                
                # Map these AtBat elements to this inning
                for elem in next_elements:
                    inning_context_map[elem] = {'inning': inning_num, 'half': half}
        
        play_sequence = 0
        current_inning = 1
        current_half = 'Top'
        current_pitcher = None
        
        # First pass: Extract pitcher information from PlayHeader elements
        play_headers = soup.select('div.PlayHeader')
        pitcher_info = {}
        
        print(f"✅ Found {len(play_headers)} PlayHeader elements for pitcher extraction")
        
        for header in play_headers:
            header_text = header.get_text(' ', strip=True)
            # Look for pitcher information patterns like "S. Schwellenbach pitching for ATL"
            pitcher_match = re.search(r'([A-Z][a-z]*\.?\s+[A-Z][a-z]+)\s+pitching\s+for\s+([A-Z]{2,3})', header_text, re.IGNORECASE)
            if pitcher_match:
                pitcher_name = pitcher_match.group(1).strip()
                team_abbr = pitcher_match.group(2).strip()
                pitcher_info[team_abbr] = pitcher_name
                print(f"⚾ Found pitcher: {pitcher_name} for {team_abbr}")
        
        # Determine which team is pitching based on inning half
        def get_current_pitcher(inning_half, away_team, home_team):
            if inning_half == 'Top':
                # Top of inning: away team batting, home team pitching
                return pitcher_info.get(home_team, None)
            else:
                # Bottom of inning: home team batting, away team pitching
                return pitcher_info.get(away_team, None)
        
        # Process each at-bat element
        for at_bat_idx, at_bat in enumerate(at_bat_elements):
            play_sequence += 1
            at_bat_text = at_bat.get_text(' ', strip=True)
            
            # Use inning context map if available, otherwise try to determine from DOM
            if at_bat in inning_context_map:
                current_inning = inning_context_map[at_bat]['inning']
                current_half = inning_context_map[at_bat]['half']
            else:
                # Fallback: try to determine inning from position and patterns
                # Look for preceding inning headers
                preceding_element = at_bat.find_previous(['h3', 'div', 'header'])
                inning_found = False
                
                while preceding_element and not inning_found:
                    element_text = preceding_element.get_text(strip=True)
                    inning_match = re.search(r'(Top|Bottom)\s+(\d+)(?:st|nd|rd|th)?', element_text, re.IGNORECASE)
                    if inning_match:
                        current_half = inning_match.group(1).title()
                        current_inning = int(inning_match.group(2))
                        inning_found = True
                        break
                    preceding_element = preceding_element.find_previous(['h3', 'div', 'header'])
                
                # Alternative: estimate based on play position (rough fallback)
                if not inning_found and play_sequence > 6:
                    # Rough estimate: assume ~6-8 plays per half inning on average
                    estimated_half_innings = (play_sequence - 1) // 7
                    if estimated_half_innings > 0:
                        if estimated_half_innings % 2 == 1:
                            current_half = 'Bottom'
                            current_inning = (estimated_half_innings // 2) + 1
                        else:
                            current_half = 'Top'  
                            current_inning = (estimated_half_innings // 2) + 1
            
            # Extract the play description (usually the first sentence)
            play_desc_match = re.match(r'^([^.]+\.)', at_bat_text)
            if play_desc_match:
                play_description = play_desc_match.group(1)
            else:
                # Handle cases where there's no period or description is incomplete
                parts = at_bat_text.split(' ')
                if len(parts) >= 2:
                    # Take first meaningful chunk (typically player name + action)
                    first_chunk = ' '.join(parts[:10])  # Reasonable limit
                    play_description = first_chunk + '.' if not first_chunk.endswith('.') else first_chunk
                else:
                    # Very short text, use as-is
                    play_description = at_bat_text.strip()
                    if not play_description.endswith('.'):
                        play_description += '.'
            
            # Extract batter name from play description with enhanced patterns
            batter_name = "Unknown"
            
            # Enhanced patterns to handle complex names, accented characters, and suffixes
            batter_patterns = [
                # Pattern 1: Full names with suffixes (Jr., Sr., etc.) and action verbs
                r'^([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]*)*(?:\s+(?:Jr\.?|Sr\.?|III?|IV))?)\s+(?:flied?|flew|struck|singled|doubled|tripled|walked|grounded|lined|popped|homered|reached|sacrificed|bunted)',
                
                # Pattern 2: Names with "intentionally" (e.g., "Harper intentionally walked")  
                r'^([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]*)*(?:\s+(?:Jr\.?|Sr\.?|III?|IV))?)\s+intentionally',
                
                # Pattern 3: Just the name at the start, more permissive
                r'^([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]*)*(?:\s+(?:Jr\.?|Sr\.?|III?|IV))?)\s+',
                
                # Pattern 4: Handle cases where the full description is just a name
                r'^([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]*)*(?:\s+(?:Jr\.?|Sr\.?|III?|IV))?)\.$',
            ]
            
            for pattern in batter_patterns:
                batter_match = re.match(pattern, play_description, re.IGNORECASE | re.UNICODE)
                if batter_match:
                    batter_name = batter_match.group(1).strip()
                    # Clean up the name (remove trailing periods, normalize spaces)
                    batter_name = re.sub(r'\.$', '', batter_name)
                    batter_name = re.sub(r'\s+', ' ', batter_name)
                    break
            
            # Fallback: try to extract from raw_text if play_description failed
            if batter_name == "Unknown" and at_bat_text:
                # Look for player names at the start of the raw text
                fallback_match = re.match(r'^([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]*)*(?:\s+(?:Jr\.?|Sr\.?|III?|IV))?)', at_bat_text, re.IGNORECASE | re.UNICODE)
                if fallback_match:
                    potential_name = fallback_match.group(1).strip()
                    # Validate it's likely a player name (not a common word)
                    if len(potential_name.split()) <= 3 and not potential_name.lower() in ['pitch', 'type', 'mph', 'ball', 'strike', 'foul', 'out']:
                        batter_name = potential_name
            
            # Determine play result
            play_result = "Other"
            lower_desc = play_description.lower()
            if 'home run' in lower_desc or 'homered' in lower_desc:
                play_result = "Home Run"
            elif 'triple' in lower_desc:
                play_result = "Triple"
            elif 'double' in lower_desc:
                play_result = "Double"
            elif 'single' in lower_desc:
                play_result = "Single"
            elif 'walk' in lower_desc:
                play_result = "Walk"
            elif 'struck out' in lower_desc or 'strikeout' in lower_desc:
                play_result = "Strikeout"
            elif 'ground' in lower_desc and 'out' in lower_desc:
                play_result = "Groundout"
            elif ('fly' in lower_desc or 'flew' in lower_desc or 'flied' in lower_desc) and 'out' in lower_desc:
                play_result = "Flyout"
            elif 'lined out' in lower_desc:
                play_result = "Lineout"
            elif 'popped' in lower_desc:
                play_result = "Popout"
            
            # Extract pitch sequence - SIMPLIFIED TABLE-BASED APPROACH
            pitch_sequence = []
            
            # Debug: Print raw text for troubleshooting (reduced to minimize output)
            debug_this_play = play_sequence <= 2  # Only debug first 2 plays
            if debug_this_play:
                print(f"🔍 DEBUG - Play {play_sequence} analyzing AtBat structure...")
            
            # Method 1: Look for structured pitch data tables within the AtBatAccordion
            pitch_tables = at_bat.find_all('table', class_=lambda x: x and ('pitch' in x.lower() if x else False))
            if not pitch_tables:
                # Look for any tables within this at-bat
                pitch_tables = at_bat.find_all('table')
            
            if pitch_tables:
                if debug_this_play:
                    print(f"🎯 Found {len(pitch_tables)} tables in AtBat element")
                
                for table in pitch_tables:
                    rows = table.find_all('tr')
                    if rows and debug_this_play:
                        print(f"  Table has {len(rows)} rows")
                    
                    for i, row in enumerate(rows[1:], 1):  # Skip header row
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:  # Reduced requirement - sometimes only 2-3 cells
                            try:
                                # Clean cell text more thoroughly
                                cell_texts = []
                                for cell in cells:
                                    text = cell.get_text(strip=True)
                                    # Remove any hidden characters or extra whitespace
                                    text = ' '.join(text.split())
                                    cell_texts.append(text)
                                
                                if debug_this_play:
                                    print(f"    Row {i}: {cell_texts} (len: {len(cells)} cells)")
                                
                                # Skip empty rows
                                if not any(cell_texts):
                                    continue
                                
                                # Parse ESPN's actual format: "1Strike Looking", "Cutter", "84"
                                first_cell = cell_texts[0] if cell_texts else ''
                                
                                # Extract pitch number and result from first cell (e.g., "1Strike Looking")
                                pitch_match = re.match(r'(\d+)(.+)', first_cell)
                                if pitch_match:
                                    pitch_num = int(pitch_match.group(1))
                                    result = pitch_match.group(2).strip()
                                    
                                    # Get pitch type and velocity from subsequent cells
                                    pitch_type = 'Unknown'
                                    velocity = None
                                    
                                    for text in cell_texts[1:]:  # Skip first cell (already processed)
                                        if not text:  # Skip empty cells
                                            continue
                                        # Look for velocity (2-3 digits)
                                        if text.isdigit() and 70 <= int(text) <= 110:
                                            velocity = int(text)
                                        # Look for pitch types - comprehensive list of ESPN pitch type names
                                        elif any(ptype in text.lower() for ptype in [
                                            'fastball', 'cutter', 'slider', 'curve', 'change', 'sinker', 'splitter', 
                                            'four-seam', 'two-seam', 'knuckle', 'curveball', 'changeup', 'split-finger',
                                            'cut fastball', 'running fastball', 'rising fastball', 'sinking fastball',
                                            'screwball', 'knuckleball', 'eephus', 'slurve', 'sweeper', 'gyro slider'
                                        ]):
                                            pitch_type = text
                                        # Fallback: if text looks like a pitch type (not velocity, not empty, reasonable length)
                                        elif len(text) > 2 and not text.isdigit() and pitch_type == 'Unknown':
                                            # Common indicators that text is likely a pitch type
                                            if any(indicator in text.lower() for indicator in ['ball', 'fast', 'cut', 'slid', 'curv', 'chang', 'sink', 'split']):
                                                pitch_type = text
                                            # If all else fails and we have text that's not velocity, use it
                                            elif not any(char.isdigit() for char in text):
                                                pitch_type = text
                                    
                                    pitch_data = {
                                        'pitch_number': pitch_num,
                                        'result': result,
                                        'pitch_type': pitch_type,
                                        'velocity': velocity
                                    }
                                    pitch_sequence.append(pitch_data)
                                    
                                    if debug_this_play:
                                        print(f"      → Extracted: Pitch {pitch_num}, {result}, {pitch_type}, {velocity} mph")
                            
                            except Exception as e:
                                if debug_this_play:
                                    print(f"      ❌ Error parsing row: {e}")
                                continue
            
            # Method 2: If no tables found, look for structured div elements with pitch data
            if not pitch_sequence:
                # Look for divs containing pitch data patterns
                all_divs = at_bat.find_all('div')
                pitch_related_divs = []
                
                for div in all_divs:
                    div_text = div.get_text(strip=True)
                    # Look for ESPN's div format: "PitchTypeMPH1SingleFour-seam FB92"
                    if any(term in div_text.lower() for term in ['pitchtypemph', 'pitch', 'mph']) and any(char.isdigit() for char in div_text):
                        pitch_related_divs.append(div)
                
                if pitch_related_divs and debug_this_play:
                    print(f"🔄 No tables found, trying {len(pitch_related_divs)} pitch divs")
                
                # Try to extract pitch data from ESPN's condensed div format
                for div in pitch_related_divs:
                    div_text = div.get_text(strip=True)
                    if debug_this_play:
                        print(f"    Analyzing div: {div_text[:60]}...")
                    
                    # Pattern for ESPN's compressed format: "PitchTypeMPH1SingleFour-seam FB92"
                    # Extract: pitch number (1), result (Single), pitch type (Four-seam FB), velocity (92)
                    compressed_pattern = r'.*?(\d+)(Ball|Strike|Single|Double|Triple|Home Run|Foul|Out|Hit|Swinging|Looking)([A-Za-z\-\s]+?)(\d{2,3})'
                    match = re.search(compressed_pattern, div_text)
                    
                    if match:
                        pitch_num = int(match.group(1))
                        result = match.group(2)
                        pitch_type_raw = match.group(3).strip()
                        velocity = int(match.group(4))
                        
                        # Clean up pitch type (remove extra spaces, common words)
                        pitch_type = re.sub(r'\s+', ' ', pitch_type_raw).strip()
                        pitch_type = re.sub(r'^(FB|fastball)\s+', '', pitch_type, flags=re.IGNORECASE)
                        if not pitch_type or len(pitch_type) < 2:
                            pitch_type = 'Fastball'  # Default fallback
                        
                        pitch_data = {
                            'pitch_number': pitch_num,
                            'result': result,
                            'pitch_type': pitch_type,
                            'velocity': velocity
                        }
                        pitch_sequence.append(pitch_data)
                        
                        if debug_this_play:
                            print(f"      → Extracted from div: Pitch {pitch_num}, {result}, {pitch_type}, {velocity} mph")
            
            # Method 3: Simple regex fallback on raw text (only if no structured data found)
            if not pitch_sequence:
                # Use the working pattern from the successful example
                pitch_pattern = r'(\d+)\s+(Foul|Ball|Strike|In Play|Hit|Out|Looking|Swinging)(?:\s+(Ball|Strike|Looking|Swinging))?\s+([A-Za-z\-\s]+?)\s+(\d{2,3})'
                pitch_matches = re.findall(pitch_pattern, at_bat_text)
                
                if pitch_matches and debug_this_play:
                    print(f"🔄 Using regex fallback: found {len(pitch_matches)} pitches")
                
                for match in pitch_matches:
                    result = match[1]
                    if match[2]:  # Has modifier like "Swinging"
                        result = f"{result} {match[2]}"
                    
                    pitch_data = {
                        'pitch_number': int(match[0]),
                        'result': result.strip(),
                        'pitch_type': match[3].strip(),
                        'velocity': int(match[4]) if match[4] else None
                    }
                    pitch_sequence.append(pitch_data)
            
            if debug_this_play:  # Debug info for first few plays only
                print(f"🎯 Play {play_sequence} extracted {len(pitch_sequence)} pitches")
            
            # Look for pitcher info in nearby PlayHeader elements or at-bat text
            # ESPN often shows "X pitching for TEAM" in headers
            pitcher_match = re.search(r'([A-Z][a-z]*\.?\s+[A-Z][a-z]+)\s+pitching\s+for\s+([A-Z]+)', at_bat_text, re.IGNORECASE)
            if pitcher_match:
                current_pitcher = pitcher_match.group(1).strip()
            else:
                # Use the get_current_pitcher function to determine active pitcher
                current_pitcher = get_current_pitcher(current_half, away_team_abbr, home_team_abbr)
            
            # Create play data
            play_data = {
                'play_sequence': play_sequence,
                'game_id': game_id,
                'inning': current_inning,
                'inning_half': current_half,
                'batter': batter_name,
                'pitcher': current_pitcher,
                'play_description': play_description.strip(),
                'play_result': play_result,
                'pitch_sequence': pitch_sequence,
                'raw_text': at_bat_text
            }
            
            game_data['plays'].append(play_data)
        
        print(f"✅ Extracted {len(game_data['plays'])} plays from {url}")
        return game_data, game_id, away_team_abbr, home_team_abbr
    
    except Exception as e:
        print(f"❌ Error extracting play-by-play data from {url}: {e}")
        return game_data, game_id, away_team_abbr, home_team_abbr

def save_playbyplay_data(game_data: Dict, date_identifier: str, game_id: str, away_team: str, home_team: str, format_type: str = 'json'):
    """Save play-by-play data in JSON or CSV format using centralized paths with team names"""
    if not game_data or not game_data.get('plays'):
        print(f"No play-by-play data to save for gameId: {game_id}")
        return
    
    # Setup separate directories for CSV and JSON as requested
    csv_pbp_dir = DATA_PATH.parent / 'CSV_BACKUPS_PBP'
    json_pbp_dir = DATA_PATH / 'play-by-play'  # Corrected to match existing directory structure
    
    csv_pbp_dir.mkdir(parents=True, exist_ok=True)
    json_pbp_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename with team names: TEAM_vs_TEAM_playbyplay_month_day_year_gameId
    team_matchup = f"{away_team}_vs_{home_team}"
    
    if format_type.lower() == 'json':
        # Save JSON to BaseballData/data/play-by-play/
        filename = f"{team_matchup}_playbyplay_{date_identifier}_{game_id}.json"
        json_path = json_pbp_dir / filename
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved JSON play-by-play data: {json_path}")
        except Exception as e:
            print(f"❌ Error saving JSON data: {e}")
    
    elif format_type.lower() == 'csv':
        # Save CSV to BaseballData/CSV_BACKUPS_PBP/
        if game_data.get('plays'):
            plays_df = pd.DataFrame(game_data['plays'])
            
            # Add metadata columns to each play
            metadata = game_data.get('metadata', {})
            for key, value in metadata.items():
                plays_df[f'game_{key}'] = value
            
            filename = f"{team_matchup}_playbyplay_{date_identifier}_{game_id}.csv"
            csv_path = csv_pbp_dir / filename
            
            try:
                plays_df.to_csv(csv_path, index=False, encoding='utf-8')
                print(f"✅ Saved CSV play-by-play data: {csv_path}")
            except Exception as e:
                print(f"❌ Error saving CSV data: {e}")
    
    else:
        print(f"⚠️ Unknown format type: {format_type}. Use 'json' or 'csv'")

def create_summary_report(processed_games: List[Dict], date_identifier: str):
    """Create a summary report of scraped play-by-play data"""
    if not processed_games:
        return
    
    total_games = len(processed_games)
    successful_games = len([g for g in processed_games if g.get('success', False)])
    total_plays = sum(len(g.get('plays', [])) for g in processed_games)
    
    report = {
        'date': date_identifier,
        'scraped_at': datetime.now().isoformat(),
        'summary': {
            'total_games_attempted': total_games,
            'successful_extractions': successful_games,
            'failed_extractions': total_games - successful_games,
            'total_plays_extracted': total_plays
        },
        'games': processed_games
    }
    
    # Save summary report in JSON directory with other playbyplay data  
    json_pbp_dir = DATA_PATH / 'playbyplay'
    json_pbp_dir.mkdir(parents=True, exist_ok=True)
    
    summary_path = json_pbp_dir / f"summary_{date_identifier}.json"
    
    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📊 Summary report saved: {summary_path}")
    except Exception as e:
        print(f"❌ Error saving summary report: {e}")

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="MLB Play-by-Play Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Process yesterday's games (automatic)
  %(prog)s july_12_2025.txt  # Process specific file  
  %(prog)s --days-ago 8      # Process games from 8 days ago
  %(prog)s --format csv      # Save as CSV instead of JSON
  %(prog)s --format both     # Save both JSON and CSV formats
        """
    )
    
    # Mutually exclusive group for file specification
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        'filename', 
        nargs='?', 
        help='Specific schedule file to process (e.g., july_12_2025.txt)'
    )
    group.add_argument(
        '--days-ago', 
        type=int, 
        help='Number of days ago to process (e.g., --days-ago 8 for 8 days ago)'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    
    return parser.parse_args()

def determine_target_filename(args):
    """Determine which file to process based on arguments"""
    if args.filename:
        target_filename = args.filename
        print(f"🎯 User specified file: {target_filename}")
    elif args.days_ago is not None:
        target_filename = get_date_filename(-args.days_ago)
        print(f"🎯 Processing file from {args.days_ago} days ago: {target_filename}")
    else:
        target_filename = get_yesterday_filename()
        print(f"🔍 Using default (yesterday's file): {target_filename}")
    
    return target_filename

def main():
    print("🏟️ MLB Play-by-Play Scraper")
    print("=" * 50)
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Determine target filename
    target_filename = determine_target_filename(args)
    
    # Check if target file exists
    if not os.path.exists(target_filename):
        print(f"❌ Target file '{target_filename}' not found.")
        print("Available .txt files in directory:")
        available_files = glob.glob("*_*_*.txt")
        for file in sorted(available_files):
            print(f"  - {file}")
        sys.exit(1)
    
    # Validate filename format
    base_name = os.path.basename(target_filename)
    date_identifier, _ = os.path.splitext(base_name)
    
    if not re.match(r'^[a-z]+_\d+_\d+', date_identifier, re.IGNORECASE):
        print(f"❌ File '{target_filename}' doesn't match expected format month_day_year.txt")
        sys.exit(1)
    
    print(f"✅ Found target file: {target_filename}")
    print(f"📅 Date identifier: {date_identifier}")
    print(f"💾 Output format: {args.format}")
    
    # Read URLs and transform them to play-by-play URLs
    boxscore_urls = read_urls_from_file(target_filename)
    playbyplay_urls = [transform_url_to_playbyplay(url) for url in boxscore_urls]
    
    print(f"📊 Found {len(playbyplay_urls)} URLs to process")
    print(f"🔄 URL transformation example:")
    if playbyplay_urls:
        print(f"   Boxscore:     {boxscore_urls[0]}")
        print(f"   Play-by-play: {playbyplay_urls[0]}")
    
    # Process each play-by-play URL
    processed_games = []
    successful_extractions = 0
    
    for i, url in enumerate(playbyplay_urls):
        print(f"\n--- Processing URL {i+1}/{len(playbyplay_urls)} ---")
        print(f"🌐 {url}")
        
        try:
            # Use same page fetching approach as enhanced_scrape.py
            html = get_page_content(url)
            
            if html:
                # Extract play-by-play data
                game_data, game_id, away_team, home_team = extract_playbyplay_data(html, url)
                
                if game_data and game_data.get('plays'):
                    # Optional: Enhance player names using boxscore data for exact roster matching
                    if BOXSCORE_NAME_MATCHER_AVAILABLE:
                        print(f"🎯 Enhancing player names using boxscore data...")
                        game_data['plays'] = enhance_play_data_with_boxscore_names(
                            game_data['plays'],
                            game_id,
                            away_team if away_team != 'AWAY' else '',
                            home_team if home_team != 'HOME' else '',
                            date_identifier
                        )
                    else:
                        print(f"⚠️ Skipping boxscore name enhancement - module not available")
                    
                    # Optional: Enhance any remaining names using roster data from CSV files
                    if ENHANCE_PLAYER_NAMES_AVAILABLE:
                        print(f"🔍 Enhancing remaining names using roster data...")
                        game_data['plays'] = enhance_play_data_with_rosters(
                            game_data['plays'],
                            date_identifier,
                            game_id,
                            away_team if away_team != 'AWAY' else '',
                            home_team if home_team != 'HOME' else ''
                        )
                    else:
                        print(f"⚠️ Skipping roster name enhancement - module not available")
                    
                    # Save data in requested format(s)
                    if args.format in ['json', 'both']:
                        save_playbyplay_data(game_data, date_identifier, game_id, away_team, home_team, 'json')
                    
                    if args.format in ['csv', 'both']:
                        save_playbyplay_data(game_data, date_identifier, game_id, away_team, home_team, 'csv')
                    
                    processed_games.append({
                        'game_id': game_id,
                        'url': url,
                        'success': True,
                        'plays': game_data.get('plays', []),
                        'metadata': game_data.get('metadata', {}),
                        'play_count': len(game_data.get('plays', [])),
                        'away_team': away_team,
                        'home_team': home_team,
                        'matchup': f"{away_team}_vs_{home_team}"
                    })
                    
                    successful_extractions += 1
                    print(f"✅ Successfully processed game {away_team} vs {home_team} ({game_id}) - {len(game_data['plays'])} plays")
                else:
                    processed_games.append({
                        'game_id': game_id if game_id else extract_game_id_from_url(url),
                        'url': url,
                        'success': False,
                        'error': 'No play data extracted',
                        'play_count': 0,
                        'away_team': away_team if away_team else 'UNKNOWN',
                        'home_team': home_team if home_team else 'UNKNOWN'
                    })
                    print(f"⚠️ No play data extracted for game {game_id}")
            else:
                processed_games.append({
                    'game_id': extract_game_id_from_url(url),
                    'url': url,
                    'success': False,
                    'error': 'Failed to fetch page content',
                    'play_count': 0,
                    'away_team': 'UNKNOWN',
                    'home_team': 'UNKNOWN'
                })
                print(f"❌ Failed to fetch page content")
        
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            processed_games.append({
                'game_id': extract_game_id_from_url(url),
                'url': url,
                'success': False,
                'error': str(e),
                'play_count': 0,
                'away_team': 'UNKNOWN',
                'home_team': 'UNKNOWN'
            })
        
        # Random delay between requests (reduced for faster processing)
        if i < len(playbyplay_urls) - 1:
            sleep_time = random.uniform(3, 8)  # Reduced from 10-35 to 3-8 seconds
            print(f"⏳ Waiting for {sleep_time:.2f} seconds before next request...")
            time.sleep(sleep_time)
    
    # Create summary report
    create_summary_report(processed_games, date_identifier)
    
    # Move processed file to SCANNED directory (matches enhanced_scrape.py pattern)
    if successful_extractions > 0:
        print(f"\n🗂️ Moving processed file to SCANNED directory...")
        if move_file_to_scanned(target_filename):
            print(f"✅ Successfully processed and archived {target_filename}")
        else:
            print(f"⚠️ File processing completed but archiving failed")
    else:
        print(f"\n⚠️ No successful extractions - keeping file for manual review")
    
    # Final summary
    print(f"\n=== Final Summary ===")
    print(f"📊 Total URLs processed: {len(playbyplay_urls)}")
    print(f"✅ Successful extractions: {successful_extractions}")
    print(f"❌ Failed extractions: {len(playbyplay_urls) - successful_extractions}")
    total_plays = sum(g.get('play_count', 0) for g in processed_games)
    print(f"📋 Total plays extracted: {total_plays}")
    print(f"📁 JSON data saved in: {DATA_PATH / 'playbyplay'}")
    print(f"📁 CSV data saved in: {DATA_PATH.parent / 'CSV_BACKUPS_PBP'}")
    print("🏁 Play-by-play scraper completed!")

def process_single_game_playbyplay(playbyplay_url: str, target_date_identifier: str = None) -> Dict:
    """
    Process a single game's play-by-play data
    
    This function is used by the historical backfill and daily automation scripts.
    It fetches, extracts, and saves play-by-play data for a single game.
    
    Args:
        playbyplay_url: The play-by-play URL to process
    
    Returns:
        Dict with success status and details
    """
    try:
        print(f"🏟️ Processing game: {playbyplay_url[:80]}...")
        
        # Fetch page content
        html = get_page_content(playbyplay_url)
        if not html:
            return {'success': False, 'error': 'Failed to fetch page content'}
        
        # Extract play-by-play data
        game_data, game_id, away_team, home_team = extract_playbyplay_data(html, playbyplay_url)
        
        if not game_data or not game_data.get('plays'):
            return {'success': False, 'error': 'No play data extracted'}
        
        # Use provided date identifier or fall back to current date
        if target_date_identifier:
            date_identifier = target_date_identifier
            print(f"📅 Using target date: {date_identifier}")
        else:
            # Fallback to current date (for backward compatibility)
            try:
                date_identifier = datetime.now().strftime('%B_%d_%Y').lower()
                print(f"📅 Using current date (fallback): {date_identifier}")
            except:
                date_identifier = datetime.now().strftime('%B_%d_%Y').lower()
        
        # Optional player name enhancement
        if BOXSCORE_NAME_MATCHER_AVAILABLE:
            print(f"🎯 Enhancing player names using boxscore data...")
            game_data['plays'] = enhance_play_data_with_boxscore_names(
                game_data['plays'],
                game_id,
                away_team if away_team != 'AWAY' else '',
                home_team if home_team != 'HOME' else '',
                date_identifier
            )
        
        if ENHANCE_PLAYER_NAMES_AVAILABLE:
            print(f"🔍 Enhancing remaining names using roster data...")
            game_data['plays'] = enhance_play_data_with_rosters(
                game_data['plays'],
                date_identifier,
                game_id,
                away_team if away_team != 'AWAY' else '',
                home_team if home_team != 'HOME' else ''
            )
        
        # Save play-by-play data (default to JSON format)
        save_playbyplay_data(game_data, date_identifier, game_id, away_team, home_team, 'json')
        
        return {
            'success': True,
            'game_id': game_id,
            'away_team': away_team,
            'home_team': home_team,
            'plays_count': len(game_data.get('plays', [])),
            'date_identifier': date_identifier
        }
        
    except Exception as e:
        print(f"❌ Error processing game: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()