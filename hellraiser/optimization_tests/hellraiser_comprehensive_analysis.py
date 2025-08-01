#!/usr/bin/env python3
"""
Comprehensive Hellraiser Statistical Analysis
- Fixed name matching between predictions and game results  
- Comprehensive statistical metrics and recommendations
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

class HellraiserComprehensiveAnalysis:
    def __init__(self):
        script_dir = Path(__file__).parent.absolute()
        self.base_dir = script_dir.parent / "BaseballTracker"
        self.hellraiser_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.games_dir = self.base_dir / "public" / "data" / "2025"
        
        print(f"🔬 Hellraiser Comprehensive Statistical Analysis")

    def normalize_name(self, name):
        """Advanced name normalization to handle various formats"""
        name = re.sub(r'[^\w\s]', ' ', name.lower().strip())
        name = ' '.join(name.split())
        
        # Handle "First Last" vs "F. Last" matching
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        
        return name

    def names_match(self, pred_name, actual_name):
        """Check if predicted name matches actual name with various formats"""
        pred_norm = self.normalize_name(pred_name)
        actual_norm = self.normalize_name(actual_name)
        
        # Direct match
        if pred_norm == actual_norm:
            return True
        
        # Check if abbreviated name matches full name
        # e.g., "m kepler" matches "max kepler"
        pred_parts = pred_norm.split()
        actual_parts = actual_norm.split()
        
        if len(pred_parts) == len(actual_parts):
            # Check if each part matches (either full or first letter)
            for p, a in zip(pred_parts, actual_parts):
                if not (p == a or (len(p) == 1 and a.startswith(p)) or (len(a) == 1 and p.startswith(a))):
                    return False
            return True
        
        # Check last name matching for common cases
        if len(pred_parts) >= 2 and len(actual_parts) >= 2:
            if pred_parts[-1] == actual_parts[-1]:  # Same last name
                # Check if first names are compatible
                if pred_parts[0][0] == actual_parts[0][0]:  # Same first initial
                    return True
        
        return False

    def extract_hr_hitters(self, game_data):
        """Extract players who hit HRs from game data"""
        hr_hitters = []
        
        if 'players' in game_data:
            for player in game_data['players']:
                if player.get('HR', 0) > 0 or player.get('homeRuns', 0) > 0:
                    name = player.get('name', '').strip()
                    if name:
                        hr_hitters.append(name)
        
        return hr_hitters

    def calculate_expected_value(self, predictions_with_results):
        """Calculate expected value assuming $100 bets"""
        total_ev = 0
        total_bets = 0
        
        for pred in predictions_with_results:
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

    def analyze_performance(self, days=15):
        """Comprehensive performance analysis"""
        print(f"📊 Analyzing last {days} days of predictions vs actual results")
        
        # Get recent prediction files
        pred_files = sorted([f for f in self.hellraiser_dir.glob("hellraiser_analysis_*.json")])[-days:]
        
        all_predictions = []
        results = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'predictions_by_confidence': defaultdict(lambda: {'total': 0, 'correct': 0, 'predictions': []}),
            'predictions_by_pathway': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'predictions_by_classification': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'player_performance': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'daily_results': [],
            'market_efficiency_performance': defaultdict(lambda: {'total': 0, 'correct': 0})
        }
        
        for pred_file in pred_files:
            date_part = pred_file.name.replace("hellraiser_analysis_", "").replace(".json", "")
            print(f"Processing {date_part}...")
            
            # Load predictions
            try:
                with open(pred_file, 'r') as f:
                    pred_data = json.load(f)
            except Exception as e:
                print(f"Error loading {pred_file}: {e}")
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
                    print(f"  Found {len(hr_hitters)} HR hitters: {[h[:15] for h in hr_hitters[:5]]}")
                except Exception as e:
                    print(f"  Error loading game data: {e}")
            
            daily_correct = 0
            daily_total = len(pred_data['picks'])
            daily_predictions = []
            
            # Process each prediction
            for pick in pred_data['picks']:
                player_name = pick.get('playerName', '')
                confidence = pick.get('confidenceScore', 0)
                pathway = pick.get('pathway', 'unknown')
                classification = pick.get('classification', 'unknown')
                
                # Check if player hit HR using improved name matching
                hit_hr = any(self.names_match(player_name, hr_name) for hr_name in hr_hitters)
                
                prediction_record = {
                    'date': date_part,
                    'player': player_name,
                    'confidence': confidence,
                    'pathway': pathway,
                    'classification': classification,
                    'hit_hr': hit_hr,
                    'odds': pick.get('odds', {}),
                    'market_efficiency': pick.get('marketEfficiency', {})
                }
                
                all_predictions.append(prediction_record)
                daily_predictions.append(prediction_record)
                
                results['total_predictions'] += 1
                if hit_hr:
                    results['correct_predictions'] += 1
                    daily_correct += 1
                
                # Track by confidence bracket
                conf_bracket = self.get_confidence_bracket(confidence)
                results['predictions_by_confidence'][conf_bracket]['total'] += 1
                results['predictions_by_confidence'][conf_bracket]['predictions'].append(prediction_record)
                if hit_hr:
                    results['predictions_by_confidence'][conf_bracket]['correct'] += 1
                
                # Track by pathway
                results['predictions_by_pathway'][pathway]['total'] += 1
                if hit_hr:
                    results['predictions_by_pathway'][pathway]['correct'] += 1
                
                # Track by classification
                results['predictions_by_classification'][classification]['total'] += 1
                if hit_hr:
                    results['predictions_by_classification'][classification]['correct'] += 1
                
                # Track by player
                normalized_player = self.normalize_name(player_name)
                results['player_performance'][normalized_player]['total'] += 1
                if hit_hr:
                    results['player_performance'][normalized_player]['correct'] += 1
                
                # Track by market efficiency
                market_value = pick.get('marketEfficiency', {}).get('value', 'unknown')
                results['market_efficiency_performance'][market_value]['total'] += 1
                if hit_hr:
                    results['market_efficiency_performance'][market_value]['correct'] += 1
            
            results['daily_results'].append({
                'date': date_part,
                'total': daily_total,
                'correct': daily_correct,
                'accuracy': round(daily_correct / daily_total * 100, 1) if daily_total > 0 else 0,
                'predictions': daily_predictions
            })
        
        # Calculate expected value
        ev_analysis = self.calculate_expected_value(all_predictions)
        results['expected_value'] = ev_analysis
        
        return results

    def get_confidence_bracket(self, confidence):
        """Get confidence bracket"""
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

    def calculate_statistical_metrics(self, results):
        """Calculate advanced statistical metrics"""
        metrics = {}
        
        # Overall statistics
        total = results['total_predictions']
        correct = results['correct_predictions']
        accuracy = correct / total if total > 0 else 0
        
        metrics['overall'] = {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy_rate': round(accuracy * 100, 2),
            'error_rate': round((1 - accuracy) * 100, 2)
        }
        
        # Confidence calibration analysis
        metrics['calibration'] = {}
        calibration_error = 0
        total_weighted_error = 0
        
        for bracket, data in results['predictions_by_confidence'].items():
            if data['total'] > 0:
                actual_rate = data['correct'] / data['total']
                
                # Expected rate based on bracket midpoint
                expected_rates = {
                    '95+': 0.95, '90-94': 0.92, '85-89': 0.87, 
                    '80-84': 0.82, '75-79': 0.77, '70-74': 0.72, '<70': 0.65
                }
                expected_rate = expected_rates.get(bracket, 0.70)
                
                bracket_error = abs(expected_rate - actual_rate)
                total_weighted_error += bracket_error * data['total']
                
                metrics['calibration'][bracket] = {
                    'sample_size': data['total'],
                    'actual_rate': round(actual_rate * 100, 1),
                    'expected_rate': round(expected_rate * 100, 1),
                    'calibration_error': round(bracket_error * 100, 1)
                }
        
        if total > 0:
            metrics['overall_calibration_error'] = round(total_weighted_error / total * 100, 1)
        
        # Pathway effectiveness
        metrics['pathway_effectiveness'] = {}
        for pathway, data in results['predictions_by_pathway'].items():
            if data['total'] > 0:
                effectiveness = data['correct'] / data['total']
                metrics['pathway_effectiveness'][pathway] = {
                    'total_predictions': data['total'],
                    'success_rate': round(effectiveness * 100, 1),
                    'volume_percentage': round(data['total'] / total * 100, 1)
                }
        
        # Market efficiency correlation
        metrics['market_efficiency'] = {}
        for market_value, data in results['market_efficiency_performance'].items():
            if data['total'] > 0:
                success_rate = data['correct'] / data['total']
                metrics['market_efficiency'][market_value] = {
                    'predictions': data['total'],
                    'success_rate': round(success_rate * 100, 1),
                    'percentage_of_total': round(data['total'] / total * 100, 1)
                }
        
        return metrics

    def generate_statistical_recommendations(self, results, metrics):
        """Generate evidence-based statistical recommendations"""
        recommendations = []
        
        # 1. Overall Accuracy Assessment
        overall_accuracy = metrics['overall']['accuracy_rate']
        if overall_accuracy < 20:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Model Performance',
                'issue': f'Extremely low accuracy rate of {overall_accuracy}%',
                'statistical_basis': 'Home run base rate is ~10-15%, model performing worse than random',
                'recommendation': 'Complete model overhaul required - current approach is fundamentally flawed',
                'specific_actions': [
                    'Pause production use until accuracy exceeds baseline random performance',
                    'Conduct feature importance analysis to identify predictive vs noise variables',
                    'Implement ensemble approach with multiple base models',
                    'Reduce prediction volume and focus on highest confidence opportunities'
                ]
            })
        elif overall_accuracy < 30:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Model Calibration',
                'issue': f'Below-expectation accuracy of {overall_accuracy}%',
                'statistical_basis': 'Significantly underperforming expected outcomes based on confidence scores',
                'recommendation': 'Major recalibration of scoring methodology required'
            })
        
        # 2. Confidence Calibration Issues
        calibration_error = metrics.get('overall_calibration_error', 0)
        if calibration_error > 20:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Confidence Calibration',
                'issue': f'Severe miscalibration with {calibration_error}% average error',
                'statistical_basis': 'Confidence scores do not correlate with actual success probability',
                'recommendation': 'Implement isotonic regression or Platt scaling for calibration',
                'specific_actions': [
                    'Create calibration curve mapping confidence scores to actual success rates',
                    'Apply post-hoc calibration to all predictions',
                    'Reduce base confidence scores by 15-25%',
                    'Implement uncertainty quantification in scoring'
                ]
            })
        
        # 3. Pathway Analysis
        pathway_stats = metrics['pathway_effectiveness']
        best_pathway = max(pathway_stats.items(), key=lambda x: x[1]['success_rate']) if pathway_stats else None
        worst_pathway = min(pathway_stats.items(), key=lambda x: x[1]['success_rate']) if pathway_stats else None
        
        if best_pathway and worst_pathway:
            performance_gap = best_pathway[1]['success_rate'] - worst_pathway[1]['success_rate']
            if performance_gap > 10:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Pathway Optimization',
                    'issue': f'Large performance gap: {best_pathway[0]} ({best_pathway[1]["success_rate"]}%) vs {worst_pathway[0]} ({worst_pathway[1]["success_rate"]}%)',
                    'statistical_basis': f'{performance_gap}% difference suggests pathway criteria are meaningful',
                    'recommendation': f'Reallocate predictions from {worst_pathway[0]} to {best_pathway[0]} pathway',
                    'specific_actions': [
                        f'Tighten criteria for {worst_pathway[0]} pathway predictions',
                        f'Expand {best_pathway[0]} pathway identification',
                        'Review feature weights contributing to pathway classification'
                    ]
                })
        
        # 4. Expected Value Analysis
        ev_data = results.get('expected_value', {})
        avg_ev = ev_data.get('avg_ev_per_bet', 0)
        if avg_ev < -10:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Expected Value',
                'issue': f'Highly negative expected value of ${avg_ev:.2f} per $100 bet',
                'statistical_basis': 'Model consistently identifies overpriced betting opportunities',
                'recommendation': 'Implement strict positive EV filtering before predictions',
                'specific_actions': [
                    'Calculate implied probability from odds and only predict when model probability > implied probability + 5% margin',
                    'Focus on longer odds where market inefficiencies are more common',
                    'Implement Kelly Criterion for optimal bet sizing based on edge'
                ]
            })
        
        # 5. Sample Size and Statistical Power
        daily_results = results['daily_results']
        if len(daily_results) > 0:
            avg_daily_predictions = sum(day['total'] for day in daily_results) / len(daily_results)
            if avg_daily_predictions > 200:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Prediction Volume',
                    'issue': f'High daily prediction volume ({avg_daily_predictions:.0f} per day)',
                    'statistical_basis': 'Volume dilution may be reducing prediction quality',
                    'recommendation': 'Implement stricter filtering to reduce volume and improve quality',
                    'specific_actions': [
                        'Increase minimum confidence threshold to 85%',
                        'Limit to top 50 predictions per day',
                        'Focus on games with optimal conditions (weather, park factors)'
                    ]
                })
        
        return recommendations

    def print_comprehensive_analysis(self, results, metrics, recommendations):
        """Print detailed analysis results"""
        print(f"\n{'='*60}")
        print(f"🎯 HELLRAISER COMPREHENSIVE STATISTICAL ANALYSIS")
        print(f"{'='*60}")
        
        # Overall Performance
        overall = metrics['overall']
        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"{'='*30}")
        print(f"Total Predictions: {overall['total_predictions']:,}")
        print(f"Correct Predictions: {overall['correct_predictions']:,}")
        print(f"Accuracy Rate: {overall['accuracy_rate']}%")
        print(f"Error Rate: {overall['error_rate']}%")
        
        # Expected Value
        ev = results['expected_value']
        print(f"\n💰 EXPECTED VALUE ANALYSIS")
        print(f"{'='*30}")
        print(f"Total Bets Analyzed: {ev['total_bets']:,}")
        print(f"Total EV: ${ev['total_ev']:,.2f}")
        print(f"Average EV per $100 bet: ${ev['avg_ev_per_bet']:.2f}")
        
        # Confidence Calibration
        print(f"\n🎯 CONFIDENCE CALIBRATION")
        print(f"{'='*35}")
        print(f"Overall Calibration Error: {metrics.get('overall_calibration_error', 'N/A')}%")
        print(f"{'Bracket':<8} {'Count':<6} {'Actual':<7} {'Expected':<8} {'Error':<6}")
        print(f"{'-'*40}")
        
        for bracket in ['95+', '90-94', '85-89', '80-84', '75-79', '70-74', '<70']:
            if bracket in metrics['calibration']:
                data = metrics['calibration'][bracket]
                print(f"{bracket:<8} {data['sample_size']:<6} {data['actual_rate']:<6.1f}% {data['expected_rate']:<7.1f}% {data['calibration_error']:<5.1f}%")
        
        # Pathway Effectiveness
        print(f"\n🛤️  PATHWAY EFFECTIVENESS")
        print(f"{'='*35}")
        print(f"{'Pathway':<15} {'Count':<6} {'Success':<8} {'Volume':<7}")
        print(f"{'-'*40}")
        
        for pathway, data in metrics['pathway_effectiveness'].items():
            print(f"{pathway:<15} {data['total_predictions']:<6} {data['success_rate']:<7.1f}% {data['volume_percentage']:<6.1f}%")
        
        # Market Efficiency
        print(f"\n📈 MARKET EFFICIENCY CORRELATION")
        print(f"{'='*40}")
        print(f"{'Market Value':<15} {'Count':<6} {'Success':<8} {'Volume':<7}")
        print(f"{'-'*40}")
        
        for market_value, data in metrics['market_efficiency'].items():
            print(f"{market_value:<15} {data['predictions']:<6} {data['success_rate']:<7.1f}% {data['percentage_of_total']:<6.1f}%")
        
        # Top Performing Players
        print(f"\n👤 TOP PERFORMERS (min 3 predictions)")
        print(f"{'='*45}")
        
        top_players = []
        for player, data in results['player_performance'].items():
            if data['total'] >= 3:
                success_rate = data['correct'] / data['total']
                top_players.append((player, data['total'], data['correct'], success_rate))
        
        top_players.sort(key=lambda x: (x[3], x[1]), reverse=True)
        
        print(f"{'Player':<20} {'Total':<6} {'Correct':<7} {'Rate':<6}")
        print(f"{'-'*40}")
        for player, total, correct, rate in top_players[:15]:
            print(f"{player[:19]:<20} {total:<6} {correct:<7} {rate*100:<5.1f}%")
        
        # Recent Daily Performance
        print(f"\n📅 RECENT DAILY PERFORMANCE")
        print(f"{'='*35}")
        
        recent_days = results['daily_results'][-10:]
        for day in recent_days:
            print(f"{day['date']}: {day['correct']:>3}/{day['total']:<3} ({day['accuracy']:>5.1f}%)")
        
        # Recommendations
        print(f"\n💡 STATISTICAL RECOMMENDATIONS")
        print(f"{'='*40}")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['category']} ({rec['priority']})")
            print(f"   Issue: {rec['issue']}")
            print(f"   Basis: {rec['statistical_basis']}")
            print(f"   Action: {rec['recommendation']}")
            if 'specific_actions' in rec:
                for action in rec['specific_actions'][:2]:  # Show top 2 actions
                    print(f"   • {action}")

    def create_statistical_report(self, results, metrics, recommendations):
        """Create detailed statistical report file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(f"hellraiser_statistical_report_{timestamp}.md")
        
        # Calculate some additional insights
        total_days = len(results['daily_results'])
        avg_daily_accuracy = sum(day['accuracy'] for day in results['daily_results']) / total_days if total_days > 0 else 0
        
        # Trend analysis
        if len(results['daily_results']) >= 7:
            recent_accuracy = sum(day['accuracy'] for day in results['daily_results'][-7:]) / 7
            early_accuracy = sum(day['accuracy'] for day in results['daily_results'][:7]) / 7
            trend = "improving" if recent_accuracy > early_accuracy else "declining"
        else:
            trend = "insufficient data"
        
        report_content = f"""# Hellraiser Statistical Validation Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

### Performance Overview
- **Total Predictions Analyzed**: {metrics['overall']['total_predictions']:,}
- **Overall Accuracy**: {metrics['overall']['accuracy_rate']}%
- **Average Daily Accuracy**: {avg_daily_accuracy:.1f}%
- **Performance Trend**: {trend}
- **Expected Value per $100 bet**: ${results['expected_value']['avg_ev_per_bet']:.2f}
- **Calibration Error**: {metrics.get('overall_calibration_error', 'N/A')}%

### Key Findings
1. **Model Performance**: {'CRITICAL ISSUES' if metrics['overall']['accuracy_rate'] < 20 else 'UNDERPERFORMING' if metrics['overall']['accuracy_rate'] < 30 else 'ACCEPTABLE'}
2. **Confidence Calibration**: {'SEVERELY MISCALIBRATED' if metrics.get('overall_calibration_error', 0) > 20 else 'NEEDS ADJUSTMENT' if metrics.get('overall_calibration_error', 0) > 10 else 'REASONABLE'}
3. **Economic Viability**: {'NOT PROFITABLE' if results['expected_value']['avg_ev_per_bet'] < -5 else 'MARGINAL' if results['expected_value']['avg_ev_per_bet'] < 5 else 'PROFITABLE'}

## Detailed Statistical Analysis

### Confidence Calibration Analysis
| Confidence Bracket | Sample Size | Actual Rate | Expected Rate | Calibration Error |
|--------------------|-------------|-------------|---------------|-------------------|
"""
        
        for bracket in ['95+', '90-94', '85-89', '80-84', '75-79', '70-74', '<70']:
            if bracket in metrics['calibration']:
                data = metrics['calibration'][bracket]
                report_content += f"| {bracket} | {data['sample_size']} | {data['actual_rate']}% | {data['expected_rate']}% | {data['calibration_error']}% |\n"
        
        report_content += f"""
### Pathway Effectiveness Analysis
| Pathway | Predictions | Success Rate | Volume % |
|---------|-------------|--------------|----------|
"""
        
        for pathway, data in metrics['pathway_effectiveness'].items():
            report_content += f"| {pathway} | {data['total_predictions']} | {data['success_rate']}% | {data['volume_percentage']}% |\n"
        
        report_content += f"""
### Market Efficiency Performance
| Market Assessment | Predictions | Success Rate | Notes |
|-------------------|-------------|--------------|-------|
"""
        
        for market_value, data in metrics['market_efficiency'].items():
            interpretation = ""
            if market_value == "positive" and data['success_rate'] > 25:
                interpretation = "✅ Good market identification"
            elif market_value == "negative" and data['success_rate'] < 15:
                interpretation = "⚠️ Correctly identified overvalued"
            elif data['success_rate'] < 15:
                interpretation = "❌ Poor performance"
            
            report_content += f"| {market_value} | {data['predictions']} | {data['success_rate']}% | {interpretation} |\n"
        
        report_content += f"""
## Statistical Recommendations

### Priority Actions
"""
        
        critical_recs = [r for r in recommendations if r['priority'] == 'CRITICAL']
        high_recs = [r for r in recommendations if r['priority'] == 'HIGH']
        
        if critical_recs:
            report_content += f"\n#### CRITICAL (Immediate Action Required)\n"
            for rec in critical_recs:
                report_content += f"- **{rec['category']}**: {rec['recommendation']}\n"
        
        if high_recs:
            report_content += f"\n#### HIGH PRIORITY\n"
            for rec in high_recs:
                report_content += f"- **{rec['category']}**: {rec['recommendation']}\n"
        
        report_content += f"""
### Mathematical Model Adjustments

#### 1. Confidence Score Recalibration
```python
# Apply calibration correction based on historical performance
calibration_factors = {{
    '95+': {metrics['calibration'].get('95+', {}).get('actual_rate', 50) / 95:.3f},
    '90-94': {metrics['calibration'].get('90-94', {}).get('actual_rate', 50) / 92:.3f},
    '85-89': {metrics['calibration'].get('85-89', {}).get('actual_rate', 50) / 87:.3f},
    # ... etc
}}

adjusted_confidence = original_confidence * calibration_factors[bracket]
```

#### 2. Expected Value Filter
```python
# Only make predictions with positive expected value
implied_prob = 1 / decimal_odds
model_prob = confidence_score / 100
edge = model_prob - implied_prob

# Minimum edge requirement
if edge > 0.05:  # 5% minimum edge
    make_prediction = True
```

#### 3. Volume Optimization
Current average: {sum(day['total'] for day in results['daily_results']) / len(results['daily_results']):.0f} predictions/day
Recommended: 50-75 predictions/day (focus on highest conviction)

## Conclusion

The Hellraiser system shows {'significant issues requiring immediate attention' if metrics['overall']['accuracy_rate'] < 20 else 'room for improvement through systematic recalibration' if metrics['overall']['accuracy_rate'] < 30 else 'reasonable performance with optimization opportunities'}. Key areas for improvement include:

1. **Confidence Calibration**: {metrics.get('overall_calibration_error', 0):.1f}% average error requires systematic correction
2. **Volume Management**: Reduce prediction volume to improve quality
3. **Market Efficiency**: {'Poor correlation between market assessment and outcomes' if any(data['success_rate'] < 15 for data in metrics['market_efficiency'].values()) else 'Market assessment shows some predictive value'}

**Recommended Implementation Timeline:**
- Week 1: Apply calibration corrections and EV filters
- Week 2-3: Optimize pathway criteria and reduce volume
- Month 2: Implement ensemble methods and advanced calibration

---
*Statistical Analysis Report - Hellraiser Prediction System*
*Analysis Period: {total_days} days | {metrics['overall']['total_predictions']:,} predictions*
"""
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Detailed statistical report saved to: {report_file}")
        return str(report_file)

