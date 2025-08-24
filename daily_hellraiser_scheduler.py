#!/usr/bin/env python3
"""
Daily Hellraiser Analysis Scheduler

Runs the Hellraiser analysis multiple times throughout the day to capture:
- Morning baseline with opening odds
- Pre-game updates with line movement
- Game-time final analysis

Handles different game start times (11 AM - 10 PM) intelligently.
"""

import subprocess
import datetime
import time
import json
import os
import shutil
from pathlib import Path

# Use centralized configuration for data paths
from config import PATHS

class HellraiserScheduler:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.log_file = self.script_dir / "logs" / "hellraiser_scheduler.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up archive directory for daily picks using centralized path
        self.archive_dir = PATHS['hellraiser'] / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        self.today = datetime.date.today().strftime("%Y-%m-%d")
        
    def log(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def run_analysis(self, run_type: str) -> bool:
        """Run the Hellraiser analysis script and archive results"""
        try:
            self.log(f"🔥 Starting {run_type} analysis run...")
            
            # Use the currently activated python (should be venv's python)
            python_executable = "python" if "VIRTUAL_ENV" in os.environ else "python3"
            
            result = subprocess.run([
                python_executable, 
                str(self.script_dir / "enhanced_comprehensive_hellraiser.py")
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"✅ {run_type} analysis completed successfully")
                # Archive the results with timestamp
                self.archive_analysis_results(run_type)
                return True
            else:
                self.log(f"❌ {run_type} analysis failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {run_type} analysis timed out after 5 minutes")
            return False
        except Exception as e:
            self.log(f"❌ {run_type} analysis error: {str(e)}")
            return False
    
    def archive_analysis_results(self, run_type: str):
        """Archive the current analysis results with timestamp"""
        try:
            hellraiser_dir = PATHS['hellraiser']
            current_analysis = hellraiser_dir / f"hellraiser_analysis_{self.today}.json"
            
            if current_analysis.exists():
                # Create timestamped filename
                timestamp = datetime.datetime.now().strftime("%H-%M-%S")
                run_type_clean = run_type.lower().replace(" ", "_")
                archive_filename = f"hellraiser_{self.today}_{timestamp}_{run_type_clean}.json"
                archive_path = self.archive_dir / archive_filename
                
                # Copy current analysis to archive
                shutil.copy2(current_analysis, archive_path)
                
                # Add metadata to archived file
                with open(archive_path, 'r') as f:
                    data = json.load(f)
                
                data['archiveMetadata'] = {
                    'archivedAt': datetime.datetime.now().isoformat(),
                    'runType': run_type,
                    'originalFilename': current_analysis.name,
                    'cronTriggered': True,  # Mark that this was cron-triggered
                    'gameContext': self.get_game_context()  # Add game timing context
                }
                
                with open(archive_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.log(f"📁 Archived analysis results: {archive_filename}")
            else:
                self.log(f"⚠️ No analysis results found to archive for {run_type}")
                
        except Exception as e:
            self.log(f"❌ Error archiving results: {str(e)}")
    
    def get_game_times_today(self) -> list:
        """Get today's game start times"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        lineup_file = PATHS['lineups'] / f"starting_lineups_{today}.json"
        
        game_times = []
        try:
            with open(lineup_file, 'r') as f:
                lineup_data = json.load(f)
            
            for game in lineup_data.get('games', []):
                game_time_str = game.get('gameTime', '')
                if game_time_str:
                    try:
                        # Parse time (format: "HH:MM")
                        hour, minute = map(int, game_time_str.split(':'))
                        game_time = datetime.time(hour, minute)
                        game_times.append(game_time)
                    except:
                        continue
                        
        except FileNotFoundError:
            self.log("⚠️ No lineup file found, using default schedule")
            # Default MLB game times
            game_times = [
                datetime.time(13, 0),  # 1 PM
                datetime.time(19, 0),  # 7 PM
                datetime.time(22, 0)   # 10 PM
            ]
        
        return sorted(game_times)
    
    def calculate_run_schedule(self) -> list:
        """Calculate optimal run times based on game schedule"""
        game_times = self.get_game_times_today()
        
        if not game_times:
            # No games today
            return []
        
        earliest_game = game_times[0]
        latest_game = game_times[-1]
        
        schedule = []
        
        # Morning baseline (2 hours before first game, but not before 8 AM)
        morning_time = datetime.time(max(8, earliest_game.hour - 2), 0)
        schedule.append(("Morning Baseline", morning_time))
        
        # Pre-game update (1 hour before first game)
        if earliest_game.hour > 9:  # Only if first game is after 10 AM
            pregame_time = datetime.time(earliest_game.hour - 1, 0)
            schedule.append(("Pre-Game Update", pregame_time))
        
        # Midday check (if there's a gap between early and late games)
        if len(game_times) > 1 and (latest_game.hour - earliest_game.hour) > 4:
            midday_time = datetime.time(earliest_game.hour + 2, 0)
            schedule.append(("Midday Check", midday_time))
        
        # Evening update (2 hours before last game if late games exist)
        if latest_game.hour >= 19:  # 7 PM or later
            evening_time = datetime.time(latest_game.hour - 2, 0)
            schedule.append(("Evening Update", evening_time))
        
        # Final check (30 minutes before last game)
        final_time = datetime.time(latest_game.hour, max(0, latest_game.minute - 30))
        schedule.append(("Final Check", final_time))
        
        return schedule
    
    def determine_run_type(self) -> str:
        """Intelligently determine what type of run this is based on game times"""
        game_times = self.get_game_times_today()
        now = datetime.datetime.now().time()
        
        if not game_times:
            return "No Games Scheduled"
        
        earliest_game = game_times[0]
        latest_game = game_times[-1]
        
        # Smart labeling based on timing relative to games
        if now < datetime.time(10, 0):
            return "Early Morning Baseline"
        elif now < datetime.time(earliest_game.hour - 1, 0):
            return "Pre-Game Analysis"
        elif now < datetime.time(earliest_game.hour + 1, 0):
            return "Game Time Update"
        elif len(game_times) > 1 and earliest_game.hour < now.hour < latest_game.hour:
            return "Midday Adjustment"
        elif now >= datetime.time(latest_game.hour - 2, 0):
            return "Evening Final Analysis"
        else:
            return "Scheduled Update"

    def get_game_context(self) -> dict:
        """Get context about today's games for metadata"""
        game_times = self.get_game_times_today()
        now = datetime.datetime.now().time()
        
        if not game_times:
            return {"gamesScheduled": False}
        
        earliest_game = game_times[0] 
        latest_game = game_times[-1]
        
        # Determine relationship to game times
        before_all_games = now < earliest_game
        after_all_games = now > latest_game
        between_games = earliest_game <= now <= latest_game
        
        return {
            "gamesScheduled": True,
            "gameCount": len(game_times),
            "earliestGame": earliest_game.strftime("%H:%M"),
            "latestGame": latest_game.strftime("%H:%M"),
            "analysisTime": now.strftime("%H:%M"),
            "timingContext": {
                "beforeAllGames": before_all_games,
                "betweenGames": between_games,
                "afterAllGames": after_all_games
            }
        }

    def run_scheduled_analysis(self):
        """Run analysis immediately with intelligent labeling"""
        # FIXED: Run analysis immediately instead of waiting for calculated times
        run_type = self.determine_run_type()
        game_context = self.get_game_context()
        
        self.log(f"📅 Game context: {game_context.get('gameCount', 0)} games today")
        if game_context.get('gamesScheduled'):
            self.log(f"🕐 Games: {game_context['earliestGame']} - {game_context['latestGame']}")
            self.log(f"🎯 Analysis type: {run_type}")
        
        # Run the analysis immediately with intelligent labeling
        success = self.run_analysis(run_type)
        return success

def main():
    """Main scheduler execution"""
    scheduler = HellraiserScheduler()
    
    # Check if we're in a valid time window (6 AM - 11 PM)
    now = datetime.datetime.now().time()
    if now < datetime.time(6, 0) or now > datetime.time(23, 0):
        scheduler.log("🌙 Outside analysis hours (6 AM - 11 PM)")
        return
    
    scheduler.log("🚀 Hellraiser Daily Scheduler Started")
    
    # Run immediate analysis or wait for next scheduled time
    has_scheduled_runs = scheduler.run_scheduled_analysis()
    
    if not has_scheduled_runs:
        # No more runs today, do a final analysis if none done recently
        scheduler.log("🔥 Running final analysis of the day")
        scheduler.run_analysis("End of Day")

if __name__ == "__main__":
    main()