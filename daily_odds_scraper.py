#!/usr/bin/env python3
"""
Daily Odds Scraper - Centralized MLB odds data collection
Downloads both HR and Hits props data and processes with movement tracking
Uses centralized configuration for data paths
"""

import os
import json
import requests
import shutil
from datetime import datetime
import subprocess
import sys

# Use centralized configuration
from config import PATHS, get_output_dirs

class DailyOddsScraper:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.hr_props_file = os.path.join(self.script_dir, 'mlb-batter-hr-props.json')
        self.hits_props_file = os.path.join(self.script_dir, 'mlb-batter-hits-props.json')
        
        # Centralized odds directory
        self.odds_dir = PATHS['odds']
        self.odds_dir.mkdir(parents=True, exist_ok=True)
        
        # Output directories for dev/prod sync
        self.output_dirs = get_output_dirs('odds')
        
        print(f"🎯 Daily Odds Scraper initialized")
        print(f"   Primary odds directory: {self.odds_dir}")
        print(f"   Output directories: {len(self.output_dirs)}")
        for i, output_dir in enumerate(self.output_dirs):
            print(f"     {i+1}. {output_dir}")
    
    def download_odds_data(self, url, output_file, prop_type):
        """Download odds data from DraftKings API"""
        try:
            print(f"📶 Downloading {prop_type} odds data...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            # Validate JSON response
            data = response.json()
            if not data or 'markets' not in data:
                print(f"⚠️ Invalid JSON structure for {prop_type} - missing 'markets'")
                return False
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            file_size = os.path.getsize(output_file)
            market_count = len(data.get('markets', []))
            selection_count = len(data.get('selections', []))
            
            print(f"✅ {prop_type} download successful:")
            print(f"   File size: {file_size:,} bytes")
            print(f"   Markets: {market_count}")
            print(f"   Selections: {selection_count}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error downloading {prop_type} odds: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response for {prop_type}: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error downloading {prop_type}: {e}")
            return False
    
    def process_odds_data(self):
        """Process downloaded odds data using existing odds-scrape.py"""
        try:
            print(f"🔄 Processing odds data with odds-scrape.py...")
            
            # Change to script directory for relative paths
            original_cwd = os.getcwd()
            os.chdir(self.script_dir)
            
            try:
                # Run the odds processing script
                result = subprocess.run([sys.executable, 'odds-scrape.py'], 
                                      capture_output=True, 
                                      text=True, 
                                      check=True)
                
                print("✅ Odds processing completed successfully")
                
                # Print any output from the script
                if result.stdout:
                    print("📊 Processing output:")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Odds processing failed (exit code {e.returncode}):")
                if e.stdout:
                    print("STDOUT:", e.stdout)
                if e.stderr:
                    print("STDERR:", e.stderr)
                return False
            
        except Exception as e:
            print(f"❌ Error processing odds data: {e}")
            return False
        finally:
            os.chdir(original_cwd)
    
    def archive_source_files(self):
        """Archive the source JSON files with timestamp"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_dir = os.path.join(self.script_dir, 'logs', 'json_archive')
            os.makedirs(archive_dir, exist_ok=True)
            
            archived_files = []
            
            # Archive HR props file
            if os.path.exists(self.hr_props_file):
                archived_hr = os.path.join(archive_dir, f'mlb-batter-hr-props_{timestamp}.json')
                shutil.copy2(self.hr_props_file, archived_hr)
                os.remove(self.hr_props_file)
                archived_files.append(f'HR props → {os.path.basename(archived_hr)}')
            
            # Archive Hits props file  
            if os.path.exists(self.hits_props_file):
                archived_hits = os.path.join(archive_dir, f'mlb-batter-hits-props_{timestamp}.json')
                shutil.copy2(self.hits_props_file, archived_hits)
                os.remove(self.hits_props_file)
                archived_files.append(f'Hits props → {os.path.basename(archived_hits)}')
            
            if archived_files:
                print(f"🗃️ Archived source files:")
                for file_info in archived_files:
                    print(f"   {file_info}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not archive source files: {e}")
    
    def generate_status_files(self):
        """Generate status files for dashboard integration"""
        try:
            # Generate daily status
            hr_odds_file = self.odds_dir / 'mlb-hr-odds-only.csv'
            hits_odds_file = self.odds_dir / 'mlb-hits-odds-only.csv'
            
            hr_count = 0
            hits_count = 0
            
            if hr_odds_file.exists():
                with open(hr_odds_file, 'r') as f:
                    hr_count = max(0, len(f.readlines()) - 1)  # Subtract header
            
            if hits_odds_file.exists():
                with open(hits_odds_file, 'r') as f:
                    hits_count = max(0, len(f.readlines()) - 1)  # Subtract header
            
            status_data = {
                'last_update': datetime.utcnow().isoformat() + 'Z',
                'session_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'active',
                'hr_players': hr_count,
                'hits_players': hits_count,
                'total_players': hr_count + hits_count,
                'tracking_active': True,
                'data_sources': {
                    'hr_props': hr_count > 0,
                    'hits_props': hits_count > 0
                }
            }
            
            # Save to primary location
            status_file = self.odds_dir / 'daily-status.json'
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            # Copy to all output directories
            for output_dir in self.output_dirs:
                if output_dir != self.odds_dir:
                    try:
                        target_status = os.path.join(output_dir, 'daily-status.json')
                        shutil.copy2(status_file, target_status)
                    except Exception as e:
                        print(f"⚠️ Warning: Could not sync status to {output_dir}: {e}")
            
            print(f"📊 Status files generated:")
            print(f"   HR players: {hr_count}")
            print(f"   Hits players: {hits_count}")
            print(f"   Total players: {hr_count + hits_count}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not generate status files: {e}")
    
    def run(self):
        """Main execution method"""
        print(f"🚀 Starting daily odds scraping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        success_count = 0
        
        # DraftKings API endpoints
        hr_url = "https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/743?=json"
        hits_url = "https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/743/subcategories/17320"  # Correct hits subcategory
        
        # Download HR props
        if self.download_odds_data(hr_url, self.hr_props_file, "HR Props"):
            success_count += 1
        
        # Download Hits props (try different endpoint - this may need adjustment)
        if self.download_odds_data(hits_url, self.hits_props_file, "Hits Props"):
            success_count += 1
        
        # Process the downloaded data if we have at least HR props
        if success_count > 0:
            print(f"\n📈 Processing {success_count} downloaded data file(s)...")
            
            if self.process_odds_data():
                print("✅ Odds data processing completed successfully")
                
                # Archive source files
                self.archive_source_files()
                
                # Generate status files
                self.generate_status_files()
                
                print(f"\n🎯 Odds scraping session completed successfully!")
                print(f"   Files generated in: {self.odds_dir}")
                print(f"   Synced to {len(self.output_dirs)} directories")
                
                return True
            else:
                print("❌ Odds data processing failed")
                return False
        else:
            print("❌ No odds data was successfully downloaded")
            return False

def main():
    """Main entry point"""
    try:
        scraper = DailyOddsScraper()
        success = scraper.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error in daily odds scraper: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()