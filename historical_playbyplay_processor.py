#!/usr/bin/env python3
"""
Historical Play-by-Play Processor
One-time script to process all existing .txt files from BaseballData/SCANNED
and generate play-by-play data for historical games

Usage:
  python historical_playbyplay_processor.py                    # Process all SCANNED files
  python historical_playbyplay_processor.py --limit 10        # Process only first 10 files
  python historical_playbyplay_processor.py --resume          # Resume from where we left off
"""

import os
import glob
import json
import argparse
import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Import centralized configuration
from config import DATA_PATH

# Import playbyplay scraper functions
from playbyplay_scraper import (
    read_urls_from_file,
    transform_url_to_playbyplay,
    get_page_content,
    extract_playbyplay_data,
    save_playbyplay_data,
    create_summary_report
)

class HistoricalProcessor:
    def __init__(self):
        self.scanned_dir = DATA_PATH.parent / 'SCANNED'
        self.processed_log = self.scanned_dir / 'playbyplay_processed.json'
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_games': 0,
            'failed_games': 0,
            'total_plays': 0,
            'start_time': datetime.now().isoformat(),
            'errors': []
        }
    
    def load_processed_log(self) -> Dict:
        """Load log of already processed files"""
        if self.processed_log.exists():
            try:
                with open(self.processed_log, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not load processed log: {e}")
        
        return {
            'processed_files': [],
            'failed_files': [],
            'last_updated': None,
            'stats': {}
        }
    
    def save_processed_log(self, processed_log: Dict):
        """Save log of processed files"""
        processed_log['last_updated'] = datetime.now().isoformat()
        processed_log['stats'] = self.stats
        
        try:
            with open(self.processed_log, 'w') as f:
                json.dump(processed_log, f, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Could not save processed log: {e}")
    
    def get_schedule_files(self) -> List[Path]:
        """Get all .txt files from SCANNED directory"""
        if not self.scanned_dir.exists():
            print(f"❌ SCANNED directory not found: {self.scanned_dir}")
            return []
        
        # Find all .txt files in SCANNED directory
        txt_files = list(self.scanned_dir.glob("*.txt"))
        
        # Sort by filename to process chronologically
        txt_files.sort()
        
        print(f"📁 Found {len(txt_files)} .txt files in SCANNED directory")
        return txt_files
    
    def extract_date_from_filename(self, filepath: Path) -> str:
        """Extract date identifier from filename"""
        filename = filepath.stem  # Remove .txt extension
        
        # Handle various filename formats
        # Examples: april_7_2025.txt, may_12_2025.txt
        if filename.count('_') >= 2:
            return filename
        else:
            print(f"⚠️ Warning: Unusual filename format: {filename}")
            return filename
    
    def process_single_file(self, filepath: Path, processed_log: Dict) -> Dict:
        """Process a single schedule file"""
        filename = filepath.name
        date_identifier = self.extract_date_from_filename(filepath)
        
        print(f"\n🏟️ Processing: {filename}")
        print(f"📅 Date identifier: {date_identifier}")
        
        # Read URLs from file
        try:
            boxscore_urls = read_urls_from_file(str(filepath))
            playbyplay_urls = [transform_url_to_playbyplay(url) for url in boxscore_urls]
            
            if not playbyplay_urls:
                print(f"❌ No valid URLs found in {filename}")
                return {
                    'filename': filename,
                    'success': False,
                    'error': 'No valid URLs found',
                    'games_processed': 0,
                    'total_plays': 0
                }
            
            print(f"📊 Found {len(playbyplay_urls)} URLs to process")
            
        except Exception as e:
            error_msg = f"Error reading file {filename}: {e}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return {
                'filename': filename,
                'success': False,
                'error': str(e),
                'games_processed': 0,
                'total_plays': 0
            }
        
        # Process each game
        processed_games = []
        successful_games = 0
        total_plays = 0
        
        for i, url in enumerate(playbyplay_urls):
            print(f"  🌐 Processing game {i+1}/{len(playbyplay_urls)}: {url.split('/')[-1]}")
            
            try:
                # Fetch page content
                html = get_page_content(url)
                
                if html:
                    # Extract play-by-play data
                    game_data, game_id, away_team, home_team = extract_playbyplay_data(html, url)
                    
                    if game_data and game_data.get('plays'):
                        # Save data in both formats
                        save_playbyplay_data(game_data, date_identifier, game_id, away_team, home_team, 'json')
                        save_playbyplay_data(game_data, date_identifier, game_id, away_team, home_team, 'csv')
                        
                        play_count = len(game_data['plays'])
                        total_plays += play_count
                        successful_games += 1
                        
                        processed_games.append({
                            'game_id': game_id,
                            'url': url,
                            'success': True,
                            'plays': game_data.get('plays', []),
                            'metadata': game_data.get('metadata', {}),
                            'play_count': play_count,
                            'away_team': away_team,
                            'home_team': home_team,
                            'matchup': f"{away_team}_vs_{home_team}"
                        })
                        
                        print(f"    ✅ Processed game {away_team} vs {home_team} ({game_id}) - {play_count} plays")
                    else:
                        processed_games.append({
                            'game_id': game_id if game_id else 'unknown',
                            'url': url,
                            'success': False,
                            'error': 'No play data extracted',
                            'play_count': 0,
                            'away_team': away_team if away_team else 'UNKNOWN',
                            'home_team': home_team if home_team else 'UNKNOWN'
                        })
                        print(f"    ⚠️ No play data for game {away_team} vs {home_team} ({game_id})")
                else:
                    game_id = url.split('/')[-1]
                    processed_games.append({
                        'game_id': game_id,
                        'url': url,
                        'success': False,
                        'error': 'Failed to fetch page content',
                        'play_count': 0,
                        'away_team': 'UNKNOWN',
                        'home_team': 'UNKNOWN'
                    })
                    print(f"    ❌ Failed to fetch game {game_id}")
                
            except Exception as e:
                error_msg = f"Error processing {url}: {e}"
                print(f"    ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                
                game_id = url.split('/')[-1] if '/' in url else 'unknown'
                processed_games.append({
                    'game_id': game_id,
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
                print(f"    ⏳ Waiting {sleep_time:.2f}s...")
                time.sleep(sleep_time)
        
        # Create summary report for this date
        create_summary_report(processed_games, date_identifier)
        
        # Update statistics
        self.stats['successful_games'] += successful_games
        self.stats['failed_games'] += len(playbyplay_urls) - successful_games
        self.stats['total_plays'] += total_plays
        
        result = {
            'filename': filename,
            'success': True,
            'games_total': len(playbyplay_urls),
            'games_successful': successful_games,
            'games_failed': len(playbyplay_urls) - successful_games,
            'total_plays': total_plays,
            'processed_at': datetime.now().isoformat()
        }
        
        print(f"  📊 File summary: {successful_games}/{len(playbyplay_urls)} games, {total_plays} total plays")
        return result
    
    def process_all_files(self, limit: int = None, resume: bool = False) -> Dict:
        """Process all schedule files"""
        print("🏟️ Historical MLB Play-by-Play Processor")
        print("=" * 60)
        
        # Load processing log
        processed_log = self.load_processed_log()
        already_processed = set(processed_log.get('processed_files', []))
        
        # Get all schedule files
        schedule_files = self.get_schedule_files()
        
        if not schedule_files:
            print("❌ No schedule files found to process")
            return processed_log
        
        # Filter files if resuming
        if resume and already_processed:
            schedule_files = [f for f in schedule_files if f.name not in already_processed]
            print(f"📄 Resuming: {len(schedule_files)} files remaining to process")
        elif already_processed:
            print(f"📄 Found {len(already_processed)} previously processed files")
            print("   Use --resume to skip already processed files")
        
        # Apply limit if specified
        if limit:
            schedule_files = schedule_files[:limit]
            print(f"📄 Limited to first {len(schedule_files)} files")
        
        self.stats['total_files'] = len(schedule_files)
        
        if not schedule_files:
            print("✅ All files already processed!")
            return processed_log
        
        print(f"\n🚀 Starting processing of {len(schedule_files)} files...")
        start_time = time.time()
        
        # Process each file
        for i, filepath in enumerate(schedule_files, 1):
            print(f"\n--- File {i}/{len(schedule_files)} ---")
            
            result = self.process_single_file(filepath, processed_log)
            
            if result['success']:
                processed_log.setdefault('processed_files', []).append(filepath.name)
                self.stats['processed_files'] += 1
            else:
                processed_log.setdefault('failed_files', []).append({
                    'filename': filepath.name,
                    'error': result['error'],
                    'processed_at': datetime.now().isoformat()
                })
            
            # Save progress periodically
            if i % 5 == 0:
                self.save_processed_log(processed_log)
                print(f"💾 Progress saved ({i}/{len(schedule_files)} files)")
        
        # Final save and summary
        self.save_processed_log(processed_log)
        
        elapsed_time = time.time() - start_time
        print(f"\n🏁 Historical processing completed!")
        print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
        print(f"📁 Files processed: {self.stats['processed_files']}/{self.stats['total_files']}")
        print(f"🎮 Games processed: {self.stats['successful_games']}")
        print(f"❌ Games failed: {self.stats['failed_games']}")
        print(f"📋 Total plays extracted: {self.stats['total_plays']:,}")
        
        if self.stats['errors']:
            print(f"⚠️  Errors encountered: {len(self.stats['errors'])}")
            print("   Check the processed log for details")
        
        print(f"\n📁 Data saved in:")
        print(f"   JSON: {DATA_PATH / 'playbyplay'}")
        print(f"   CSV:  {DATA_PATH.parent / 'CSV_BACKUPS_PBP'}")
        print(f"   Log:  {self.processed_log}")
        
        return processed_log

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Historical Play-by-Play Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Process all SCANNED files
  %(prog)s --limit 10         # Process only first 10 files
  %(prog)s --resume           # Resume from where we left off
  %(prog)s --limit 5 --resume # Resume but limit to 5 files
        """
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of files to process (useful for testing)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Skip already processed files'
    )
    
    return parser.parse_args()

def main():
    """Main execution"""
    args = parse_arguments()
    
    processor = HistoricalProcessor()
    
    try:
        processed_log = processor.process_all_files(
            limit=args.limit,
            resume=args.resume
        )
        
        print("\n✅ Historical processing completed successfully!")
        
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        print("   Progress has been saved - use --resume to continue")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()