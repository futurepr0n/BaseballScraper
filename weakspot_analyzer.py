#!/usr/bin/env python3
"""
Comprehensive Weakspot Analysis Engine
=====================================

Multi-tier pitcher vulnerability analysis system that combines:
- Play-by-play granular data (pitch-level detail)
- Advanced pitcher/batter metrics (300+ pitcher, 150+ batter stats)
- Situational context analysis (lineup spots, innings, pitch patterns)
- Historical pattern recognition (multi-year handedness and performance data)

Key Innovation: Moving beyond traditional "pitcher vs team" to 
"pitcher vs lineup spot vs situation" analysis with confidence scoring.

Author: BaseballScraper Enhancement System
Date: August 2025
"""

import json
import csv
import os
import sys
from datetime import datetime, timedelta
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import logging
from collections import defaultdict, Counter

# Add the BaseballScraper directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the comprehensive pitcher name mapper
try:
    from pitcher_name_mapper import PitcherNameMapper
    PITCHER_MAPPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import PitcherNameMapper: {e}")
    PITCHER_MAPPER_AVAILABLE = False

class PlayerIDMapper:
    """Legacy fallback mapper for anonymous play-by-play IDs - replaced by PitcherNameMapper"""
    
    def __init__(self, base_data_path: str):
        self.base_data_path = Path(base_data_path)
        self.player_name_cache = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize the comprehensive pitcher mapper if available
        if PITCHER_MAPPER_AVAILABLE:
            self.pitcher_mapper = PitcherNameMapper(base_data_path)
            self.pitcher_mapper.load_all_data_sources()
            self.logger.info("Loaded comprehensive PitcherNameMapper")
        else:
            self.pitcher_mapper = None
            self.logger.warning("Using fallback PlayerIDMapper - results may be limited")
    
    def resolve_player_id(self, player_id: str, team: str = None) -> Optional[str]:
        """
        Resolve anonymous player ID to actual name using comprehensive mapper
        
        Args:
            player_id: Anonymous ID like "Batter_42404" or "Pitcher_4307825"
            team: Team abbreviation to help with lookup
        
        Returns:
            Player name if found, None otherwise
        """
        # Use comprehensive pitcher mapper for pitchers if available
        if (PITCHER_MAPPER_AVAILABLE and self.pitcher_mapper and 
            player_id.startswith('Pitcher_')):
            
            # Build mapping if not already done
            if not self.pitcher_mapper.anonymous_to_name:
                playbyplay_dir = Path("../BaseballData/data/play-by-play")
                if playbyplay_dir.exists():
                    pbp_files = list(playbyplay_dir.glob("*_vs_*_playbyplay_*.json"))[:50]
                    if pbp_files:
                        self.pitcher_mapper.build_anonymous_mapping(pbp_files)
            
            real_name = self.pitcher_mapper.get_pitcher_name(player_id)
            if real_name and not real_name.startswith("Unknown"):
                return real_name
        
        # Fallback for batters and failed pitcher lookups
        return self._fallback_resolve(player_id, team)
    
    def _fallback_resolve(self, player_id: str, team: str = None) -> Optional[str]:
        """Fallback resolution for player IDs when comprehensive mapper fails"""
        # Simple fallback - return formatted anonymous ID
        if player_id.startswith(('Pitcher_', 'Batter_')):
            return f"Unknown_{player_id}"
        return None

