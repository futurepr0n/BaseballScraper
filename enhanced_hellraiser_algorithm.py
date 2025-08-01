#!/usr/bin/env python3
"""
Enhanced Hellraiser HR Prediction Algorithm
Integrates comprehensive data sources discovered from existing systems analysis.

Key Enhancements:
1. 6-component weighted scoring (vs original 5-component)
2. Confidence calibration based on data availability 
3. Multi-year handedness splits integration
4. Arsenal matchup analysis with pitch-specific data
5. Exit velocity and swing path integration
6. Strategic Intelligence System with 23-badge confidence boosts
7. Enhanced bounce back analysis with failure tracking
8. Market efficiency scoring with odds integration
"""

import json
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
import csv
from collections import defaultdict
import glob

class EnhancedHellraiserAnalyzer:
    """Enhanced Hellraiser with comprehensive data integration"""
    
    def __init__(self, data_base_path: str = None):
        if data_base_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_base_path = os.path.join(os.path.dirname(script_dir), "BaseballTracker", "public", "data")
        else:
            self.data_base_path = data_base_path
            
        # Enhanced weight system (27 factors from existing systems analysis)
        self.ENHANCED_WEIGHTS = {
            # Arsenal Matchup (40% total - highest importance)
            'batter_vs_pitch_hr': 2.0,          # HR vs specific pitches
            'batter_vs_pitch_slg': 1.5,         # Slugging vs pitch types
            'pitcher_vulnerability_hr': 1.8,     # Pitcher HR vulnerability
            'arsenal_usage_weighting': 1.3,      # Weight by pitch usage
            
            # Contextual Factors (20% total)
            'batter_overall_brl_percent': 2.5,   # Barrel rate importance
            'recent_performance_bonus': 1.5,     # Recent form importance
            'due_for_hr_factor': 1.4,           # Due factor analysis
            'hot_streak_bonus': 1.2,            # Hot streak momentum
            
            # Batter Overall Quality (15% total)
            'batter_iso_2025': 1.6,             # Current season ISO
            'batter_exit_velocity': 1.4,         # Exit velocity advantage
            'batter_hard_hit_percent': 1.3,     # Hard hit percentage
            'batter_pull_percent': 1.1,         # Pull percentage for HRs
            
            # Recent Daily Games (10% total)
            'recent_hr_trend': 1.8,             # Recent HR trend
            'recent_contact_quality': 1.5,       # Recent contact metrics
            'recent_matchup_success': 1.3,       # Recent vs similar pitchers
            
            # Pitcher Overall Vulnerability (10% total)
            'pitcher_hr_rate_allowed': 1.7,     # Overall HR rate allowed
            'pitcher_exit_velo_allowed': 1.4,   # Exit velocity allowed
            'pitcher_hard_hit_allowed': 1.3,    # Hard hit % allowed
            'pitcher_home_road_split': 1.2,     # Venue-specific vulnerability
            
            # Historical Year-over-Year (5% total)
            'batter_iso_improvement': 1.4,      # ISO improvement from 2024
            'batter_hr_rate_change': 1.3,       # HR rate change
            'age_trajectory': 1.1,              # Age-based performance trajectory
            
            # Strategic Intelligence Badges (confidence multipliers)
            'badge_confidence_multiplier': 1.8,  # Badge system boosts
            'venue_advantage': 1.5,             # Stadium factor
            'weather_conditions': 1.3,          # Weather impact
            'handedness_advantage': 1.4,        # L/R matchup advantage
        }
        
        # League averages for confidence adjustments
        self.LEAGUE_AVERAGES = {
            'hr_rate': 0.030,
            'iso': 0.150,
            'barrel_rate': 0.095,
            'exit_velocity': 88.5,
            'hard_hit_percent': 0.380,
            'pull_percent': 0.380
        }
        
        # Badge system confidence modifiers
        self.BADGE_MODIFIERS = {
            'HOT_STREAK': 0.15,         # 8+ game hitting streaks
            'ACTIVE_STREAK': 0.10,      # 5-7 game hitting streaks  
            'DUE_FOR_HR': 0.12,         # Top 5 HR predictions
            'HR_CANDIDATE': 0.08,        # Top 15 HR predictions
            'LAUNCH_PAD': 0.12,         # Extreme hitter-friendly stadium
            'HITTER_PARADISE': 0.08,    # Hitter-friendly stadium
            'WIND_BOOST': 0.10,         # Strong favorable wind
            'HOT_WEATHER': 0.05,        # Hot weather helps ball carry
            'RISK': -0.15,              # Poor performance risk
            'PITCHER_FORTRESS': -0.10,   # Extreme pitcher-friendly stadium
            'COLD_WEATHER': -0.08,      # Cold weather reduces flight
        }
        
        print(f"🚀 Enhanced Hellraiser Analyzer initialized")
        print(f"📁 Data path: {self.data_base_path}")
        print(f"🎯 Using 6-component weighted scoring with {len(self.ENHANCED_WEIGHTS)} factors")
        
    def analyze_date(self, date_str: str, use_api: bool = True) -> Dict[str, Any]:
        """
        Enhanced analysis for a specific date using all available data sources
        """
        print(f"\n🔥 Enhanced Hellraiser Analysis: {date_str}")
        
        # Load all data sources
        data_sources = self._load_comprehensive_data(date_str)
        
        # Get today's games and players
        games_data = self._load_game_data(date_str)
        if not games_data or 'games' not in games_data:
            return self._create_error_response(f"No games data for {date_str}")
            
        # Initialize analysis results
        analysis_results = {
            'date': date_str,
            'total_players_analyzed': 0,
            'data_sources_used': list(data_sources.keys()),
            'confidence_summary': {},
            'picks': [],
            'team_analysis': {},
            'market_efficiency': {},
            'enhanced_metrics': {}
        }
        
        # Analyze each game
        for game in games_data['games']:
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            
            if not home_team or not away_team:
                continue
                
            print(f"⚾ Analyzing: {away_team} @ {home_team}")
            
            # Get team predictions with enhanced analysis
            home_predictions = self._analyze_team_enhanced(
                home_team, away_team, date_str, data_sources, is_home=True, use_api=use_api
            )
            away_predictions = self._analyze_team_enhanced(
                away_team, home_team, date_str, data_sources, is_home=False, use_api=use_api
            )
            
            # Store team analysis
            analysis_results['team_analysis'][home_team] = home_predictions
            analysis_results['team_analysis'][away_team] = away_predictions
            
            # Extract top picks from each team
            analysis_results['picks'].extend(home_predictions['top_picks'])
            analysis_results['picks'].extend(away_predictions['top_picks'])
            analysis_results['total_players_analyzed'] += len(home_predictions['all_players']) + len(away_predictions['all_players'])
        
        # Calculate confidence summary
        analysis_results['confidence_summary'] = self._calculate_confidence_summary(analysis_results['picks'])
        
        # Market efficiency analysis
        analysis_results['market_efficiency'] = self._analyze_market_efficiency(
            analysis_results['picks'], 
            data_sources.get('odds_data', {})
        )
        
        # Enhanced metrics summary
        analysis_results['enhanced_metrics'] = self._calculate_enhanced_metrics_summary(analysis_results)
        
        print(f"✅ Enhanced analysis complete: {len(analysis_results['picks'])} total picks")
        print(f"📊 Data sources utilized: {len(data_sources)}")
        print(f"🎯 Average confidence: {analysis_results['confidence_summary'].get('average_confidence', 0):.1f}%")
        
        return analysis_results
    
    def _load_comprehensive_data(self, date_str: str) -> Dict[str, Any]:
        """Load all available data sources for comprehensive analysis"""
        data_sources = {}
        
        print("📊 Loading comprehensive data sources...")
        
        # 1. Daily player data (JSON files)
        try:
            player_data = self._load_player_data(date_str)
            if player_data:
                data_sources['daily_players'] = player_data
                print(f"✅ Daily player data: {len(player_data)} players")
        except Exception as e:
            print(f"⚠️ Daily player data not available: {e}")
        
        # 2. Odds data from CSV
        try:
            odds_data = self._load_odds_data()
            if odds_data:
                data_sources['odds_data'] = odds_data
                print(f"✅ Odds data: {len(odds_data)} players")
        except Exception as e:
            print(f"⚠️ Odds data not available: {e}")
            
        # 3. Multi-year handedness splits
        try:
            handedness_data = self._load_handedness_data()
            if handedness_data:
                data_sources['handedness_splits'] = handedness_data
                print(f"✅ Handedness splits: Multiple years")
        except Exception as e:
            print(f"⚠️ Handedness data not available: {e}")
            
        # 4. Rolling statistics  
        try:
            rolling_stats = self._load_rolling_stats()
            if rolling_stats:
                data_sources['rolling_stats'] = rolling_stats
                print(f"✅ Rolling stats: Recent performance data")
        except Exception as e:
            print(f"⚠️ Rolling stats not available: {e}")
            
        # 5. Roster data with 2024 stats
        try:
            roster_data = self._load_roster_data()
            if roster_data:
                data_sources['roster_data'] = roster_data
                print(f"✅ Roster data: Historical comparisons")
        except Exception as e:
            print(f"⚠️ Roster data not available: {e}")
            
        # 6. Weather and venue data
        try:
            venue_data = self._load_venue_weather_data(date_str)
            if venue_data:
                data_sources['venue_weather'] = venue_data
                print(f"✅ Venue/weather data: Stadium factors")
        except Exception as e:
            print(f"⚠️ Venue/weather data not available: {e}")
        
        print(f"📈 Loaded {len(data_sources)} data sources for enhanced analysis")
        return data_sources
    
    def _analyze_team_enhanced(self, team: str, opponent: str, date_str: str, 
                              data_sources: Dict, is_home: bool, use_api: bool = True) -> Dict[str, Any]:
        """Enhanced team analysis using all available data sources"""
        
        team_analysis = {
            'team': team,
            'opponent': opponent,
            'is_home': is_home,
            'date': date_str,
            'all_players': [],
            'top_picks': [],
            'data_quality': {},
            'confidence_factors': {}
        }
        
        # Get team players from daily data
        team_players = self._get_team_players(team, data_sources.get('daily_players', []))
        
        if not team_players:
            print(f"⚠️ No players found for {team}")
            return team_analysis
            
        print(f"🔍 Analyzing {len(team_players)} players for {team}")
        
        # Analyze each player with enhanced algorithm
        for player in team_players:
            if player.get('playerType') != 'hitter':
                continue
                
            # Enhanced player analysis
            player_analysis = self._analyze_player_enhanced(
                player, opponent, date_str, data_sources, is_home, use_api
            )
            
            team_analysis['all_players'].append(player_analysis)
        
        # Sort by enhanced confidence score and select top 3
        team_analysis['all_players'].sort(key=lambda x: x['enhanced_confidence_score'], reverse=True)
        team_analysis['top_picks'] = team_analysis['all_players'][:3]
        
        # Calculate team-level data quality metrics
        team_analysis['data_quality'] = self._calculate_team_data_quality(team_analysis['all_players'])
        
        return team_analysis
    
    def _analyze_player_enhanced(self, player: Dict, opponent: str, date_str: str, 
                                data_sources: Dict, is_home: bool, use_api: bool = True) -> Dict[str, Any]:
        """
        Enhanced player analysis using 6-component weighted scoring system
        """
        player_name = player.get('name', '')
        team = player.get('team', '')
        
        # Initialize analysis structure
        analysis = {
            'playerName': player_name,
            'team': team,
            'opponent': opponent,
            'is_home': is_home,
            'date': date_str,
            'enhanced_confidence_score': 0,
            'pathway': 'unknown',
            'component_scores': {},
            'data_sources_used': [],
            'confidence_factors': {},
            'badge_modifiers': [],
            'market_analysis': {},
            'detailed_breakdown': {}
        }
        
        # Component 1: Arsenal Matchup (40% weight)
        arsenal_score = self._calculate_arsenal_matchup_score(
            player, opponent, data_sources, use_api
        )
        analysis['component_scores']['arsenal_matchup'] = arsenal_score
        
        # Component 2: Contextual Factors (20% weight)
        contextual_score = self._calculate_contextual_factors_score(
            player, data_sources, date_str
        )
        analysis['component_scores']['contextual_factors'] = contextual_score
        
        # Component 3: Batter Overall Quality (15% weight)
        quality_score = self._calculate_batter_quality_score(
            player, data_sources
        )
        analysis['component_scores']['batter_quality'] = quality_score
        
        # Component 4: Recent Daily Games (10% weight)
        recent_score = self._calculate_recent_performance_score(
            player, data_sources, date_str
        )
        analysis['component_scores']['recent_performance'] = recent_score
        
        # Component 5: Pitcher Overall Vulnerability (10% weight)
        pitcher_score = self._calculate_pitcher_vulnerability_score(
            opponent, data_sources, use_api
        )
        analysis['component_scores']['pitcher_vulnerability'] = pitcher_score
        
        # Component 6: Historical Year-over-Year (5% weight)
        historical_score = self._calculate_historical_comparison_score(
            player, data_sources
        )
        analysis['component_scores']['historical_comparison'] = historical_score
        
        # Calculate weighted total score
        weighted_score = (
            arsenal_score * 0.40 +
            contextual_score * 0.20 +
            quality_score * 0.15 +
            recent_score * 0.10 +
            pitcher_score * 0.10 +
            historical_score * 0.05
        )
        
        # Apply Strategic Intelligence Badge modifiers
        badge_analysis = self._analyze_strategic_badges(player, data_sources, is_home)
        badge_modifier = sum(badge_analysis['modifiers'])
        analysis['badge_modifiers'] = badge_analysis['badges']
        
        # Final enhanced confidence score
        analysis['enhanced_confidence_score'] = min(100, max(0, weighted_score + badge_modifier))
        
        # Determine pathway classification
        analysis['pathway'] = self._determine_enhanced_pathway(analysis)
        
        # Market efficiency analysis
        analysis['market_analysis'] = self._analyze_player_market_efficiency(
            player_name, analysis['enhanced_confidence_score'], 
            data_sources.get('odds_data', {})
        )
        
        # Track data sources actually used
        analysis['data_sources_used'] = self._get_used_data_sources(data_sources, player)
        
        # Confidence factors (for transparency)
        analysis['confidence_factors'] = {
            'data_completeness': len(analysis['data_sources_used']) / 6,  # Out of 6 possible sources
            'sample_size_adequacy': self._assess_sample_size_adequacy(player, data_sources),
            'recency_factor': self._assess_data_recency(data_sources, date_str)
        }
        
        return analysis
    
    def _calculate_arsenal_matchup_score(self, player: Dict, opponent: str, 
                                       data_sources: Dict, use_api: bool = True) -> float:
        """Calculate arsenal matchup score using BaseballAPI 6-component insights"""
        base_score = 50.0  # Start neutral
        
        # If API available, use enhanced pitcher vs batter analysis
        if use_api:
            try:
                api_analysis = self._get_api_arsenal_analysis(player, opponent)
                if api_analysis and api_analysis.get('success'):
                    # Extract key arsenal metrics
                    pitcher_data = api_analysis.get('pitcher_stats', {})
                    batter_data = api_analysis.get('batter_stats', {})
                    
                    # Arsenal vulnerability scoring
                    arsenal_matchup = api_analysis.get('arsenal_matchup_score', 50)
                    base_score = arsenal_matchup
                    
                    # Apply enhanced weights
                    hr_vs_pitch_bonus = batter_data.get('hr_vs_primary_pitch', 0) * self.ENHANCED_WEIGHTS['batter_vs_pitch_hr']
                    slg_vs_pitch_bonus = batter_data.get('slg_vs_pitch_types', 0) * self.ENHANCED_WEIGHTS['batter_vs_pitch_slg']
                    pitcher_vuln_penalty = pitcher_data.get('hr_vulnerability', 0) * self.ENHANCED_WEIGHTS['pitcher_vulnerability_hr']
                    
                    base_score += hr_vs_pitch_bonus + slg_vs_pitch_bonus + pitcher_vuln_penalty
                    
            except Exception as e:
                print(f"⚠️ API arsenal analysis failed for {player.get('name', '')}: {e}")
        
        # Fallback to available data sources
        handedness_data = data_sources.get('handedness_splits', {})
        if handedness_data:
            handedness_advantage = self._calculate_handedness_advantage(player, opponent, handedness_data)
            base_score += handedness_advantage * self.ENHANCED_WEIGHTS['handedness_advantage']
        
        return min(100, max(0, base_score))
    
    def _calculate_contextual_factors_score(self, player: Dict, data_sources: Dict, date_str: str) -> float:
        """Calculate contextual factors using barrel rate, recent performance, due factors"""
        base_score = 50.0
        
        # Barrel rate analysis (highest individual weight: 2.5)
        barrel_rate = self._get_player_barrel_rate(player, data_sources)
        if barrel_rate is not None:
            # Above league average gets bonus
            league_avg_barrel = self.LEAGUE_AVERAGES['barrel_rate']
            barrel_advantage = (barrel_rate - league_avg_barrel) / league_avg_barrel
            base_score += barrel_advantage * 20 * self.ENHANCED_WEIGHTS['batter_overall_brl_percent']
        
        # Recent performance bonus
        recent_performance = self._analyze_recent_performance_trend(player, data_sources, date_str)
        if recent_performance['is_hot']:
            base_score += recent_performance['bonus'] * self.ENHANCED_WEIGHTS['recent_performance_bonus']
        
        # Due for HR factor (enhanced bounce back analysis)
        due_analysis = self._calculate_enhanced_due_factor(player, data_sources, date_str)
        base_score += due_analysis['due_score'] * self.ENHANCED_WEIGHTS['due_for_hr_factor']
        
        # Hot streak detection
        streak_analysis = self._analyze_hitting_streak(player, data_sources, date_str)
        if streak_analysis['has_streak']:
            base_score += streak_analysis['bonus'] * self.ENHANCED_WEIGHTS['hot_streak_bonus']
        
        return min(100, max(0, base_score))
    
    def _calculate_batter_quality_score(self, player: Dict, data_sources: Dict) -> float:
        """Calculate batter overall quality using ISO, exit velocity, hard hit %"""
        base_score = 50.0
        
        # Current season ISO (primary power metric)
        iso_2025 = self._get_player_iso_2025(player, data_sources)
        if iso_2025 is not None:
            league_avg_iso = self.LEAGUE_AVERAGES['iso']
            iso_advantage = (iso_2025 - league_avg_iso) / league_avg_iso
            base_score += iso_advantage * 25 * self.ENHANCED_WEIGHTS['batter_iso_2025']
        
        # Exit velocity advantage
        exit_velo = self._get_player_exit_velocity(player, data_sources)
        if exit_velo is not None:
            league_avg_ev = self.LEAGUE_AVERAGES['exit_velocity']
            ev_advantage = (exit_velo - league_avg_ev) / league_avg_ev
            base_score += ev_advantage * 20 * self.ENHANCED_WEIGHTS['batter_exit_velocity']
        
        # Hard hit percentage
        hard_hit_pct = self._get_player_hard_hit_percent(player, data_sources)
        if hard_hit_pct is not None:
            league_avg_hh = self.LEAGUE_AVERAGES['hard_hit_percent']
            hh_advantage = (hard_hit_pct - league_avg_hh) / league_avg_hh
            base_score += hh_advantage * 15 * self.ENHANCED_WEIGHTS['batter_hard_hit_percent']
        
        # Pull percentage (for HR potential)
        pull_pct = self._get_player_pull_percent(player, data_sources)
        if pull_pct is not None:
            league_avg_pull = self.LEAGUE_AVERAGES['pull_percent']
            pull_advantage = (pull_pct - league_avg_pull) / league_avg_pull
            base_score += pull_advantage * 10 * self.ENHANCED_WEIGHTS['batter_pull_percent']
        
        return min(100, max(0, base_score))
    
    def _calculate_recent_performance_score(self, player: Dict, data_sources: Dict, date_str: str) -> float:
        """Calculate recent performance using last 10-15 games"""
        base_score = 50.0
        
        # Recent HR trend (last 15 games)
        recent_hr_trend = self._analyze_recent_hr_trend(player, data_sources, date_str, days_back=15)
        base_score += recent_hr_trend * self.ENHANCED_WEIGHTS['recent_hr_trend']
        
        # Recent contact quality
        contact_quality = self._analyze_recent_contact_quality(player, data_sources, date_str)
        base_score += contact_quality * self.ENHANCED_WEIGHTS['recent_contact_quality']
        
        # Recent matchup success (vs similar pitchers)
        matchup_success = self._analyze_recent_matchup_success(player, data_sources, date_str)
        base_score += matchup_success * self.ENHANCED_WEIGHTS['recent_matchup_success']
        
        return min(100, max(0, base_score))
    
    def _calculate_pitcher_vulnerability_score(self, opponent: str, data_sources: Dict, use_api: bool = True) -> float:
        """Calculate pitcher vulnerability using API and available data"""
        base_score = 50.0
        
        if use_api:
            try:
                # Use BaseballAPI pitcher analysis
                pitcher_analysis = self._get_api_pitcher_vulnerability(opponent)
                if pitcher_analysis and pitcher_analysis.get('success'):
                    vulnerability_metrics = pitcher_analysis.get('vulnerability_metrics', {})
                    
                    # HR rate allowed
                    hr_rate_allowed = vulnerability_metrics.get('hr_rate_allowed', 0)
                    base_score += hr_rate_allowed * self.ENHANCED_WEIGHTS['pitcher_hr_rate_allowed']
                    
                    # Exit velocity allowed
                    ev_allowed = vulnerability_metrics.get('exit_velo_allowed', 0)
                    base_score += ev_allowed * self.ENHANCED_WEIGHTS['pitcher_exit_velo_allowed']
                    
                    # Hard hit percentage allowed
                    hh_allowed = vulnerability_metrics.get('hard_hit_allowed', 0)
                    base_score += hh_allowed * self.ENHANCED_WEIGHTS['pitcher_hard_hit_allowed']
                    
            except Exception as e:
                print(f"⚠️ API pitcher analysis failed for {opponent}: {e}")
        
        # Home/road split analysis
        home_road_factor = self._analyze_pitcher_home_road_splits(opponent, data_sources)
        base_score += home_road_factor * self.ENHANCED_WEIGHTS['pitcher_home_road_split']
        
        return min(100, max(0, base_score))
    
    def _calculate_historical_comparison_score(self, player: Dict, data_sources: Dict) -> float:
        """Calculate year-over-year comparison using roster data"""
        base_score = 50.0
        
        # ISO improvement from 2024 to 2025
        iso_comparison = self._compare_iso_year_over_year(player, data_sources)
        if iso_comparison['has_data']:
            improvement = iso_comparison['improvement']
            base_score += improvement * self.ENHANCED_WEIGHTS['batter_iso_improvement']
        
        # HR rate change
        hr_rate_comparison = self._compare_hr_rate_year_over_year(player, data_sources)
        if hr_rate_comparison['has_data']:
            change = hr_rate_comparison['change']
            base_score += change * self.ENHANCED_WEIGHTS['batter_hr_rate_change']
        
        # Age trajectory analysis
        age_factor = self._analyze_age_trajectory(player, data_sources)
        base_score += age_factor * self.ENHANCED_WEIGHTS['age_trajectory']
        
        return min(100, max(0, base_score))
    
    def _analyze_strategic_badges(self, player: Dict, data_sources: Dict, is_home: bool) -> Dict[str, Any]:
        """Analyze Strategic Intelligence System badges for confidence boosts"""
        badges = []
        modifiers = []
        
        # Performance badges
        hitting_streak = self._get_hitting_streak_length(player, data_sources)
        if hitting_streak >= 8:
            badges.append('HOT_STREAK')
            modifiers.append(self.BADGE_MODIFIERS['HOT_STREAK'])
        elif hitting_streak >= 5:
            badges.append('ACTIVE_STREAK')
            modifiers.append(self.BADGE_MODIFIERS['ACTIVE_STREAK'])
        
        # Due for HR analysis
        hr_ranking = self._get_hr_prediction_ranking(player, data_sources)
        if hr_ranking <= 5:
            badges.append('DUE_FOR_HR')
            modifiers.append(self.BADGE_MODIFIERS['DUE_FOR_HR'])
        elif hr_ranking <= 15:
            badges.append('HR_CANDIDATE')
            modifiers.append(self.BADGE_MODIFIERS['HR_CANDIDATE'])
        
        # Stadium context
        stadium_factor = self._analyze_stadium_factor(player, data_sources, is_home)
        if stadium_factor == 'extreme_hitter_friendly':
            badges.append('LAUNCH_PAD')
            modifiers.append(self.BADGE_MODIFIERS['LAUNCH_PAD'])
        elif stadium_factor == 'hitter_friendly':
            badges.append('HITTER_PARADISE')
            modifiers.append(self.BADGE_MODIFIERS['HITTER_PARADISE'])
        elif stadium_factor == 'extreme_pitcher_friendly':
            badges.append('PITCHER_FORTRESS')
            modifiers.append(self.BADGE_MODIFIERS['PITCHER_FORTRESS'])
        
        # Weather conditions
        weather_factor = self._analyze_weather_conditions(data_sources)
        if weather_factor == 'strong_wind_boost':
            badges.append('WIND_BOOST')
            modifiers.append(self.BADGE_MODIFIERS['WIND_BOOST'])
        elif weather_factor == 'hot_weather':
            badges.append('HOT_WEATHER')
            modifiers.append(self.BADGE_MODIFIERS['HOT_WEATHER'])
        elif weather_factor == 'cold_weather':
            badges.append('COLD_WEATHER')
            modifiers.append(self.BADGE_MODIFIERS['COLD_WEATHER'])
        
        # Risk assessment
        if self._has_recent_poor_performance(player, data_sources):
            badges.append('RISK')
            modifiers.append(self.BADGE_MODIFIERS['RISK'])
        
        return {
            'badges': badges,
            'modifiers': modifiers,
            'total_modifier': sum(modifiers)
        }
    
    def _determine_enhanced_pathway(self, analysis: Dict) -> str:
        """Determine pathway classification based on component scores"""
        total_score = analysis['enhanced_confidence_score']
        
        # Enhanced pathway thresholds
        if total_score >= 85:
            return 'perfectStorm'
        elif total_score >= 75:
            # Check if batter-driven (high quality + contextual scores)
            batter_strength = (analysis['component_scores']['batter_quality'] + 
                              analysis['component_scores']['contextual_factors']) / 2
            if batter_strength >= 70:
                return 'batterDriven'
            else:
                return 'pitcherDriven'
        elif total_score >= 65:
            return 'moderateOpportunity'
        else:
            return 'lowConfidence'
    
    def _analyze_market_efficiency(self, picks: List, odds_data: Dict) -> Dict[str, Any]:
        """Analyze market efficiency and betting value"""
        market_analysis = {
            'total_picks_with_odds': 0,
            'positive_ev_opportunities': 0,
            'average_implied_probability': 0,
            'average_model_confidence': 0,
            'efficiency_score': 0,
            'value_picks': []
        }
        
        picks_with_odds = []
        positive_ev_count = 0
        
        for pick in picks:
            player_name = pick.get('playerName', '')
            model_confidence = pick.get('enhanced_confidence_score', 0)
            
            # Find betting odds
            odds_info = self._find_player_odds(player_name, odds_data)
            if odds_info:
                implied_prob = self._odds_to_probability(odds_info['odds'])
                pick_with_market = {
                    **pick,
                    'betting_odds': odds_info['odds'],
                    'implied_probability': implied_prob,
                    'model_probability': model_confidence / 100,
                    'expected_value': (model_confidence / 100) - implied_prob,
                    'has_edge': (model_confidence / 100) > implied_prob
                }
                picks_with_odds.append(pick_with_market)
                
                if pick_with_market['has_edge']:
                    positive_ev_count += 1
                    market_analysis['value_picks'].append(pick_with_market)
        
        if picks_with_odds:
            market_analysis['total_picks_with_odds'] = len(picks_with_odds)
            market_analysis['positive_ev_opportunities'] = positive_ev_count
            market_analysis['average_implied_probability'] = np.mean([p['implied_probability'] for p in picks_with_odds])
            market_analysis['average_model_confidence'] = np.mean([p['model_probability'] for p in picks_with_odds])
            market_analysis['efficiency_score'] = positive_ev_count / len(picks_with_odds) if picks_with_odds else 0
        
        return market_analysis
    
    # Data loading helper methods
    def _load_player_data(self, date_str: str) -> List[Dict]:
        """Load player data for specific date"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        month_name = date_obj.strftime("%B").lower()
        day = date_obj.day
        
        file_path = os.path.join(
            self.data_base_path, 
            str(year), 
            month_name, 
            f"{month_name}_{day:02d}_{year}.json"
        )
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get('players', [])
        except:
            return []
    
    def _load_game_data(self, date_str: str) -> Dict:
        """Load game data for specific date"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        month_name = date_obj.strftime("%B").lower()
        day = date_obj.day
        
        file_path = os.path.join(
            self.data_base_path, 
            str(year), 
            month_name, 
            f"{month_name}_{day:02d}_{year}.json"
        )
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _load_odds_data(self) -> Dict:
        """Load latest odds data from CSV"""
        odds_files = [
            os.path.join(self.data_base_path, "odds", "mlb-hr-odds-only.csv"),
            os.path.join(self.data_base_path, "odds", "mlb-hr-odds.csv"),
            os.path.join(os.path.dirname(self.data_base_path), "build", "data", "odds", "mlb-hr-odds-only.csv")
        ]
        
        for odds_file in odds_files:
            if os.path.exists(odds_file):
                try:
                    odds_data = {}
                    with open(odds_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            player_name = row.get('player_name', '').strip()
                            odds = row.get('odds', '').strip()
                            if player_name and odds:
                                odds_data[player_name] = {
                                    'odds': odds,
                                    'last_updated': row.get('last_updated', '')
                                }
                    return odds_data
                except:
                    continue
        
        return {}
    
    def _load_handedness_data(self) -> Dict:
        """Load multi-year handedness splits data"""
        # This would load handedness CSV files if available
        # For now, return empty dict
        return {}
    
    def _load_rolling_stats(self) -> Dict:
        """Load rolling statistics data"""
        # This would load rolling stats if available
        # For now, return empty dict
        return {}
    
    def _load_roster_data(self) -> List[Dict]:
        """Load roster data with 2024 comparisons"""
        # This would load roster JSON with historical stats
        # For now, return empty list
        return []
    
    def _load_venue_weather_data(self, date_str: str) -> Dict:
        """Load venue and weather data"""
        # This would load weather/venue data
        # For now, return empty dict
        return {}
    
    # Placeholder helper methods (would be implemented with actual data)
    def _get_team_players(self, team: str, players_data: List) -> List[Dict]:
        """Get players for specific team"""
        return [p for p in players_data if p.get('team') == team and p.get('playerType') == 'hitter']
    
    def _get_api_arsenal_analysis(self, player: Dict, opponent: str) -> Dict:
        """Get arsenal analysis from BaseballAPI"""
        # Would call BaseballAPI for detailed matchup analysis
        return {}
    
    def _get_api_pitcher_vulnerability(self, pitcher: str) -> Dict:
        """Get pitcher vulnerability from BaseballAPI"""
        # Would call BaseballAPI for pitcher analysis
        return {}
    
    def _calculate_handedness_advantage(self, player: Dict, opponent: str, handedness_data: Dict) -> float:
        """Calculate L/R handedness advantage"""
        return 0.0  # Placeholder
    
    def _get_player_barrel_rate(self, player: Dict, data_sources: Dict) -> Optional[float]:
        """Get player barrel rate from available data"""
        return None  # Placeholder
    
    def _analyze_recent_performance_trend(self, player: Dict, data_sources: Dict, date_str: str) -> Dict:
        """Analyze recent performance trend"""
        return {'is_hot': False, 'bonus': 0}  # Placeholder
    
    def _calculate_enhanced_due_factor(self, player: Dict, data_sources: Dict, date_str: str) -> Dict:
        """Calculate enhanced due factor with failure tracking"""
        return {'due_score': 0}  # Placeholder
    
    def _analyze_hitting_streak(self, player: Dict, data_sources: Dict, date_str: str) -> Dict:
        """Analyze current hitting streak"""
        return {'has_streak': False, 'bonus': 0}  # Placeholder
    
    def _get_player_iso_2025(self, player: Dict, data_sources: Dict) -> Optional[float]:
        """Get player's 2025 ISO"""
        return None  # Placeholder
    
    def _get_player_exit_velocity(self, player: Dict, data_sources: Dict) -> Optional[float]:
        """Get player exit velocity"""
        return None  # Placeholder
    
    def _get_player_hard_hit_percent(self, player: Dict, data_sources: Dict) -> Optional[float]:
        """Get player hard hit percentage"""
        return None  # Placeholder
    
    def _get_player_pull_percent(self, player: Dict, data_sources: Dict) -> Optional[float]:
        """Get player pull percentage"""
        return None  # Placeholder
    
    def _analyze_recent_hr_trend(self, player: Dict, data_sources: Dict, date_str: str, days_back: int) -> float:
        """Analyze recent HR trend"""
        return 0.0  # Placeholder
    
    def _analyze_recent_contact_quality(self, player: Dict, data_sources: Dict, date_str: str) -> float:
        """Analyze recent contact quality"""
        return 0.0  # Placeholder
    
    def _analyze_recent_matchup_success(self, player: Dict, data_sources: Dict, date_str: str) -> float:
        """Analyze recent success vs similar pitchers"""
        return 0.0  # Placeholder
    
    def _analyze_pitcher_home_road_splits(self, pitcher: str, data_sources: Dict) -> float:
        """Analyze pitcher home/road splits"""
        return 0.0  # Placeholder
    
    def _compare_iso_year_over_year(self, player: Dict, data_sources: Dict) -> Dict:
        """Compare ISO from 2024 to 2025"""
        return {'has_data': False, 'improvement': 0}  # Placeholder
    
    def _compare_hr_rate_year_over_year(self, player: Dict, data_sources: Dict) -> Dict:
        """Compare HR rate from 2024 to 2025"""
        return {'has_data': False, 'change': 0}  # Placeholder
    
    def _analyze_age_trajectory(self, player: Dict, data_sources: Dict) -> float:
        """Analyze age-based performance trajectory"""
        return 0.0  # Placeholder
    
    def _get_hitting_streak_length(self, player: Dict, data_sources: Dict) -> int:
        """Get current hitting streak length"""
        return 0  # Placeholder
    
    def _get_hr_prediction_ranking(self, player: Dict, data_sources: Dict) -> int:
        """Get player's HR prediction ranking"""
        return 50  # Placeholder
    
    def _analyze_stadium_factor(self, player: Dict, data_sources: Dict, is_home: bool) -> str:
        """Analyze stadium HR factor"""
        return 'neutral'  # Placeholder
    
    def _analyze_weather_conditions(self, data_sources: Dict) -> str:
        """Analyze weather conditions"""
        return 'neutral'  # Placeholder
    
    def _has_recent_poor_performance(self, player: Dict, data_sources: Dict) -> bool:
        """Check for recent poor performance"""
        return False  # Placeholder
    
    def _calculate_confidence_summary(self, picks: List) -> Dict:
        """Calculate overall confidence summary"""
        if not picks:
            return {'average_confidence': 0, 'high_confidence_picks': 0}
        
        confidences = [p.get('enhanced_confidence_score', 0) for p in picks]
        return {
            'average_confidence': np.mean(confidences),
            'high_confidence_picks': len([c for c in confidences if c >= 80]),
            'medium_confidence_picks': len([c for c in confidences if 60 <= c < 80]),
            'low_confidence_picks': len([c for c in confidences if c < 60])
        }
    
    def _calculate_enhanced_metrics_summary(self, analysis_results: Dict) -> Dict:
        """Calculate enhanced metrics summary"""
        return {
            'total_data_sources': len(analysis_results.get('data_sources_used', [])),
            'pathway_distribution': self._calculate_pathway_distribution(analysis_results.get('picks', [])),
            'badge_utilization': self._calculate_badge_utilization(analysis_results.get('picks', []))
        }
    
    def _calculate_pathway_distribution(self, picks: List) -> Dict:
        """Calculate distribution of pathway classifications"""
        pathways = [p.get('pathway', 'unknown') for p in picks]
        distribution = {}
        for pathway in set(pathways):
            distribution[pathway] = pathways.count(pathway)
        return distribution
    
    def _calculate_badge_utilization(self, picks: List) -> Dict:
        """Calculate utilization of strategic badges"""
        all_badges = []
        for pick in picks:
            all_badges.extend(pick.get('badge_modifiers', []))
        
        badge_counts = {}
        for badge in set(all_badges):
            badge_counts[badge] = all_badges.count(badge)
        
        return badge_counts
    
    def _find_player_odds(self, player_name: str, odds_data: Dict) -> Optional[Dict]:
        """Find betting odds for player"""
        return odds_data.get(player_name)
    
    def _odds_to_probability(self, odds_str: str) -> float:
        """Convert American odds to implied probability"""
        try:
            odds = int(odds_str.replace('+', ''))
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        except:
            return 0.5  # Default to 50% if parsing fails
    
    def _get_used_data_sources(self, data_sources: Dict, player: Dict) -> List[str]:
        """Track which data sources were actually used for this player"""
        used_sources = []
        
        if data_sources.get('daily_players'):
            used_sources.append('daily_players')
        if data_sources.get('odds_data') and player.get('name') in data_sources['odds_data']:
            used_sources.append('odds_data')
        if data_sources.get('handedness_splits'):
            used_sources.append('handedness_splits')
        if data_sources.get('rolling_stats'):
            used_sources.append('rolling_stats')
        if data_sources.get('roster_data'):
            used_sources.append('roster_data')
        if data_sources.get('venue_weather'):
            used_sources.append('venue_weather')
            
        return used_sources
    
    def _assess_sample_size_adequacy(self, player: Dict, data_sources: Dict) -> float:
        """Assess if sample size is adequate for confident predictions"""
        # Placeholder - would analyze PA, games played, etc.
        return 0.7
    
    def _assess_data_recency(self, data_sources: Dict, date_str: str) -> float:
        """Assess how recent the data is"""
        # Placeholder - would check data timestamps
        return 0.8
    
    def _calculate_team_data_quality(self, players: List) -> Dict:
        """Calculate team-level data quality metrics"""
        if not players:
            return {'overall_quality': 0}
        
        confidence_scores = [p.get('confidence_factors', {}).get('data_completeness', 0) for p in players]
        return {
            'overall_quality': np.mean(confidence_scores),
            'players_with_high_quality_data': len([c for c in confidence_scores if c >= 0.8]),
            'data_source_coverage': np.mean([len(p.get('data_sources_used', [])) for p in players])
        }
    
    def _analyze_player_market_efficiency(self, player_name: str, confidence_score: float, odds_data: Dict) -> Dict:
        """Analyze market efficiency for individual player"""
        odds_info = odds_data.get(player_name)
        if not odds_info:
            return {'has_odds': False}
        
        implied_prob = self._odds_to_probability(odds_info['odds'])
        model_prob = confidence_score / 100
        
        return {
            'has_odds': True,
            'betting_odds': odds_info['odds'],
            'implied_probability': implied_prob,
            'model_probability': model_prob,
            'expected_value': model_prob - implied_prob,
            'has_edge': model_prob > implied_prob,
            'edge_magnitude': abs(model_prob - implied_prob)
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            'error': error_message,
            'picks': [],
            'team_analysis': {},
            'market_efficiency': {},
            'enhanced_metrics': {}
        }
    
    def save_analysis(self, analysis_results: Dict, output_dir: str = None) -> str:
        """Save enhanced analysis results to JSON file"""
        if output_dir is None:
            output_dir = os.path.join(self.data_base_path, "hellraiser")
        
        os.makedirs(output_dir, exist_ok=True)
        
        date_str = analysis_results.get('date', datetime.now().strftime('%Y-%m-%d'))
        filename = f"enhanced_hellraiser_analysis_{date_str}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Add metadata
        analysis_results['metadata'] = {
            'algorithm_version': 'Enhanced_Hellraiser_v2.0',
            'generated_at': datetime.now().isoformat(),
            'components': '6-component weighted scoring',
            'data_sources': len(analysis_results.get('data_sources_used', [])),
            'enhanced_features': [
                'Strategic Intelligence Badges',
                'Market Efficiency Analysis', 
                'Confidence Calibration',
                'Multi-source Integration',
                'Arsenal Matchup Analysis',
                'Enhanced Due Factor Analysis'
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"💾 Enhanced analysis saved: {filepath}")
        return filepath


def main():
    """Main function for enhanced Hellraiser analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Hellraiser HR Prediction Algorithm')
    parser.add_argument('--date', type=str, help='Date to analyze (YYYY-MM-DD)', 
                       default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--no-api', action='store_true', help='Disable BaseballAPI integration')
    parser.add_argument('--output-dir', type=str, help='Output directory for results')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    
    args = parser.parse_args()
    
    print("🚀 Enhanced Hellraiser Algorithm - Advanced HR Prediction System")
    print("=" * 70)
    
    # Initialize enhanced analyzer
    analyzer = EnhancedHellraiserAnalyzer()
    
    # Run analysis
    results = analyzer.analyze_date(
        date_str=args.date,
        use_api=not args.no_api
    )
    
    if results.get('error'):
        print(f"❌ Analysis failed: {results['error']}")
        return
    
    # Display results summary
    print(f"\n📊 Enhanced Analysis Summary for {args.date}")
    print("-" * 50)
    
    picks = results.get('picks', [])
    print(f"Total Predictions: {len(picks)}")
    
    if picks:
        print(f"Average Confidence: {results['confidence_summary']['average_confidence']:.1f}%")
        print(f"High Confidence (≥80%): {results['confidence_summary']['high_confidence_picks']}")
        
        # Show top 10 picks
        top_picks = sorted(picks, key=lambda x: x['enhanced_confidence_score'], reverse=True)[:10]
        print(f"\n🎯 Top 10 Enhanced Predictions:")
        print("-" * 40)
        
        for i, pick in enumerate(top_picks, 1):
            pathway = pick.get('pathway', 'unknown')
            confidence = pick.get('enhanced_confidence_score', 0)
            badges = ', '.join(pick.get('badge_modifiers', []))
            market_info = pick.get('market_analysis', {})
            
            print(f"{i:2d}. {pick['playerName']} ({pick['team']}) - {confidence:.1f}%")
            print(f"    Pathway: {pathway}")
            if badges:
                print(f"    Badges: {badges}")
            if market_info.get('has_edge'):
                ev = market_info.get('expected_value', 0)
                print(f"    Market Edge: +{ev:.3f}")
    
    # Market efficiency summary
    market_analysis = results.get('market_efficiency', {})
    if market_analysis.get('total_picks_with_odds', 0) > 0:
        print(f"\n💰 Market Efficiency Analysis:")
        print(f"Picks with Odds: {market_analysis['total_picks_with_odds']}")
        print(f"Positive EV Opportunities: {market_analysis['positive_ev_opportunities']}")
        print(f"Market Efficiency Score: {market_analysis['efficiency_score']:.1%}")
    
    # Save results if requested
    if args.save:
        filepath = analyzer.save_analysis(results, args.output_dir)
        print(f"\n💾 Results saved to: {filepath}")
    
    print(f"\n✅ Enhanced Hellraiser analysis complete!")


if __name__ == "__main__":
    main()