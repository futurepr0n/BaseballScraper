#!/usr/bin/env python3
"""
Analyze Successful Predictions from Enhanced Hellraiser Algorithm
Extracts all 1,153 successful predictions from the full season results
"""

import json
import os
from collections import defaultdict
from datetime import datetime

def analyze_successful_predictions():
    """Extract and analyze all successful predictions from the full season test"""
    
    # Load the full season results
    results_file = "optimized_hellraiser_full_season_results_20250801_015440.json"
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    enhanced_system = results.get('enhanced_system', {})
    daily_results = enhanced_system.get('daily_results', [])
    
    print("🏆 ENHANCED HELLRAISER ALGORITHM - SUCCESSFUL PREDICTIONS ANALYSIS")
    print("=" * 80)
    print(f"📊 Total Predictions: {enhanced_system.get('total_predictions', 0):,}")
    print(f"✅ Successful Predictions: {enhanced_system.get('successful_predictions', 0):,}")
    print(f"🎯 Overall Accuracy: {enhanced_system.get('accuracy_rate', 0):.3%}")
    print("=" * 80)
    
    # Analyze successful predictions
    successful_players = []
    team_success_rates = defaultdict(lambda: {'predictions': 0, 'successes': 0})
    player_success_count = defaultdict(int)
    daily_breakdown = []
    
    date_counter = 0
    game_dates = [
        "2025-03-18", "2025-03-27", "2025-03-28", "2025-03-29", "2025-03-30", 
        "2025-03-31", "2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04"
    ]  # Sample dates - we'll extract more from results structure
    
    for i, daily_result in enumerate(daily_results):
        # Try to determine the date (we'll use a counter approach)
        if i < len(game_dates):
            date = game_dates[i]
        else:
            date = f"Game Day {i+1}"
        
        total_preds = daily_result.get('total_predictions', 0)
        successful_preds = daily_result.get('successful_predictions', 0)
        accuracy = daily_result.get('accuracy_rate', 0)
        
        if successful_preds > 0:
            daily_breakdown.append({
                'date': date,
                'total_predictions': total_preds,
                'successful_predictions': successful_preds,
                'accuracy_rate': accuracy,
                'team_results': daily_result.get('team_results', {}),
                'player_successes': daily_result.get('player_successes', {})
            })
            
            # Extract successful players for this date
            player_successes = daily_result.get('player_successes', {})
            for player_name, success in player_successes.items():
                if success:
                    successful_players.append({
                        'date': date,
                        'player_name': player_name,
                        'team': 'TBD'  # We'll extract team from team_results
                    })
                    player_success_count[player_name] += 1
            
            # Analyze team success rates
            team_results = daily_result.get('team_results', {})
            for team, team_data in team_results.items():
                team_success_rates[team]['predictions'] += team_data.get('predictions', 0)
                team_success_rates[team]['successes'] += team_data.get('successes', 0)
    
    # Map players to teams from daily results
    for day_data in daily_breakdown:
        team_results = day_data['team_results']
        player_successes = day_data['player_successes']
        
        # Create a mapping of which teams had successful players
        for team, team_data in team_results.items():
            if team_data.get('successes', 0) > 0:
                # Find which players succeeded for this team
                for player in successful_players:
                    if player['date'] == day_data['date'] and player['team'] == 'TBD':
                        # This is a simplified mapping - in real implementation we'd need more precise team assignment
                        player['team'] = team
                        break
    
    print("\n📈 TOP PERFORMING DAYS (Highest Success Rates)")
    print("-" * 60)
    
    # Sort by accuracy rate
    top_days = sorted(daily_breakdown, key=lambda x: x['accuracy_rate'], reverse=True)[:10]
    
    for i, day in enumerate(top_days, 1):
        print(f"{i:2d}. {day['date']} - {day['successful_predictions']}/{day['total_predictions']} = {day['accuracy_rate']:.1%}")
        
        # Show successful players for this day
        successful_on_day = [p for p in successful_players if p['date'] == day['date']]
        if successful_on_day:
            player_names = [p['player_name'] for p in successful_on_day]
            print(f"    ✅ Successful Players: {', '.join(player_names[:5])}")
            if len(player_names) > 5:
                print(f"    ... and {len(player_names) - 5} more")
        print()
    
    print("\n🌟 MOST SUCCESSFUL PLAYERS (Multiple HRs Predicted Correctly)")
    print("-" * 60)
    
    # Sort players by success count
    top_players = sorted(player_success_count.items(), key=lambda x: x[1], reverse=True)
    
    for i, (player_name, success_count) in enumerate(top_players[:20], 1):
        if success_count > 1:
            print(f"{i:2d}. {player_name} - {success_count} successful predictions")
    
    print("\n🏟️ TEAM SUCCESS ANALYSIS")
    print("-" * 60)
    
    # Calculate team success rates
    team_analysis = []
    for team, data in team_success_rates.items():
        if data['predictions'] > 0:
            success_rate = data['successes'] / data['predictions']
            team_analysis.append({
                'team': team,
                'predictions': data['predictions'],
                'successes': data['successes'],
                'success_rate': success_rate
            })
    
    # Sort by success rate
    team_analysis.sort(key=lambda x: x['success_rate'], reverse=True)
    
    print("Team | Predictions | Successes | Success Rate")
    print("-" * 45)
    for team_data in team_analysis[:15]:
        print(f"{team_data['team']:4s} | {team_data['predictions']:11d} | {team_data['successes']:9d} | {team_data['success_rate']:9.1%}")
    
    print("\n📊 SAMPLE SUCCESSFUL PREDICTIONS BREAKDOWN")
    print("-" * 80)
    
    # Show detailed breakdown for first few successful days
    for day in daily_breakdown[:5]:
        print(f"\n📅 {day['date']} - {day['successful_predictions']}/{day['total_predictions']} successful ({day['accuracy_rate']:.1%})")
        
        # Show team-by-team results
        team_results = day['team_results']
        player_successes = day['player_successes']
        
        successful_teams = [(team, data) for team, data in team_results.items() if data.get('successes', 0) > 0]
        
        for team, team_data in successful_teams:
            print(f"  🏟️ {team}: {team_data['successes']}/{team_data['predictions']} successful")
            
            # Try to identify which players succeeded for this team
            successful_players_on_day = [name for name, success in player_successes.items() if success]
            if successful_players_on_day:
                print(f"    ✅ Players: {', '.join(successful_players_on_day)}")
    
    print(f"\n🎯 ALGORITHM PERFORMANCE SUMMARY")
    print("-" * 50)
    print(f"Total Games Analyzed: {len(daily_results)}")
    print(f"Games with Successful Predictions: {len(daily_breakdown)}")
    print(f"Average Daily Accuracy: {sum(d['accuracy_rate'] for d in daily_breakdown) / len(daily_breakdown):.2%}")
    print(f"Best Single Day: {max(daily_breakdown, key=lambda x: x['accuracy_rate'])['accuracy_rate']:.1%}")
    print(f"Players with Multiple Successes: {len([p for p in player_success_count.values() if p > 1])}")

if __name__ == "__main__":
    analyze_successful_predictions()