class PlayByPlayProcessor:
    """Processes play-by-play data for vulnerability analysis"""
    
    def __init__(self, base_data_path: str):
        self.base_data_path = Path(base_data_path)
        self.playbyplay_path = self.base_data_path / "playbyplay"
        self.daily_data_path = self.base_data_path / "2025"
        self.logger = logging.getLogger(__name__)
        self.player_mapper = PlayerIDMapper(base_data_path)
        
    def load_playbyplay_files(self, date_range: Optional[Tuple[str, str]] = None) -> List[Dict]:
        """
        Load play-by-play files for analysis
        
        Args:
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
        
        Returns:
            List of play-by-play game data
        """
        playbyplay_files = list(self.playbyplay_path.glob("*_vs_*_playbyplay_*.json"))
        games_data = []
        
        for file_path in playbyplay_files:
            try:
                # Extract date from filename for filtering
                if date_range:
                    # Parse filename like "ARI_vs_ATL_playbyplay_june_3_2025_401695803.json"
                    filename_parts = file_path.stem.split('_')
                    if len(filename_parts) >= 5:
                        month = filename_parts[-3]
                        day = filename_parts[-2]
                        year = filename_parts[-1].split('_')[0]  # Remove game ID
                        
                        # Convert to standard date format
                        try:
                            file_date = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").strftime("%Y-%m-%d")
                            if not (date_range[0] <= file_date <= date_range[1]):
                                continue
                        except ValueError:
                            self.logger.warning(f"Could not parse date from filename: {file_path}")
                            continue
                
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                    game_data['file_path'] = str(file_path)
                    games_data.append(game_data)
                    
            except Exception as e:
                self.logger.error(f"Error loading play-by-play file {file_path}: {e}")
                
        self.logger.info(f"Loaded {len(games_data)} play-by-play games")
        return games_data
    
    def extract_lineup_positions(self, game_data: Dict) -> Dict[str, int]:
        """
        Extract batting order positions from play-by-play data
        
        Args:
            game_data: Single game play-by-play data
        
        Returns:
            Dictionary mapping batter_id -> lineup_position
        """
        lineup_positions = {}
        sequence_tracker = {}
        
        for play in game_data.get('plays', []):
            batter_id = play.get('batter')
            inning = play.get('inning', 1)
            inning_half = play.get('inning_half', '')
            
            if not batter_id:
                continue
                
            # Track sequence within each team's at-bats
            team_key = f"{inning_half}_{inning}"
            
            if team_key not in sequence_tracker:
                sequence_tracker[team_key] = {}
            
            if batter_id not in sequence_tracker[team_key]:
                # Assign lineup position based on order of appearance
                current_position = len(sequence_tracker[team_key]) + 1
                if current_position <= 9:  # Standard 9-batter lineup
                    sequence_tracker[team_key][batter_id] = current_position
                    lineup_positions[batter_id] = current_position
                    
        return lineup_positions
    
    def analyze_inning_patterns(self, games_data: List[Dict], pitcher_filter: Optional[str] = None) -> Dict:
        """
        Analyze pitcher performance by inning
        
        Args:
            games_data: List of play-by-play game data
            pitcher_filter: Optional pitcher name to filter analysis
        
        Returns:
            Dictionary of inning-based analysis results
        """
        inning_analysis = defaultdict(lambda: {
            'appearances': 0,
            'outcomes': defaultdict(int),
            'pitch_types': defaultdict(int),
            'pitch_counts': [],
            'velocities': []
        })
        
        for game_data in games_data:
            for play in game_data.get('plays', []):
                pitcher_id = play.get('pitcher')
                inning = play.get('inning')
                
                if not pitcher_id or not inning:
                    continue
                
                # Resolve pitcher name
                pitcher_name = self.player_mapper.resolve_player_id(
                    pitcher_id, 
                    game_data['metadata'].get('home_team')
                )
                
                if pitcher_filter and pitcher_name and pitcher_filter.lower() not in pitcher_name.lower():
                    continue
                
                pitcher_key = pitcher_name or pitcher_id
                
                # Track inning-specific performance
                inning_key = f"inning_{inning}"
                
                # Ensure the pitcher and inning key structure exists
                if pitcher_key not in inning_analysis:
                    inning_analysis[pitcher_key] = {}
                if inning_key not in inning_analysis[pitcher_key]:
                    inning_analysis[pitcher_key][inning_key] = {
                        'appearances': 0,
                        'outcomes': defaultdict(int),
                        'pitch_types': defaultdict(int),
                        'velocities': [],
                        'pitch_counts': []
                    }
                
                inning_analysis[pitcher_key][inning_key]['appearances'] += 1
                
                # Track outcome
                result = play.get('play_result', 'Unknown')
                inning_analysis[pitcher_key][inning_key]['outcomes'][result] += 1
                
                # Track pitch data
                for pitch in play.get('pitch_sequence', []):
                    pitch_type = pitch.get('pitch_type')
                    velocity = pitch.get('velocity')
                    
                    if pitch_type:
                        inning_analysis[pitcher_key][inning_key]['pitch_types'][pitch_type] += 1
                    if velocity:
                        inning_analysis[pitcher_key][inning_key]['velocities'].append(velocity)
                
                # Track pitch count context
                total_pitches = len(play.get('pitch_sequence', []))
                inning_analysis[pitcher_key][inning_key]['pitch_counts'].append(total_pitches)
        
        return dict(inning_analysis)
    
    def analyze_lineup_vulnerabilities(self, games_data: List[Dict], pitcher_filter: Optional[str] = None) -> Dict:
        """
        Analyze pitcher vulnerability to specific lineup positions
        
        Args:
            games_data: List of play-by-play game data  
            pitcher_filter: Optional pitcher name to filter analysis
        
        Returns:
            Dictionary of lineup position vulnerability analysis
        """
        lineup_analysis = defaultdict(lambda: defaultdict(lambda: {
            'at_bats': 0,
            'outcomes': defaultdict(int),
            'pitch_types_faced': defaultdict(int),
            'avg_velocity': [],
            'leverage_situations': 0
        }))
        
        for game_data in games_data:
            # First, determine lineup positions
            lineup_positions = self.extract_lineup_positions(game_data)
            
            for play in game_data.get('plays', []):
                pitcher_id = play.get('pitcher')
                batter_id = play.get('batter')
                
                if not pitcher_id or not batter_id:
                    continue
                
                # Resolve pitcher name
                pitcher_name = self.player_mapper.resolve_player_id(
                    pitcher_id,
                    game_data['metadata'].get('home_team')
                )
                
                if pitcher_filter and pitcher_name and pitcher_filter.lower() not in pitcher_name.lower():
                    continue
                
                pitcher_key = pitcher_name or pitcher_id
                lineup_position = lineup_positions.get(batter_id, 0)
                
                if lineup_position == 0:
                    continue  # Skip if we can't determine lineup position
                
                position_key = f"position_{lineup_position}"
                
                # Ensure the pitcher and position key structure exists
                if pitcher_key not in lineup_analysis:
                    lineup_analysis[pitcher_key] = {}
                if position_key not in lineup_analysis[pitcher_key]:
                    lineup_analysis[pitcher_key][position_key] = {
                        'at_bats': 0,
                        'outcomes': defaultdict(int),
                        'pitch_types_faced': defaultdict(int),
                        'avg_velocity': [],
                        'leverage_situations': 0
                    }
                
                # Track at-bat
                lineup_analysis[pitcher_key][position_key]['at_bats'] += 1
                
                # Track outcome
                result = play.get('play_result', 'Unknown')
                lineup_analysis[pitcher_key][position_key]['outcomes'][result] += 1
                
                # Calculate leverage (simplified - based on inning and game situation)
                inning = play.get('inning', 1)
                if inning >= 7:  # Late inning = higher leverage
                    lineup_analysis[pitcher_key][position_key]['leverage_situations'] += 1
                
                # Track pitch data
                velocities = []
                for pitch in play.get('pitch_sequence', []):
                    pitch_type = pitch.get('pitch_type')
                    velocity = pitch.get('velocity')
                    
                    if pitch_type:
                        lineup_analysis[pitcher_key][position_key]['pitch_types_faced'][pitch_type] += 1
                    if velocity:
                        velocities.append(velocity)
                
                if velocities:
                    lineup_analysis[pitcher_key][position_key]['avg_velocity'].extend(velocities)
        
        return dict(lineup_analysis)
    
    def analyze_pitch_patterns(self, games_data: List[Dict], pitcher_filter: Optional[str] = None) -> Dict:
        """
        Analyze pitch sequence patterns and predictability
        
        Args:
            games_data: List of play-by-play game data
            pitcher_filter: Optional pitcher name to filter analysis
        
        Returns:
            Dictionary of pitch pattern analysis results
        """
        pattern_analysis = defaultdict(lambda: {
            'count_patterns': defaultdict(lambda: defaultdict(int)),
            'sequence_patterns': defaultdict(int),
            'handedness_patterns': defaultdict(lambda: defaultdict(int)),
            'predictability_score': 0.0,
            'total_sequences': 0
        })
        
        for game_data in games_data:
            for play in game_data.get('plays', []):
                pitcher_id = play.get('pitcher')
                
                if not pitcher_id:
                    continue
                
                # Resolve pitcher name
                pitcher_name = self.player_mapper.resolve_player_id(
                    pitcher_id,
                    game_data['metadata'].get('home_team')
                )
                
                if pitcher_filter and pitcher_name and pitcher_filter.lower() not in pitcher_name.lower():
                    continue
                
                pitcher_key = pitcher_name or pitcher_id
                pitch_sequence = play.get('pitch_sequence', [])
                
                if len(pitch_sequence) < 2:
                    continue  # Need at least 2 pitches for pattern analysis
                
                pattern_analysis[pitcher_key]['total_sequences'] += 1
                
                # Analyze count-based patterns
                for pitch in pitch_sequence:
                    balls = pitch.get('balls', 0)
                    strikes = pitch.get('strikes', 0)
                    pitch_type = pitch.get('pitch_type')
                    
                    count_key = f"{balls}-{strikes}"
                    if pitch_type:
                        pattern_analysis[pitcher_key]['count_patterns'][count_key][pitch_type] += 1
                
                # Analyze sequence patterns (up to 3-pitch sequences)
                pitch_types = [p.get('pitch_type') for p in pitch_sequence if p.get('pitch_type')]
                
                for i in range(len(pitch_types) - 1):
                    # Two-pitch sequences
                    sequence = f"{pitch_types[i]} -> {pitch_types[i+1]}"
                    pattern_analysis[pitcher_key]['sequence_patterns'][sequence] += 1
                    
                    # Three-pitch sequences
                    if i < len(pitch_types) - 2:
                        sequence = f"{pitch_types[i]} -> {pitch_types[i+1]} -> {pitch_types[i+2]}"
                        pattern_analysis[pitcher_key]['sequence_patterns'][sequence] += 1
        
        # Calculate predictability scores
        for pitcher_key in pattern_analysis:
            data = pattern_analysis[pitcher_key]
            
            # Calculate predictability based on pattern frequency
            total_patterns = sum(data['sequence_patterns'].values())
            if total_patterns > 0:
                # Higher frequency of repeated patterns = more predictable
                pattern_frequencies = list(data['sequence_patterns'].values())
                max_frequency = max(pattern_frequencies) if pattern_frequencies else 0
                predictability = (max_frequency / total_patterns) * 100
                pattern_analysis[pitcher_key]['predictability_score'] = round(predictability, 2)
        
        return dict(pattern_analysis)

