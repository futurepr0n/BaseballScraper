#!/usr/bin/env python3
"""
PinheadsPlayhouse Field Mapping Analysis
Compare what the dashboard expects vs what enhanced algorithm provides
"""

import json
import os

def analyze_field_mapping():
    """Analyze field mapping between PinheadsPlayhouse expectations and enhanced algorithm output"""
    
    print("🎯 PINHEADSPLAYHOUSE FIELD MAPPING ANALYSIS")
    print("=" * 80)
    
    # Fields expected by PinheadsPlayhouse based on code analysis
    expected_fields = {
        'Core Player Fields': {
            'player_name': 'Player name (required)',
            'team': 'Team abbreviation (required)',
            'matchup_pitcher': 'Opposing pitcher name',
            'matchup_team': 'Opposing team abbreviation',
            'pitcher_name': 'Alternative pitcher field',
            'opponent': 'Opponent team'
        },
        'Scoring Fields': {
            'hr_score': 'Base HR score (0-100)',
            'enhanced_hr_score': 'Enhanced HR score with badges',
            'standout_score': 'Standout player score',
            'enhanced_confidence_score': 'Overall confidence (0-100)',
            'confidence_score': 'Legacy confidence field',
            'confidenceScore': 'Alternative confidence field'
        },
        'Probability Fields': {
            'hr_probability': 'HR probability percentage',
            'hit_probability': 'Hit probability percentage'
        },
        'Component Scores': {
            'arsenal_matchup': 'Arsenal matchup component score',
            'contextual_factors': 'Contextual factors score', 
            'batter_quality': 'Batter overall quality score',
            'recent_performance': 'Recent games performance score',
            'pitcher_vulnerability': 'Pitcher vulnerability score',
            'historical_comparison': 'Year-over-year comparison score'
        },
        'Badge System Fields': {
            'dashboard_context': 'Context object with badges and boost',
            'dashboard_context.badges': 'Array of badge emojis',
            'dashboard_context.confidence_boost': 'Total confidence boost from badges',
            'dashboard_context.standout_score': 'Enhanced score with boost',
            'dashboard_context.is_standout': 'Boolean for standout player'
        },
        'Handedness Fields': {
            'pitcher_hand': 'Pitcher handedness (L/R)',
            'batter_hand': 'Batter handedness (L/R)'
        },
        'Data Quality Fields': {
            'is_fallback_prediction': 'Using fallback data flag',
            'used_fallback': 'Alternative fallback flag',
            'fallback_type': 'Type of fallback (e.g., league_average)',
            'data_confidence': 'Data quality confidence (0-100)'
        },
        'Additional Context': {
            'pathway': 'Classification pathway',
            'market_analysis': 'Market efficiency analysis',
            'detailed_breakdown': 'Detailed scoring breakdown',
            'badge_modifiers': 'List of applied badges',
            'confidence_factors': 'Data quality factors'
        }
    }
    
    # Fields provided by enhanced algorithm
    enhanced_algorithm_fields = {
        'Core Output': {
            'playerName': '✅ Maps to player_name',
            'team': '✅ Provided',
            'opponent': '✅ Provided',
            'is_home': '✅ Home/away indicator',
            'date': '✅ Analysis date'
        },
        'Scoring Output': {
            'enhanced_confidence_score': '✅ Main confidence score (0-100)',
            'component_scores': '✅ Dictionary with all 6 components',
            'component_scores.arsenal_matchup': '✅ Arsenal score',
            'component_scores.contextual_factors': '✅ Context score',
            'component_scores.batter_quality': '✅ Quality score',
            'component_scores.recent_performance': '✅ Recent score',
            'component_scores.pitcher_vulnerability': '✅ Pitcher score',
            'component_scores.historical_comparison': '✅ Historical score'
        },
        'Classification': {
            'pathway': '✅ Perfect Storm/Batter-Driven/Pitcher-Driven',
            'badge_modifiers': '✅ List of badge strings',
            'market_analysis': '✅ Market efficiency data',
            'detailed_breakdown': '✅ Component explanations'
        },
        'Data Quality': {
            'data_sources_used': '✅ List of data sources',
            'confidence_factors': '✅ Quality metrics',
            'confidence_factors.data_completeness': '✅ Ratio of sources used',
            'confidence_factors.sample_size_adequacy': '✅ Sample size assessment',
            'confidence_factors.recency_factor': '✅ Data freshness'
        }
    }
    
    # Required field mappings
    print("\n📋 REQUIRED FIELD MAPPINGS FOR PINHEADSPLAYHOUSE:")
    print("-" * 80)
    
    mappings_needed = [
        {
            'Dashboard Field': 'player_name',
            'Algorithm Field': 'playerName',
            'Mapping': 'Rename playerName → player_name',
            'Status': '🔄 Easy fix'
        },
        {
            'Dashboard Field': 'hr_score',
            'Algorithm Field': 'enhanced_confidence_score',
            'Mapping': 'Use enhanced_confidence_score as hr_score',
            'Status': '🔄 Add field'
        },
        {
            'Dashboard Field': 'matchup_pitcher',
            'Algorithm Field': 'opponent (team only)',
            'Mapping': 'Need to add pitcher name from game context',
            'Status': '⚠️ Requires pitcher data'
        },
        {
            'Dashboard Field': 'matchup_team',
            'Algorithm Field': 'opponent',
            'Mapping': 'Copy opponent → matchup_team',
            'Status': '🔄 Easy fix'
        },
        {
            'Dashboard Field': 'dashboard_context',
            'Algorithm Field': 'badge_modifiers + market_analysis',
            'Mapping': 'Create context object with badges array',
            'Status': '🔄 Transform data'
        },
        {
            'Dashboard Field': 'hr_probability',
            'Algorithm Field': 'Not provided',
            'Mapping': 'Calculate from confidence score',
            'Status': '⚠️ Add calculation'
        },
        {
            'Dashboard Field': 'hit_probability', 
            'Algorithm Field': 'Not provided',
            'Mapping': 'Calculate from contextual factors',
            'Status': '⚠️ Add calculation'
        }
    ]
    
    print("Field Mapping Requirements:")
    print("-" * 80)
    for mapping in mappings_needed:
        print(f"• {mapping['Dashboard Field']:20s} ← {mapping['Algorithm Field']:30s} | {mapping['Status']}")
        print(f"  Action: {mapping['Mapping']}")
        print()
    
    # Sample transformation code
    print("\n💻 SAMPLE TRANSFORMATION CODE:")
    print("-" * 80)
    print("""
def transform_for_pinheads_playhouse(enhanced_analysis):
    '''Transform enhanced algorithm output for PinheadsPlayhouse compatibility'''
    
    # Extract picks from team analysis
    all_picks = []
    for team_data in enhanced_analysis.get('team_analysis', {}).values():
        for pick in team_data.get('top_picks', []):
            transformed_pick = {
                # Core fields (rename as needed)
                'player_name': pick.get('playerName', ''),
                'team': pick.get('team', ''),
                'matchup_team': pick.get('opponent', ''),
                'matchup_pitcher': 'TBD',  # Need pitcher data from game context
                
                # Scoring fields
                'hr_score': pick.get('enhanced_confidence_score', 0),
                'enhanced_hr_score': pick.get('enhanced_confidence_score', 0),
                'enhanced_confidence_score': pick.get('enhanced_confidence_score', 0),
                
                # Probabilities (calculate from scores)
                'hr_probability': min(30, pick.get('enhanced_confidence_score', 0) * 0.3),
                'hit_probability': min(40, pick.get('component_scores', {}).get('contextual_factors', 0) * 0.4),
                
                # Component scores (already in correct format)
                'arsenal_matchup': pick.get('component_scores', {}).get('arsenal_matchup', 0),
                'contextual_factors': pick.get('component_scores', {}).get('contextual_factors', 0),
                'batter_quality': pick.get('component_scores', {}).get('batter_quality', 0),
                'recent_performance': pick.get('component_scores', {}).get('recent_performance', 0),
                'pitcher_vulnerability': pick.get('component_scores', {}).get('pitcher_vulnerability', 0),
                'historical_comparison': pick.get('component_scores', {}).get('historical_comparison', 0),
                
                # Dashboard context (transform badges)
                'dashboard_context': {
                    'badges': convert_badges_to_emojis(pick.get('badge_modifiers', [])),
                    'confidence_boost': sum_badge_boosts(pick.get('badge_modifiers', [])),
                    'standout_score': pick.get('enhanced_confidence_score', 0),
                    'is_standout': pick.get('enhanced_confidence_score', 0) >= 80
                },
                
                # Classification
                'pathway': pick.get('pathway', 'unknown'),
                
                # Data quality
                'data_confidence': pick.get('confidence_factors', {}).get('data_completeness', 0) * 100,
                'is_fallback_prediction': False,  # Set based on data sources used
                
                # Market analysis
                'market_edge': pick.get('market_analysis', {}).get('edge_percentage', 0),
                'implied_probability': pick.get('market_analysis', {}).get('implied_probability', 0)
            }
            
            all_picks.append(transformed_pick)
    
    return {
        'date': enhanced_analysis.get('date', ''),
        'version': enhanced_analysis.get('version', 'enhanced_v1.0'),
        'total_players_analyzed': enhanced_analysis.get('total_players_analyzed', 0),
        'picks': all_picks,
        'data_sources_used': enhanced_analysis.get('data_sources_used', []),
        'confidence_summary': enhanced_analysis.get('confidence_summary', {})
    }

def convert_badges_to_emojis(badge_list):
    '''Convert badge strings to emoji array for dashboard'''
    badge_emoji_map = {
        'HOT_STREAK': '🔥',
        'DUE_FOR_HR': '⚡',
        'POWER_SURGE': '💪',
        'FAVORABLE_MATCHUP': '🎯',
        'HOME_ADVANTAGE': '🏠',
        'WEATHER_BOOST': '☀️',
        # Add more mappings as needed
    }
    
    return [badge_emoji_map.get(badge, '⭐') for badge in badge_list]

def sum_badge_boosts(badge_list):
    '''Calculate total confidence boost from badges'''
    badge_boost_map = {
        'HOT_STREAK': 15,
        'DUE_FOR_HR': 12,
        'POWER_SURGE': 10,
        'FAVORABLE_MATCHUP': 8,
        'HOME_ADVANTAGE': 6,
        'WEATHER_BOOST': 5,
        # Add more mappings as needed
    }
    
    return sum(badge_boost_map.get(badge, 0) for badge in badge_list)
""")
    
    print("\n✅ SUMMARY:")
    print("-" * 80)
    print("1. Enhanced algorithm provides most required data")
    print("2. Simple field renaming needed (playerName → player_name)")
    print("3. Need to add probability calculations")
    print("4. Dashboard context transformation required for badges")
    print("5. Pitcher name needs to be added from game context")
    print("6. All component scores are already in correct format")

if __name__ == "__main__":
    analyze_field_mapping()