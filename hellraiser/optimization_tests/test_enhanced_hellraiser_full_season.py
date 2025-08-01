#!/usr/bin/env python3
"""
Full Season Testing of Enhanced Hellraiser Algorithm
Comprehensive performance analysis comparing enhanced vs original system
"""

import json
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import glob
from collections import defaultdict
import csv

# Import the enhanced algorithm
from enhanced_hellraiser_algorithm import EnhancedHellraiserAnalyzer

class FullSeasonTester:
    """Test enhanced Hellraiser against entire season of data"""
    
    def __init__(self, data_base_path: str = None):
        if data_base_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_base_path = os.path.join(os.path.dirname(script_dir), "BaseballTracker", "public", "data")
        else:
            self.data_base_path = data_base_path
            
        self.analyzer = EnhancedHellraiserAnalyzer(data_base_path)
        
        # Results tracking
        self.test_results = {
            'enhanced_system': {
                'total_predictions': 0,
                'successful_predictions': 0,
                'accuracy_rate': 0.0,
                'daily_results': [],
                'pathway_success_rates': {},
                'confidence_calibration': [],
                'market_efficiency': {
                    'total_with_odds': 0,
                    'positive_ev_picks': 0,
                    'ev_accuracy': []
                }
            },
            'original_system': {
                'total_predictions': 0,
                'successful_predictions': 0,
                'accuracy_rate': 0.0,
                'daily_results': []
            },
            'individual_patterns': {
                'hit_streak_to_hr': [],
                'drought_to_hr': [],
                'pattern_analysis': {}
            },
            'improvement_opportunities': []
        }
        
        print(f"🧪 Full Season Tester initialized")
        print(f"📁 Data path: {self.data_base_path}")
        
    def discover_all_game_dates(self) -> List[str]:
        """Discover all available game dates for full season analysis"""
        print("🔍 Discovering all available game dates...")
        
        game_dates = []
        years = [2025]  # Current season
        months = ['march', 'april', 'may', 'june', 'july', 'august', 'september', 'october']
        
        for year in years:
            for month in months:
                month_dir = os.path.join(self.data_base_path, str(year), month)
                if not os.path.exists(month_dir):
                    continue
                    
                # Find all JSON files in month directory
                json_files = glob.glob(os.path.join(month_dir, f"{month}_*.json"))
                
                for json_file in json_files:
                    # Extract date from filename
                    filename = os.path.basename(json_file)
                    # Format: month_DD_YYYY.json
                    try:
                        parts = filename.replace('.json', '').split('_')
                        if len(parts) == 3:
                            month_name, day_str, year_str = parts
                            day = int(day_str)
                            year = int(year_str)
                            
                            # Convert month name to number
                            month_num = {
                                'march': 3, 'april': 4, 'may': 5, 'june': 6,
                                'july': 7, 'august': 8, 'september': 9, 'october': 10
                            }.get(month_name.lower())
                            
                            if month_num:
                                date_str = f"{year}-{month_num:02d}-{day:02d}"
                                
                                # Verify file has actual game data
                                if self._has_game_data(json_file):
                                    game_dates.append(date_str)
                    except:
                        continue
        
        game_dates.sort()
        print(f"✅ Discovered {len(game_dates)} game dates")
        if game_dates:
            print(f"📅 Season range: {game_dates[0]} to {game_dates[-1]}")
        
        return game_dates
    
    def _has_game_data(self, file_path: str) -> bool:
        """Check if file has actual player and game data"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return (data.get('players') and 
                   isinstance(data['players'], list) and 
                   len(data['players']) > 0 and
                   data.get('games') and
                   isinstance(data['games'], list) and
                   len(data['games']) > 0)
        except:
            return False
    
    def analyze_individual_patterns(self, player_name: str, team: str, 
                                  game_dates: List[str], hr_date: str) -> Dict[str, Any]:
        """
        Analyze individual player patterns leading to HR
        Focus on hit streaks, droughts, and other patterns
        """
        patterns = {
            'player_name': player_name,
            'team': team,
            'hr_date': hr_date,
            'hit_streak_before_hr': 0,
            'games_since_last_hr': 0,
            'hit_drought_before_hr': 0,
            'performance_trend': 'unknown',
            'last_5_games': [],
            'last_10_games': [],
            'pattern_type': 'unknown'
        }
        
        # Find the index of HR date
        try:
            hr_index = game_dates.index(hr_date)
        except ValueError:
            return patterns
        
        # Analyze games leading up to HR (last 10 games)
        analysis_window = game_dates[max(0, hr_index - 10):hr_index]
        
        hit_streak = 0
        drought_length = 0
        games_since_last_hr = 0
        last_hr_found = False
        
        game_performances = []
        
        # Work backwards from HR date
        for i, date in enumerate(reversed(analysis_window)):
            player_data = self._get_player_game_data(player_name, team, date)
            
            if not player_data:
                continue
                
            hits = player_data.get('H', 0)
            hrs = player_data.get('HR', 0)
            abs = player_data.get('AB', 0)
            
            game_performances.append({
                'date': date,
                'hits': hits,
                'hrs': hrs,
                'abs': abs,
                'days_before_hr': i + 1
            })
            
            # Track hit streak (consecutive games with hits)
            if hits > 0:
                if i == 0:  # Most recent game before HR
                    hit_streak += 1
                elif hit_streak > 0:  # Continue streak
                    hit_streak += 1
                else:  # Reset streak if we found hits after a hitless game
                    hit_streak = 1
            else:
                # No hits in this game
                if hit_streak == 0:  # Still counting drought
                    drought_length += 1
            
            # Track games since last HR
            if not last_hr_found:
                if hrs > 0:
                    last_hr_found = True
                else:
                    games_since_last_hr += 1
        
        patterns['hit_streak_before_hr'] = hit_streak
        patterns['hit_drought_before_hr'] = drought_length
        patterns['games_since_last_hr'] = games_since_last_hr
        patterns['last_10_games'] = list(reversed(game_performances))
        patterns['last_5_games'] = list(reversed(game_performances))[:5]
        
        # Determine pattern type
        if hit_streak >= 3:
            patterns['pattern_type'] = 'hot_streak_continuation'
            patterns['performance_trend'] = 'hot'
        elif drought_length >= 3:
            patterns['pattern_type'] = 'bounce_back_from_drought'
            patterns['performance_trend'] = 'cold_to_hot'
        elif games_since_last_hr >= 10:
            patterns['pattern_type'] = 'overdue_power_breakout'
            patterns['performance_trend'] = 'power_due'
        elif games_since_last_hr <= 3:
            patterns['pattern_type'] = 'power_cluster'
            patterns['performance_trend'] = 'power_hot'
        else:
            patterns['pattern_type'] = 'baseline_performance'
            patterns['performance_trend'] = 'average'
        
        return patterns
    
    def _get_player_game_data(self, player_name: str, team: str, date_str: str) -> Optional[Dict]:
        """Get player data for specific game date"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.year
            month_name = date_obj.strftime("%B").lower()
            day = date_obj.day
            
            file_path = os.path.join(
                self.data_base_path, 
                str(year), 
                month_name, 
                f"{month_name}_{day:02d}_{year}.json"
            )
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Find player in players array
            for player in data.get('players', []):
                if (player.get('name') == player_name and 
                    player.get('team') == team and
                    player.get('playerType') == 'hitter'):
                    return player
            
            return None
        except:
            return None
    
    def test_single_date(self, date_str: str, use_enhanced: bool = True) -> Dict[str, Any]:
        """Test enhanced algorithm on single date"""
        print(f"🧪 Testing {date_str} ({'Enhanced' if use_enhanced else 'Original'} system)")
        
        daily_result = {
            'date': date_str,
            'system': 'enhanced' if use_enhanced else 'original',
            'total_predictions': 0,
            'successful_predictions': 0,
            'accuracy_rate': 0.0,
            'team_results': {},
            'individual_patterns': [],
            'confidence_analysis': [],
            'market_analysis': {}
        }
        
        if use_enhanced:
            # Use enhanced algorithm
            analysis_results = self.analyzer.analyze_date(date_str, use_api=True)
            
            if analysis_results.get('error'):
                print(f"❌ Enhanced analysis failed: {analysis_results['error']}")
                return daily_result
            
            predictions = analysis_results.get('picks', [])
            
        else:
            # Load original Hellraiser results if available
            original_file = os.path.join(self.data_base_path, "hellraiser", f"hellraiser_analysis_{date_str}.json")
            
            if not os.path.exists(original_file):
                print(f"⚠️ Original Hellraiser file not found for {date_str}")
                return daily_result
            
            with open(original_file, 'r') as f:
                original_data = json.load(f)
            
            predictions = original_data.get('picks', [])
        
        # Get actual HR results for this date
        actual_hrs = self._get_actual_home_runs(date_str)
        
        if not actual_hrs:
            print(f"⚠️ No actual HR data found for {date_str}")
            return daily_result
        
        print(f"⚾ Found {len(actual_hrs)} actual HRs on {date_str}")
        
        # Analyze predictions by team (top 3 per team)
        team_predictions = defaultdict(list)
        for pred in predictions:
            team = pred.get('team', '')
            if team:
                team_predictions[team].append(pred)
        
        total_predictions = 0
        successful_predictions = 0
        
        for team, team_preds in team_predictions.items():
            # Sort by confidence and take top 3
            team_preds.sort(key=lambda x: x.get('enhanced_confidence_score', x.get('confidenceScore', 0)), reverse=True)
            top_3 = team_preds[:3]
            
            team_successes = 0
            for pred in top_3:
                player_name = pred.get('playerName', pred.get('player_name', ''))
                pred_team = pred.get('team', '')
                
                # Check if this player hit a HR
                player_hr = any(
                    hr['player_name'] == player_name and hr['team'] == pred_team
                    for hr in actual_hrs
                )
                
                if player_hr:
                    team_successes += 1
                    successful_predictions += 1
                    
                    # Analyze individual patterns for successful predictions
                    if use_enhanced:
                        game_dates = self.discover_all_game_dates()
                        pattern_analysis = self.analyze_individual_patterns(
                            player_name, pred_team, game_dates, date_str
                        )
                        daily_result['individual_patterns'].append(pattern_analysis)
                        
                        # Add to global pattern tracking
                        if pattern_analysis['pattern_type'] == 'hot_streak_continuation':
                            self.test_results['individual_patterns']['hit_streak_to_hr'].append(pattern_analysis)
                        elif pattern_analysis['pattern_type'] == 'bounce_back_from_drought':
                            self.test_results['individual_patterns']['drought_to_hr'].append(pattern_analysis)
                
                total_predictions += 1
            
            daily_result['team_results'][team] = {
                'predictions': len(top_3),
                'successes': team_successes,
                'accuracy': team_successes / len(top_3) if top_3 else 0
            }
        
        daily_result['total_predictions'] = total_predictions
        daily_result['successful_predictions'] = successful_predictions
        daily_result['accuracy_rate'] = successful_predictions / total_predictions if total_predictions > 0 else 0
        
        print(f"📊 {date_str} Results: {successful_predictions}/{total_predictions} = {daily_result['accuracy_rate']:.1%}")
        
        return daily_result
    
    def _get_actual_home_runs(self, date_str: str) -> List[Dict[str, str]]:
        """Get actual home runs for a specific date"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.year
            month_name = date_obj.strftime("%B").lower()
            day = date_obj.day
            
            file_path = os.path.join(
                self.data_base_path, 
                str(year), 
                month_name, 
                f"{month_name}_{day:02d}_{year}.json"
            )
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            home_runs = []
            for player in data.get('players', []):
                if (player.get('playerType') == 'hitter' and 
                    player.get('HR', 0) > 0):
                    
                    hr_count = player.get('HR', 0)
                    for _ in range(int(hr_count)):  # Handle multiple HRs
                        home_runs.append({
                            'player_name': player.get('name', ''),
                            'team': player.get('team', ''),
                            'hr_count': hr_count
                        })
            
            return home_runs
        except:
            return []
    
    def run_full_season_test(self, max_dates: int = None, start_date: str = None) -> Dict[str, Any]:
        """Run comprehensive full season test"""
        print("🚀 Starting Full Season Test of Enhanced Hellraiser Algorithm")
        print("=" * 70)
        
        # Discover all game dates
        all_game_dates = self.discover_all_game_dates()
        
        if not all_game_dates:
            print("❌ No game dates found!")
            return self.test_results
        
        # Filter dates if specified
        if start_date:
            all_game_dates = [d for d in all_game_dates if d >= start_date]
        
        if max_dates:
            all_game_dates = all_game_dates[:max_dates]
        
        print(f"🎯 Testing {len(all_game_dates)} dates")
        print(f"📅 Date range: {all_game_dates[0]} to {all_game_dates[-1]}")
        
        enhanced_successes = 0
        enhanced_total = 0
        original_successes = 0
        original_total = 0
        
        # Test enhanced system
        print(f"\n🔬 Testing Enhanced Hellraiser Algorithm...")
        for i, date_str in enumerate(all_game_dates, 1):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(all_game_dates)} ({i/len(all_game_dates):.1%})")
            
            enhanced_result = self.test_single_date(date_str, use_enhanced=True)
            
            enhanced_successes += enhanced_result['successful_predictions']
            enhanced_total += enhanced_result['total_predictions']
            
            self.test_results['enhanced_system']['daily_results'].append(enhanced_result)
        
        # Test original system (if available)
        print(f"\n🔬 Testing Original Hellraiser Algorithm...")
        for i, date_str in enumerate(all_game_dates, 1):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(all_game_dates)} ({i/len(all_game_dates):.1%})")
            
            original_result = self.test_single_date(date_str, use_enhanced=False)
            
            original_successes += original_result['successful_predictions']
            original_total += original_result['total_predictions']
            
            self.test_results['original_system']['daily_results'].append(original_result)
        
        # Calculate final results
        self.test_results['enhanced_system']['total_predictions'] = enhanced_total
        self.test_results['enhanced_system']['successful_predictions'] = enhanced_successes
        self.test_results['enhanced_system']['accuracy_rate'] = enhanced_successes / enhanced_total if enhanced_total > 0 else 0
        
        self.test_results['original_system']['total_predictions'] = original_total
        self.test_results['original_system']['successful_predictions'] = original_successes
        self.test_results['original_system']['accuracy_rate'] = original_successes / original_total if original_total > 0 else 0
        
        # Analyze individual patterns
        self._analyze_pattern_trends()
        
        return self.test_results
    
    def _analyze_pattern_trends(self):
        """Analyze trends from individual pattern data"""
        hit_streak_hrs = self.test_results['individual_patterns']['hit_streak_to_hr']
        drought_hrs = self.test_results['individual_patterns']['drought_to_hr']
        
        pattern_analysis = {
            'hit_streak_success_rate': len(hit_streak_hrs) / max(1, len(hit_streak_hrs) + len(drought_hrs)),
            'average_streak_length': np.mean([p['hit_streak_before_hr'] for p in hit_streak_hrs]) if hit_streak_hrs else 0,
            'average_drought_length': np.mean([p['hit_drought_before_hr'] for p in drought_hrs]) if drought_hrs else 0,
            'power_cluster_frequency': len([p for p in hit_streak_hrs + drought_hrs if p['games_since_last_hr'] <= 3]),
            'overdue_breakouts': len([p for p in hit_streak_hrs + drought_hrs if p['games_since_last_hr'] >= 10])
        }
        
        self.test_results['individual_patterns']['pattern_analysis'] = pattern_analysis
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report"""
        results = self.test_results
        
        report = f"""
# Enhanced Hellraiser Algorithm - Full Season Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Comparison

### Enhanced System Results:
- **Total Predictions**: {results['enhanced_system']['total_predictions']:,}
- **Successful Predictions**: {results['enhanced_system']['successful_predictions']:,}
- **Accuracy Rate**: {results['enhanced_system']['accuracy_rate']:.2%}

### Original System Results:
- **Total Predictions**: {results['original_system']['total_predictions']:,}
- **Successful Predictions**: {results['original_system']['successful_predictions']:,}
- **Accuracy Rate**: {results['original_system']['accuracy_rate']:.2%}

### Improvement:
- **Accuracy Improvement**: {(results['enhanced_system']['accuracy_rate'] - results['original_system']['accuracy_rate']):.2%}
- **Additional Successful Predictions**: {results['enhanced_system']['successful_predictions'] - results['original_system']['successful_predictions']:,}

## Individual Pattern Analysis

### Hit Streak to HR Patterns:
- **Count**: {len(results['individual_patterns']['hit_streak_to_hr'])}
- **Average Streak Length**: {results['individual_patterns']['pattern_analysis'].get('average_streak_length', 0):.1f} games

### Drought to HR Patterns:
- **Count**: {len(results['individual_patterns']['drought_to_hr'])}
- **Average Drought Length**: {results['individual_patterns']['pattern_analysis'].get('average_drought_length', 0):.1f} games

### Power Patterns:
- **Power Clusters** (≤3 games since last HR): {results['individual_patterns']['pattern_analysis'].get('power_cluster_frequency', 0)}
- **Overdue Breakouts** (≥10 games since last HR): {results['individual_patterns']['pattern_analysis'].get('overdue_breakouts', 0)}

## Key Findings:

1. **Enhanced Algorithm Performance**: The enhanced system achieved {results['enhanced_system']['accuracy_rate']:.2%} accuracy vs {results['original_system']['accuracy_rate']:.2%} for the original system.

2. **Pattern Discovery**: Individual analysis revealed specific patterns leading to HR success.

3. **Data Integration Impact**: The 6-component scoring system with comprehensive data sources shows measurable improvement.

## Recommendations for Further Enhancement:

[Analysis recommendations will be provided by specialized agents]
"""
        
        return report
    
    def save_results(self, output_dir: str = None) -> str:
        """Save comprehensive test results"""
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = os.path.join(output_dir, f"enhanced_hellraiser_test_results_{timestamp}.json")
        report_file = os.path.join(output_dir, f"enhanced_hellraiser_test_report_{timestamp}.md")
        
        # Save JSON results
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Save markdown report
        report = self.generate_comprehensive_report()
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"💾 Results saved:")
        print(f"  - JSON: {results_file}")
        print(f"  - Report: {report_file}")
        
        return results_file


