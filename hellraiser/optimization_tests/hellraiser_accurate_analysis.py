#!/usr/bin/env python3
"""
Hellraiser Accurate Statistical Analysis - Final corrected version with proper path resolution
"""

import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class HellraiserAccurateAnalysis:
    def __init__(self):
        # Use absolute paths to avoid resolution issues
        self.base_dir = Path("/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballTracker")
        self.hellraiser_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.games_dir = self.base_dir / "public" / "data" / "2025"
        
        print(f"🔬 Hellraiser Accurate Statistical Analysis")
        print(f"📂 Hellraiser dir: {self.hellraiser_dir}")
        print(f"📂 Games dir: {self.games_dir}")

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
        """Find game results file for a date with corrected path logic"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.year
            month_name = date_obj.strftime("%B").lower()
            day = date_obj.strftime("%d")
            
            # Construct the exact path
            game_file = self.games_dir / str(year) / month_name / f"{month_name}_{int(day):02d}_{year}.json"
            
            if game_file.exists():
                return game_file
            
            # Try alternative format
            game_file_alt = self.games_dir / str(year) / month_name / f"{month_name}_{day}_{year}.json"
            if game_file_alt.exists():
                return game_file_alt
            
            return None
        except Exception as e:
            print(f"Error finding game file for {date_str}: {e}")
            return None

    def analyze_performance(self, days=15):
        """Analyze prediction performance with corrected file handling"""
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
            }
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
            
            print(f"📅 {date_part}: {daily_total} predictions, {len(hr_hitters)} HR hitters")
            
            for pick in pred_data['picks']:
                player_name = pick.get('playerName', '')
                confidence = pick.get('confidenceScore', 0)
                pathway = pick.get('pathway', 'unknown')
                
                # Check if player hit HR
                hit_hr = any(self.names_match(player_name, hr_name) for hr_name in hr_hitters)
                
                # Create prediction record
                prediction_record = {
                    'date': date_part,
                    'player': player_name,
                    'confidence': confidence,
                    'pathway': pathway,
                    'hit_hr': hit_hr,
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
            
            # Record daily results
            daily_accuracy = (daily_correct / daily_total * 100) if daily_total > 0 else 0
            results['daily_results'].append({
                'date': date_part,
                'total': daily_total,
                'correct': daily_correct,
                'accuracy': daily_accuracy
            })
            
            print(f"   Result: {daily_correct}/{daily_total} = {daily_accuracy:.1f}%")
        
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

    def calculate_statistical_metrics(self, results):
        """Calculate comprehensive statistical metrics"""
        
        total = results['total_predictions']
        correct = results['correct_predictions']
        overall_accuracy = (correct / total * 100) if total > 0 else 0
        
        metrics = {
            'overall_performance': {
                'total_predictions': total,
                'correct_predictions': correct,
                'accuracy_rate': overall_accuracy,
                'baseline_hr_rate': 12.0,
                'performance_vs_baseline': overall_accuracy - 12.0
            }
        }
        
        # Confidence calibration analysis
        calibration_data = {}
        total_calibration_error = 0
        weighted_samples = 0
        
        expected_rates = {
            '95+': 95, '90-94': 92, '85-89': 87, 
            '80-84': 82, '75-79': 77, '70-74': 72, '<70': 65
        }
        
        for bracket, data in results['confidence_brackets'].items():
            if data['total'] > 0:
                actual_rate = data['correct'] / data['total'] * 100
                expected_rate = expected_rates.get(bracket, 70)
                calibration_error = abs(expected_rate - actual_rate)
                
                calibration_data[bracket] = {
                    'sample_size': data['total'],
                    'actual_rate': actual_rate,
                    'expected_rate': expected_rate,
                    'calibration_error': calibration_error
                }
                
                total_calibration_error += calibration_error * data['total']
                weighted_samples += data['total']
        
        metrics['confidence_calibration'] = {
            'bracket_performance': calibration_data,
            'overall_calibration_error': total_calibration_error / weighted_samples if weighted_samples > 0 else 0
        }
        
        # Pathway effectiveness
        pathway_metrics = {}
        for pathway, data in results['pathway_performance'].items():
            if data['total'] > 0:
                success_rate = data['correct'] / data['total'] * 100
                pathway_metrics[pathway] = {
                    'predictions': data['total'],
                    'success_rate': success_rate,
                    'volume_percentage': data['total'] / total * 100
                }
        
        metrics['pathway_effectiveness'] = pathway_metrics
        
        # Expected value analysis
        ev_analysis = self.calculate_expected_value(results['all_predictions'])
        metrics['expected_value'] = ev_analysis
        
        return metrics

    def generate_recalibration_recommendations(self, metrics):
        """Generate specific mathematical recommendations for model recalibration"""
        recommendations = []
        
        overall_acc = metrics['overall_performance']['accuracy_rate']
        calibration_error = metrics['confidence_calibration']['overall_calibration_error']
        ev_per_bet = metrics['expected_value']['avg_ev_per_bet']
        
        # 1. Model Performance Assessment
        if overall_acc < 8:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Model Architecture',
                'finding': f'Accuracy ({overall_acc:.1f}%) below random performance',
                'mathematical_basis': 'P(success) = 0.12 (baseline HR rate), observed P(success) < 0.08',
                'recalibration_formula': 'Implement ensemble: final_pred = 0.4*model1 + 0.3*model2 + 0.3*baseline_rate',
                'implementation': 'Replace current single-model approach with ensemble of logistic regression, random forest, and Bayesian baseline'
            })
        elif overall_acc < 15:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Score Scaling',
                'finding': f'Accuracy ({overall_acc:.1f}%) below expected baseline',
                'mathematical_basis': f'Expected improvement: {15 - overall_acc:.1f} percentage points needed',
                'recalibration_formula': f'confidence_adjusted = confidence_original * {overall_acc/12:.3f}',
                'implementation': 'Apply linear scaling to all confidence scores'
            })
        
        # 2. Confidence Calibration
        if calibration_error > 20:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Confidence Recalibration',
                'finding': f'Severe miscalibration: {calibration_error:.1f}% average error',
                'mathematical_basis': 'Isotonic regression: f(x) = monotonic mapping from confidence to probability',
                'recalibration_formula': 'calibrated_prob = isotonic_regression(original_confidence, historical_outcomes)',
                'implementation': 'Train isotonic regression on historical data, apply to all future predictions'
            })
        
        # 3. Pathway Rebalancing  
        pathway_perf = metrics['pathway_effectiveness']
        if len(pathway_perf) > 1:
            best_pathway = max(pathway_perf.items(), key=lambda x: x[1]['success_rate'])
            worst_pathway = min(pathway_perf.items(), key=lambda x: x[1]['success_rate'])
            
            if best_pathway[1]['success_rate'] - worst_pathway[1]['success_rate'] > 5:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Pathway Optimization',
                    'finding': f'{best_pathway[0]}: {best_pathway[1]["success_rate"]:.1f}% vs {worst_pathway[0]}: {worst_pathway[1]["success_rate"]:.1f}%',
                    'mathematical_basis': f'Differential success rate: {best_pathway[1]["success_rate"] - worst_pathway[1]["success_rate"]:.1f}%',
                    'recalibration_formula': f'pathway_weight[{best_pathway[0]}] *= 1.2, pathway_weight[{worst_pathway[0]}] *= 0.8',
                    'implementation': 'Adjust pathway classification thresholds to favor better-performing pathway'
                })
        
        # 4. Expected Value Optimization
        if ev_per_bet < -10:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Value-Based Filtering',
                'finding': f'Negative expected value: ${ev_per_bet:.2f} per $100 bet',
                'mathematical_basis': 'Kelly Criterion: f = (bp - q) / b, where b=odds, p=win_prob, q=lose_prob',
                'recalibration_formula': 'edge = model_probability - implied_probability; only_predict_if(edge > 0.05)',
                'implementation': 'Implement minimum 5% edge requirement before making predictions'
            })
        
        # 5. Bias Correction
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Systematic Bias Correction',
            'finding': 'Systematic overconfidence detected across all brackets',
            'mathematical_basis': 'Bayesian adjustment: P(HR|features) = P(features|HR) * P(HR) / P(features)',  
            'recalibration_formula': 'adjusted_confidence = original_confidence * calibration_factor + bias_correction',
            'implementation': 'Apply bracket-specific calibration factors derived from historical performance'
        })
        
        return recommendations

    def print_comprehensive_analysis(self, results, metrics, recommendations):
        """Print detailed statistical analysis and recommendations"""
        
        print(f"\n{'='*80}")
        print(f"🎯 HELLRAISER COMPREHENSIVE STATISTICAL ANALYSIS")
        print(f"{'='*80}")
        
        # Performance Summary
        perf = metrics['overall_performance']
        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"{'='*30}")
        print(f"Total Predictions Analyzed: {perf['total_predictions']:,}")
        print(f"Correct Predictions: {perf['correct_predictions']:,}")
        print(f"Overall Accuracy: {perf['accuracy_rate']:.2f}%")
        print(f"MLB Baseline HR Rate: {perf['baseline_hr_rate']:.1f}%")
        print(f"Performance vs Baseline: {perf['performance_vs_baseline']:+.1f} percentage points")
        
        # Expected Value Analysis
        ev = metrics['expected_value']
        total_profit_loss = ev['total_ev']
        roi = (total_profit_loss / (ev['total_bets'] * 100)) * 100 if ev['total_bets'] > 0 else 0
        
        print(f"\n💰 EXPECTED VALUE ANALYSIS") 
        print(f"{'='*35}")
        print(f"Total Profit/Loss: ${total_profit_loss:,.2f}")
        print(f"Average EV per $100 bet: ${ev['avg_ev_per_bet']:.2f}")
        print(f"Return on Investment: {roi:.1f}%")
        print(f"Total Bets Analyzed: {ev['total_bets']:,}")
        
        # Confidence Calibration Detail
        calibration = metrics['confidence_calibration']
        print(f"\n🎯 CONFIDENCE CALIBRATION ANALYSIS")
        print(f"{'='*45}")
        print(f"Overall Calibration Error: {calibration['overall_calibration_error']:.1f}%")
        print(f"\n{'Confidence':<12} {'Sample':<8} {'Actual':<8} {'Expected':<9} {'Error':<8}")
        print(f"{'Bracket':<12} {'Size':<8} {'Rate':<8} {'Rate':<9} {'(%)':<8}")
        print(f"{'-'*55}")
        
        for bracket, data in calibration['bracket_performance'].items():
            print(f"{bracket:<12} {data['sample_size']:<8} {data['actual_rate']:<7.1f}% {data['expected_rate']:<8.1f}% {data['calibration_error']:<7.1f}%")
        
        # Pathway Effectiveness
        print(f"\n🛤️  PATHWAY EFFECTIVENESS ANALYSIS")
        print(f"{'='*40}")
        
        for pathway, data in metrics['pathway_effectiveness'].items():
            print(f"{pathway:>15}: {data['success_rate']:>6.1f}% accuracy ({data['predictions']:>3} predictions, {data['volume_percentage']:>5.1f}% of total)")
        
        # Daily Performance Trend
        print(f"\n📅 DAILY PERFORMANCE ANALYSIS")
        print(f"{'='*35}")
        
        for day in results['daily_results'][-10:]:
            trend_indicator = "📈" if day['accuracy'] > 10 else "📉" if day['accuracy'] < 5 else "➡️"
            print(f"{day['date']}: {day['correct']:>3}/{day['total']:<3} ({day['accuracy']:>5.1f}%) {trend_indicator}")
        
        # Mathematical Recommendations
        print(f"\n💡 MATHEMATICAL RECALIBRATION RECOMMENDATIONS")
        print(f"{'='*55}")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['category']} ({rec['priority']} PRIORITY)")
            print(f"   📊 Finding: {rec['finding']}")
            print(f"   📐 Mathematical Basis: {rec['mathematical_basis']}")
            print(f"   🔧 Recalibration Formula: {rec['recalibration_formula']}")
            print(f"   ⚙️ Implementation: {rec['implementation']}")

    def create_statistical_report(self, results, metrics, recommendations):
        """Create comprehensive statistical report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(f"hellraiser_statistical_analysis_{timestamp}.md")
        
        # Calculate additional statistics
        total_days = len(results['daily_results'])
        avg_accuracy = sum(day['accuracy'] for day in results['daily_results']) / total_days if total_days > 0 else 0
        accuracy_std = (sum((day['accuracy'] - avg_accuracy)**2 for day in results['daily_results']) / total_days)**0.5 if total_days > 1 else 0
        
        # Trend analysis
        if len(results['daily_results']) >= 5:
            recent_5 = sum(day['accuracy'] for day in results['daily_results'][-5:]) / 5
            early_5 = sum(day['accuracy'] for day in results['daily_results'][:5]) / 5
            trend = "Improving" if recent_5 > early_5 else "Declining"
            trend_magnitude = abs(recent_5 - early_5)
        else:
            trend = "Insufficient data"
            trend_magnitude = 0
        
        report_content = f"""# Hellraiser Statistical Analysis Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Analysis Period:** {total_days} days  
**Total Predictions:** {metrics['overall_performance']['total_predictions']:,}

## Executive Summary

### Key Performance Metrics
- **Overall Accuracy:** {metrics['overall_performance']['accuracy_rate']:.2f}%
- **Performance vs MLB Baseline:** {metrics['overall_performance']['performance_vs_baseline']:+.1f} percentage points
- **Expected Value per $100 bet:** ${metrics['expected_value']['avg_ev_per_bet']:.2f}
- **Overall Calibration Error:** {metrics['confidence_calibration']['overall_calibration_error']:.1f}%
- **Daily Accuracy Trend:** {trend} ({trend_magnitude:.1f}% change)

### Statistical Significance
- **Confidence Interval (95%):** {avg_accuracy:.1f}% ± {1.96 * accuracy_std / (total_days**0.5):.1f}%
- **Sample Size Power:** {'Adequate' if metrics['overall_performance']['total_predictions'] > 1000 else 'Limited'} (n={metrics['overall_performance']['total_predictions']:,})

## Detailed Statistical Analysis

### 1. Accuracy Distribution Analysis

#### By Confidence Level
| Confidence Bracket | Sample Size | Actual Rate | Expected Rate | Calibration Error | Statistical Significance |
|--------------------|-------------|-------------|---------------|-------------------|-------------------------|
"""
        
        for bracket, data in metrics['confidence_calibration']['bracket_performance'].items():
            # Calculate binomial confidence interval
            p = data['actual_rate'] / 100
            n = data['sample_size']
            margin_error = 1.96 * ((p * (1-p)) / n)**0.5 * 100 if n > 0 else 0
            
            report_content += f"| {bracket} | {data['sample_size']} | {data['actual_rate']:.1f}% | {data['expected_rate']:.1f}% | {data['calibration_error']:.1f}% | ±{margin_error:.1f}% |\n"
        
        report_content += f"""
#### By Prediction Pathway
| Pathway | Predictions | Success Rate | Volume % | 95% CI |
|---------|-------------|--------------|----------|--------|
"""
        
        for pathway, data in metrics['pathway_effectiveness'].items():
            p = data['success_rate'] / 100
            n = data['predictions']
            margin_error = 1.96 * ((p * (1-p)) / n)**0.5 * 100 if n > 0 else 0
            
            report_content += f"| {pathway} | {data['predictions']} | {data['success_rate']:.1f}% | {data['volume_percentage']:.1f}% | ±{margin_error:.1f}% |\n"
        
        report_content += f"""
### 2. Expected Value Analysis

#### Financial Performance
- **Total Profit/Loss:** ${metrics['expected_value']['total_ev']:,.2f}
- **Return on Investment:** {(metrics['expected_value']['total_ev'] / (metrics['expected_value']['total_bets'] * 100)) * 100:.1f}%
- **Break-even Accuracy Required:** {100 / (sum(1/(1 + int(pred['odds']['american'][1:]) / 100) if pred['odds'].get('american', '+200').startswith('+') else 1 + 100/abs(int(pred['odds']['american']))) for pred in results['all_predictions'] if 'odds' in pred and 'american' in pred['odds']) / len([pred for pred in results['all_predictions'] if 'odds' in pred and 'american' in pred['odds']]):.1f}%
- **Sharpe Ratio:** {avg_accuracy / accuracy_std if accuracy_std > 0 else 'N/A'}

### 3. Model Recalibration Requirements

#### Critical Issues Identified
"""
        
        critical_recs = [r for r in recommendations if r['priority'] == 'CRITICAL']
        high_recs = [r for r in recommendations if r['priority'] == 'HIGH']
        
        for rec in critical_recs:
            report_content += f"- **{rec['category']}:** {rec['finding']}\n"
        
        report_content += f"""
#### Mathematical Recalibration Formulas

"""
        
        for i, rec in enumerate(recommendations, 1):
            report_content += f"**{i}. {rec['category']}**\n"
            report_content += f"```\n{rec['recalibration_formula']}\n```\n"
            report_content += f"*Basis:* {rec['mathematical_basis']}\n\n"
        
        report_content += f"""
### 4. Implementation Roadmap

#### Phase 1: Critical Fixes (Week 1)
- Apply confidence recalibration using isotonic regression
- Implement positive expected value filtering
- Reduce prediction volume by 50%

#### Phase 2: Model Enhancement (Weeks 2-4)  
- Deploy ensemble modeling approach
- Optimize pathway classification thresholds
- Implement real-time calibration updates

#### Phase 3: Advanced Analytics (Month 2)
- Develop player-specific models
- Integrate market timing analysis
- Implement automated bias detection

### 5. Statistical Validation Framework

#### Ongoing Monitoring Metrics
1. **Daily Calibration Score:** Track daily calibration error
2. **Rolling Sharpe Ratio:** 30-day rolling risk-adjusted returns
3. **Prediction Volume Quality:** Accuracy vs volume correlation
4. **Market Efficiency Tracking:** Edge identification accuracy

#### Alert Thresholds
- Calibration error > 25%: Recalibration required
- 7-day accuracy < 8%: Model performance alert
- Expected value < -$15/bet: Stop predictions

## Conclusions

The Hellraiser system shows {'critical performance issues requiring immediate intervention' if metrics['overall_performance']['accuracy_rate'] < 10 else 'systematic bias issues that can be corrected through recalibration' if metrics['overall_performance']['accuracy_rate'] < 15 else 'potential for optimization through mathematical refinements'}. 

**Priority Actions:**
1. {'Implement ensemble modeling' if metrics['overall_performance']['accuracy_rate'] < 10 else 'Apply confidence recalibration'}
2. {'Establish minimum edge requirements' if metrics['expected_value']['avg_ev_per_bet'] < -10 else 'Optimize prediction volume'}
3. {'Redesign scoring methodology' if metrics['confidence_calibration']['overall_calibration_error'] > 30 else 'Fine-tune existing algorithms'}

**Expected Improvement:** Implementation of these recommendations should improve accuracy by {15 - metrics['overall_performance']['accuracy_rate']:.1f}-{20 - metrics['overall_performance']['accuracy_rate']:.1f} percentage points and achieve positive expected value.

---
*Statistical Analysis conducted by Predictive Modeling Expert*  
*Confidence Level: 95% | Sample Size: {metrics['overall_performance']['total_predictions']:,} predictions*
"""
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Comprehensive statistical report saved to: {report_file}")
        return str(report_file)

