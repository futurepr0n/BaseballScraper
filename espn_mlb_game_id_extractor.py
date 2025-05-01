import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, timedelta
import time
import random
import json
import gc  # Garbage collection
import pickle  # For saving checkpoint
import sys  # For memory debugging

# Configure settings
DEBUG = True  # Set to True to enable debug output
SAVE_HTML = True  # Save HTML content for debugging
USE_CHECKPOINT = True  # Enable checkpoint system to resume from last successful date

def debug_print(message):
    """Print debug messages if DEBUG is enabled"""
    if DEBUG:
        print(f"[DEBUG] {message}")

def save_checkpoint(current_date, processed_dates):
    """Save checkpoint to resume from later"""
    if not USE_CHECKPOINT:
        return
    
    checkpoint_data = {
        'current_date': current_date,
        'processed_dates': processed_dates
    }
    
    try:
        with open('espn_scraper_checkpoint.pkl', 'wb') as f:
            pickle.dump(checkpoint_data, f)
        debug_print(f"Checkpoint saved: {current_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error saving checkpoint: {e}")

def load_checkpoint():
    """Load checkpoint if available"""
    if not USE_CHECKPOINT or not os.path.exists('espn_scraper_checkpoint.pkl'):
        return None, set()
    
    try:
        with open('espn_scraper_checkpoint.pkl', 'rb') as f:
            checkpoint_data = pickle.load(f)
        current_date = checkpoint_data.get('current_date')
        processed_dates = checkpoint_data.get('processed_dates', set())
        debug_print(f"Checkpoint loaded: {current_date.strftime('%Y-%m-%d')}")
        print(f"Resuming from checkpoint: {current_date.strftime('%Y-%m-%d')}")
        return current_date, processed_dates
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return None, set()

