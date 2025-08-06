#!/usr/bin/env python3
"""
MLB Lineup Scheduler
Handles periodic updates of starting lineup data and manages day transitions.
Designed to run as a cron job every 15-30 minutes during game hours.
"""

import json
import datetime
import os
import glob
import logging
import sys
from typing import Dict, Optional
from fetch_starting_lineups import StartingLineupFetcher

# Import centralized configuration
from config import PATHS

class LineupScheduler:
    def __init__(self):
        self.lineups_dir = str(PATHS['lineups'])
        self.log_file = "lineup_updates.log"
        self.setup_logging()
        
        # Ensure lineups directory exists
        os.makedirs(self.lineups_dir, exist_ok=True)
        
        self.fetcher = StartingLineupFetcher()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_todays_lineup_file(self) -> str:
        """Get today's lineup file path"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.lineups_dir, f"starting_lineups_{today}.json")
    
    def load_existing_lineup_data(self, filepath: str) -> Optional[Dict]:
        """Load existing lineup data from file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading existing lineup data: {e}")
        return None
    
    def detect_changes(self, old_data: Dict, new_data: Dict) -> Dict:
        """Detect changes between old and new lineup data"""
        changes = {
            "pitcher_changes": [],
            "status_changes": [],
            "new_games": [],
            "time_changes": [],
            "total_changes": 0
        }
        
        if not old_data:
            changes["new_games"] = new_data.get("games", [])
            changes["total_changes"] = len(changes["new_games"])
            return changes
        
        old_games = {g.get("gameId", ""): g for g in old_data.get("games", [])}
        new_games = {g.get("gameId", ""): g for g in new_data.get("games", [])}
        
        # Check for new games
        for game_id, game in new_games.items():
            if game_id not in old_games:
                changes["new_games"].append(game)
                changes["total_changes"] += 1
        
        # Check for changes in existing games
        for game_id, new_game in new_games.items():
            if game_id in old_games:
                old_game = old_games[game_id]
                
                # Check pitcher changes
                old_home_pitcher = old_game.get("pitchers", {}).get("home", {}).get("name", "")
                new_home_pitcher = new_game.get("pitchers", {}).get("home", {}).get("name", "")
                old_away_pitcher = old_game.get("pitchers", {}).get("away", {}).get("name", "")
                new_away_pitcher = new_game.get("pitchers", {}).get("away", {}).get("name", "")
                
                if old_home_pitcher != new_home_pitcher:
                    changes["pitcher_changes"].append({
                        "game": game_id,
                        "team": "home",
                        "old_pitcher": old_home_pitcher,
                        "new_pitcher": new_home_pitcher
                    })
                    changes["total_changes"] += 1
                
                if old_away_pitcher != new_away_pitcher:
                    changes["pitcher_changes"].append({
                        "game": game_id,
                        "team": "away", 
                        "old_pitcher": old_away_pitcher,
                        "new_pitcher": new_away_pitcher
                    })
                    changes["total_changes"] += 1
                
                # Check status changes
                old_status = old_game.get("status", "")
                new_status = new_game.get("status", "")
                if old_status != new_status:
                    changes["status_changes"].append({
                        "game": game_id,
                        "old_status": old_status,
                        "new_status": new_status
                    })
                    changes["total_changes"] += 1
                
                # Check time changes
                old_time = old_game.get("gameTime", "")
                new_time = new_game.get("gameTime", "")
                if old_time != new_time:
                    changes["time_changes"].append({
                        "game": game_id,
                        "old_time": old_time,
                        "new_time": new_time
                    })
                    changes["total_changes"] += 1
        
        return changes
    
    def update_lineup_data(self, old_data: Dict, new_data: Dict, changes: Dict) -> Dict:
        """Update lineup data with change tracking"""
        # Increment update count
        update_count = old_data.get("updateCount", 0) + 1 if old_data else 1
        new_data["updateCount"] = update_count
        
        # Add update records
        if not new_data.get("updates"):
            new_data["updates"] = []
        
        # Record changes
        timestamp = datetime.datetime.now().isoformat()
        for change in changes["pitcher_changes"]:
            new_data["updates"].append({
                "timestamp": timestamp,
                "type": "pitcher_change",
                "description": f"{change['team']} pitcher changed from {change['old_pitcher']} to {change['new_pitcher']}",
                "gameId": change["game"],
                "previousValue": change["old_pitcher"],
                "newValue": change["new_pitcher"]
            })
        
        for change in changes["status_changes"]:
            new_data["updates"].append({
                "timestamp": timestamp,
                "type": "status_change", 
                "description": f"Game status changed from {change['old_status']} to {change['new_status']}",
                "gameId": change["game"],
                "previousValue": change["old_status"],
                "newValue": change["new_status"]
            })
        
        # Generate alerts for significant changes
        alerts = []
        for change in changes["pitcher_changes"]:
            if change["old_pitcher"] != "TBD" and change["new_pitcher"] != "TBD":
                alerts.append({
                    "type": "pitcher_scratch",
                    "message": f"{change['old_pitcher']} scratched - {change['new_pitcher']} now starting",
                    "timestamp": timestamp,
                    "gameId": change["game"]
                })
        
        new_data["alerts"] = alerts
        
        return new_data
    
    def cleanup_old_lineup_files(self, days_to_keep: int = 7):
        """Remove lineup files older than specified days"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            pattern = os.path.join(self.lineups_dir, "starting_lineups_*.json")
            
            removed_count = 0
            for filepath in glob.glob(pattern):
                filename = os.path.basename(filepath)
                # Extract date from filename: starting_lineups_YYYY-MM-DD.json
                if "starting_lineups_" in filename:
                    date_str = filename.replace("starting_lineups_", "").replace(".json", "")
                    try:
                        file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        if file_date < cutoff_date:
                            os.remove(filepath)
                            removed_count += 1
                            self.logger.info(f"Removed old lineup file: {filename}")
                    except ValueError:
                        continue
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old lineup files")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old files: {e}")
    
    def is_game_day(self) -> bool:
        """Check if today is likely to have MLB games"""
        today = datetime.datetime.now()
        
        # MLB season typically runs March-October
        if today.month < 3 or today.month > 10:
            return False
        
        # All-Star break is typically mid-July (skip for simplicity)
        return True
    
    def should_update(self, existing_data: Optional[Dict]) -> bool:
        """Determine if we should fetch new data"""
        if not existing_data:
            return True
        
        # Check last update time
        last_updated_str = existing_data.get("lastUpdated", "")
        if last_updated_str:
            try:
                last_updated = datetime.datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                now = datetime.datetime.now()
                
                # Always update if more than 2 hours old
                if (now - last_updated.replace(tzinfo=None)).total_seconds() > 7200:
                    return True
                
                # Update more frequently during peak lineup posting hours (10 AM - 6 PM ET)
                if 10 <= now.hour <= 18:
                    if (now - last_updated.replace(tzinfo=None)).total_seconds() > 1800:  # 30 minutes
                        return True
                
                # Less frequent updates outside peak hours
                if (now - last_updated.replace(tzinfo=None)).total_seconds() > 3600:  # 1 hour
                    return True
                    
            except Exception as e:
                self.logger.error(f"Error parsing last updated time: {e}")
                return True
        
        return False
    
    def run_update(self) -> bool:
        """Run the main update process"""
        try:
            # Check if it's likely a game day
            if not self.is_game_day():
                self.logger.info("Not likely a game day, skipping update")
                return True
            
            # Get current file path
            lineup_file = self.get_todays_lineup_file()
            
            # Load existing data
            existing_data = self.load_existing_lineup_data(lineup_file)
            
            # Check if we should update
            if not self.should_update(existing_data):
                self.logger.info("No update needed based on timing")
                return True
            
            self.logger.info("Starting lineup data update...")
            
            # Fetch new data
            new_data = self.fetcher.fetch_todays_lineups()
            if not new_data:
                self.logger.error("Failed to fetch new lineup data")
                return False
            
            # Detect changes
            changes = self.detect_changes(existing_data, new_data)
            
            # Update data with change tracking
            updated_data = self.update_lineup_data(existing_data, new_data, changes)
            
            # Save updated data
            try:
                with open(lineup_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"✅ Updated lineup data with {changes['total_changes']} changes")
                
                # Log specific changes
                if changes["pitcher_changes"]:
                    for change in changes["pitcher_changes"]:
                        self.logger.info(f"🔄 Pitcher change: {change['old_pitcher']} → {change['new_pitcher']}")
                
                if changes["new_games"]:
                    self.logger.info(f"🆕 Found {len(changes['new_games'])} new games")
                
                # Cleanup old files
                self.cleanup_old_lineup_files()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving updated lineup data: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in update process: {e}")
            return False

def main():
    """Main execution function"""
    scheduler = LineupScheduler()
    
    try:
        success = scheduler.run_update()
        if success:
            scheduler.logger.info("✅ Lineup update completed successfully")
        else:
            scheduler.logger.error("❌ Lineup update failed")
        
        return success
        
    except Exception as e:
        scheduler.logger.error(f"Fatal error in lineup scheduler: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)