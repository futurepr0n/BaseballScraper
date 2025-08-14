#!/usr/bin/env python3
"""
Efficient Play-by-Play Backfill Script
Backfills only missing play-by-play dates instead of regenerating everything from scratch

Usage:
  python3 backfill_playbyplay_missing_dates.py                 # Auto-detect missing dates
  python3 backfill_playbyplay_missing_dates.py --start-date 2025-08-07 --end-date 2025-08-14
  python3 backfill_playbyplay_missing_dates.py --dry-run      # Show what would be processed
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Import centralized configuration and existing functions
from config import DATA_PATH, PATHS
from playbyplay_scraper import process_single_game_playbyplay, transform_url_to_playbyplay
from enhanced_scrape import read_urls_from_file, get_date_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/playbyplay_backfill.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlayByPlayBackfill:
    """Efficient play-by-play backfill for missing dates only"""
    
    def __init__(self):
        self.play_by_play_dir = DATA_PATH / 'play-by-play'
        self.scanned_dir = PATHS['scanned']
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # Ensure directories exist
        self.play_by_play_dir.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
    
    def get_existing_dates(self) -> set:
        """Get set of dates that already have play-by-play data"""
        existing_dates = set()
        
        if not self.play_by_play_dir.exists():
            return existing_dates
            
        for file_path in self.play_by_play_dir.glob("*.json"):
            # Extract date from filename: TEAM_vs_TEAM_playbyplay_month_day_year_gameId.json
            filename = file_path.stem
            parts = filename.split('_')
            
            # Find the date parts (month, day, year appear after 'playbyplay')
            try:
                playbyplay_idx = parts.index('playbyplay')
                if len(parts) > playbyplay_idx + 3:
                    month = parts[playbyplay_idx + 1]
                    day = parts[playbyplay_idx + 2]
                    year = parts[playbyplay_idx + 3]
                    
                    # Convert to standard date format YYYY-MM-DD
                    month_num = self.month_name_to_number(month)
                    if month_num:
                        date_str = f"{year}-{month_num:02d}-{int(day):02d}"
                        existing_dates.add(date_str)
            except (ValueError, IndexError):
                continue
                
        logger.info(f"📊 Found play-by-play data for {len(existing_dates)} dates")
        return existing_dates
    
    def month_name_to_number(self, month_name: str) -> Optional[int]:
        """Convert month name to number"""
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return month_map.get(month_name.lower())
    
    def get_available_schedule_files(self) -> Dict[str, str]:
        """Get available schedule files from both local and SCANNED directories"""
        schedule_files = {}
        
        # Check local directory first (current/unprocessed)
        local_dir = Path('.')
        for file_path in local_dir.glob("*.txt"):
            if self.is_schedule_file(file_path.name):
                date_str = self.schedule_filename_to_date(file_path.name)
                if date_str:
                    schedule_files[date_str] = str(file_path)
        
        # Check SCANNED directory (processed files)
        if self.scanned_dir.exists():
            for file_path in self.scanned_dir.glob("*.txt"):
                if self.is_schedule_file(file_path.name):
                    date_str = self.schedule_filename_to_date(file_path.name)
                    if date_str and date_str not in schedule_files:  # Don't override local files
                        schedule_files[date_str] = str(file_path)
        
        return schedule_files
    
    def is_schedule_file(self, filename: str) -> bool:
        """Check if filename looks like a schedule file"""
        # Pattern: month_day_year.txt (e.g., august_7_2025.txt)
        return filename.endswith('.txt') and len(filename.split('_')) >= 3
    
    def schedule_filename_to_date(self, filename: str) -> Optional[str]:
        """Convert schedule filename to YYYY-MM-DD format"""
        try:
            # Remove .txt extension and split
            name_parts = filename.replace('.txt', '').split('_')
            if len(name_parts) >= 3:
                month_name = name_parts[0]
                day = int(name_parts[1])
                year = int(name_parts[2])
                
                month_num = self.month_name_to_number(month_name)
                if month_num:
                    return f"{year}-{month_num:02d}-{day:02d}"
        except (ValueError, IndexError):
            pass
        return None
    
    def identify_missing_dates(self, start_date: str = None, end_date: str = None) -> List[str]:
        """Identify dates missing play-by-play data (excluding today and future dates)"""
        existing_dates = self.get_existing_dates()
        available_schedules = self.get_available_schedule_files()
        
        # CRITICAL: Never process today's date or future dates (games incomplete)
        today = datetime.now().strftime('%Y-%m-%d')
        
        if start_date and end_date:
            # Use specified date range, but exclude today and future
            missing_dates = []
            current = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                # EXCLUDE today and future dates - games not complete
                if date_str >= today:
                    logger.info(f"⚠️ Skipping {date_str} (today or future - games incomplete)")
                    current += timedelta(days=1)
                    continue
                    
                if date_str not in existing_dates and date_str in available_schedules:
                    missing_dates.append(date_str)
                current += timedelta(days=1)
        else:
            # Auto-detect: find all available schedules that don't have play-by-play data
            missing_dates = []
            for date_str in available_schedules:
                # EXCLUDE today and future dates - games not complete
                if date_str >= today:
                    continue
                    
                if date_str not in existing_dates:
                    missing_dates.append(date_str)
            
            missing_dates.sort()
        
        logger.info(f"🔍 Identified {len(missing_dates)} missing dates (excluding today/future): {missing_dates}")
        return missing_dates
    
    def date_to_schedule_filename(self, date_str: str) -> str:
        """Convert YYYY-MM-DD to schedule filename format"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month_name = date_obj.strftime('%B').lower()
        day = date_obj.day  # No zero padding
        year = date_obj.year
        return f"{month_name}_{day}_{year}.txt"
    
    def process_missing_date(self, date_str: str, dry_run: bool = False) -> Dict:
        """Process play-by-play data for a missing date"""
        schedule_filename = self.date_to_schedule_filename(date_str)
        available_schedules = self.get_available_schedule_files()
        
        if date_str not in available_schedules:
            logger.warning(f"⚠️ No schedule file found for {date_str} ({schedule_filename})")
            return {'success': False, 'error': 'Schedule file not found'}
        
        schedule_file_path = available_schedules[date_str]
        logger.info(f"🎯 Processing {date_str} using {schedule_file_path}")
        
        if dry_run:
            logger.info("🧪 DRY RUN - No actual processing")
            return {'success': True, 'dry_run': True, 'date': date_str}
        
        try:
            # Read URLs from schedule file
            urls = read_urls_from_file(schedule_file_path)
            if not urls:
                logger.warning(f"⚠️ No URLs found in {schedule_file_path}")
                return {'success': False, 'error': 'No URLs found'}
            
            logger.info(f"📊 Found {len(urls)} games to process for {date_str}")
            
            processed = 0
            failed = 0
            
            # Process each game
            for i, url in enumerate(urls):
                try:
                    logger.info(f"🏟️ Processing game {i+1}/{len(urls)} for {date_str}")
                    
                    # Transform to play-by-play URL
                    playbyplay_url = transform_url_to_playbyplay(url)
                    
                    # Convert date_str (YYYY-MM-DD) to date_identifier (month_day_year)
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    target_date_identifier = f"{date_obj.strftime('%B').lower()}_{date_obj.day}_{date_obj.year}"
                    
                    # Process the game with correct date identifier
                    result = process_single_game_playbyplay(playbyplay_url, target_date_identifier)
                    
                    if result and result.get('success'):
                        processed += 1
                        self.processed_count += 1
                        logger.info(f"   ✅ Play-by-play data collected successfully")
                    else:
                        failed += 1
                        self.failed_count += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                        logger.warning(f"   ⚠️ Play-by-play collection failed: {error_msg}")
                    
                    # Add delay between games for respectful scraping
                    if i < len(urls) - 1:
                        import time
                        time.sleep(20)  # 20 seconds between games
                
                except Exception as e:
                    logger.error(f"❌ Error processing game {i+1} for {date_str}: {e}")
                    failed += 1
                    self.failed_count += 1
                    continue
            
            success_rate = (processed / len(urls)) * 100 if urls else 0
            
            logger.info(f"📊 Completed {date_str}: {processed}/{len(urls)} games ({success_rate:.1f}%)")
            
            return {
                'success': True,
                'date': date_str,
                'processed': processed,
                'failed': failed,
                'total': len(urls),
                'success_rate': success_rate
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing {date_str}: {e}")
            return {'success': False, 'date': date_str, 'error': str(e)}
    
    def run_backfill(self, missing_dates: List[str], dry_run: bool = False) -> Dict:
        """Run backfill process for missing dates"""
        logger.info(f"🚀 Starting play-by-play backfill for {len(missing_dates)} dates")
        
        if dry_run:
            logger.info("🧪 DRY RUN MODE - No actual processing")
        
        results = []
        successful_dates = 0
        
        for date_str in missing_dates:
            logger.info(f"📅 Processing date {date_str}")
            result = self.process_missing_date(date_str, dry_run)
            results.append(result)
            
            if result.get('success') and not result.get('dry_run'):
                successful_dates += 1
        
        # Summary
        summary = {
            'backfill_summary': {
                'total_dates_requested': len(missing_dates),
                'successful_dates': successful_dates,
                'total_games_processed': self.processed_count,
                'total_games_failed': self.failed_count,
                'results': results
            }
        }
        
        logger.info(f"🎉 Backfill completed!")
        logger.info(f"   ✅ Successful dates: {successful_dates}/{len(missing_dates)}")
        logger.info(f"   ✅ Games processed: {self.processed_count}")
        logger.info(f"   ❌ Games failed: {self.failed_count}")
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='Backfill missing play-by-play dates')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without doing it')
    parser.add_argument('--list-missing', action='store_true', help='Only list missing dates without processing')
    
    args = parser.parse_args()
    
    try:
        backfill = PlayByPlayBackfill()
        
        # Identify missing dates
        missing_dates = backfill.identify_missing_dates(args.start_date, args.end_date)
        
        if not missing_dates:
            logger.info("✅ No missing dates found - play-by-play data appears complete!")
            return
        
        if args.list_missing:
            logger.info(f"📋 Missing dates ({len(missing_dates)}):")
            for date in missing_dates:
                schedule_filename = backfill.date_to_schedule_filename(date)
                logger.info(f"   - {date} (schedule: {schedule_filename})")
            return
        
        # Run backfill
        summary = backfill.run_backfill(missing_dates, args.dry_run)
        
        # Save summary report
        if not args.dry_run:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = Path(f"playbyplay_backfill_report_{timestamp}.json")
            
            try:
                import json
                with open(report_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                logger.info(f"📊 Summary report saved: {report_file}")
            except Exception as e:
                logger.warning(f"⚠️ Could not save summary report: {e}")
    
    except KeyboardInterrupt:
        logger.info("🛑 Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()