class VulnerabilityCalculator:
    """Calculates composite vulnerability scores using advanced metrics"""
    
    def __init__(self, base_data_path: str):
        self.base_data_path = Path(base_data_path)
        self.stats_path = self.base_data_path / "stats"
        self.logger = logging.getLogger(__name__)
        self.pitcher_stats = {}
        self.batter_stats = {}
        
    def load_advanced_stats(self):
        """Load advanced pitcher and batter statistics"""
        try:
            # Load custom pitcher stats (300+ metrics)
            pitcher_stats_file = self.stats_path / "custom_pitcher_2025.csv"
            if pitcher_stats_file.exists():
                pitcher_df = pd.read_csv(pitcher_stats_file)
                self.pitcher_stats = pitcher_df.to_dict('records')
                self.logger.info(f"Loaded {len(self.pitcher_stats)} pitcher stat records")
            
            # Load custom batter stats (150+ metrics)
            batter_stats_file = self.stats_path / "custom_batter_2025.csv"
            if batter_stats_file.exists():
                batter_df = pd.read_csv(batter_stats_file)
                self.batter_stats = batter_df.to_dict('records')
                self.logger.info(f"Loaded {len(self.batter_stats)} batter stat records")
                
        except Exception as e:
            self.logger.error(f"Error loading advanced stats: {e}")
    
    def calculate_lineup_vulnerability_score(self, lineup_analysis: Dict, pitcher_name: str) -> Dict:
        """
        Calculate vulnerability scores for each lineup position
        
        Args:
            lineup_analysis: Results from lineup vulnerability analysis
            pitcher_name: Pitcher to analyze
        
        Returns:
            Dictionary with vulnerability scores by position
        """
        if pitcher_name not in lineup_analysis:
            return {}
        
        pitcher_data = lineup_analysis[pitcher_name]
        vulnerability_scores = {}
        
        for position, stats in pitcher_data.items():
            if not position.startswith('position_'):
                continue
                
            at_bats = stats.get('at_bats', 0)
            if at_bats < 3:  # Need minimum sample size
                continue
            
            outcomes = stats.get('outcomes', {})
            
            # Calculate negative outcome rate (HR, hits, walks)
            negative_outcomes = (
                outcomes.get('Home Run', 0) +
                outcomes.get('Single', 0) +
                outcomes.get('Double', 0) +
                outcomes.get('Triple', 0) +
                outcomes.get('Walk', 0)
            )
            
            vulnerability_rate = negative_outcomes / at_bats if at_bats > 0 else 0
            
            # Weight by leverage situations
            leverage_weight = 1.0 + (stats.get('leverage_situations', 0) / at_bats * 0.5)
            
            # Calculate average velocity (fatigue indicator)
            velocities = stats.get('avg_velocity', [])
            avg_velocity = np.mean(velocities) if velocities else 0
            
            # Composite vulnerability score (0-100)
            base_score = vulnerability_rate * 100
            leverage_adjustment = base_score * leverage_weight
            
            # Velocity penalty (lower velocity = higher vulnerability)
            velocity_penalty = max(0, (95 - avg_velocity) * 2) if avg_velocity > 0 else 0
            
            final_score = min(100, leverage_adjustment + velocity_penalty)
            
            vulnerability_scores[position] = {
                'vulnerability_score': round(final_score, 2),
                'sample_size': at_bats,
                'vulnerability_rate': round(vulnerability_rate, 3),
                'avg_velocity': round(avg_velocity, 1) if avg_velocity > 0 else None,
                'leverage_situations': stats.get('leverage_situations', 0),
                'confidence': self._calculate_confidence(at_bats)
            }
        
        return vulnerability_scores
    
    def calculate_inning_vulnerability_score(self, inning_analysis: Dict, pitcher_name: str) -> Dict:
        """
        Calculate vulnerability scores for each inning
        
        Args:
            inning_analysis: Results from inning pattern analysis
            pitcher_name: Pitcher to analyze
        
        Returns:
            Dictionary with vulnerability scores by inning
        """
        if pitcher_name not in inning_analysis:
            return {}
        
        pitcher_data = inning_analysis[pitcher_name]
        vulnerability_scores = {}
        
        for inning_key, stats in pitcher_data.items():
            if not inning_key.startswith('inning_'):
                continue
            
            appearances = stats.get('appearances', 0)
            if appearances < 2:  # Need minimum sample size
                continue
            
            outcomes = stats.get('outcomes', {})
            
            # Calculate negative outcome rate
            total_outcomes = sum(outcomes.values())
            if total_outcomes == 0:
                continue
            
            negative_outcomes = (
                outcomes.get('Home Run', 0) +
                outcomes.get('Single', 0) +
                outcomes.get('Double', 0) +
                outcomes.get('Triple', 0) +
                outcomes.get('Walk', 0)
            )
            
            vulnerability_rate = negative_outcomes / total_outcomes
            
            # Calculate velocity decline (fatigue indicator)
            velocities = stats.get('velocities', [])
            avg_velocity = np.mean(velocities) if velocities else 0
            
            # Calculate pitch count stress
            pitch_counts = stats.get('pitch_counts', [])
            avg_pitch_count = np.mean(pitch_counts) if pitch_counts else 0
            
            # Composite score
            base_score = vulnerability_rate * 100
            
            # Velocity penalty
            velocity_penalty = max(0, (95 - avg_velocity) * 1.5) if avg_velocity > 0 else 0
            
            # Pitch count penalty (higher counts = more stress)
            pitch_count_penalty = max(0, (avg_pitch_count - 4) * 5) if avg_pitch_count > 0 else 0
            
            final_score = min(100, base_score + velocity_penalty + pitch_count_penalty)
            
            inning_num = inning_key.split('_')[1]
            vulnerability_scores[f"inning_{inning_num}"] = {
                'vulnerability_score': round(final_score, 2),
                'sample_size': appearances,
                'vulnerability_rate': round(vulnerability_rate, 3),
                'avg_velocity': round(avg_velocity, 1) if avg_velocity > 0 else None,
                'avg_pitch_count': round(avg_pitch_count, 1) if avg_pitch_count > 0 else None,
                'confidence': self._calculate_confidence(appearances)
            }
        
        return vulnerability_scores
    
    def _calculate_confidence(self, sample_size: int) -> float:
        """
        Calculate confidence score based on sample size
        
        Args:
            sample_size: Number of observations
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if sample_size >= 20:
            return 1.0
        elif sample_size >= 10:
            return 0.8
        elif sample_size >= 5:
            return 0.6
        elif sample_size >= 3:
            return 0.4
        else:
            return 0.2

class WeakspotAnalyzer:
    """Main weakspot analysis orchestrator"""
    
    def __init__(self, base_data_path: str):
        self.base_data_path = base_data_path
        self.processor = PlayByPlayProcessor(base_data_path)
        self.calculator = VulnerabilityCalculator(base_data_path)
        self.logger = logging.getLogger(__name__)
        
        # Load required data 
        # Note: PitcherNameMapper loads data automatically during initialization
        self.calculator.load_advanced_stats()
    
    def analyze_pitcher_weakspots(self, pitcher_name: str, date_range: Optional[Tuple[str, str]] = None) -> Dict:
        """
        Comprehensive pitcher vulnerability analysis
        
        Args:
            pitcher_name: Name of pitcher to analyze
            date_range: Optional date range for analysis
        
        Returns:
            Complete weakspot analysis report
        """
        self.logger.info(f"Starting weakspot analysis for {pitcher_name}")
        
        # Load play-by-play data
        games_data = self.processor.load_playbyplay_files(date_range)
        
        if not games_data:
            return {"error": "No play-by-play data available"}
        
        # Run all analysis types
        lineup_analysis = self.processor.analyze_lineup_vulnerabilities(games_data, pitcher_name)
        inning_analysis = self.processor.analyze_inning_patterns(games_data, pitcher_name)
        pattern_analysis = self.processor.analyze_pitch_patterns(games_data, pitcher_name)
        
        # Calculate vulnerability scores
        lineup_scores = self.calculator.calculate_lineup_vulnerability_score(lineup_analysis, pitcher_name)
        inning_scores = self.calculator.calculate_inning_vulnerability_score(inning_analysis, pitcher_name)
        
        # Compile comprehensive report
        report = {
            "pitcher_name": pitcher_name,
            "analysis_date": datetime.now().isoformat(),
            "analysis_period": date_range or "All available data",
            "data_summary": {
                "games_analyzed": len(games_data),
                "lineup_positions_analyzed": len(lineup_scores),
                "innings_analyzed": len(inning_scores)
            },
            "lineup_vulnerabilities": lineup_scores,
            "inning_patterns": inning_scores,
            "pitch_patterns": pattern_analysis.get(pitcher_name, {}),
            "overall_confidence": self._calculate_overall_confidence(lineup_scores, inning_scores)
        }
        
        return report
    
    def generate_filterable_rankings(self, analysis_type: str, date_range: Optional[Tuple[str, str]] = None) -> Dict:
        """
        Generate rankings for specific analysis type across all pitchers
        
        Args:
            analysis_type: Type of analysis ('lineup', 'inning', 'patterns', 'overall')
            date_range: Optional date range for analysis
        
        Returns:
            Rankings data for the specified analysis type
        """
        self.logger.info(f"Generating {analysis_type} rankings")
        
        # Load play-by-play data
        games_data = self.processor.load_playbyplay_files(date_range)
        
        if not games_data:
            return {"error": "No play-by-play data available"}
        
        rankings = {
            "analysis_type": analysis_type,
            "analysis_date": datetime.now().isoformat(),
            "analysis_period": date_range or "All available data",
            "rankings": []
        }
        
        if analysis_type == "lineup":
            # Analyze all pitchers for lineup vulnerabilities
            lineup_analysis = self.processor.analyze_lineup_vulnerabilities(games_data)
            
            for pitcher_name in lineup_analysis:
                lineup_scores = self.calculator.calculate_lineup_vulnerability_score(lineup_analysis, pitcher_name)
                if lineup_scores:
                    # Find highest vulnerability position
                    max_vulnerability = max(
                        (pos_data['vulnerability_score'] for pos_data in lineup_scores.values()),
                        default=0
                    )
                    
                    rankings["rankings"].append({
                        "pitcher": pitcher_name,
                        "max_vulnerability_score": max_vulnerability,
                        "position_breakdowns": lineup_scores,
                        "total_sample_size": sum(pos_data.get('sample_size', 0) for pos_data in lineup_scores.values())
                    })
        
        elif analysis_type == "inning":
            # Analyze all pitchers for inning patterns
            inning_analysis = self.processor.analyze_inning_patterns(games_data)
            
            for pitcher_name in inning_analysis:
                inning_scores = self.calculator.calculate_inning_vulnerability_score(inning_analysis, pitcher_name)
                if inning_scores:
                    # Find highest vulnerability inning
                    max_vulnerability = max(
                        (inning_data['vulnerability_score'] for inning_data in inning_scores.values()),
                        default=0
                    )
                    
                    rankings["rankings"].append({
                        "pitcher": pitcher_name,
                        "max_vulnerability_score": max_vulnerability,
                        "inning_breakdowns": inning_scores,
                        "total_sample_size": sum(inning_data.get('sample_size', 0) for inning_data in inning_scores.values())
                    })
        
        elif analysis_type == "patterns":
            # Analyze all pitchers for pitch patterns
            pattern_analysis = self.processor.analyze_pitch_patterns(games_data)
            
            for pitcher_name in pattern_analysis:
                pitcher_patterns = pattern_analysis[pitcher_name]
                predictability = pitcher_patterns.get('predictability_score', 0)
                
                rankings["rankings"].append({
                    "pitcher": pitcher_name,
                    "predictability_score": predictability,
                    "total_sequences": pitcher_patterns.get('total_sequences', 0),
                    "pattern_details": pitcher_patterns
                })
        
        # Sort rankings by vulnerability/predictability
        if analysis_type in ["lineup", "inning"]:
            rankings["rankings"].sort(key=lambda x: x.get('max_vulnerability_score', 0), reverse=True)
        elif analysis_type == "patterns":
            rankings["rankings"].sort(key=lambda x: x.get('predictability_score', 0), reverse=True)
        
        return rankings
    
    def _calculate_overall_confidence(self, lineup_scores: Dict, inning_scores: Dict) -> float:
        """Calculate overall confidence in the analysis"""
        total_samples = 0
        weighted_confidences = 0
        
        for pos_data in lineup_scores.values():
            sample_size = pos_data.get('sample_size', 0)
            confidence = pos_data.get('confidence', 0)
            total_samples += sample_size
            weighted_confidences += sample_size * confidence
        
        for inning_data in inning_scores.values():
            sample_size = inning_data.get('sample_size', 0)
            confidence = inning_data.get('confidence', 0)
            total_samples += sample_size
            weighted_confidences += sample_size * confidence
        
        if total_samples == 0:
            return 0.0
        
        return round(weighted_confidences / total_samples, 3)

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('weakspot_analysis.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Weakspot Analysis Engine')
    parser.add_argument('--pitcher', help='Specific pitcher to analyze')
    parser.add_argument('--analysis-type', choices=['lineup', 'inning', 'patterns', 'overall'], 
                       help='Type of analysis to perform')
    parser.add_argument('--start-date', help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for analysis (YYYY-MM-DD)')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--data-path', default='../BaseballData/data', 
                       help='Path to baseball data directory')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        analyzer = WeakspotAnalyzer(args.data_path)
        
        date_range = None
        if args.start_date and args.end_date:
            date_range = (args.start_date, args.end_date)
        
        if args.pitcher:
            # Analyze specific pitcher
            result = analyzer.analyze_pitcher_weakspots(args.pitcher, date_range)
        elif args.analysis_type:
            # Generate rankings for analysis type
            result = analyzer.generate_filterable_rankings(args.analysis_type, date_range)
        else:
            logger.error("Must specify either --pitcher or --analysis-type")
            return
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()