#!/usr/bin/env python3
"""
Final Hellraiser Statistical Analysis - Fixed version with correct result tracking
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

class HellraiserFinalAnalysis:
    def __init__(self):
        script_dir = Path(__file__).parent.absolute()
        self.base_dir = script_dir.parent / "BaseballTracker"
        self.hellraiser_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.games_dir = self.base_dir / "public" / "data" / "2025"
        
        print(f"🔬 Hellraiser Final Statistical Analysis")

    def normalize_name(self, name):
        """Normalize player names for matching"""
        name = re.sub(r'[^\w\s]', ' ', name.lower().strip())
        name = ' '.join(name.split())
        
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        
        return name

    def names_match(self, pred_name, actual_name):
        """Check if predicted name matches actual name"""
        pred_norm = self.normalize_name(pred_name)
        actual_norm = self.normalize_name(actual_name)
        
        # Direct match
        if pred_norm == actual_norm:
            return True
        
        # Handle abbreviated vs full names
        pred_parts = pred_norm.split()
        actual_parts = actual_norm.split()
        
        if len(pred_parts) == len(actual_parts):
            # Check if each part matches (either full or first letter)
            for p, a in zip(pred_parts, actual_parts):
                if not (p == a or (len(p) == 1 and a.startswith(p)) or (len(a) == 1 and p.startswith(a))):
                    return False
            return True
        
        # Check last name + first initial matching
        if len(pred_parts) >= 2 and len(actual_parts) >= 2:
            if pred_parts[-1] == actual_parts[-1]:  # Same last name
                if pred_parts[0][0] == actual_parts[0][0]:  # Same first initial
                    return True
        
        return False

    def extract_hr_hitters(self, game_data):
        """Extract players who hit HRs from game data"""
        hr_hitters = []
        
        if 'players' in game_data:
            for player in game_data['players']:
                if player.get('HR', 0) > 0:
                    name = player.get('name', '').strip()
                    if name:
                        hr_hitters.append(name)
        
        return hr_hitters

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

    def analyze_performance(self, days=15):
        """Analyze prediction performance with proper result tracking"""
        print(f"📊 Analyzing last {days} days of predictions")
        
        # Get recent prediction files
        pred_files = sorted([f for f in self.hellraiser_dir.glob("hellraiser_analysis_*.json")])[-days:]
        
        results = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'all_predictions': [],
            'daily_results': [],
            'confidence_brackets': {
                '95+': {'total': 0, 'correct': 0},
                '90-94': {'total': 0, 'correct': 0},
                '85-89': {'total': 0, 'correct': 0},
                '80-84': {'total': 0, 'correct': 0},
                '75-79': {'total': 0, 'correct': 0},
                '70-74': {'total': 0, 'correct': 0},
                '<70': {'total': 0, 'correct': 0}
            },
            'pathway_performance': {
                'perfectStorm': {'total': 0, 'correct': 0},
                'batterDriven': {'total': 0, 'correct': 0},
                'pitcherDriven': {'total': 0, 'correct': 0}
            },
            'classification_performance': {},
            'market_efficiency': {},
            'player_performance': {}
        }
        
        for pred_file in pred_files:
            date_part = pred_file.name.replace("hellraiser_analysis_", "").replace(".json", "")
            
            # Load predictions
            try:
                with open(pred_file, 'r') as f:
                    pred_data = json.load(f)
            except Exception as e:
                print(f"❌ Error loading {pred_file}: {e}")
                continue
            
            if 'picks' not in pred_data or not pred_data['picks']:
                continue
            
            # Load game results
            game_file = self.find_game_file(date_part)
            hr_hitters = []
            if game_file:
                try:
                    with open(game_file, 'r') as f:
                        game_data = json.load(f)
                    hr_hitters = self.extract_hr_hitters(game_data)
                except Exception as e:
                    print(f"❌ Error loading game data for {date_part}: {e}")
            
            # Process predictions for this day
            daily_total = len(pred_data['picks'])
            daily_correct = 0
            
            print(f"Processing {date_part}: {daily_total} predictions, {len(hr_hitters)} HR hitters")
            
            for pick in pred_data['picks']:
                player_name = pick.get('playerName', '')
                confidence = pick.get('confidenceScore', 0)
                pathway = pick.get('pathway', 'unknown')
                classification = pick.get('classification', 'unknown') 
                
                # Check if player hit HR - THIS IS THE CRITICAL PART
                hit_hr = any(self.names_match(player_name, hr_name) for hr_name in hr_hitters)
                
                # Create prediction record
                prediction_record = {
                    'date': date_part,
                    'player': player_name,
                    'confidence': confidence,
                    'pathway': pathway,
                    'classification': classification,
                    'hit_hr': hit_hr,  # Make sure this is properly set
                    'odds': pick.get('odds', {}),
                    'market_efficiency': pick.get('marketEfficiency', {})
                }
                
                results['all_predictions'].append(prediction_record)
                results['total_predictions'] += 1
                
                # Update counters if hit HR
                if hit_hr:
                    results['correct_predictions'] += 1
                    daily_correct += 1
                
                # Update confidence bracket tracking
                bracket = self.get_confidence_bracket(confidence)
                results['confidence_brackets'][bracket]['total'] += 1
                if hit_hr:
                    results['confidence_brackets'][bracket]['correct'] += 1
                
                # Update pathway tracking
                if pathway in results['pathway_performance']:
                    results['pathway_performance'][pathway]['total'] += 1
                    if hit_hr:
                        results['pathway_performance'][pathway]['correct'] += 1
                
                # Track classification performance
                if classification not in results['classification_performance']:
                    results['classification_performance'][classification] = {'total': 0, 'correct': 0}
                results['classification_performance'][classification]['total'] += 1
                if hit_hr:
                    results['classification_performance'][classification]['correct'] += 1
                
                # Track market efficiency
                market_value = pick.get('marketEfficiency', {}).get('value', 'unknown')
                if market_value not in results['market_efficiency']:
                    results['market_efficiency'][market_value] = {'total': 0, 'correct': 0}
                results['market_efficiency'][market_value]['total'] += 1
                if hit_hr:
                    results['market_efficiency'][market_value]['correct'] += 1
                
                # Track player performance
                if player_name not in results['player_performance']:
                    results['player_performance'][player_name] = {'total': 0, 'correct': 0}
                results['player_performance'][player_name]['total'] += 1
                if hit_hr:
                    results['player_performance'][player_name]['correct'] += 1
            
            # Record daily results
            daily_accuracy = (daily_correct / daily_total * 100) if daily_total > 0 else 0
            results['daily_results'].append({
                'date': date_part,
                'total': daily_total,
                'correct': daily_correct,
                'accuracy': daily_accuracy
            })
            
            print(f"  {date_part}: {daily_correct}/{daily_total} = {daily_accuracy:.1f}%")
        
        return results

    def get_confidence_bracket(self, confidence):
        """Get confidence bracket for a score"""
        if confidence >= 95:
            return '95+'
        elif confidence >= 90:
            return '90-94'
        elif confidence >= 85:
            return '85-89'
        elif confidence >= 80:
            return '80-84'
        elif confidence >= 75:
            return '75-79'
        elif confidence >= 70:
            return '70-74'
        else:
            return '<70'

    def calculate_expected_value(self, predictions):
        """Calculate expected value analysis"""
        total_ev = 0
        total_bets = 0
        
        for pred in predictions:
            odds = pred.get('odds', {})
            if not isinstance(odds, dict) or 'american' not in odds:
                continue
            
            american_odds = odds['american']
            try:
                if isinstance(american_odds, str):
                    if american_odds.startswith('+'):
                        decimal_odds = 1 + (int(american_odds[1:]) / 100)
                    else:
                        decimal_odds = 1 + (100 / abs(int(american_odds)))
                else:
                    decimal_odds = 1 + (american_odds / 100) if american_odds > 0 else 1 + (100 / abs(american_odds))
            except:
                continue
            
            bet_amount = 100
            if pred['hit_hr']:
                profit = (decimal_odds - 1) * bet_amount
            else:
                profit = -bet_amount
            
            total_ev += profit
            total_bets += 1
        
        return {
            'total_ev': total_ev,
            'avg_ev_per_bet': total_ev / total_bets if total_bets > 0 else 0,
            'total_bets': total_bets
        }

    def generate_insights_and_recommendations(self, results):
        """Generate statistical insights and model improvement recommendations"""
        
        total = results['total_predictions']
        correct = results['correct_predictions']
        overall_accuracy = (correct / total * 100) if total > 0 else 0
        
        insights = {
            'performance_summary': {
                'total_predictions': total,
                'correct_predictions': correct,
                'overall_accuracy': overall_accuracy,
                'baseline_comparison': f"{'Above' if overall_accuracy > 12 else 'Below'} typical HR rate (~12%)"
            }
        }
        
        # Confidence calibration analysis
        calibration_issues = []
        confidence_performance = {}
        
        for bracket, data in results['confidence_brackets'].items():
            if data['total'] > 0:
                actual_rate = data['correct'] / data['total'] * 100
                
                # Expected rates based on bracket
                expected_rates = {
                    '95+': 95, '90-94': 92, '85-89': 87, 
                    '80-84': 82, '75-79': 77, '70-74': 72, '<70': 65
                }
                expected_rate = expected_rates.get(bracket, 70)
                
                calibration_error = abs(expected_rate - actual_rate)
                
                confidence_performance[bracket] = {
                    'actual_rate': actual_rate,
                    'expected_rate': expected_rate,
                    'calibration_error': calibration_error,
                    'sample_size': data['total']
                }
                
                if calibration_error > 20:
                    calibration_issues.append(f"{bracket} bracket: {actual_rate:.1f}% actual vs {expected_rate}% expected")
        
        insights['confidence_calibration'] = confidence_performance
        insights['calibration_issues'] = calibration_issues
        
        # Pathway effectiveness
        pathway_effectiveness = {}
        for pathway, data in results['pathway_performance'].items():
            if data['total'] > 0:
                success_rate = data['correct'] / data['total'] * 100
                pathway_effectiveness[pathway] = {
                    'success_rate': success_rate,
                    'volume': data['total'],
                    'volume_percentage': data['total'] / total * 100
                }
        
        insights['pathway_effectiveness'] = pathway_effectiveness
        
        # Market efficiency correlation
        market_performance = {}
        for market_value, data in results['market_efficiency'].items():
            if data['total'] > 0:
                success_rate = data['correct'] / data['total'] * 100
                market_performance[market_value] = {
                    'success_rate': success_rate,
                    'volume': data['total']
                }
        
        insights['market_efficiency'] = market_performance
        
        # Expected value analysis
        ev_analysis = self.calculate_expected_value(results['all_predictions'])
        insights['expected_value'] = ev_analysis
        
        # Generate recommendations
        recommendations = self.generate_recommendations(insights, results)
        
        return insights, recommendations

    def generate_recommendations(self, insights, results):
        """Generate specific mathematical and statistical recommendations"""
        recommendations = []
        
        overall_accuracy = insights['performance_summary']['overall_accuracy']
        
        # 1. Overall Performance Assessment
        if overall_accuracy < 8:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Model Validity',
                'issue': f'Accuracy ({overall_accuracy:.1f}%) below random baseline',
                'recommendation': 'Fundamental model redesign required',
                'mathematical_adjustment': 'Current model lacks predictive power - implement ensemble approach'
            })
        elif overall_accuracy < 15:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Model Calibration',
                'issue': f'Accuracy ({overall_accuracy:.1f}%) needs improvement',
                'recommendation': 'Systematic recalibration of scoring components'
            })
        
        # 2. Confidence Calibration
        avg_calibration_error = sum(perf['calibration_error'] for perf in insights['confidence_calibration'].values()) / len(insights['confidence_calibration']) if insights['confidence_calibration'] else 0
        
        if avg_calibration_error > 30:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Confidence Recalibration',
                'issue': f'Average calibration error: {avg_calibration_error:.1f}%',
                'recommendation': 'Apply isotonic regression for confidence mapping',
                'mathematical_adjustment': 'calibrated_confidence = original_confidence * (actual_rate / expected_rate)'
            })
        
        # 3. Pathway Optimization
        pathway_perf = insights['pathway_effectiveness']
        if pathway_perf:
            best_pathway = max(pathway_perf.items(), key=lambda x: x[1]['success_rate'])
            worst_pathway = min(pathway_perf.items(), key=lambda x: x[1]['success_rate'])
            
            performance_gap = best_pathway[1]['success_rate'] - worst_pathway[1]['success_rate']
            
            if performance_gap > 5:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Pathway Rebalancing',
                    'issue': f'{best_pathway[0]} ({best_pathway[1]["success_rate"]:.1f}%) vs {worst_pathway[0]} ({worst_pathway[1]["success_rate"]:.1f}%)',
                    'recommendation': f'Shift volume from {worst_pathway[0]} to {best_pathway[0]}',
                    'mathematical_adjustment': f'Increase {best_pathway[0]} threshold by -5%, decrease {worst_pathway[0]} threshold by +10%'
                })
        
        # 4. Expected Value Optimization
        ev_data = insights['expected_value']
        if ev_data['avg_ev_per_bet'] < -20:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Expected Value',
                'issue': f'Highly negative EV: ${ev_data["avg_ev_per_bet"]:.2f} per bet',
                'recommendation': 'Implement positive EV filtering',
                'mathematical_adjustment': 'Only predict when: model_probability > implied_probability + 0.05'
            })
        
        # 5. Volume Management
        daily_avg = sum(day['total'] for day in results['daily_results']) / len(results['daily_results']) if results['daily_results'] else 0
        
        if daily_avg > 200:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Volume Optimization',
                'issue': f'High daily volume: {daily_avg:.0f} predictions/day',
                'recommendation': 'Reduce volume to improve quality',
                'mathematical_adjustment': 'Increase minimum confidence threshold to 80%'
            })
        
        return recommendations

    def print_final_analysis(self, results, insights, recommendations):
        """Print comprehensive final analysis"""
        
        print(f"\n{'='*70}")
        print(f"🎯 HELLRAISER FINAL STATISTICAL ANALYSIS RESULTS")
        print(f"{'='*70}")
        
        # Performance Summary
        perf = insights['performance_summary']
        print(f"\n📊 PERFORMANCE SUMMARY")
        print(f"{'='*30}")
        print(f"Total Predictions: {perf['total_predictions']:,}")
        print(f"Correct Predictions: {perf['correct_predictions']:,}")
        print(f"Overall Accuracy: {perf['overall_accuracy']:.2f}%")
        print(f"Baseline Comparison: {perf['baseline_comparison']}")
        
        # Expected Value
        ev = insights['expected_value']
        print(f"\n💰 EXPECTED VALUE ANALYSIS")
        print(f"{'='*30}")
        print(f"Total EV: ${ev['total_ev']:,.2f}")
        print(f"Average EV per $100 bet: ${ev['avg_ev_per_bet']:.2f}")
        print(f"Total Bets Analyzed: {ev['total_bets']:,}")
        
        # Confidence Calibration
        print(f"\n🎯 CONFIDENCE CALIBRATION")
        print(f"{'='*35}")
        print(f"{'Bracket':<8} {'Count':<6} {'Actual':<7} {'Expected':<8} {'Error':<6}")
        print(f"{'-'*40}")
        
        for bracket, data in insights['confidence_calibration'].items():
            print(f"{bracket:<8} {data['sample_size']:<6} {data['actual_rate']:<6.1f}% {data['expected_rate']:<7.1f}% {data['calibration_error']:<5.1f}%")
        
        # Pathway Performance
        print(f"\n🛤️  PATHWAY EFFECTIVENESS")
        print(f"{'='*30}")
        for pathway, data in insights['pathway_effectiveness'].items():
            print(f"{pathway}: {data['success_rate']:.1f}% ({data['volume']} predictions, {data['volume_percentage']:.1f}% of total)")
        
        # Market Efficiency
        print(f"\n📈 MARKET EFFICIENCY")
        print(f"{'='*25}")
        for market_value, data in insights['market_efficiency'].items():
            print(f"{market_value}: {data['success_rate']:.1f}% ({data['volume']} predictions)")
        
        # Daily Performance Trend
        print(f"\n📅 DAILY PERFORMANCE (Last 10 days)")
        print(f"{'='*40}")
        recent_days = results['daily_results'][-10:]
        for day in recent_days:
            print(f"{day['date']}: {day['correct']:>3}/{day['total']:<3} ({day['accuracy']:>5.1f}%)")
        
        # Top/Worst Players
        print(f"\n👤 PLAYER PERFORMANCE LEADERS")
        print(f"{'='*35}")
        
        # Filter players with at least 5 predictions
        qualified_players = [(name, data) for name, data in results['player_performance'].items() if data['total'] >= 5]
        qualified_players.sort(key=lambda x: (x[1]['correct'] / x[1]['total'], x[1]['total']), reverse=True)
        
        print("Top 10 Performers (min 5 predictions):")
        for player, data in qualified_players[:10]:
            success_rate = data['correct'] / data['total'] * 100
            print(f"  {player[:25]:<25}: {data['correct']:>2}/{data['total']:<2} ({success_rate:>5.1f}%)")
        
        # Recommendations
        print(f"\n💡 STATISTICAL RECOMMENDATIONS")
        print(f"{'='*40}")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['category']} ({rec['priority']})")
            print(f"   Issue: {rec['issue']}")
            print(f"   Recommendation: {rec['recommendation']}")
            if 'mathematical_adjustment' in rec:
                print(f"   Formula: {rec['mathematical_adjustment']}")

def main():
    analyzer = HellraiserFinalAnalysis()
    
    # Run analysis
    print("🔄 Running comprehensive performance analysis...")
    results = analyzer.analyze_performance(days=15)
    
    # Generate insights and recommendations
    print("🔄 Calculating statistical insights...")
    insights, recommendations = analyzer.generate_insights_and_recommendations(results)
    
    # Print final analysis
    analyzer.print_final_analysis(results, insights, recommendations)
    
    # Summary
    overall_accuracy = insights['performance_summary']['overall_accuracy']
    ev_per_bet = insights['expected_value']['avg_ev_per_bet']
    critical_issues = len([r for r in recommendations if r['priority'] == 'CRITICAL'])
    
    print(f"\n🔬 ANALYSIS COMPLETE")
    print(f"{'='*30}")
    print(f"✅ Analyzed {results['total_predictions']:,} predictions")
    print(f"🎯 Overall accuracy: {overall_accuracy:.2f}%")
    print(f"💰 Expected value: ${ev_per_bet:.2f} per $100 bet")
    print(f"⚠️  {critical_issues} critical issues identified")
    print(f"📊 {len(recommendations)} total recommendations")

if __name__ == "__main__":
    main()