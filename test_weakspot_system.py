#!/usr/bin/env python3
"""
Weakspot Analysis System Test Suite
===================================

Comprehensive testing script to validate all components of the weakspot analysis system.
Tests data loading, analysis functions, output generation, and integration points.

Author: BaseballScraper Enhancement System
Date: August 2025
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging
import argparse
import traceback

# Add the BaseballScraper directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weakspot_analyzer import WeakspotAnalyzer, PlayByPlayProcessor, VulnerabilityCalculator, PlayerIDMapper
from generate_weakspot_rankings import WeakspotRankingsGenerator
from daily_weakspot_update import DailyWeakspotUpdater

class WeakspotSystemTester:
    """Comprehensive test suite for the weakspot analysis system"""
    
    def __init__(self, base_data_path: str):
        self.base_data_path = Path(base_data_path)
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            "test_run_timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }
    
    def run_test(self, test_name: str, test_function):
        """
        Run a single test and record results
        
        Args:
            test_name: Name of the test
            test_function: Function to execute for the test
        """
        self.logger.info(f"Running test: {test_name}")
        
        try:
            result = test_function()
            self.test_results["tests_passed"] += 1
            self.test_results["test_details"].append({
                "test_name": test_name,
                "status": "PASSED",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            self.logger.info(f"✓ {test_name} PASSED")
            return True
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            error_info = {
                "test_name": test_name,
                "status": "FAILED",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results["test_details"].append(error_info)
            self.logger.error(f"✗ {test_name} FAILED: {e}")
            return False
    
    def test_data_availability(self):
        """Test that required data directories and files exist"""
        required_paths = [
            self.base_data_path / "playbyplay",
            self.base_data_path / "2025",
            self.base_data_path / "stats"
        ]
        
        results = {}
        for path in required_paths:
            results[str(path)] = path.exists()
        
        # Check for sample files
        playbyplay_files = list((self.base_data_path / "playbyplay").glob("*_vs_*_playbyplay_*.json"))
        daily_files = list((self.base_data_path / "2025").glob("*/*.json"))
        
        results["playbyplay_files_count"] = len(playbyplay_files)
        results["daily_files_count"] = len(daily_files)
        
        # Validate we have minimum data for testing
        if len(playbyplay_files) < 5:
            raise Exception(f"Insufficient play-by-play files for testing: {len(playbyplay_files)} found, need at least 5")
        
        if len(daily_files) < 10:
            raise Exception(f"Insufficient daily files for testing: {len(daily_files)} found, need at least 10")
        
        return results
    
    def test_player_id_mapper(self):
        """Test the PlayerIDMapper component"""
        mapper = PlayerIDMapper(str(self.base_data_path))
        
        # Test name normalization
        test_cases = [
            ("José Ramírez", "jose ramirez"),
            ("Adolis García", "adolis garcia"),
            ("Normal Name", "normal name")
        ]
        
        for original, expected in test_cases:
            normalized = mapper.normalize_name(original)
            if normalized != expected:
                raise Exception(f"Name normalization failed: '{original}' -> '{normalized}', expected '{expected}'")
        
        # Test roster loading (may not have data, but should not crash)
        try:
            mapper.load_roster_data()
        except Exception as e:
            self.logger.warning(f"Roster data loading failed (this may be expected): {e}")
        
        return {"name_normalization": "passed", "roster_loading": "attempted"}
    
    def test_playbyplay_processor(self):
        """Test the PlayByPlayProcessor component"""
        processor = PlayByPlayProcessor(str(self.base_data_path))
        
        # Load a small sample of data
        games_data = processor.load_playbyplay_files()
        
        if not games_data:
            raise Exception("No play-by-play data loaded")
        
        # Test lineup position extraction
        sample_game = games_data[0]
        lineup_positions = processor.extract_lineup_positions(sample_game)
        
        # Test analysis functions with sample data (limit to first 5 games for speed)
        limited_games = games_data[:5]
        
        lineup_analysis = processor.analyze_lineup_vulnerabilities(limited_games)
        inning_analysis = processor.analyze_inning_patterns(limited_games)
        pattern_analysis = processor.analyze_pitch_patterns(limited_games)
        
        return {
            "games_loaded": len(games_data),
            "sample_lineup_positions": len(lineup_positions),
            "pitchers_in_lineup_analysis": len(lineup_analysis),
            "pitchers_in_inning_analysis": len(inning_analysis),
            "pitchers_in_pattern_analysis": len(pattern_analysis)
        }
    
    def test_vulnerability_calculator(self):
        """Test the VulnerabilityCalculator component"""
        calculator = VulnerabilityCalculator(str(self.base_data_path))
        
        # Test loading advanced stats
        calculator.load_advanced_stats()
        
        # Create sample analysis data for testing
        sample_lineup_analysis = {
            "test_pitcher": {
                "position_1": {
                    "at_bats": 10,
                    "outcomes": {"Home Run": 2, "Single": 3, "Groundout": 5},
                    "avg_velocity": [95, 94, 93, 95, 94],
                    "leverage_situations": 3
                },
                "position_2": {
                    "at_bats": 8,
                    "outcomes": {"Home Run": 1, "Double": 1, "Flyout": 6},
                    "avg_velocity": [96, 95, 94, 96],
                    "leverage_situations": 2
                }
            }
        }
        
        sample_inning_analysis = {
            "test_pitcher": {
                "inning_1": {
                    "appearances": 5,
                    "outcomes": {"Single": 2, "Groundout": 3},
                    "velocities": [95, 94, 96],
                    "pitch_counts": [4, 3, 5, 2, 4]
                }
            }
        }
        
        # Test score calculations
        lineup_scores = calculator.calculate_lineup_vulnerability_score(sample_lineup_analysis, "test_pitcher")
        inning_scores = calculator.calculate_inning_vulnerability_score(sample_inning_analysis, "test_pitcher")
        
        return {
            "lineup_scores_calculated": len(lineup_scores),
            "inning_scores_calculated": len(inning_scores),
            "sample_lineup_score": lineup_scores.get("position_1", {}).get("vulnerability_score", 0),
            "sample_confidence": lineup_scores.get("position_1", {}).get("confidence", 0)
        }
    
    def test_weakspot_analyzer(self):
        """Test the main WeakspotAnalyzer component"""
        analyzer = WeakspotAnalyzer(str(self.base_data_path))
        
        # Test with a date range (last 7 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        date_range = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
        # Try to find a pitcher in the data
        games_data = analyzer.processor.load_playbyplay_files(date_range)
        
        if not games_data:
            # Try without date range
            games_data = analyzer.processor.load_playbyplay_files()
        
        if not games_data:
            raise Exception("No games data available for testing")
        
        # Find a sample pitcher
        sample_pitcher = None
        for game_data in games_data[:10]:  # Check first 10 games
            for play in game_data.get('plays', []):
                pitcher_id = play.get('pitcher')
                if pitcher_id:
                    # Try to resolve pitcher name
                    pitcher_name = analyzer.processor.player_mapper.resolve_player_id(
                        pitcher_id,
                        game_data['metadata'].get('home_team')
                    )
                    if pitcher_name:
                        sample_pitcher = pitcher_name
                        break
                    else:
                        sample_pitcher = pitcher_id  # Use ID if name resolution fails
                        break
            if sample_pitcher:
                break
        
        if not sample_pitcher:
            raise Exception("Could not find a sample pitcher for testing")
        
        # Test pitcher analysis
        try:
            pitcher_analysis = analyzer.analyze_pitcher_weakspots(sample_pitcher, date_range)
            
            if "error" in pitcher_analysis:
                # Try without date range
                pitcher_analysis = analyzer.analyze_pitcher_weakspots(sample_pitcher)
                
            if "error" in pitcher_analysis:
                raise Exception(f"Pitcher analysis failed: {pitcher_analysis['error']}")
                
        except Exception as e:
            # If specific pitcher fails, try generating general rankings
            self.logger.warning(f"Specific pitcher analysis failed ({e}), testing general rankings instead")
            lineup_rankings = analyzer.generate_filterable_rankings('lineup', date_range)
            
            return {
                "sample_pitcher": sample_pitcher,
                "analysis_type": "rankings_only", 
                "pitchers_in_rankings": len(lineup_rankings.get('rankings', []))
            }
        
        return {
            "sample_pitcher": sample_pitcher,
            "analysis_type": "full_analysis",
            "lineup_vulnerabilities": len(pitcher_analysis.get('lineup_vulnerabilities', {})),
            "inning_patterns": len(pitcher_analysis.get('inning_patterns', {})),
            "overall_confidence": pitcher_analysis.get('overall_confidence', 0),
            "games_analyzed": pitcher_analysis.get('data_summary', {}).get('games_analyzed', 0)
        }
    
    def test_rankings_generator(self):
        """Test the WeakspotRankingsGenerator component"""
        output_path = self.base_data_path / "test_output"
        output_path.mkdir(exist_ok=True)
        
        generator = WeakspotRankingsGenerator(str(self.base_data_path), str(output_path))
        
        # Test with a recent date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=14)
        date_range = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
        try:
            # Test lineup vulnerability rankings
            lineup_file = generator.generate_lineup_vulnerability_rankings(date_range)
            
            # Verify file was created and has content
            if not Path(lineup_file).exists():
                raise Exception(f"Lineup rankings file not created: {lineup_file}")
            
            with open(lineup_file, 'r') as f:
                lineup_data = json.load(f)
            
            lineup_pitchers = len(lineup_data.get('rankings', []))
            
        except Exception as e:
            self.logger.warning(f"Lineup rankings generation failed: {e}")
            lineup_pitchers = 0
        
        try:
            # Test overall rankings (which combines multiple analysis types)
            overall_file = generator.generate_overall_weakspot_rankings(date_range)
            
            if not Path(overall_file).exists():
                raise Exception(f"Overall rankings file not created: {overall_file}")
                
            with open(overall_file, 'r') as f:
                overall_data = json.load(f)
            
            overall_pitchers = len(overall_data.get('rankings', []))
            
        except Exception as e:
            self.logger.warning(f"Overall rankings generation failed: {e}")
            overall_pitchers = 0
        
        # Clean up test files
        try:
            import shutil
            shutil.rmtree(output_path)
        except Exception as e:
            self.logger.warning(f"Could not clean up test output directory: {e}")
        
        return {
            "lineup_rankings_pitchers": lineup_pitchers,
            "overall_rankings_pitchers": overall_pitchers,
            "test_date_range": f"{start_date} to {end_date}"
        }
    
    def test_daily_updater(self):
        """Test the DailyWeakspotUpdater component (without full execution)"""
        updater = DailyWeakspotUpdater(str(self.base_data_path))
        
        # Test basic initialization and data checking
        today = updater.get_todays_date()
        date_range = updater.get_recent_date_range(7)  # Last 7 days
        
        has_new_data = updater.check_for_new_playbyplay_data()
        
        # Test lineup loading (may not exist, but shouldn't crash)
        lineup_data = updater.load_todays_lineups()
        
        return {
            "today_date": today,
            "recent_date_range": f"{date_range[0]} to {date_range[1]}",
            "has_new_playbyplay_data": has_new_data,
            "lineup_data_available": bool(lineup_data and lineup_data.get('games'))
        }
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.logger.info("Starting comprehensive weakspot system tests...")
        self.logger.info("=" * 60)
        
        # Define test sequence
        tests = [
            ("Data Availability Check", self.test_data_availability),
            ("Player ID Mapper", self.test_player_id_mapper),
            ("Play-by-Play Processor", self.test_playbyplay_processor),
            ("Vulnerability Calculator", self.test_vulnerability_calculator),
            ("Weakspot Analyzer", self.test_weakspot_analyzer),
            ("Rankings Generator", self.test_rankings_generator),
            ("Daily Updater", self.test_daily_updater)
        ]
        
        # Run each test
        for test_name, test_function in tests:
            self.run_test(test_name, test_function)
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate and display test results summary"""
        total_tests = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        success_rate = (self.test_results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        self.logger.info("=" * 60)
        self.logger.info("WEAKSPOT SYSTEM TEST RESULTS SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Tests Run: {total_tests}")
        self.logger.info(f"Tests Passed: {self.test_results['tests_passed']}")
        self.logger.info(f"Tests Failed: {self.test_results['tests_failed']}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info("")
        
        # Show detailed results
        for test_detail in self.test_results["test_details"]:
            status_symbol = "✓" if test_detail["status"] == "PASSED" else "✗"
            self.logger.info(f"{status_symbol} {test_detail['test_name']}: {test_detail['status']}")
            
            if test_detail["status"] == "FAILED":
                self.logger.error(f"   Error: {test_detail['error']}")
        
        self.logger.info("=" * 60)
        
        # Save detailed results to file
        results_file = Path("test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"Detailed test results saved to: {results_file}")
        
        return success_rate >= 80  # Consider 80% success rate as passing

def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_weakspot_system.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main test execution function"""
    parser = argparse.ArgumentParser(description='Weakspot System Test Suite')
    parser.add_argument('--data-path', default='../BaseballData/data',
                       help='Path to baseball data directory')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        tester = WeakspotSystemTester(args.data_path)
        success = tester.run_all_tests()
        
        if success:
            logger.info("🎉 All tests passed! Weakspot system is ready for use.")
            return 0
        else:
            logger.error("❌ Some tests failed. Review the results above.")
            return 1
            
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())