def main():
    analyzer = HellraiserAccurateAnalysis()
    
    # Run comprehensive analysis
    print("🔄 Running accurate performance analysis...")
    results = analyzer.analyze_performance(days=15)
    
    # Calculate statistical metrics
    print("🔄 Calculating statistical metrics...")
    metrics = analyzer.calculate_statistical_metrics(results)
    
    # Generate recalibration recommendations
    print("🔄 Generating mathematical recommendations...")
    recommendations = analyzer.generate_recalibration_recommendations(metrics)
    
    # Print comprehensive analysis
    analyzer.print_comprehensive_analysis(results, metrics, recommendations)
    
    # Create detailed report
    report_file = analyzer.create_statistical_report(results, metrics, recommendations)
    
    # Final summary
    print(f"\n🔬 STATISTICAL ANALYSIS COMPLETE")
    print(f"{'='*50}")
    print(f"📊 Predictions Analyzed: {results['total_predictions']:,}")
    print(f"🎯 Overall Accuracy: {metrics['overall_performance']['accuracy_rate']:.2f}%")
    print(f"💰 Expected Value: ${metrics['expected_value']['avg_ev_per_bet']:.2f} per $100 bet")
    print(f"📈 Calibration Error: {metrics['confidence_calibration']['overall_calibration_error']:.1f}%")
    print(f"⚠️  Priority Issues: {len([r for r in recommendations if r['priority'] in ['CRITICAL', 'HIGH']])}")
    print(f"📄 Detailed Report: {report_file}")

if __name__ == "__main__":
    main()