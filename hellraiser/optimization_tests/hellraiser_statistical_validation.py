#!/usr/bin/env python3
"""
Hellraiser Statistical Validation and Performance Analysis

This script performs comprehensive statistical analysis of the Hellraiser prediction system
by comparing predictions against actual game results, calculating accuracy metrics,
and providing specific recommendations for model recalibration.

Author: Statistical Analysis Expert
Date: August 2025
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class HellraiserStatisticalValidator:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            script_dir = Path(__file__).parent.absolute()
            self.base_dir = script_dir.parent / "BaseballTracker"
        else:
            self.base_dir = Path(base_dir)
        
        self.hellraiser_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.games_dir = self.base_dir / "public" / "data" / "2025"
        self.output_dir = Path("hellraiser_validation_results")
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"🔬 Hellraiser Statistical Validator Initialized")
        print(f"📊 Output directory: {self.output_dir}")

    def load_prediction_data(self, file_path: Path) -> Optional[Dict]:
        """Load Hellraiser prediction data"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            return None

    def load_game_results(self, date: str) -> Optional[Dict]:
        """Load actual game results for a specific date"""
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            year = date_obj.year
            month_name = date_obj.strftime("%B").lower()
            day = date_obj.strftime("%d")
            
            # Try different file formats
            possible_paths = [
                self.games_dir / str(year) / month_name / f"{month_name}_{day}_{year}.json",
                self.games_dir / str(year) / month_name / f"{month_name}_{int(day):02d}_{year}.json"
            ]
            
            for game_file in possible_paths:
                if game_file.exists():
                    with open(game_file, 'r') as f:
                        return json.load(f)
            
            return None
        except Exception as e:
            print(f"❌ Error loading game results for {date}: {e}")
            return None

    def extract_home_runs(self, game_data: Dict) -> List[str]:
        """Extract players who hit home runs from game data"""
        home_run_hitters = []
        
        if not game_data or 'games' not in game_data:
            return home_run_hitters
        
        for game in game_data['games']:
            # Check both teams' player stats
            for team_key in ['awayTeam', 'homeTeam']:
                if team_key in game and 'playerStats' in game[team_key]:
                    for player in game[team_key]['playerStats']:
                        if 'battingStats' in player:
                            stats = player['battingStats']
                            # Check for home runs
                            if stats.get('HR', 0) > 0 or stats.get('homeRuns', 0) > 0:
                                player_name = player.get('name', '').strip()
                                if player_name:
                                    # Handle name formats
                                    home_run_hitters.append(player_name)
        
        return home_run_hitters

    def normalize_player_name(self, name: str) -> str:
        """Normalize player names for comparison"""
        # Convert to lowercase and remove extra spaces
        name = ' '.join(name.lower().strip().split())
        
        # Handle common name format variations
        # "First Last" vs "Last, First" vs "F. Last"
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        
        return name

    def calculate_prediction_accuracy(self, start_date: str = None, end_date: str = None, days: int = 30) -> Dict:
        """Calculate comprehensive prediction accuracy metrics"""
        
        # Get date range
        if days and not end_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            start_date_str = start_date or "2025-06-23"
            end_date_str = end_date or datetime.now().strftime("%Y-%m-%d")
        
        print(f"\n📅 Analyzing predictions from {start_date_str} to {end_date_str}")
        
        # Initialize tracking structures
        all_predictions = []
        prediction_results = []
        pathway_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'confidence_sum': 0})
        confidence_brackets = {
            '90-95': {'correct': 0, 'total': 0, 'predictions': []},
            '85-89': {'correct': 0, 'total': 0, 'predictions': []},
            '80-84': {'correct': 0, 'total': 0, 'predictions': []},
            '75-79': {'correct': 0, 'total': 0, 'predictions': []},
            '70-74': {'correct': 0, 'total': 0, 'predictions': []},
            '60-69': {'correct': 0, 'total': 0, 'predictions': []},
            '<60': {'correct': 0, 'total': 0, 'predictions': []}
        }
        classification_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        # Process each prediction file
        for file_path in sorted(self.hellraiser_dir.glob("hellraiser_analysis_*.json")):
            date_part = file_path.name.replace("hellraiser_analysis_", "").replace(".json", "")
            
            if start_date_str <= date_part <= end_date_str:
                pred_data = self.load_prediction_data(file_path)
                if not pred_data or 'picks' not in pred_data:
                    continue
                
                # Load game results for this date
                game_results = self.load_game_results(date_part)
                home_run_hitters = self.extract_home_runs(game_results) if game_results else []
                
                # Normalize home run hitter names
                normalized_hr_hitters = [self.normalize_player_name(name) for name in home_run_hitters]
                
                # Process each prediction
                for pick in pred_data['picks']:
                    player_name = pick.get('playerName', '')
                    confidence = pick.get('confidenceScore', 0)
                    pathway = pick.get('pathway', 'unknown')
                    classification = pick.get('classification', 'unknown')
                    odds = pick.get('odds', {})
                    
                    # Normalize predicted player name
                    normalized_pred_name = self.normalize_player_name(player_name)
                    
                    # Check if prediction was correct
                    hit_hr = normalized_pred_name in normalized_hr_hitters
                    
                    # Create prediction record
                    prediction_record = {
                        'date': date_part,
                        'player': player_name,
                        'confidence': confidence,
                        'pathway': pathway,
                        'classification': classification,
                        'odds': odds,
                        'hit_hr': hit_hr,
                        'market_efficiency': pick.get('marketEfficiency', {})
                    }
                    
                    all_predictions.append(prediction_record)
                    prediction_results.append({
                        'confidence': confidence,
                        'hit_hr': hit_hr,
                        'pathway': pathway,
                        'classification': classification
                    })
                    
                    # Update pathway performance
                    pathway_performance[pathway]['total'] += 1
                    pathway_performance[pathway]['confidence_sum'] += confidence
                    if hit_hr:
                        pathway_performance[pathway]['correct'] += 1
                    
                    # Update confidence bracket performance
                    bracket = self._get_confidence_bracket(confidence)
                    confidence_brackets[bracket]['total'] += 1
                    confidence_brackets[bracket]['predictions'].append(prediction_record)
                    if hit_hr:
                        confidence_brackets[bracket]['correct'] += 1
                    
                    # Update classification performance
                    classification_performance[classification]['total'] += 1
                    if hit_hr:
                        classification_performance[classification]['correct'] += 1
        
        print(f"✅ Analyzed {len(all_predictions)} predictions")
        
        # Calculate comprehensive metrics
        metrics = self._calculate_comprehensive_metrics(
            all_predictions, 
            prediction_results,
            pathway_performance,
            confidence_brackets,
            classification_performance
        )
        
        return metrics

    def _get_confidence_bracket(self, confidence: float) -> str:
        """Determine confidence bracket for a score"""
        if confidence >= 90:
            return '90-95'
        elif confidence >= 85:
            return '85-89'
        elif confidence >= 80:
            return '80-84'
        elif confidence >= 75:
            return '75-79'
        elif confidence >= 70:
            return '70-74'
        elif confidence >= 60:
            return '60-69'
        else:
            return '<60'

    def _calculate_comprehensive_metrics(self, all_predictions, prediction_results, 
                                       pathway_performance, confidence_brackets,
                                       classification_performance) -> Dict:
        """Calculate comprehensive statistical metrics"""
        
        # Overall accuracy
        total_predictions = len(prediction_results)
        correct_predictions = sum(1 for p in prediction_results if p['hit_hr'])
        overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # Expected value calculations
        ev_analysis = self._calculate_expected_value(all_predictions)
        
        # Confidence calibration
        calibration_analysis = self._analyze_confidence_calibration(confidence_brackets)
        
        # Statistical tests
        statistical_tests = self._perform_statistical_tests(prediction_results, confidence_brackets)
        
        # Bias analysis
        bias_analysis = self._analyze_prediction_biases(all_predictions)
        
        # ROC analysis
        roc_analysis = self._calculate_roc_metrics(prediction_results)
        
        return {
            'summary': {
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'overall_accuracy': round(overall_accuracy * 100, 2),
                'date_range': f"{all_predictions[0]['date']} to {all_predictions[-1]['date']}" if all_predictions else "N/A"
            },
            'pathway_performance': self._format_pathway_performance(pathway_performance),
            'confidence_accuracy': self._format_confidence_accuracy(confidence_brackets),
            'classification_performance': self._format_classification_performance(classification_performance),
            'expected_value': ev_analysis,
            'calibration': calibration_analysis,
            'statistical_tests': statistical_tests,
            'bias_analysis': bias_analysis,
            'roc_analysis': roc_analysis
        }

    def _calculate_expected_value(self, predictions: List[Dict]) -> Dict:
        """Calculate expected value analysis"""
        ev_results = {
            'overall': {'total_ev': 0, 'avg_ev_per_bet': 0, 'profitable_rate': 0},
            'by_confidence': {},
            'by_pathway': {},
            'by_odds_range': {}
        }
        
        # Process each prediction for EV
        total_bets = 0
        profitable_bets = 0
        
        for pred in predictions:
            odds = pred['odds']
            if isinstance(odds, dict) and 'american' in odds:
                american_odds = odds['american']
            else:
                continue
            
            # Convert American odds to decimal
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
            
            # Calculate EV (assuming $100 bet)
            bet_amount = 100
            if pred['hit_hr']:
                profit = (decimal_odds - 1) * bet_amount
            else:
                profit = -bet_amount
            
            total_bets += 1
            if profit > 0:
                profitable_bets += 1
            
            ev_results['overall']['total_ev'] += profit
            
            # Track by confidence
            bracket = self._get_confidence_bracket(pred['confidence'])
            if bracket not in ev_results['by_confidence']:
                ev_results['by_confidence'][bracket] = {'total_ev': 0, 'bets': 0}
            ev_results['by_confidence'][bracket]['total_ev'] += profit
            ev_results['by_confidence'][bracket]['bets'] += 1
            
            # Track by pathway
            pathway = pred['pathway']
            if pathway not in ev_results['by_pathway']:
                ev_results['by_pathway'][pathway] = {'total_ev': 0, 'bets': 0}
            ev_results['by_pathway'][pathway]['total_ev'] += profit
            ev_results['by_pathway'][pathway]['bets'] += 1
        
        # Calculate averages
        if total_bets > 0:
            ev_results['overall']['avg_ev_per_bet'] = round(ev_results['overall']['total_ev'] / total_bets, 2)
            ev_results['overall']['profitable_rate'] = round(profitable_bets / total_bets * 100, 2)
        
        # Calculate averages for segments
        for segment in ['by_confidence', 'by_pathway']:
            for key in ev_results[segment]:
                if ev_results[segment][key]['bets'] > 0:
                    ev_results[segment][key]['avg_ev'] = round(
                        ev_results[segment][key]['total_ev'] / ev_results[segment][key]['bets'], 2
                    )
        
        return ev_results

    def _analyze_confidence_calibration(self, confidence_brackets: Dict) -> Dict:
        """Analyze confidence score calibration"""
        calibration = {
            'brier_score': 0,
            'calibration_error': 0,
            'bracket_analysis': {},
            'recommendations': []
        }
        
        # Calculate calibration for each bracket
        total_predictions = 0
        weighted_calibration_error = 0
        
        for bracket, data in confidence_brackets.items():
            if data['total'] == 0:
                continue
            
            # Get midpoint of bracket for expected probability
            if bracket == '90-95':
                expected_prob = 0.925
            elif bracket == '85-89':
                expected_prob = 0.87
            elif bracket == '80-84':
                expected_prob = 0.82
            elif bracket == '75-79':
                expected_prob = 0.77
            elif bracket == '70-74':
                expected_prob = 0.72
            elif bracket == '60-69':
                expected_prob = 0.645
            else:  # <60
                expected_prob = 0.50
            
            actual_prob = data['correct'] / data['total']
            calibration_error = abs(expected_prob - actual_prob)
            
            calibration['bracket_analysis'][bracket] = {
                'expected_accuracy': round(expected_prob * 100, 1),
                'actual_accuracy': round(actual_prob * 100, 1),
                'calibration_error': round(calibration_error * 100, 1),
                'sample_size': data['total']
            }
            
            weighted_calibration_error += calibration_error * data['total']
            total_predictions += data['total']
            
            # Generate recommendation if poorly calibrated
            if calibration_error > 0.15:  # 15% calibration error threshold
                if actual_prob < expected_prob:
                    calibration['recommendations'].append(
                        f"Confidence scores in {bracket} range are overconfident by {calibration_error*100:.1f}%"
                    )
                else:
                    calibration['recommendations'].append(
                        f"Confidence scores in {bracket} range are underconfident by {calibration_error*100:.1f}%"
                    )
        
        # Overall calibration error
        if total_predictions > 0:
            calibration['calibration_error'] = round(weighted_calibration_error / total_predictions * 100, 2)
        
        # Brier score calculation
        brier_sum = 0
        for pred_data in confidence_brackets.values():
            for pred in pred_data['predictions']:
                prob = pred['confidence'] / 100
                outcome = 1 if pred['hit_hr'] else 0
                brier_sum += (prob - outcome) ** 2
        
        if total_predictions > 0:
            calibration['brier_score'] = round(brier_sum / total_predictions, 4)
        
        return calibration

    def _perform_statistical_tests(self, predictions: List[Dict], confidence_brackets: Dict) -> Dict:
        """Perform statistical significance tests"""
        tests = {
            'chi_square_pathway': {},
            'confidence_correlation': {},
            'binomial_test': {},
            'recommendations': []
        }
        
        # Chi-square test for pathway independence
        pathway_counts = defaultdict(lambda: {'hit': 0, 'miss': 0})
        for pred in predictions:
            if pred['hit_hr']:
                pathway_counts[pred['pathway']]['hit'] += 1
            else:
                pathway_counts[pred['pathway']]['miss'] += 1
        
        # Create contingency table
        pathways = list(pathway_counts.keys())
        if len(pathways) >= 2:
            contingency_table = []
            for pathway in pathways:
                contingency_table.append([
                    pathway_counts[pathway]['hit'],
                    pathway_counts[pathway]['miss']
                ])
            
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            tests['chi_square_pathway'] = {
                'chi2_statistic': round(chi2, 4),
                'p_value': round(p_value, 4),
                'significant': p_value < 0.05,
                'interpretation': 'Pathways have significantly different success rates' if p_value < 0.05 
                                else 'No significant difference between pathway success rates'
            }
        
        # Correlation between confidence and accuracy
        confidences = [p['confidence'] for p in predictions]
        outcomes = [1 if p['hit_hr'] else 0 for p in predictions]
        
        if len(set(confidences)) > 1:  # Need variation in confidence scores
            correlation, p_value = stats.pearsonr(confidences, outcomes)
            tests['confidence_correlation'] = {
                'correlation': round(correlation, 4),
                'p_value': round(p_value, 4),
                'significant': p_value < 0.05,
                'interpretation': f"{'Positive' if correlation > 0 else 'Negative'} correlation between confidence and success"
            }
            
            if abs(correlation) < 0.1:
                tests['recommendations'].append(
                    "Weak correlation between confidence scores and outcomes suggests poor calibration"
                )
        
        # Binomial test for overall accuracy vs expected
        total = len(predictions)
        successes = sum(1 for p in predictions if p['hit_hr'])
        
        # Expected success rate based on average odds
        avg_confidence = np.mean(confidences)
        expected_rate = avg_confidence / 100
        
        binomial_result = stats.binomtest(successes, total, expected_rate)
        tests['binomial_test'] = {
            'observed_rate': round(successes / total, 4),
            'expected_rate': round(expected_rate, 4),
            'p_value': round(binomial_result.pvalue, 4),
            'significant': binomial_result.pvalue < 0.05,
            'interpretation': 'Actual success rate significantly differs from expected' if binomial_result.pvalue < 0.05
                            else 'Actual success rate matches expected'
        }
        
        return tests

    def _analyze_prediction_biases(self, predictions: List[Dict]) -> Dict:
        """Analyze various biases in predictions"""
        biases = {
            'player_concentration': {},
            'team_distribution': {},
            'temporal_patterns': {},
            'market_efficiency_bias': {},
            'recommendations': []
        }
        
        # Player concentration analysis
        player_counts = Counter(p['player'] for p in predictions)
        top_10_players = player_counts.most_common(10)
        total_predictions = len(predictions)
        top_10_predictions = sum(count for _, count in top_10_players)
        
        biases['player_concentration'] = {
            'top_10_players': top_10_players,
            'top_10_percentage': round(top_10_predictions / total_predictions * 100, 2),
            'unique_players': len(player_counts),
            'gini_coefficient': self._calculate_gini(list(player_counts.values()))
        }
        
        if biases['player_concentration']['top_10_percentage'] > 40:
            biases['recommendations'].append(
                f"High player concentration: Top 10 players account for {biases['player_concentration']['top_10_percentage']}% of predictions"
            )
        
        # Temporal patterns (day of week bias)
        day_performance = defaultdict(lambda: {'total': 0, 'correct': 0})
        for pred in predictions:
            date_obj = datetime.strptime(pred['date'], "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            day_performance[day_name]['total'] += 1
            if pred['hit_hr']:
                day_performance[day_name]['correct'] += 1
        
        biases['temporal_patterns']['day_of_week'] = {
            day: {
                'accuracy': round(data['correct'] / data['total'] * 100, 2) if data['total'] > 0 else 0,
                'sample_size': data['total']
            }
            for day, data in day_performance.items()
        }
        
        # Market efficiency bias
        market_categories = defaultdict(lambda: {'total': 0, 'correct': 0})
        for pred in predictions:
            market_eff = pred.get('market_efficiency', {})
            value = market_eff.get('value', 'neutral')
            market_categories[value]['total'] += 1
            if pred['hit_hr']:
                market_categories[value]['correct'] += 1
        
        biases['market_efficiency_bias'] = {
            category: {
                'accuracy': round(data['correct'] / data['total'] * 100, 2) if data['total'] > 0 else 0,
                'sample_size': data['total']
            }
            for category, data in market_categories.items()
        }
        
        return biases

    def _calculate_gini(self, values: List[int]) -> float:
        """Calculate Gini coefficient for concentration analysis"""
        sorted_values = sorted(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        return round((n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n, 4)

    def _calculate_roc_metrics(self, predictions: List[Dict]) -> Dict:
        """Calculate ROC curve metrics"""
        if not predictions:
            return {}
        
        # Sort by confidence descending
        sorted_preds = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
        
        # Calculate ROC points
        roc_points = []
        total_positive = sum(1 for p in predictions if p['hit_hr'])
        total_negative = len(predictions) - total_positive
        
        true_positives = 0
        false_positives = 0
        
        for i, pred in enumerate(sorted_preds):
            if pred['hit_hr']:
                true_positives += 1
            else:
                false_positives += 1
            
            tpr = true_positives / total_positive if total_positive > 0 else 0
            fpr = false_positives / total_negative if total_negative > 0 else 0
            
            roc_points.append({
                'threshold': pred['confidence'],
                'tpr': tpr,
                'fpr': fpr
            })
        
        # Calculate AUC using trapezoidal rule
        auc = 0
        for i in range(1, len(roc_points)):
            auc += (roc_points[i]['fpr'] - roc_points[i-1]['fpr']) * \
                   (roc_points[i]['tpr'] + roc_points[i-1]['tpr']) / 2
        
        return {
            'auc': round(auc, 4),
            'interpretation': self._interpret_auc(auc),
            'optimal_threshold': self._find_optimal_threshold(roc_points)
        }

    def _interpret_auc(self, auc: float) -> str:
        """Interpret AUC value"""
        if auc >= 0.9:
            return "Excellent discrimination"
        elif auc >= 0.8:
            return "Good discrimination"
        elif auc >= 0.7:
            return "Fair discrimination"
        elif auc >= 0.6:
            return "Poor discrimination"
        else:
            return "No discrimination (random performance)"

    def _find_optimal_threshold(self, roc_points: List[Dict]) -> Dict:
        """Find optimal confidence threshold using Youden's J statistic"""
        best_j = -1
        best_threshold = 0
        
        for point in roc_points:
            j = point['tpr'] - point['fpr']  # Youden's J
            if j > best_j:
                best_j = j
                best_threshold = point['threshold']
        
        return {
            'confidence_threshold': best_threshold,
            'youden_j': round(best_j, 4)
        }

    def _format_pathway_performance(self, pathway_performance: Dict) -> Dict:
        """Format pathway performance data"""
        formatted = {}
        for pathway, data in pathway_performance.items():
            accuracy = data['correct'] / data['total'] if data['total'] > 0 else 0
            avg_confidence = data['confidence_sum'] / data['total'] if data['total'] > 0 else 0
            
            formatted[pathway] = {
                'total_predictions': data['total'],
                'correct_predictions': data['correct'],
                'accuracy': round(accuracy * 100, 2),
                'average_confidence': round(avg_confidence, 2)
            }
        return formatted

    def _format_confidence_accuracy(self, confidence_brackets: Dict) -> Dict:
        """Format confidence bracket accuracy data"""
        formatted = {}
        for bracket, data in confidence_brackets.items():
            if data['total'] > 0:
                accuracy = data['correct'] / data['total']
                formatted[bracket] = {
                    'total_predictions': data['total'],
                    'correct_predictions': data['correct'],
                    'accuracy': round(accuracy * 100, 2)
                }
        return formatted

    def _format_classification_performance(self, classification_performance: Dict) -> Dict:
        """Format classification performance data"""
        formatted = {}
        for classification, data in classification_performance.items():
            if data['total'] > 0:
                accuracy = data['correct'] / data['total']
                formatted[classification] = {
                    'total_predictions': data['total'],
                    'correct_predictions': data['correct'],
                    'accuracy': round(accuracy * 100, 2)
                }
        return formatted

    def generate_recalibration_recommendations(self, metrics: Dict) -> List[Dict]:
        """Generate specific model recalibration recommendations"""
        recommendations = []
        
        # 1. Confidence Calibration
        calibration = metrics['calibration']
        if calibration['calibration_error'] > 10:  # 10% threshold
            recommendations.append({
                'category': 'Confidence Calibration',
                'priority': 'HIGH',
                'issue': f"Overall calibration error of {calibration['calibration_error']}%",
                'recommendation': "Implement isotonic regression or Platt scaling for confidence recalibration",
                'specific_actions': [
                    "Create calibration mapping based on historical accuracy by confidence bracket",
                    "Apply sigmoid transformation to compress overconfident predictions",
                    f"Reduce base confidence scores by {calibration['calibration_error']/2:.1f}% as initial adjustment"
                ]
            })
        
        # 2. Pathway Reweighting
        pathway_perf = metrics['pathway_performance']
        for pathway, perf in pathway_perf.items():
            if perf['total_predictions'] > 20:  # Sufficient sample size
                expected_accuracy = perf['average_confidence']
                actual_accuracy = perf['accuracy']
                
                if abs(expected_accuracy - actual_accuracy) > 15:
                    recommendations.append({
                        'category': 'Pathway Adjustment',
                        'priority': 'MEDIUM',
                        'issue': f"{pathway} pathway: {actual_accuracy}% accuracy vs {expected_accuracy}% expected",
                        'recommendation': f"Adjust {pathway} pathway scoring",
                        'specific_actions': [
                            f"Reduce {pathway} base scores by {(expected_accuracy - actual_accuracy)/2:.1f}%",
                            f"Review feature weights for {pathway} pathway",
                            "Consider pathway-specific confidence adjustments"
                        ]
                    })
        
        # 3. Expected Value Optimization
        ev_analysis = metrics['expected_value']
        if ev_analysis['overall']['avg_ev_per_bet'] < -5:  # Losing more than $5 per $100 bet
            recommendations.append({
                'category': 'Value Optimization',
                'priority': 'HIGH',
                'issue': f"Negative expected value of ${ev_analysis['overall']['avg_ev_per_bet']} per bet",
                'recommendation': "Focus on positive expected value selections",
                'specific_actions': [
                    "Increase minimum confidence threshold for predictions",
                    "Add market value filter to exclude negative EV bets",
                    "Weight market efficiency higher in scoring algorithm"
                ]
            })
        
        # 4. Statistical Significance Issues
        stat_tests = metrics['statistical_tests']
        if 'confidence_correlation' in stat_tests:
            if stat_tests['confidence_correlation']['correlation'] < 0.2:
                recommendations.append({
                    'category': 'Model Architecture',
                    'priority': 'HIGH',
                    'issue': f"Weak correlation ({stat_tests['confidence_correlation']['correlation']}) between confidence and outcomes",
                    'recommendation': "Redesign confidence scoring mechanism",
                    'specific_actions': [
                        "Implement ensemble methods for confidence estimation",
                        "Add uncertainty quantification to the model",
                        "Use calibrated probability outputs instead of heuristic scores"
                    ]
                })
        
        # 5. Bias Corrections
        biases = metrics['bias_analysis']
        if biases['player_concentration']['gini_coefficient'] > 0.6:
            recommendations.append({
                'category': 'Selection Bias',
                'priority': 'MEDIUM',
                'issue': f"High player concentration (Gini: {biases['player_concentration']['gini_coefficient']})",
                'recommendation': "Diversify player selection",
                'specific_actions': [
                    "Implement player selection penalties for over-representation",
                    "Add minimum player diversity requirements",
                    "Review and adjust player-specific feature weights"
                ]
            })
        
        # 6. Classification Threshold Optimization
        roc = metrics.get('roc_analysis', {})
        if 'optimal_threshold' in roc:
            optimal = roc['optimal_threshold']['confidence_threshold']
            recommendations.append({
                'category': 'Classification Optimization',
                'priority': 'MEDIUM',
                'issue': "Classification thresholds may not be optimal",
                'recommendation': f"Adjust classification thresholds based on ROC analysis",
                'specific_actions': [
                    f"Set primary threshold at {optimal}% confidence (optimal by Youden's J)",
                    "Implement dynamic thresholds based on market conditions",
                    "Consider cost-sensitive classification adjustments"
                ]
            })
        
        return recommendations

    def create_statistical_report(self, metrics: Dict, recommendations: List[Dict]) -> str:
        """Create comprehensive statistical analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"statistical_validation_{timestamp}.md"
        
        report_content = f"""# Hellraiser Statistical Validation Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

### Overall Performance
- **Total Predictions**: {metrics['summary']['total_predictions']:,}
- **Correct Predictions**: {metrics['summary']['correct_predictions']:,}
- **Overall Accuracy**: {metrics['summary']['overall_accuracy']}%
- **Analysis Period**: {metrics['summary']['date_range']}

### Key Statistical Findings
- **AUC Score**: {metrics['roc_analysis']['auc']} ({metrics['roc_analysis']['interpretation']})
- **Calibration Error**: {metrics['calibration']['calibration_error']}%
- **Brier Score**: {metrics['calibration']['brier_score']}
- **Average EV per Bet**: ${metrics['expected_value']['overall']['avg_ev_per_bet']}

## Detailed Statistical Analysis

### 1. Accuracy by Confidence Bracket
| Confidence Range | Predictions | Correct | Accuracy | Expected | Calibration Error |
|-----------------|-------------|---------|----------|----------|-------------------|
"""
        
        for bracket in ['90-95', '85-89', '80-84', '75-79', '70-74', '60-69', '<60']:
            if bracket in metrics['confidence_accuracy']:
                conf_data = metrics['confidence_accuracy'][bracket]
                cal_data = metrics['calibration']['bracket_analysis'].get(bracket, {})
                report_content += f"| {bracket} | {conf_data['total_predictions']} | "
                report_content += f"{conf_data['correct_predictions']} | {conf_data['accuracy']}% | "
                report_content += f"{cal_data.get('expected_accuracy', 'N/A')}% | "
                report_content += f"{cal_data.get('calibration_error', 'N/A')}% |\n"

        report_content += f"""
### 2. Pathway Performance Analysis
| Pathway | Predictions | Accuracy | Avg Confidence | Avg EV |
|---------|-------------|----------|----------------|--------|
"""
        
        for pathway, perf in metrics['pathway_performance'].items():
            ev_data = metrics['expected_value']['by_pathway'].get(pathway, {})
            report_content += f"| {pathway} | {perf['total_predictions']} | "
            report_content += f"{perf['accuracy']}% | {perf['average_confidence']}% | "
            report_content += f"${ev_data.get('avg_ev', 'N/A')} |\n"

        report_content += f"""
### 3. Statistical Significance Tests

#### Chi-Square Test (Pathway Independence)
- **Chi-Square Statistic**: {metrics['statistical_tests']['chi_square_pathway'].get('chi2_statistic', 'N/A')}
- **P-Value**: {metrics['statistical_tests']['chi_square_pathway'].get('p_value', 'N/A')}
- **Interpretation**: {metrics['statistical_tests']['chi_square_pathway'].get('interpretation', 'N/A')}

#### Confidence-Outcome Correlation
- **Pearson Correlation**: {metrics['statistical_tests']['confidence_correlation'].get('correlation', 'N/A')}
- **P-Value**: {metrics['statistical_tests']['confidence_correlation'].get('p_value', 'N/A')}
- **Interpretation**: {metrics['statistical_tests']['confidence_correlation'].get('interpretation', 'N/A')}

### 4. Bias Analysis

#### Player Concentration
- **Top 10 Players**: {metrics['bias_analysis']['player_concentration']['top_10_percentage']}% of predictions
- **Unique Players**: {metrics['bias_analysis']['player_concentration']['unique_players']}
- **Gini Coefficient**: {metrics['bias_analysis']['player_concentration']['gini_coefficient']}

#### Top 5 Most Predicted Players:
"""
        
        for i, (player, count) in enumerate(metrics['bias_analysis']['player_concentration']['top_10_players'][:5]):
            report_content += f"{i+1}. {player}: {count} predictions\n"

        report_content += f"""
### 5. Expected Value Analysis
- **Total EV**: ${metrics['expected_value']['overall']['total_ev']:,.2f}
- **Average EV per Bet**: ${metrics['expected_value']['overall']['avg_ev_per_bet']}
- **Profitable Bet Rate**: {metrics['expected_value']['overall']['profitable_rate']}%

## Model Recalibration Recommendations

"""
        
        for i, rec in enumerate(recommendations, 1):
            report_content += f"""### {i}. {rec['category']} (Priority: {rec['priority']})
**Issue**: {rec['issue']}
**Recommendation**: {rec['recommendation']}

**Specific Actions**:
"""
            for action in rec['specific_actions']:
                report_content += f"- {action}\n"
            report_content += "\n"

        report_content += f"""
## Mathematical Model Adjustments

### 1. Confidence Score Recalibration Formula
```
adjusted_confidence = original_confidence * calibration_factor + bias_adjustment

where:
- calibration_factor = actual_accuracy / expected_accuracy (by bracket)
- bias_adjustment = -1 * (overall_calibration_error / 2)
```

### 2. Pathway Weight Optimization
```
new_weight = original_weight * (actual_accuracy / expected_accuracy) ^ 0.5
```

### 3. Expected Value Filter
```
minimum_confidence = -100 / (decimal_odds - 1)
only_predict_if: confidence > minimum_confidence + safety_margin
```

## Implementation Priority

1. **Immediate Actions** (Week 1)
   - Apply confidence recalibration mapping
   - Implement minimum EV threshold filter
   - Adjust pathway base scores

2. **Short-term Actions** (Weeks 2-4)
   - Develop isotonic regression calibration
   - Implement player diversity requirements
   - Add market timing analysis

3. **Long-term Actions** (Months 2-3)
   - Redesign confidence scoring architecture
   - Implement ensemble methods
   - Develop real-time calibration updates

## Conclusion

The Hellraiser system shows promise but requires significant recalibration to achieve profitability. The primary issues are confidence score inflation and poor calibration between expected and actual outcomes. Implementing the recommended adjustments should improve both accuracy and expected value.

---
*Statistical Validation Report - Hellraiser Performance Analysis*
"""
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Statistical report saved to: {report_file}")
        return str(report_file)

    def run_validation(self, days: int = 30) -> Tuple[Dict, List[Dict]]:
        """Run complete statistical validation"""
        print(f"\n🔬 Running Statistical Validation")
        print(f"📊 Analyzing last {days} days of predictions")
        
        # Calculate accuracy metrics
        metrics = self.calculate_prediction_accuracy(days=days)
        
        # Generate recalibration recommendations
        recommendations = self.generate_recalibration_recommendations(metrics)
        
        # Create report
        report_path = self.create_statistical_report(metrics, recommendations)
        
        # Save raw data
        data_file = self.output_dir / f"validation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(data_file, 'w') as f:
            json.dump({
                'metrics': metrics,
                'recommendations': [rec for rec in recommendations]
            }, f, indent=2, default=str)
        
        print(f"\n✅ Validation Complete!")
        print(f"📊 Key Findings:")
        print(f"   • Overall Accuracy: {metrics['summary']['overall_accuracy']}%")
        print(f"   • Calibration Error: {metrics['calibration']['calibration_error']}%")
        print(f"   • AUC Score: {metrics['roc_analysis']['auc']}")
        print(f"   • Avg EV per Bet: ${metrics['expected_value']['overall']['avg_ev_per_bet']}")
        print(f"   • {len(recommendations)} recommendations generated")
        
        return metrics, recommendations


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Hellraiser Statistical Validation')
    parser.add_argument('--days', type=int, default=30, help='Days to analyze (default: 30)')
    parser.add_argument('--output', help='Output directory for results')
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = HellraiserStatisticalValidator()
    
    # Run validation
    metrics, recommendations = validator.run_validation(days=args.days)
    
    print("\n🎯 Top 3 Priority Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"\n{i}. {rec['category']} ({rec['priority']})")
        print(f"   Issue: {rec['issue']}")
        print(f"   Action: {rec['recommendation']}")


if __name__ == "__main__":
    main()