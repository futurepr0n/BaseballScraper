#!/usr/bin/env python3
"""
Daily Play-by-Play Automation Script
Integrates play-by-play data collection into the daily baseball analytics pipeline

This script extends the daily automation to include play-by-play data collection,
using centralized configuration and proper integration with the existing workflow.

Usage:
  python daily_playbyplay_automation.py                    # Process yesterday's games
  python daily_playbyplay_automation.py --date 2025-08-05  # Process specific date
  python daily_playbyplay_automation.py --dry-run          # Test run without processing
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Import centralized configuration
from config import PATHS, DATA_PATH

# Import playbyplay scraper functionality
from playbyplay_scraper import (
    transform_url_to_playbyplay,
    extract_playbyplay_data,
    save_playbyplay_data,
    process_single_game_playbyplay
)

# Import enhanced scraper utilities
from enhanced_scrape import (
    read_urls_from_file,
    get_date_filename,
    get_yesterday_filename,
    move_file_to_scanned
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_playbyplay_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyPlaybyPlayAutomation:
    """Daily play-by-play data collection automation"""
    
    def __init__(self, target_date: Optional[str] = None):
        self.target_date = target_date
        self.processed_games = 0
        self.failed_games = 0
        self.start_time = datetime.now()
        
        # Ensure output directories exist
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            PATHS['hellraiser'] / 'playbyplay',
            PATHS['scanned'],
            Path('logs')
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def determine_target_filename(self) -> str:
        """Determine which date file to process"""
        if self.target_date:
            # Convert YYYY-MM-DD to expected filename format
            date_obj = datetime.strptime(self.target_date, '%Y-%m-%d')
            month_name = date_obj.strftime('%B').lower()
            day = str(date_obj.day)  # No zero padding
            year = str(date_obj.year)
            filename = f"{month_name}_{day}_{year}.txt"
            logger.info(f"🎯 Target date specified: {self.target_date} → {filename}")
        else:
            # Use yesterday's file (default behavior)
            filename = get_yesterday_filename()
            logger.info(f"📅 Using yesterday's file: {filename}")
        
        return filename
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met for play-by-play processing"""
        from config import PATHS
        
        # Check centralized CSV backup location first (enhanced_scrape outputs here)
        csv_backup_path = PATHS['csv_backups']
        csv_files = []
        
        if csv_backup_path.exists():
            csv_files = list(csv_backup_path.glob('*_hitting_*.csv')) + list(csv_backup_path.glob('*_pitching_*.csv'))
            if csv_files:
                logger.info(f"✅ Found {len(csv_files)} CSV files in centralized backup location")
                return True
            else:
                logger.debug(f"🔍 Checked centralized location: {csv_backup_path} (no CSV files found)")
        
        # Fallback: check local directory (for backward compatibility or manual runs)
        local_csv_files = list(Path('.').glob('*_hitting_*.csv')) + list(Path('.').glob('*_pitching_*.csv'))
        if local_csv_files:
            logger.info(f"✅ Found {len(local_csv_files)} CSV files in local directory")
            return True
        
        logger.warning("⚠️ No CSV files found in either centralized backup or local directory")
        logger.info("💡 Recommendation: Run enhanced_scrape.py first to collect basic game data")
        logger.info(f"🔍 Checked locations:")
        logger.info(f"   - Centralized: {csv_backup_path}")
        logger.info(f"   - Local: {Path('.').resolve()}")
        return False
    
    def find_schedule_file(self, filename: str) -> str:
        """Find schedule file with fallback locations and date ranges"""
        from config import PATHS
        from datetime import datetime, timedelta
        
        # Define locations to check (prioritize local first for current day, then centralized for processed)
        locations = [
            Path('.'),                    # Local directory (current/unprocessed files)
            PATHS['scanned'],            # Centralized SCANNED (processed files)
        ]
        
        # Check for exact filename match
        for location in locations:
            file_path = location / filename
            if file_path.exists():
                logger.info(f"✅ Found schedule file: {file_path}")
                return str(file_path)
        
        # If exact file not found, try alternative dates (useful for automation)
        logger.debug(f"🔍 Exact file {filename} not found, trying alternative dates...")
        
        for days_back in [0, 1, 2]:  # Try today, yesterday, day before yesterday
            alt_date = datetime.now() - timedelta(days=days_back)
            alt_filename = f"{alt_date.strftime('%B').lower()}_{alt_date.day}_{alt_date.year}.txt"
            
            for location in locations:
                file_path = location / alt_filename
                if file_path.exists():
                    logger.info(f"✅ Found alternative schedule file: {file_path} (instead of {filename})")
                    return str(file_path)
        
        # Log detailed search results
        logger.error(f"❌ No schedule file found for {filename}")
        logger.info(f"🔍 Searched locations:")
        for location in locations:
            logger.info(f"   - {location}: {'exists' if location.exists() else 'not found'}")
        
        raise FileNotFoundError(f"Schedule file not found: {filename}")

    def process_daily_playbyplay(self, filename: str, dry_run: bool = False) -> Dict:
        """Process play-by-play data for the specified date file"""
        logger.info(f"🎯 Processing daily play-by-play for: {filename}")
        
        if dry_run:
            logger.info("🧪 DRY RUN MODE - No actual processing will occur")
            return {'success': True, 'dry_run': True}
        
        try:
            # Find the schedule file using smart search
            actual_file_path = self.find_schedule_file(filename)
        except FileNotFoundError as e:
            logger.error(str(e))
            return {'success': False, 'error': 'File not found'}
        
        try:
            # Read URLs from the found file
            urls = read_urls_from_file(actual_file_path)
            if not urls:
                logger.warning(f"⚠️ No URLs found in {actual_file_path}")
                return {'success': False, 'error': 'No URLs found'}
            
            logger.info(f"📊 Found {len(urls)} games to process for play-by-play data")
            
            # Process each game
            processed = 0
            failed = 0
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"🏟️ Processing game {i+1}/{len(urls)}")
                    logger.debug(f"   URL: {url[:80]}...")
                    
                    # Transform to play-by-play URL
                    playbyplay_url = transform_url_to_playbyplay(url)
                    
                    # Process the game
                    result = process_single_game_playbyplay(playbyplay_url)
                    
                    if result and result.get('success'):
                        processed += 1
                        self.processed_games += 1
                        logger.info(f"   ✅ Play-by-play data collected successfully")
                    else:
                        failed += 1
                        self.failed_games += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                        logger.warning(f"   ⚠️ Play-by-play collection failed: {error_msg}")
                    
                    # Add delay between games for respectful scraping
                    if i < len(urls) - 1:
                        delay_time = 20  # 20 seconds between games
                        logger.debug(f"   ⏳ Waiting {delay_time}s before next game...")
                        time.sleep(delay_time)
                
                except Exception as e:
                    logger.error(f"❌ Error processing game {i+1}: {e}")
                    failed += 1
                    self.failed_games += 1
                    continue
            
            success_rate = (processed / len(urls)) * 100 if urls else 0
            
            logger.info(f"📊 Daily play-by-play processing complete:")
            logger.info(f"   ✅ Processed: {processed}/{len(urls)} ({success_rate:.1f}%)")
            logger.info(f"   ❌ Failed: {failed}")
            
            return {
                'success': True,
                'processed': processed,
                'failed': failed,
                'total': len(urls),
                'success_rate': success_rate
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing daily play-by-play: {e}")
            return {'success': False, 'error': str(e)}
    
    def integrate_with_daily_workflow(self, dry_run: bool = False) -> Dict:
        """Integration point for daily automation workflow"""
        logger.info("🔗 Integrating play-by-play collection into daily workflow")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            return {
                'success': False, 
                'error': 'Prerequisites not met - run enhanced_scrape.py first'
            }
        
        # Step 2: Determine target file
        filename = self.determine_target_filename()
        
        # Step 3: Process play-by-play data
        result = self.process_daily_playbyplay(filename, dry_run)
        
        # Step 4: Move processed file to SCANNED (if successful and not dry run)
        if result.get('success') and not dry_run and not result.get('dry_run'):
            try:
                if move_file_to_scanned(filename):
                    logger.info(f"📦 Moved {filename} to SCANNED directory")
                    result['file_archived'] = True
                else:
                    logger.warning(f"⚠️ Failed to move {filename} to SCANNED")
                    result['file_archived'] = False
            except Exception as e:
                logger.warning(f"⚠️ Error moving file to SCANNED: {e}")
                result['file_archived'] = False
        
        return result
    
    def generate_summary_report(self, result: Dict) -> Dict:
        """Generate summary report for daily play-by-play processing"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = {
            'daily_playbyplay_summary': {
                'date': self.target_date or 'yesterday',
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'duration_formatted': str(duration),
                'result': result,
                'configuration': {
                    'data_path': str(DATA_PATH),
                    'playbyplay_output_path': str(PATHS['hellraiser'] / 'playbyplay'),
                    'scanned_path': str(PATHS['scanned'])
                }
            }
        }
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = PATHS['hellraiser'] / 'playbyplay' / f'daily_playbyplay_report_{timestamp}.json'
        
        try:
            with open(report_file, 'w') as f:
                import json
                json.dump(report, f, indent=2)
            logger.info(f"📊 Summary report saved: {report_file}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save summary report: {e}")
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Daily Play-by-Play Automation')
    parser.add_argument('--date', help='Specific date to process (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually doing it')
    parser.add_argument('--check-only', action='store_true', help='Only check prerequisites without processing')
    
    args = parser.parse_args()
    
    # Initialize automation
    automation = DailyPlaybyPlayAutomation(target_date=args.date)
    
    try:
        if args.check_only:
            # Only check prerequisites
            logger.info("🔍 Checking prerequisites for play-by-play processing")
            if automation.check_prerequisites():
                logger.info("✅ All prerequisites met")
                sys.exit(0)
            else:
                logger.error("❌ Prerequisites not met")
                sys.exit(1)
        else:
            # Full processing
            logger.info("🚀 Starting daily play-by-play automation")
            result = automation.integrate_with_daily_workflow(dry_run=args.dry_run)
            
            # Generate summary
            summary = automation.generate_summary_report(result)
            
            if result.get('success'):
                logger.info("🎉 Daily play-by-play automation completed successfully!")
                if not args.dry_run and not result.get('dry_run'):
                    processed = result.get('processed', 0)
                    total = result.get('total', 0)
                    success_rate = result.get('success_rate', 0)
                    logger.info(f"📊 Processed {processed}/{total} games ({success_rate:.1f}% success rate)")
                sys.exit(0)
            else:
                logger.error(f"❌ Daily play-by-play automation failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("🛑 Daily automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error in daily automation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()