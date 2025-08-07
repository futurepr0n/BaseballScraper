#!/usr/bin/env python3
"""
Enhanced Historical Backfill for MLB Play-by-Play Data
Processes multiple historical dates in batch with centralized data storage

This script extends playbyplay_scraper.py functionality for historical data collection,
using centralized configuration and proper error handling for large-scale backfills.

Usage:
  python enhanced_historical_backfill_playbyplay.py --start-date 2025-07-01 --end-date 2025-07-31
  python enhanced_historical_backfill_playbyplay.py --date-list july_dates.txt
  python enhanced_historical_backfill_playbyplay.py --specific-date 2025-07-15
"""

import json
import os
import sys
import time
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging

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
    move_file_to_scanned
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_backfill_playbyplay.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricalPlaybyPlayBackfill:
    """Enhanced historical backfill processor with centralized storage"""
    
    def __init__(self):
        self.processed_games = 0
        self.failed_games = 0
        self.skipped_games = 0
        self.total_games = 0
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
            logger.info(f"✅ Ensured directory exists: {directory}")
    
    def get_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Generate list of dates between start and end (inclusive)"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        logger.info(f"📅 Generated {len(dates)} dates from {start_date} to {end_date}")
        return dates
    
    def convert_date_to_filename(self, date_str: str) -> str:
        """Convert YYYY-MM-DD to month_day_year.txt format"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month_name = date_obj.strftime('%B').lower()
        day = str(date_obj.day)  # No zero padding
        year = str(date_obj.year)
        
        filename = f"{month_name}_{day}_{year}.txt"
        logger.debug(f"📝 Converted {date_str} → {filename}")
        return filename
    
    def process_date_file(self, filename: str) -> Dict:
        """Process a single date file for play-by-play data"""
        logger.info(f"🎯 Processing file: {filename}")
        
        if not os.path.exists(filename):
            logger.warning(f"⚠️ File not found: {filename}")
            return {'success': False, 'error': 'File not found'}
        
        try:
            # Read URLs from file
            urls = read_urls_from_file(filename)
            if not urls:
                logger.warning(f"⚠️ No URLs found in {filename}")
                return {'success': False, 'error': 'No URLs found'}
            
            logger.info(f"📊 Found {len(urls)} games in {filename}")
            self.total_games += len(urls)
            
            # Process each game
            games_processed = 0
            games_failed = 0
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"🏟️ Processing game {i+1}/{len(urls)}: {url[:80]}...")
                    
                    # Transform to play-by-play URL
                    playbyplay_url = transform_url_to_playbyplay(url)
                    
                    # Process the game
                    result = process_single_game_playbyplay(playbyplay_url)
                    
                    if result and result.get('success'):
                        games_processed += 1
                        self.processed_games += 1
                        logger.info(f"✅ Game processed successfully")
                    else:
                        games_failed += 1
                        self.failed_games += 1
                        logger.warning(f"⚠️ Game processing failed: {result.get('error', 'Unknown error')}")
                    
                    # Add delay between games (respectful scraping)
                    if i < len(urls) - 1:
                        delay = random.uniform(15, 30)  # Longer delays for historical backfill
                        logger.debug(f"⏳ Waiting {delay:.1f}s before next game...")
                        time.sleep(delay)
                
                except Exception as e:
                    logger.error(f"❌ Error processing game {url}: {e}")
                    games_failed += 1
                    self.failed_games += 1
                    continue
            
            # Move processed file to SCANNED
            try:
                if move_file_to_scanned(filename):
                    logger.info(f"📦 Moved {filename} to SCANNED directory")
                else:
                    logger.warning(f"⚠️ Failed to move {filename} to SCANNED")
            except Exception as e:
                logger.warning(f"⚠️ Error moving file to SCANNED: {e}")
            
            return {
                'success': True,
                'processed': games_processed,
                'failed': games_failed,
                'total': len(urls)
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing file {filename}: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_date_range(self, start_date: str, end_date: str) -> Dict:
        """Process all files in a date range"""
        logger.info(f"🚀 Starting historical backfill: {start_date} to {end_date}")
        
        dates = self.get_date_range(start_date, end_date)
        results = []
        
        for date_str in dates:
            filename = self.convert_date_to_filename(date_str)
            
            if os.path.exists(filename):
                result = self.process_date_file(filename)
                results.append({
                    'date': date_str,
                    'filename': filename,
                    'result': result
                })
                
                # Progress update
                elapsed = datetime.now() - self.start_time
                logger.info(f"📊 Progress: {len(results)}/{len(dates)} dates processed ({elapsed})")
            else:
                logger.info(f"⏭️ Skipping {date_str} - file {filename} not found")
                self.skipped_games += 1
        
        return {
            'success': True,
            'dates_processed': len(results),
            'dates_skipped': len(dates) - len(results),
            'total_dates': len(dates),
            'results': results
        }
    
    def process_date_list(self, date_list_file: str) -> Dict:
        """Process dates from a text file list"""
        logger.info(f"📋 Processing dates from list file: {date_list_file}")
        
        try:
            with open(date_list_file, 'r') as f:
                dates = [line.strip() for line in f if line.strip()]
            
            logger.info(f"📅 Found {len(dates)} dates in list file")
            
            results = []
            for date_str in dates:
                try:
                    # Validate date format
                    datetime.strptime(date_str, '%Y-%m-%d')
                    filename = self.convert_date_to_filename(date_str)
                    
                    if os.path.exists(filename):
                        result = self.process_date_file(filename)
                        results.append({
                            'date': date_str,
                            'filename': filename,
                            'result': result
                        })
                    else:
                        logger.info(f"⏭️ Skipping {date_str} - file {filename} not found")
                        self.skipped_games += 1
                        
                except ValueError:
                    logger.warning(f"⚠️ Invalid date format: {date_str} (expected YYYY-MM-DD)")
                    continue
            
            return {
                'success': True,
                'dates_processed': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Error reading date list file: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_specific_date(self, date_str: str) -> Dict:
        """Process a specific date"""
        logger.info(f"🎯 Processing specific date: {date_str}")
        
        try:
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
            filename = self.convert_date_to_filename(date_str)
            
            result = self.process_date_file(filename)
            
            return {
                'success': True,
                'date': date_str,
                'filename': filename,
                'result': result
            }
            
        except ValueError:
            logger.error(f"❌ Invalid date format: {date_str} (expected YYYY-MM-DD)")
            return {'success': False, 'error': 'Invalid date format'}
        except Exception as e:
            logger.error(f"❌ Error processing date {date_str}: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_summary_report(self) -> Dict:
        """Generate summary report of backfill operation"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = {
            'backfill_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'duration_formatted': str(duration),
                'total_games': self.total_games,
                'processed_games': self.processed_games,
                'failed_games': self.failed_games,
                'skipped_games': self.skipped_games,
                'success_rate': round((self.processed_games / max(self.total_games, 1)) * 100, 2)
            },
            'configuration': {
                'data_path': str(DATA_PATH),
                'playbyplay_output_path': str(PATHS['hellraiser'] / 'playbyplay'),
                'scanned_path': str(PATHS['scanned'])
            }
        }
        
        # Save report to file
        report_file = PATHS['hellraiser'] / 'playbyplay' / f'backfill_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📊 Summary report saved: {report_file}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save summary report: {e}")
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Enhanced Historical Backfill for MLB Play-by-Play Data')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--start-date', help='Start date (YYYY-MM-DD) for range processing')
    group.add_argument('--date-list', help='File containing list of dates to process')
    group.add_argument('--specific-date', help='Process a specific date (YYYY-MM-DD)')
    
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD) for range processing (required with --start-date)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually doing it')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.start_date and not args.end_date:
        parser.error("--end-date is required when using --start-date")
    
    if args.dry_run:
        logger.info("🧪 DRY RUN MODE - No actual processing will occur")
        return
    
    # Initialize backfill processor
    backfill = HistoricalPlaybyPlayBackfill()
    
    try:
        if args.start_date and args.end_date:
            # Process date range
            result = backfill.process_date_range(args.start_date, args.end_date)
        elif args.date_list:
            # Process from date list file
            result = backfill.process_date_list(args.date_list)
        elif args.specific_date:
            # Process specific date
            result = backfill.process_specific_date(args.specific_date)
        
        # Generate and display summary
        summary = backfill.generate_summary_report()
        
        logger.info("🎉 Historical Backfill Complete!")
        logger.info("="*50)
        logger.info(f"📊 Total Games: {summary['backfill_summary']['total_games']}")
        logger.info(f"✅ Processed: {summary['backfill_summary']['processed_games']}")
        logger.info(f"❌ Failed: {summary['backfill_summary']['failed_games']}")
        logger.info(f"⏭️ Skipped: {summary['backfill_summary']['skipped_games']}")
        logger.info(f"📈 Success Rate: {summary['backfill_summary']['success_rate']}%")
        logger.info(f"⏱️ Duration: {summary['backfill_summary']['duration_formatted']}")
        
        if summary['backfill_summary']['success_rate'] >= 90:
            logger.info("🎯 Excellent success rate!")
        elif summary['backfill_summary']['success_rate'] >= 75:
            logger.info("✅ Good success rate")
        else:
            logger.warning("⚠️ Low success rate - review logs for issues")
        
    except KeyboardInterrupt:
        logger.info("🛑 Backfill interrupted by user")
        summary = backfill.generate_summary_report()
        logger.info(f"📊 Partial completion: {backfill.processed_games} games processed")
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()