#!/usr/bin/env python3
"""
Hellraiser Performance Analysis - Top 3 Accuracy
Analyzes if our top 3 predictions per team actually hit home runs
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
import glob
from collections import defaultdict

def load_hellraiser_prediction(date_str):
    """Load Hellraiser predictions for a given date"""
    hellraiser_path = f"../BaseballTracker/public/data/hellraiser/hellraiser_analysis_{date_str}.json"
    if os.path.exists(hellraiser_path):
        with open(hellraiser_path, 'r') as f:
            return json.load(f)
    return None

def load_game_results(date_str):
    """Load actual game results for a given date"""
    year, month, day = date_str.split('-')
    month_name = datetime.strptime(month, '%m').strftime('%B').lower()
    game_path = f"../BaseballTracker/public/data/{year}/{month_name}/{month_name}_{day}_{year}.json"
    
    if os.path.exists(game_path):
        with open(game_path, 'r') as f:
            return json.load(f)
    return None

def normalize_name(name):
    """Normalize player names for matching"""
    if not name:
        return ""
    # Remove extra spaces and convert to lowercase
    name = ' '.join(name.strip().split()).lower()
    # Handle common variations
    name = name.replace('.', '').replace(',', '')
    return name

def extract_home_runs_from_games(game_data):
    """Extract players who hit home runs from game data"""
    home_run_players = set()
    
    if not game_data or 'games' not in game_data:
        return home_run_players
    
    for game in game_data['games']:
        if 'hitting' in game:
            for team in ['away', 'home']:
                if team in game['hitting']:
                    for player_name, stats in game['hitting'][team].items():
                        if isinstance(stats, dict) and stats.get('HR', 0) > 0:
                            home_run_players.add(normalize_name(player_name))
    
    return home_run_players

def get_team_top3_predictions(hellraiser_data, team_abbrev):
    """Get top 3 predictions for a specific team"""
    if not hellraiser_data or 'picks' not in hellraiser_data:
        return []
    
    team_predictions = []
    for prediction in hellraiser_data['picks']:
        if prediction.get('team', '').upper() == team_abbrev.upper():
            team_predictions.append({
                'player': normalize_name(prediction.get('playerName', '')),
                'confidence': prediction.get('confidenceScore', 0),
                'raw_player': prediction.get('playerName', '')
            })
    
    # Sort by confidence descending and take top 3
    team_predictions.sort(key=lambda x: x['confidence'], reverse=True)
    return team_predictions[:3]

def analyze_date_performance(date_str):
    """Analyze performance for a specific date"""
    print(f"\n--- Analyzing {date_str} ---")
    
    hellraiser_data = load_hellraiser_prediction(date_str)
    if not hellraiser_data:
        print(f"No Hellraiser predictions found for {date_str}")
        return None
    
    game_results = load_game_results(date_str)
    if not game_results:
        print(f"No game results found for {date_str}")
        return None
    
    home_run_players = extract_home_runs_from_games(game_results)
    print(f"Players who hit HRs: {len(home_run_players)}")
    if home_run_players:
        print(f"HR Players: {list(home_run_players)}")
    
    # Get all teams that had predictions
    teams_with_predictions = set()
    if 'picks' in hellraiser_data:
        for pred in hellraiser_data['picks']:
            teams_with_predictions.add(pred.get('team', '').upper())
    
    results = {
        'date': date_str,
        'total_teams': len(teams_with_predictions),
        'successful_teams': 0,
        'total_predictions': 0,
        'successful_predictions': 0,
        'team_details': []
    }
    
    for team in teams_with_predictions:
        top3_predictions = get_team_top3_predictions(hellraiser_data, team)
        if not top3_predictions:
            continue
            
        results['total_predictions'] += len(top3_predictions)
        team_success = False
        successful_players = []
        
        for i, pred in enumerate(top3_predictions, 1):
            if pred['player'] in home_run_players:
                results['successful_predictions'] += 1
                team_success = True
                successful_players.append(f"{pred['raw_player']} (#{i}, {pred['confidence']:.1f}%)")
                print(f"✅ {team} - {pred['raw_player']} hit HR (#{i} prediction, {pred['confidence']:.1f}% confidence)")
        
        if team_success:
            results['successful_teams'] += 1
        
        results['team_details'].append({
            'team': team,
            'predictions': [(p['raw_player'], p['confidence']) for p in top3_predictions],
            'successful': team_success,
            'successful_players': successful_players
        })
        
        if not team_success:
            pred_list = [f"{p['raw_player']} ({p['confidence']:.1f}%)" for p in top3_predictions]
            print(f"❌ {team} - No HR from top 3: {', '.join(pred_list)}")
    
    # Calculate accuracies
    team_accuracy = (results['successful_teams'] / results['total_teams'] * 100) if results['total_teams'] > 0 else 0
    prediction_accuracy = (results['successful_predictions'] / results['total_predictions'] * 100) if results['total_predictions'] > 0 else 0
    
    print(f"\nResults for {date_str}:")
    print(f"Team Success Rate: {results['successful_teams']}/{results['total_teams']} = {team_accuracy:.1f}%")
    print(f"Individual Prediction Rate: {results['successful_predictions']}/{results['total_predictions']} = {prediction_accuracy:.1f}%")
    
    results['team_accuracy'] = team_accuracy
    results['prediction_accuracy'] = prediction_accuracy
    
    return results

def main():
    """Main analysis function"""
    print("=== Hellraiser Top 3 Performance Analysis ===")
    print("Success Criteria: Top 3 predictions per team, did any hit a HR that day?")
    
    # Analyze recent dates (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    all_results = []
    date_range = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        date_range.append(date_str)
        current_date += timedelta(days=1)
    
    print(f"Analyzing {len(date_range)} dates from {date_range[0]} to {date_range[-1]}")
    
    for date_str in date_range:
        result = analyze_date_performance(date_str)
        if result:
            all_results.append(result)
    
    if not all_results:
        print("No valid data found for analysis")
        return
    
    # Summary statistics
    print(f"\n{'='*60}")
    print("OVERALL PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    total_teams = sum(r['total_teams'] for r in all_results)
    successful_teams = sum(r['successful_teams'] for r in all_results)
    total_predictions = sum(r['total_predictions'] for r in all_results)
    successful_predictions = sum(r['successful_predictions'] for r in all_results)
    
    overall_team_accuracy = (successful_teams / total_teams * 100) if total_teams > 0 else 0
    overall_prediction_accuracy = (successful_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    print(f"Analysis Period: {len(all_results)} days with data")
    print(f"Team Success Rate: {successful_teams}/{total_teams} = {overall_team_accuracy:.1f}%")
    print(f"Individual Prediction Accuracy: {successful_predictions}/{total_predictions} = {overall_prediction_accuracy:.1f}%")
    
    # Daily breakdown
    print(f"\nDaily Breakdown:")
    for result in all_results[-10:]:  # Show last 10 days
        print(f"{result['date']}: Teams {result['successful_teams']}/{result['total_teams']} ({result['team_accuracy']:.1f}%), "
              f"Predictions {result['successful_predictions']}/{result['total_predictions']} ({result['prediction_accuracy']:.1f}%)")
    
    # Best and worst days
    if len(all_results) > 1:
        best_day = max(all_results, key=lambda x: x['team_accuracy'])
        worst_day = min(all_results, key=lambda x: x['team_accuracy'])
        
        print(f"\nBest Day: {best_day['date']} - {best_day['team_accuracy']:.1f}% team success")
        print(f"Worst Day: {worst_day['date']} - {worst_day['team_accuracy']:.1f}% team success")
    
    # Performance insights
    print(f"\n{'='*60}")
    print("PERFORMANCE INSIGHTS")
    print(f"{'='*60}")
    
    if overall_team_accuracy > 30:
        print("✅ STRONG: Team success rate > 30% (better than random)")
    elif overall_team_accuracy > 20:
        print("🔶 MODERATE: Team success rate 20-30% (acceptable)")
    else:
        print("❌ WEAK: Team success rate < 20% (needs improvement)")
    
    if overall_prediction_accuracy > 15:
        print("✅ GOOD: Individual prediction rate > 15% (above MLB average)")
    elif overall_prediction_accuracy > 10:
        print("🔶 FAIR: Individual prediction rate 10-15% (near MLB average)")
    else:
        print("❌ POOR: Individual prediction rate < 10% (below MLB average)")
    
    # Recommendations
    print(f"\nRECOMMENDations:")
    if overall_team_accuracy < 25:
        print("- Consider reducing number of teams predicted per day")
        print("- Focus on higher confidence thresholds")
        print("- Improve team-specific analysis")
    
    if overall_prediction_accuracy < 12:
        print("- Recalibrate confidence scoring")
        print("- Add more situational factors (weather, rest, etc.)")
        print("- Consider ensemble methods")
    
    # Save detailed results
    output_file = f"hellraiser_top3_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'total_days': len(all_results),
                'team_success_rate': overall_team_accuracy,
                'prediction_accuracy': overall_prediction_accuracy,
                'total_teams': total_teams,
                'successful_teams': successful_teams,
                'total_predictions': total_predictions,
                'successful_predictions': successful_predictions
            },
            'daily_results': all_results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()