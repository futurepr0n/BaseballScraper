#!/usr/bin/env python3
"""
Daily Weakspot Analysis Update
=============================

Integrates with the existing BaseballScraper daily processing pipeline
to generate updated weakspot analysis data. Runs after play-by-play data
has been scraped and processed.

This script:
1. Checks for new play-by-play data since last run
2. Generates updated weakspot rankings for all analysis types
3. Creates lineup-specific analysis for today's games
4. Updates JSON files for fast frontend loading

Designed to integrate with the existing daily_update.sh workflow.

Author: BaseballScraper Enhancement System
Date: August 2025
"""

import json
import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
import argparse
import glob
from typing import Dict, List, Optional, Tuple, Any

# Add the BaseballScraper directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weakspot_analyzer import WeakspotAnalyzer
from generate_weakspot_rankings import WeakspotRankingsGenerator

class DailyWeakspotUpdater:
    """Handles daily weakspot analysis updates"""
    
    def __init__(self, base_data_path: str):
        self.base_data_path = Path(base_data_path)
        self.output_path = self.base_data_path / "weakspot_analysis"
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.analyzer = WeakspotAnalyzer(str(base_data_path))
        self.generator = WeakspotRankingsGenerator(str(base_data_path), str(self.output_path))
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def get_todays_date(self) -> str:
        """Get today's date in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_recent_date_range(self, days: int = 30) -> tuple:
        """Get date range for recent analysis (last N days)"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    def check_for_new_playbyplay_data(self) -> bool:
        """
        Check if there's new play-by-play data since last update
        
        Returns:
            True if new data is available, False otherwise
        """
        playbyplay_path = self.base_data_path / "playbyplay"
        
        if not playbyplay_path.exists():
            self.logger.warning("Play-by-play data directory not found")
            return False
        
        # Check for files modified in the last 24 hours
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        recent_files = []
        for file_path in playbyplay_path.glob("*_vs_*_playbyplay_*.json"):
            if datetime.fromtimestamp(file_path.stat().st_mtime) > yesterday:
                recent_files.append(file_path)
        
        self.logger.info(f"Found {len(recent_files)} new play-by-play files")
        return len(recent_files) > 0
    
    def load_todays_lineups(self) -> Dict:
        """
        Load today's starting lineups from scraped data
        
        Returns:
            Dictionary of today's lineup data
        """
        today = self.get_todays_date()
        
        # Look for today's lineup data in various possible locations
        lineup_files = [
            self.base_data_path / "lineups" / f"lineups_{today}.json",
            self.base_data_path / f"lineups_{today}.json",
            self.base_data_path / "2025" / f"{today.replace('-', '')}_lineups.json"
        ]
        
        for lineup_file in lineup_files:
            if lineup_file.exists():
                try:
                    with open(lineup_file, 'r') as f:
                        lineup_data = json.load(f)
                    self.logger.info(f"Loaded today's lineups from {lineup_file}")
                    return lineup_data
                except Exception as e:
                    self.logger.warning(f"Error loading lineups from {lineup_file}: {e}")
        
        self.logger.warning("Could not find today's lineup data")
        return {}
    
    def generate_todays_weakspot_opportunities(self, lineup_data: Dict) -> Dict:
        """
        Generate weakspot opportunities for today's games
        
        Args:
            lineup_data: Today's lineup information
        
        Returns:
            Dictionary of today's weakspot opportunities
        """
        if not lineup_data:
            return {"error": "No lineup data available for today"}
        
        self.logger.info("Generating today's weakspot opportunities...")
        
        todays_opportunities = {
            "analysis_date": self.get_todays_date(),
            "generated_at": datetime.now().isoformat(),
            "games": []
        }
        
        # Process each game
        for game_data in lineup_data.get('games', []):
            home_team = game_data.get('homeTeam')
            away_team = game_data.get('awayTeam')
            
            if not home_team or not away_team:
                continue
            
            # Get starting pitchers
            home_pitcher = game_data.get('homePitcher')
            away_pitcher = game_data.get('awayPitcher')
            
            game_analysis = {
                "game_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_pitcher": home_pitcher,
                    "away_pitcher": away_pitcher,
                    "venue": game_data.get('venue'),
                    "game_time": game_data.get('gameTime')
                },
                "weakspot_opportunities": {}
            }
            
            # Analyze home pitcher vs away team lineup
            if home_pitcher and away_team:
                home_pitcher_analysis = self.analyze_pitcher_vs_todays_lineup(
                    home_pitcher, 
                    game_data.get('awayLineup', []),
                    away_team
                )
                game_analysis["weakspot_opportunities"]["home_pitcher_vulnerabilities"] = home_pitcher_analysis
            
            # Analyze away pitcher vs home team lineup
            if away_pitcher and home_team:
                away_pitcher_analysis = self.analyze_pitcher_vs_todays_lineup(
                    away_pitcher,
                    game_data.get('homeLineup', []),
                    home_team
                )
                game_analysis["weakspot_opportunities"]["away_pitcher_vulnerabilities"] = away_pitcher_analysis
            
            todays_opportunities["games"].append(game_analysis)
        
        return todays_opportunities
    
    def analyze_pitcher_vs_todays_lineup(self, pitcher_name: str, lineup: List, team: str) -> Dict:
        """
        Analyze specific pitcher against today's opposing lineup
        
        Args:
            pitcher_name: Name of the starting pitcher
            lineup: List of batters in lineup order
            team: Team name
        
        Returns:
            Dictionary of vulnerability analysis for this specific matchup
        """
        if not pitcher_name or not lineup:
            return {"error": "Insufficient data for analysis"}
        
        # Get recent weakspot analysis for this pitcher (last 30 days)
        date_range = self.get_recent_date_range(30)
        pitcher_analysis = self.analyzer.analyze_pitcher_weakspots(pitcher_name, date_range)
        
        if "error" in pitcher_analysis:
            return pitcher_analysis
        
        # Map lineup positions to vulnerabilities
        lineup_vulnerabilities = pitcher_analysis.get('lineup_vulnerabilities', {})
        
        position_analysis = {}
        high_opportunity_positions = []
        
        for i, batter in enumerate(lineup[:9], 1):  # Standard 9-batter lineup
            position_key = f"position_{i}"
            
            if position_key in lineup_vulnerabilities:
                vuln_data = lineup_vulnerabilities[position_key]
                vulnerability_score = vuln_data.get('vulnerability_score', 0)
                confidence = vuln_data.get('confidence', 0)
                
                position_analysis[f"position_{i}"] = {
                    "batter": batter,
                    "vulnerability_score": vulnerability_score,
                    "confidence": confidence,
                    "sample_size": vuln_data.get('sample_size', 0),
                    "recommendation": self._generate_position_recommendation(vulnerability_score, confidence)
                }
                
                # Flag high-opportunity positions (high vulnerability + high confidence)
                if vulnerability_score > 60 and confidence > 0.7:
                    high_opportunity_positions.append({
                        "position": i,
                        "batter": batter,
                        "vulnerability_score": vulnerability_score,
                        "confidence": confidence
                    })
        
        # Analyze inning patterns for game strategy
        inning_patterns = pitcher_analysis.get('inning_patterns', {})
        most_vulnerable_inning = None
        max_inning_score = 0
        
        for inning_key, inning_data in inning_patterns.items():
            score = inning_data.get('vulnerability_score', 0)
            if score > max_inning_score:
                max_inning_score = score
                most_vulnerable_inning = inning_key
        
        return {
            "pitcher": pitcher_name,
            "opposing_team": team,
            "position_analysis": position_analysis,
            "high_opportunity_positions": high_opportunity_positions,
            "most_vulnerable_inning": most_vulnerable_inning,
            "inning_vulnerability_score": max_inning_score,
            "overall_confidence": pitcher_analysis.get('overall_confidence', 0),
            "analysis_summary": {
                "total_positions_analyzed": len(position_analysis),
                "high_opportunity_count": len(high_opportunity_positions),
                "avg_vulnerability": round(sum(p.get('vulnerability_score', 0) for p in position_analysis.values()) / len(position_analysis) if position_analysis else 0, 2),
                "recommendation": self._generate_overall_recommendation(high_opportunity_positions, max_inning_score)
            }
        }
    
    def _generate_position_recommendation(self, vulnerability_score: float, confidence: float) -> str:
        """Generate recommendation text for a lineup position"""
        if vulnerability_score > 70 and confidence > 0.8:
            return "Strong target - High vulnerability with high confidence"
        elif vulnerability_score > 60 and confidence > 0.6:
            return "Good opportunity - Moderate vulnerability with decent confidence"
        elif vulnerability_score > 50:
            return "Potential target - Some vulnerability detected"
        else:
            return "Low priority - Limited vulnerability shown"
    
    def _generate_overall_recommendation(self, high_opportunities: List, inning_score: float) -> str:
        """Generate overall game recommendation"""
        if len(high_opportunities) >= 3:
            return f"High exploitation potential - {len(high_opportunities)} strong lineup targets identified"
        elif len(high_opportunities) >= 1:
            return f"Moderate exploitation potential - {len(high_opportunities)} good lineup targets"
        elif inning_score > 60:
            return f"Inning-based strategy recommended - Target late innings (vulnerability score: {inning_score})"
        else:
            return "Limited exploitation opportunities detected"
    
    def run_full_update(self, force_update: bool = False) -> Dict:
        """
        Run complete daily weakspot update
        
        Args:
            force_update: Force update even if no new data detected
        
        Returns:
            Dictionary with update results
        """
        self.logger.info("Starting daily weakspot analysis update...")
        
        update_results = {
            "update_date": self.get_todays_date(),
            "update_timestamp": datetime.now().isoformat(),
            "components_updated": [],
            "errors": []
        }
        
        # Check for new data
        has_new_data = self.check_for_new_playbyplay_data()
        if not has_new_data and not force_update:
            self.logger.info("No new play-by-play data detected. Use --force to update anyway.")
            update_results["status"] = "skipped"
            update_results["reason"] = "no_new_data"
            return update_results
        
        # Generate updated rankings (last 30 days)
        try:
            self.logger.info("Generating updated weakspot rankings...")
            date_range = self.get_recent_date_range(30)
            ranking_results = self.generator.generate_all_rankings(date_range)
            update_results["components_updated"].append("weakspot_rankings")
            update_results["ranking_files"] = ranking_results
        except Exception as e:
            error_msg = f"Failed to generate rankings: {e}"
            self.logger.error(error_msg)
            update_results["errors"].append(error_msg)
        
        # Generate today's specific opportunities
        try:
            self.logger.info("Analyzing today's lineup opportunities...")
            lineup_data = self.load_todays_lineups()
            todays_opportunities = self.generate_todays_weakspot_opportunities(lineup_data)
            
            # Save today's opportunities
            today_file = self.output_path / f"todays_opportunities_{self.get_todays_date()}.json"
            with open(today_file, 'w') as f:
                json.dump(todays_opportunities, f, indent=2)
            
            # Also save as "latest" for easy access
            latest_file = self.output_path / "todays_opportunities_latest.json"
            with open(latest_file, 'w') as f:
                json.dump(todays_opportunities, f, indent=2)
            
            update_results["components_updated"].append("todays_opportunities")
            update_results["todays_opportunities_file"] = str(today_file)
            
        except Exception as e:
            error_msg = f"Failed to generate today's opportunities: {e}"
            self.logger.error(error_msg)
            update_results["errors"].append(error_msg)
        
        # Update status
        if update_results["errors"]:
            update_results["status"] = "completed_with_errors"
        else:
            update_results["status"] = "completed_successfully"
        
        # Save update log
        update_log_file = self.output_path / "daily_update_log.json"
        with open(update_log_file, 'w') as f:
            json.dump(update_results, f, indent=2)
        
        self.logger.info(f"Daily weakspot update completed. Status: {update_results['status']}")
        return update_results

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('daily_weakspot_update.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Daily Weakspot Analysis Update')
    parser.add_argument('--data-path', default='../BaseballData/data',
                       help='Path to baseball data directory')
    parser.add_argument('--force', action='store_true',
                       help='Force update even if no new data detected')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        updater = DailyWeakspotUpdater(args.data_path)
        results = updater.run_full_update(args.force)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("DAILY WEAKSPOT UPDATE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Status: {results.get('status', 'unknown')}")
        logger.info(f"Components Updated: {', '.join(results.get('components_updated', []))}")
        
        if results.get('errors'):
            logger.error("Errors encountered:")
            for error in results['errors']:
                logger.error(f"  - {error}")
        
        if results.get('ranking_files'):
            logger.info("Generated ranking files:")
            for analysis_type, file_path in results['ranking_files'].items():
                logger.info(f"  - {analysis_type}: {file_path}")
        
        if results.get('todays_opportunities_file'):
            logger.info(f"Today's opportunities: {results['todays_opportunities_file']}")
        
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Daily weakspot update failed: {e}")
        raise

if __name__ == "__main__":
    main()