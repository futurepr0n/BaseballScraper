#!/usr/bin/env python3
"""
Quick Hellraiser Statistical Analysis - Focused version for immediate insights
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

class QuickHellraiserAnalysis:
    def __init__(self):
        script_dir = Path(__file__).parent.absolute()
        self.base_dir = script_dir.parent / "BaseballTracker"
        self.hellraiser_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.games_dir = self.base_dir / "public" / "data" / "2025"
        
        print(f"🔍 Quick Hellraiser Analysis")

    def normalize_name(self, name):
        """Normalize player names for matching"""
        # Remove common prefixes and suffixes, handle formatting
        name = name.lower().strip()
        # Handle "First Last" vs "F. Last" vs "Last, First"
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        return ' '.join(name.split())

    def extract_hr_hitters(self, game_data):
        """Extract players who hit HRs from game data"""
        hr_hitters = []
        
        if 'players' in game_data:
            for player in game_data['players']:
                if player.get('HR', 0) > 0 or player.get('homeRuns', 0) > 0:
                    name = player.get('name', '').strip()
                    if name:
                        hr_hitters.append(self.normalize_name(name))
        
        return hr_hitters

    def analyze_recent_performance(self, days=10):
        """Analyze recent prediction performance"""
        print(f"📊 Analyzing last {days} days of predictions vs actual results")
        
        # Get recent prediction files
        pred_files = []
        for file_path in sorted(self.hellraiser_dir.glob("hellraiser_analysis_*.json")):
            if file_path.name.startswith("hellraiser_analysis_"):
                pred_files.append(file_path)
        
        # Take most recent files
        pred_files = sorted(pred_files)[-days:]
        
        results = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'predictions_by_confidence': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'predictions_by_pathway': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'player_performance': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'daily_results': []
        }
        
        for pred_file in pred_files:
            date_part = pred_file.name.replace("hellraiser_analysis_", "").replace(".json", "")
            print(f"Processing {date_part}...")
            
            # Load predictions
            try:
                with open(pred_file, 'r') as f:
                    pred_data = json.load(f)
            except:
                continue
            
            if 'picks' not in pred_data:
                continue
            
            # Load game results
            game_file = self.find_game_file(date_part)
            hr_hitters = []
            if game_file:
                try:
                    with open(game_file, 'r') as f:
                        game_data = json.load(f)
                    hr_hitters = self.extract_hr_hitters(game_data)
                except:
                    pass
            
            daily_correct = 0
            daily_total = len(pred_data['picks'])
            
            # Process each prediction
            for pick in pred_data['picks']:
                player_name = self.normalize_name(pick.get('playerName', ''))
                confidence = pick.get('confidenceScore', 0)
                pathway = pick.get('pathway', 'unknown')
                
                hit_hr = player_name in hr_hitters
                
                results['total_predictions'] += 1
                if hit_hr:
                    results['correct_predictions'] += 1
                    daily_correct += 1
                
                # Track by confidence bracket
                conf_bracket = self.get_confidence_bracket(confidence)
                results['predictions_by_confidence'][conf_bracket]['total'] += 1
                if hit_hr:
                    results['predictions_by_confidence'][conf_bracket]['correct'] += 1
                
                # Track by pathway
                results['predictions_by_pathway'][pathway]['total'] += 1
                if hit_hr:
                    results['predictions_by_pathway'][pathway]['correct'] += 1
                
                # Track by player
                results['player_performance'][player_name]['total'] += 1
                if hit_hr:
                    results['player_performance'][player_name]['correct'] += 1
            
            results['daily_results'].append({
                'date': date_part,
                'total': daily_total,
                'correct': daily_correct,
                'accuracy': round(daily_correct / daily_total * 100, 1) if daily_total > 0 else 0
            })
        
        return results

    def get_confidence_bracket(self, confidence):
        """Get confidence bracket"""
        if confidence >= 90:
            return '90+'
        elif confidence >= 80:
            return '80-89'
        elif confidence >= 70:
            return '70-79'
        else:
            return '<70'

    def find_game_file(self, date_str):
        """Find game results file for a date"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.year
            month_name = date_obj.strftime("%B").lower()
            day = date_obj.strftime("%d")
            
            possible_paths = [
                self.games_dir / str(year) / month_name / f"{month_name}_{day}_{year}.json",
                self.games_dir / str(year) / month_name / f"{month_name}_{int(day):02d}_{year}.json"
            ]
            
            for path in possible_paths:
                if path.exists():
                    return path
            return None
        except:
            return None

    def print_analysis(self, results):
        """Print analysis results"""
        total = results['total_predictions']
        correct = results['correct_predictions']
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        
        print(f"\n🎯 HELLRAISER PERFORMANCE SUMMARY")
        print(f"{'='*50}")
        print(f"Total Predictions: {total:,}")
        print(f"Correct Predictions: {correct:,}")
        print(f"Overall Accuracy: {accuracy}%")
        
        print(f"\n📊 ACCURACY BY CONFIDENCE LEVEL")
        print(f"{'='*40}")
        for bracket in ['90+', '80-89', '70-79', '<70']:
            if bracket in results['predictions_by_confidence']:
                data = results['predictions_by_confidence'][bracket]
                bracket_accuracy = round(data['correct'] / data['total'] * 100, 1) if data['total'] > 0 else 0
                print(f"{bracket:>6}: {data['correct']:>3}/{data['total']:<3} ({bracket_accuracy:>5.1f}%)")
        
        print(f"\n🛤️  ACCURACY BY PATHWAY")
        print(f"{'='*35}")
        for pathway, data in results['predictions_by_pathway'].items():
            if data['total'] > 0:
                pathway_accuracy = round(data['correct'] / data['total'] * 100, 1)
                print(f"{pathway:>15}: {data['correct']:>3}/{data['total']:<3} ({pathway_accuracy:>5.1f}%)")
        
        print(f"\n👤 TOP PERFORMING PLAYERS")
        print(f"{'='*35}")
        # Sort players by total predictions, then by success rate
        top_players = []
        for player, data in results['player_performance'].items():
            if data['total'] >= 2:  # At least 2 predictions
                success_rate = data['correct'] / data['total']
                top_players.append((player, data['total'], data['correct'], success_rate))
        
        top_players.sort(key=lambda x: (x[1], x[3]), reverse=True)
        
        for player, total_preds, correct_preds, success_rate in top_players[:10]:
            print(f"{player[:20]:>20}: {correct_preds:>2}/{total_preds:<2} ({success_rate*100:>5.1f}%)")
        
        print(f"\n📅 DAILY PERFORMANCE")
        print(f"{'='*30}")
        for day in results['daily_results'][-7:]:  # Last 7 days
            print(f"{day['date']}: {day['correct']:>2}/{day['total']:<2} ({day['accuracy']:>5.1f}%)")
        
        # Calculate some key statistics
        print(f"\n🔍 KEY INSIGHTS")
        print(f"{'='*25}")
        
        # Check if high confidence predictions are actually more accurate
        high_conf = results['predictions_by_confidence']['90+']
        low_conf = results['predictions_by_confidence']['<70']
        
        if high_conf['total'] > 0 and low_conf['total'] > 0:
            high_conf_rate = high_conf['correct'] / high_conf['total'] * 100
            low_conf_rate = low_conf['correct'] / low_conf['total'] * 100
            print(f"• Confidence calibration: 90%+ predictions hit {high_conf_rate:.1f}% vs <70% hit {low_conf_rate:.1f}%")
        
        # Check pathway effectiveness
        best_pathway = max(results['predictions_by_pathway'].items(), 
                          key=lambda x: x[1]['correct']/x[1]['total'] if x[1]['total'] > 0 else 0)
        if best_pathway[1]['total'] > 0:
            best_rate = best_pathway[1]['correct'] / best_pathway[1]['total'] * 100
            print(f"• Best pathway: {best_pathway[0]} ({best_rate:.1f}% accuracy)")
        
        # Check if there's improvement over time
        recent_days = results['daily_results'][-3:]
        if len(recent_days) >= 3:
            recent_avg = sum(day['accuracy'] for day in recent_days) / len(recent_days)
            print(f"• Recent 3-day average: {recent_avg:.1f}%")
        
        return {
            'overall_accuracy': accuracy,
            'total_predictions': total,
            'confidence_analysis': results['predictions_by_confidence'],
            'pathway_analysis': results['predictions_by_pathway']
        }

def main():
    analyzer = QuickHellraiserAnalysis()
    results = analyzer.analyze_recent_performance(days=10)
    summary = analyzer.print_analysis(results)
    
    print(f"\n💡 RECOMMENDATIONS")
    print(f"{'='*25}")
    
    # Generate quick recommendations based on results
    if summary['overall_accuracy'] < 15:
        print("• Overall accuracy is very low - major model recalibration needed")
    elif summary['overall_accuracy'] < 25:
        print("• Below expected accuracy - review confidence scoring")
    
    # Check confidence calibration
    high_conf = summary['confidence_analysis']['90+']
    if high_conf['total'] > 0:
        high_conf_rate = high_conf['correct'] / high_conf['total'] * 100
        if high_conf_rate < 80:
            print(f"• 90%+ confidence predictions only hit {high_conf_rate:.1f}% - overconfident model")
    
    # Check pathway balance
    pathway_counts = [data['total'] for data in summary['pathway_analysis'].values()]
    if max(pathway_counts) / sum(pathway_counts) > 0.7:
        print("• One pathway dominates predictions - review pathway criteria")

if __name__ == "__main__":
    main()