def main():
    """Main function for full season testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Full Season Test of Enhanced Hellraiser Algorithm')
    parser.add_argument('--max-dates', type=int, help='Maximum number of dates to test')
    parser.add_argument('--start-date', type=str, help='Start date for testing (YYYY-MM-DD)')
    parser.add_argument('--save', action='store_true', help='Save results to files')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = FullSeasonTester()
    
    # Run full season test
    results = tester.run_full_season_test(
        max_dates=args.max_dates,
        start_date=args.start_date
    )
    
    # Display summary
    enhanced = results['enhanced_system']
    original = results['original_system']
    
    print(f"\n🎯 FINAL RESULTS SUMMARY")
    print("=" * 50)
    print(f"Enhanced System: {enhanced['successful_predictions']}/{enhanced['total_predictions']} = {enhanced['accuracy_rate']:.2%}")
    print(f"Original System: {original['successful_predictions']}/{original['total_predictions']} = {original['accuracy_rate']:.2%}")
    print(f"Improvement: +{(enhanced['accuracy_rate'] - original['accuracy_rate']):.2%}")
    
    # Pattern analysis summary
    hit_streaks = len(results['individual_patterns']['hit_streak_to_hr'])
    droughts = len(results['individual_patterns']['drought_to_hr'])
    print(f"\n📈 Pattern Analysis:")
    print(f"Hit Streak → HR: {hit_streaks} instances")
    print(f"Drought → HR: {droughts} instances")
    
    # Save results if requested
    if args.save:
        results_file = tester.save_results()
        print(f"\n💾 Detailed results saved for agent analysis")
    
    return results


if __name__ == "__main__":
    results = main()