def main():
    analyzer = HellraiserComprehensiveAnalysis()
    
    # Run comprehensive analysis
    results = analyzer.analyze_performance(days=15)
    
    # Calculate statistical metrics
    metrics = analyzer.calculate_statistical_metrics(results)
    
    # Generate recommendations
    recommendations = analyzer.generate_statistical_recommendations(results, metrics)
    
    # Print analysis
    analyzer.print_comprehensive_analysis(results, metrics, recommendations)
    
    # Create detailed report
    report_file = analyzer.create_statistical_report(results, metrics, recommendations)
    
    # Summary for user
    print(f"\n🔬 STATISTICAL ANALYSIS COMPLETE")
    print(f"📊 Analyzed {results['total_predictions']:,} predictions over {len(results['daily_results'])} days")
    print(f"🎯 Overall accuracy: {metrics['overall']['accuracy_rate']}%")
    print(f"💰 Average EV per bet: ${results['expected_value']['avg_ev_per_bet']:.2f}")
    print(f"📈 Calibration error: {metrics.get('overall_calibration_error', 'N/A')}%")
    print(f"⚠️  {len([r for r in recommendations if r['priority'] == 'CRITICAL'])} critical issues identified")
    print(f"📄 Detailed report: {report_file}")

if __name__ == "__main__":
    main()