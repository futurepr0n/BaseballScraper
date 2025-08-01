#!/usr/bin/env python3
"""
Hellraiser Performance Analysis - Using CSV Game Data
Analyzes if our top 3 predictions per team actually hit home runs using CSV files
"""

import json
import os
import pandas as pd
import glob
from datetime import datetime, timedelta
from collections import defaultdict

def load_hellraiser_prediction(date_str):
    """Load Hellraiser predictions for a given date"""
    hellraiser_path = f"../BaseballTracker/public/data/hellraiser/hellraiser_analysis_{date_str}.json"
    if os.path.exists(hellraiser_path):
        with open(hellraiser_path, 'r') as f:
            return json.load(f)
    return None

def normalize_name(name):
    """Normalize player names for matching"""
    if not name:
        return ""
    # Remove extra spaces and convert to lowercase
    name = ' '.join(name.strip().split()).lower()
    # Remove common suffixes and prefixes
    name = name.replace(' jr.', '').replace(' sr.', '').replace(' jr', '').replace(' sr', '')
    name = name.replace('.', '').replace(',', '')
    return name

def find_csv_files_for_date(date_str):
    """Find all hitting CSV files for a specific date"""
    # Convert date format from YYYY-MM-DD to month_day_year
    year, month, day = date_str.split('-')
    month_name = datetime.strptime(month, '%m').strftime('%B').lower()
    date_pattern = f"{month_name}_{int(day)}_{year}"
    
    # Look for hitting CSV files with game ID pattern
    csv_pattern = f"*_hitting_{date_pattern}_*.csv"
    csv_files = glob.glob(csv_pattern)
    
    return csv_files

def extract_home_runs_from_csv(csv_files):
    """Extract players who hit home runs from CSV files"""
    home_run_players = set()
    
    for csv_file in csv_files:
        try:
            # Extract team from filename
            team_abbr = csv_file.split('_')[0].upper()
            
            df = pd.read_csv(csv_file)
            
            # Look for HR column (check both cases)
            hr_col = None
            if 'HR' in df.columns:
                hr_col = 'HR'
            elif 'hr' in df.columns:
                hr_col = 'hr'
            
            if hr_col:
                hr_players = df[df[hr_col] > 0]
                for _, player in hr_players.iterrows():
                    if 'player' in player:
                        player_name = normalize_name(str(player['player']))
                        home_run_players.add((player_name, team_abbr))
                        print(f"Found HR: {player['player']} ({team_abbr}) - {player[hr_col]} HRs")
            
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue
    
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
    
    csv_files = find_csv_files_for_date(date_str)
    if not csv_files:
        print(f"No CSV files found for {date_str}")
        return None
    
    print(f"Found {len(csv_files)} CSV files: {csv_files}")
    
    home_run_players = extract_home_runs_from_csv(csv_files)
    print(f"Players who hit HRs: {len(home_run_players)}")
    
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
            # Check if this player hit a HR (name and team match)
            player_hit_hr = False
            for hr_player_name, hr_team in home_run_players:
                if pred['player'] == hr_player_name and team == hr_team:
                    player_hit_hr = True
                    break
            
            if player_hit_hr:
                results['successful_predictions'] += 1
                team_success = True
                successful_players.append(f"{pred['raw_player']} (#{i}, {pred['confidence']:.1f}%)")
                print(f"✅ {team} - {pred['raw_player']} hit HR (#{i} prediction, {pred['confidence']:.1f}% confidence)")
        
        if team_success:
            results['successful_teams'] += 1
        else:
            pred_list = [f"{p['raw_player']} ({p['confidence']:.1f}%)" for p in top3_predictions]
            print(f"❌ {team} - No HR from top 3: {', '.join(pred_list)}")
        
        results['team_details'].append({
            'team': team,
            'predictions': [(p['raw_player'], p['confidence']) for p in top3_predictions],
            'successful': team_success,
            'successful_players': successful_players
        })
    
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
    print("=== Hellraiser Top 3 Performance Analysis (CSV Data) ===")
    print("Success Criteria: Top 3 predictions per team, did any hit a HR that day?")
    print("Data Source: BaseballScraper CSV files")
    
    # Check what dates have CSV files available
    csv_files = glob.glob("*_hitting_*.csv")
    available_dates = set()
    
    for csv_file in csv_files:
        try:
            # Extract date from filename format: TEAM_hitting_month_day_year_gameid.csv
            parts = csv_file.split('_')
            if len(parts) >= 5:
                month_name, day, year = parts[2], parts[3], parts[4]
                month_num = datetime.strptime(month_name, '%B').month
                date_str = f"{year}-{month_num:02d}-{int(day):02d}"
                available_dates.add(date_str)
        except Exception as e:
            continue
    
    available_dates = sorted(list(available_dates))
    print(f"Found CSV files for {len(available_dates)} dates: {available_dates[:5]}...{available_dates[-5:] if len(available_dates) > 5 else ''}")
    
    # Analyze the most recent 10 dates with data
    recent_dates = available_dates[-10:] if len(available_dates) >= 10 else available_dates
    
    all_results = []
    for date_str in recent_dates:
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
    for result in all_results:
        print(f"{result['date']}: Teams {result['successful_teams']}/{result['total_teams']} ({result['team_accuracy']:.1f}%), "
              f"Predictions {result['successful_predictions']}/{result['total_predictions']} ({result['prediction_accuracy']:.1f}%)")
    
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
    
    # Save detailed results
    output_file = f"hellraiser_csv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'CSV files',
            'summary': {
                'total_days': len(all_results),
                'team_success_rate': overall_team_accuracy,
                'prediction_accuracy': overall_prediction_accuracy,
                'total_teams': total_teams,
                'successful_teams': successful_teams,
                'total_predictions': total_predictions,
                'successful_predictions': successful_predictions
            },
            'daily_results': all_results,
            'available_dates': available_dates
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()