def get_mlb_schedule(date_str):
    """
    Fetch MLB schedule from ESPN for a specific date.
    
    Args:
        date_str: Date string in format YYYYMMDD
    
    Returns:
        HTML content of the schedule page
    """
    url = f"https://www.espn.com/mlb/schedule/_/date/{date_str}"
    
    # Rotating user agents to appear more like a human
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }
    
    try:
        debug_print(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        debug_print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Save HTML for debugging if enabled
            if SAVE_HTML:
                debug_dir = "debug_html"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                with open(f"{debug_dir}/espn_schedule_{date_str}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                debug_print(f"Saved HTML to {debug_dir}/espn_schedule_{date_str}.html")
            
            return html_content
        else:
            print(f"Failed to fetch schedule: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def parse_html_safely(html_content):
    """Parse HTML content with memory considerations"""
    try:
        # Use the lxml parser which is faster and more memory-efficient
        soup = BeautifulSoup(html_content, 'lxml')
        return soup
    except Exception as e:
        print(f"Error parsing HTML with lxml: {e}")
        try:
            # Fall back to html.parser which uses less memory
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as e:
            print(f"Error parsing HTML with html.parser: {e}")
            return None

def extract_game_ids(html_content, date_str):
    """
    Extract game IDs and dates from the ESPN MLB schedule HTML.
    
    Args:
        html_content: HTML content of the schedule page
        date_str: The date string used to fetch the schedule (for debugging)
    
    Returns:
        Dictionary with dates as keys and lists of game IDs as values
    """
    if not html_content:
        return {}
    
    # Attempt to free memory before processing
    gc.collect()
    
    # Use a more memory-efficient parsing approach
    soup = parse_html_safely(html_content)
    if not soup:
        return {}
    
    result = {}
    debug_print(f"Parsing HTML for date {date_str}")
    
    try:
        # Check if we can find date headers
        date_headers = soup.find_all('h2', class_='Table__Title')
        debug_print(f"Found {len(date_headers)} date headers with class 'Table__Title'")
        
        if not date_headers:
            debug_print("No date headers found, trying alternative selectors")
            # Try alternative selectors that might match date headers
            date_headers = soup.find_all(['h2', 'h3', 'div'], class_=lambda c: c and ('title' in c.lower() or 'header' in c.lower()))
            debug_print(f"Found {len(date_headers)} date headers with alternative selectors")
        
        # Process date headers if found
        for i, header in enumerate(date_headers):
            try:
                date_text = header.text.strip()
                debug_print(f"Processing date header {i+1}: '{date_text}'")
                
                # Find the table following this header
                table = header.find_next('table')
                if not table:
                    debug_print(f"No table found for date header: '{date_text}'")
                    continue
                
                # Extract game IDs from links
                game_ids = []
                
                # Try different selectors for links containing game IDs
                links = table.find_all('a', href=True)
                debug_print(f"Found {len(links)} links in table")
                
                for link in links:
                    href = link.get('href', '')
                    match = re.search(r'gameId/(\d+)', href)
                    if match:
                        game_id = match.group(1)
                        debug_print(f"Extracted game ID: {game_id}")
                        game_ids.append(game_id)
                
                if game_ids:
                    result[date_text] = game_ids
                    debug_print(f"Added {len(game_ids)} game IDs for date '{date_text}'")
                else:
                    debug_print(f"No game IDs found for date '{date_text}'")
                
                # Force garbage collection after each table to prevent memory buildup
                gc.collect()
                
            except Exception as e:
                print(f"Error processing header {i+1}: {e}")
                # Continue with next header
        
        # If we didn't find any results with headers, try a direct approach
        if not result:
            debug_print("No results from headers approach, trying to process page directly")
            links = soup.find_all('a', href=True)
            game_ids = []
            
            for link in links:
                href = link.get('href', '')
                match = re.search(r'gameId/(\d+)', href)
                if match:
                    game_id = match.group(1)
                    game_ids.append(game_id)
            
            if game_ids:
                # Use the input date if we can't determine date from page
                try:
                    page_date = datetime.strptime(date_str, "%Y%m%d")
                    formatted_date = page_date.strftime("%A, %B %d, %Y")
                    result[formatted_date] = game_ids
                    debug_print(f"Added {len(game_ids)} game IDs using direct approach")
                except ValueError:
                    result[f"Unknown Date ({date_str})"] = game_ids
    
    except Exception as e:
        print(f"Error extracting game IDs: {e}")
    
    # Force garbage collection after processing
    gc.collect()
    
    # Log the final result
    debug_print(f"Found data for {len(result)} dates")
    return result

def format_date_for_filename(date_str):
    """
    Convert date string (e.g., "Friday, May 2, 2025") to filename format (e.g., "may_2_2025.txt")
    
    Args:
        date_str: Date string in format "Day, Month D, YYYY"
    
    Returns:
        Formatted filename string
    """
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, "%A, %B %d, %Y")
        # Format as month_day_year
        return date_obj.strftime("%B").lower() + "_" + str(date_obj.day) + "_" + str(date_obj.year) + ".txt"
    except ValueError as e:
        print(f"Error parsing date '{date_str}': {e}")
        # Fallback to a simplified approach
        parts = date_str.split(', ')
        if len(parts) >= 3:
            month_day = parts[1].split(' ')
            month = month_day[0].lower()
            day = month_day[1]
            year = parts[2]
            return f"{month}_{day}_{year}.txt"
        
        # If there's "Unknown Date" in the string
        if "Unknown Date" in date_str:
            match = re.search(r'\((\d{8})\)', date_str)
            if match:
                date_code = match.group(1)
                try:
                    date_obj = datetime.strptime(date_code, "%Y%m%d")
                    return date_obj.strftime("%B").lower() + "_" + str(date_obj.day) + "_" + str(date_obj.year) + ".txt"
                except ValueError:
                    pass
        
        # Last resort
        return "unknown_date_" + str(int(time.time())) + ".txt"

def create_or_update_boxscore_file(date_str, game_ids):
    """
    Create or update a text file with boxscore URLs for a specific date.
    Checks if the file exists and avoids duplicate entries.
    
    Args:
        date_str: Date string in format "Day, Month D, YYYY"
        game_ids: List of game IDs for this date
    """
    filename = format_date_for_filename(date_str)
    debug_print(f"Processing file: {filename}")
    
    existing_urls = set()
    
    # Check if file exists and read existing URLs
    if os.path.exists(filename):
        debug_print(f"File {filename} exists, reading existing content")
        with open(filename, 'r') as f:
            existing_urls = set(line.strip() for line in f if line.strip())
        debug_print(f"Found {len(existing_urls)} existing URLs")
    else:
        debug_print(f"File {filename} does not exist, will create new file")
    
    # Create set of new URLs
    new_urls = set()
    for game_id in game_ids:
        boxscore_url = f"https://www.espn.com/mlb/boxscore/_/gameId/{game_id}"
        new_urls.add(boxscore_url)
    
    debug_print(f"Generated {len(new_urls)} new URLs")
    
    # Combine existing and new URLs, removing duplicates
    all_urls = existing_urls.union(new_urls)
    
    # Write back to file
    with open(filename, 'w') as f:
        for url in sorted(all_urls):
            f.write(url + "\n")
    
    # Count new URLs added
    new_count = len(new_urls - existing_urls)
    if new_count > 0:
        print(f"Updated file: {filename} - Added {new_count} new URLs")
    else:
        print(f"No new URLs added to {filename}")

def process_date_range(start_date_str, end_date_str):
    """
    Process a range of dates, fetching game IDs and creating/updating files.
    
    Args:
        start_date_str: Start date in format YYYYMMDD
        end_date_str: End date in format YYYYMMDD
    """
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    end_date = datetime.strptime(end_date_str, "%Y%m%d")
    
    # Try to load checkpoint
    current_date, processed_dates = load_checkpoint()
    if current_date is None:
        current_date = start_date
    
    success_count = 0
    error_count = 0
    
    try:
        while current_date <= end_date:
            # Format date for ESPN URL
            current_date_str = current_date.strftime("%Y%m%d")
            print(f"\nProcessing date: {current_date.strftime('%Y-%m-%d')}")
            
            try:
                # Fetch schedule HTML
                html_content = get_mlb_schedule(current_date_str)
                
                if html_content:
                    game_ids_by_date = extract_game_ids(html_content, current_date_str)
                    
                    if not game_ids_by_date:
                        print(f"No game IDs found for {current_date.strftime('%Y-%m-%d')}")
                        error_count += 1
                    else:
                        # Process each date in the returned HTML
                        for date_str, game_ids in game_ids_by_date.items():
                            try:
                                # Parse the date string to check if it's within our range
                                try:
                                    page_date = datetime.strptime(date_str, "%A, %B %d, %Y")
                                    date_key = page_date.strftime("%Y-%m-%d")
                                except ValueError:
                                    # For dates with other formats
                                    date_key = date_str
                                
                                # Check if we've already processed this date
                                if date_key not in processed_dates:
                                    # Create or update the file for this date
                                    create_or_update_boxscore_file(date_str, game_ids)
                                    processed_dates.add(date_key)
                                    success_count += 1
                                else:
                                    debug_print(f"Already processed date: {date_str}")
                                    
                            except Exception as e:
                                print(f"Error processing date '{date_str}': {e}")
                                error_count += 1
                else:
                    print(f"Failed to retrieve MLB schedule for {current_date_str}")
                    error_count += 1
                
                # Add a human-like random delay between requests (as requested)
                sleep_time = random.uniform(10, 35)
                print(f"Waiting for {sleep_time:.2f} seconds before next request...")
                time.sleep(sleep_time)
            
            except Exception as e:
                print(f"Error during processing of {current_date_str}: {e}")
                error_count += 1
            
            # Save checkpoint after each date
            next_date = current_date + timedelta(days=3)
            save_checkpoint(next_date, processed_dates)
            
            # Advance to the next date
            current_date = next_date
            
            # Force garbage collection to prevent memory buildup
            gc.collect()
    
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Progress has been saved.")
        return success_count, error_count
    
    return success_count, error_count

def main():
    # Date range from May 2, 2025 to September 28, 2025
    start_date = "20250327"  # May 2, 2025
    end_date = "20250928"    # September 28, 2025
    
    print(f"Starting MLB schedule processing from {start_date} to {end_date}")
    print(f"Memory usage stats will be tracked to prevent segmentation faults")
    
    # Create debug directory if needed
    if DEBUG and not os.path.exists("debug_html"):
        os.makedirs("debug_html")
    
    try:
        success_count, error_count = process_date_range(start_date, end_date)
        
        print("\nProcessing complete!")
        print(f"Successfully processed dates: {success_count}")
        print(f"Errors encountered: {error_count}")
        
        if DEBUG:
            print(f"\nDebug information saved to 'debug_html' directory")
    
    except Exception as e:
        print(f"Critical error in main execution: {e}")
        # Try to save checkpoint if possible
        try:
            current_date = datetime.strptime(start_date, "%Y%m%d")
            save_checkpoint(current_date, set())
        except:
            pass

if __name__ == "__main__":
    main()