#!/usr/bin/env python3
"""
Lineup Position Vulnerability Analyzer
Analyzes how pitchers perform against different batting order positions
Integrates with daily lineup data for targeted matchup identification
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np

class LineupPositionAnalyzer:
    def __init__(self, playbyplay_engine=None):
        self.playbyplay_engine = playbyplay_engine
        self.lineup_vulnerabilities = defaultdict(lambda: {
            'vs_leadoff': [],      # Position 1
            'vs_two_hole': [],     # Position 2  
            'vs_heart_order': [],  # Positions 3-4-5
            'vs_bottom_order': [], # Positions 6-7-8-9
            'positional_breakdown': defaultdict(list)  # Individual positions
        })
        self.batter_lineup_success = defaultdict(lambda: defaultdict(list))
        
    def analyze_lineup_vulnerabilities(self, min_matchups=3):
        """Analyze pitcher vulnerabilities by lineup position"""
        print("🎯 Analyzing lineup position vulnerabilities...")
        
        if not self.playbyplay_engine or not self.playbyplay_engine.matchup_data:
            print("❌ No matchup data available for lineup analysis")
            return {}
        
        # Process each matchup for lineup patterns
        for matchup in self.playbyplay_engine.matchup_data:
            pitcher = matchup['pitcher']
            batter = matchup['batter']
            lineup_position = matchup['lineup_position']
            result = matchup['result']
            
            if lineup_position == 0:  # Skip if position unknown
                continue
                
            # Score outcome for pitcher
            outcome_score = self.playbyplay_engine._score_outcome_for_pitcher(result)
            
            # Categorize lineup positions
            if lineup_position == 1:
                category = 'vs_leadoff'
            elif lineup_position == 2:
                category = 'vs_two_hole'
            elif lineup_position in [3, 4, 5]:
                category = 'vs_heart_order'
            else:
                category = 'vs_bottom_order'
                
            # Store data
            self.lineup_vulnerabilities[pitcher][category].append({
                'batter': batter,
                'result': result,
                'outcome_score': outcome_score,
                'lineup_position': lineup_position,
                'inning': matchup['inning']
            })
            
            # Store by specific position
            position_key = f'position_{lineup_position}'
            self.lineup_vulnerabilities[pitcher]['positional_breakdown'][position_key].append({
                'batter': batter,
                'result': result,
                'outcome_score': outcome_score,
                'inning': matchup['inning']
            })
            
            # Track batter success by position
            batter_score = self.playbyplay_engine._score_outcome_for_batter(result)
            self.batter_lineup_success[batter][position_key].append({
                'pitcher': pitcher,
                'result': result,
                'success_score': batter_score
            })
        
        # Generate vulnerability rankings
        return self._generate_lineup_vulnerability_rankings(min_matchups)
    
    def _generate_lineup_vulnerability_rankings(self, min_matchups):
        """Generate ranked list of lineup vulnerabilities"""
        vulnerability_rankings = []
        
        for pitcher, data in self.lineup_vulnerabilities.items():
            pitcher_analysis = {'pitcher': pitcher, 'lineup_vulnerabilities': {}}
            
            # Analyze each lineup category
            for category, matchups in data.items():
                if category == 'positional_breakdown':
                    continue  # Handle separately
                    
                if len(matchups) >= min_matchups:
                    avg_outcome = np.mean([m['outcome_score'] for m in matchups])
                    
                    # Negative scores indicate pitcher struggles
                    if avg_outcome < -0.3:
                        pitcher_analysis['lineup_vulnerabilities'][category] = {
                            'avg_outcome_score': avg_outcome,
                            'matchup_count': len(matchups),
                            'vulnerability_rating': abs(avg_outcome) * len(matchups),
                            'worst_results': [m['result'] for m in matchups if m['outcome_score'] < -1],
                            'common_batters': self._get_common_batters([m['batter'] for m in matchups])
                        }
            
            # Analyze specific positions
            position_vulns = {}
            for position, matchups in data['positional_breakdown'].items():
                if len(matchups) >= min_matchups:
                    avg_outcome = np.mean([m['outcome_score'] for m in matchups])
                    
                    if avg_outcome < -0.3:
                        position_vulns[position] = {
                            'avg_outcome_score': avg_outcome,
                            'matchup_count': len(matchups),
                            'vulnerability_rating': abs(avg_outcome) * len(matchups)
                        }
            
            if position_vulns:
                pitcher_analysis['lineup_vulnerabilities']['specific_positions'] = position_vulns
            
            # Only include pitchers with vulnerabilities
            if pitcher_analysis['lineup_vulnerabilities']:
                # Calculate overall lineup vulnerability score
                total_vuln_rating = sum(
                    v['vulnerability_rating'] for v in pitcher_analysis['lineup_vulnerabilities'].values()
                    if isinstance(v, dict) and 'vulnerability_rating' in v
                )
                pitcher_analysis['total_lineup_vulnerability'] = total_vuln_rating
                vulnerability_rankings.append(pitcher_analysis)
        
        # Sort by total vulnerability
        vulnerability_rankings.sort(key=lambda x: x['total_lineup_vulnerability'], reverse=True)
        
        return vulnerability_rankings
    
    def analyze_batter_lineup_optimization(self, min_matchups=3):
        """Analyze optimal lineup positions for batters vs specific pitcher types"""
        print("📊 Analyzing batter lineup position optimization...")
        
        batter_optimizations = []
        
        for batter, position_data in self.batter_lineup_success.items():
            batter_analysis = {'batter': batter, 'position_performance': {}}
            
            for position, matchups in position_data.items():
                if len(matchups) >= min_matchups:
                    avg_success = np.mean([m['success_score'] for m in matchups])
                    
                    batter_analysis['position_performance'][position] = {
                        'avg_success_score': avg_success,
                        'matchup_count': len(matchups),
                        'success_rating': avg_success * len(matchups),
                        'best_results': [m['result'] for m in matchups if m['success_score'] > 1]
                    }
            
            if len(batter_analysis['position_performance']) >= 2:  # Need multiple positions
                # Find optimal position
                best_position = max(
                    batter_analysis['position_performance'].items(),
                    key=lambda x: x[1]['avg_success_score']
                )
                batter_analysis['optimal_position'] = best_position[0]
                batter_analysis['optimal_position_score'] = best_position[1]['avg_success_score']
                
                batter_optimizations.append(batter_analysis)
        
        # Sort by optimization potential
        batter_optimizations.sort(key=lambda x: x['optimal_position_score'], reverse=True)
        
        return batter_optimizations
    
    def generate_daily_lineup_matchups(self, today_lineups=None, today_pitchers=None):
        """Generate today's recommended lineup matchups based on vulnerabilities"""
        print("🎯 Generating daily lineup matchup recommendations...")
        
        if not today_lineups or not today_pitchers:
            # Generate sample structure for now
            return self._generate_sample_matchup_structure()
        
        matchup_recommendations = []
        
        for game in today_lineups:
            away_lineup = game.get('away_lineup', [])
            home_lineup = game.get('home_lineup', [])
            away_pitcher = game.get('away_pitcher')
            home_pitcher = game.get('home_pitcher')
            
            # Analyze away team hitting vs home pitcher
            if home_pitcher and home_pitcher in self.lineup_vulnerabilities:
                away_recommendations = self._analyze_team_vs_pitcher_lineup(
                    away_lineup, home_pitcher, 'away'
                )
                matchup_recommendations.extend(away_recommendations)
            
            # Analyze home team hitting vs away pitcher
            if away_pitcher and away_pitcher in self.lineup_vulnerabilities:
                home_recommendations = self._analyze_team_vs_pitcher_lineup(
                    home_lineup, away_pitcher, 'home'
                )
                matchup_recommendations.extend(home_recommendations)
        
        return matchup_recommendations
    
    def _analyze_team_vs_pitcher_lineup(self, lineup, pitcher, team_side):
        """Analyze specific team lineup vs pitcher vulnerabilities"""
        recommendations = []
        pitcher_vulns = self.lineup_vulnerabilities[pitcher]
        
        for position, batter in enumerate(lineup, 1):
            position_key = f'position_{position}'
            category_key = self._get_lineup_category(position)
            
            # Check if pitcher is vulnerable to this position
            if category_key in pitcher_vulns and len(pitcher_vulns[category_key]) >= 2:
                vuln_data = pitcher_vulns[category_key]
                avg_outcome = np.mean([m['outcome_score'] for m in vuln_data])
                
                if avg_outcome < -0.3:  # Pitcher struggles against this position
                    recommendations.append({
                        'batter': batter,
                        'lineup_position': position,
                        'pitcher': pitcher,
                        'team': team_side,
                        'vulnerability_type': category_key,
                        'pitcher_weakness_score': abs(avg_outcome),
                        'historical_matchups': len(vuln_data),
                        'recommendation': f'{batter} in position {position} vs {pitcher}',
                        'confidence': 'High' if len(vuln_data) >= 5 else 'Medium'
                    })
        
        return recommendations
    
    def _get_lineup_category(self, position):
        """Get lineup category for position"""
        if position == 1:
            return 'vs_leadoff'
        elif position == 2:
            return 'vs_two_hole'
        elif position in [3, 4, 5]:
            return 'vs_heart_order'
        else:
            return 'vs_bottom_order'
    
    def _get_common_batters(self, batters, top_n=3):
        """Get most common batters from list"""
        return Counter(batters).most_common(top_n)
    
    def _generate_sample_matchup_structure(self):
        """Generate sample structure for daily matchups"""
        return {
            'analysis_type': 'daily_lineup_matchups',
            'timestamp': datetime.now().isoformat(),
            'description': 'Recommended lineup matchups based on pitcher vulnerabilities',
            'structure': {
                'game': {
                    'away_team': 'team_abbr',
                    'home_team': 'team_abbr', 
                    'away_pitcher': 'pitcher_name',
                    'home_pitcher': 'pitcher_name',
                    'recommendations': [
                        {
                            'batter': 'batter_name',
                            'lineup_position': 'position_number',
                            'vulnerability_type': 'category',
                            'confidence': 'High/Medium/Low',
                            'pitcher_weakness_score': 'numerical_score'
                        }
                    ]
                }
            }
        }
    
    def save_lineup_analysis(self, output_dir="../BaseballData/data/weakspot_analysis"):
        """Save lineup position analysis to JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("💾 Saving lineup position analysis...")
        
        # Generate vulnerability rankings
        vulnerability_rankings = self.analyze_lineup_vulnerabilities()
        
        # Generate batter optimizations
        batter_optimizations = self.analyze_batter_lineup_optimization()
        
        # Save vulnerability rankings
        with open(output_path / 'lineup_vulnerability_rankings.json', 'w') as f:
            json.dump({
                'analysis_type': 'lineup_vulnerability_rankings',
                'timestamp': datetime.now().isoformat(),
                'description': 'Pitcher vulnerabilities by batting order position',
                'data': vulnerability_rankings[:30]  # Top 30
            }, f, indent=2, default=str)
        
        # Save batter optimizations
        with open(output_path / 'batter_lineup_optimization.json', 'w') as f:
            json.dump({
                'analysis_type': 'batter_lineup_optimization',
                'timestamp': datetime.now().isoformat(),
                'description': 'Optimal lineup positions for batters',
                'data': batter_optimizations[:50]  # Top 50
            }, f, indent=2, default=str)
        
        # Generate daily matchup template
        daily_matchups = self.generate_daily_lineup_matchups()
        with open(output_path / 'daily_lineup_matchup_template.json', 'w') as f:
            json.dump(daily_matchups, f, indent=2, default=str)
        
        print(f"   ✅ Lineup analysis saved to {output_path}")
        print(f"   📄 Generated 3 lineup analysis files")
        
        return {
            'vulnerability_rankings': len(vulnerability_rankings),
            'batter_optimizations': len(batter_optimizations),
            'files_created': 3
        }

# Integration function for use with main analysis engine
def add_lineup_analysis_to_engine(weakspot_engine):
    """Add lineup position analysis to existing weakspot engine"""
    lineup_analyzer = LineupPositionAnalyzer(weakspot_engine)
    results = lineup_analyzer.save_lineup_analysis()
    return lineup_analyzer, results