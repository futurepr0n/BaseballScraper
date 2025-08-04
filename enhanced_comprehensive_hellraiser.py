#!/usr/bin/env python3
"""
Enhanced Comprehensive Hellraiser Generator - Version 6.0
True Integration with All Available Baseball Data Sources

This system properly integrates:
1. ALL CSV files with correct field mappings
2. BaseballAPI for sophisticated 6-component analysis  
3. Rolling trend analysis from daily JSON files
4. Percentile-based scoring (no more flat ratings)
5. Comprehensive name matching and data validation
6. Multi-source data integration with quality scoring

Expected runtime: 2-3 minutes for thorough analysis
Expected results: Varied scores (25-95%) with detailed reasoning
"""

import json
import csv
import os
import sys
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics
import re

# Team normalization utilities for CHW/CWS and other team abbreviation mismatches
TEAM_MAPPINGS = {
    # Forward mappings (less common → standard)
    'ATH': 'OAK',  # Athletics
    'CWS': 'CHW',  # White Sox  
    'LAD': 'LA',   # Dodgers
    'NYM': 'NYN',  # Mets
    'NYY': 'NY',   # Yankees
    'SD': 'SDN',   # Padres
    'SF': 'SFN',   # Giants
    'TB': 'TBR',   # Rays
    'WSH': 'WAS',  # Nationals
    
    # Reverse mappings (standard → less common)
    'OAK': 'ATH',
    'CHW': 'CWS', 
    'LA': 'LAD',
    'NYN': 'NYM',
    'NY': 'NYY',
    'SDN': 'SD',
    'SFN': 'SF',
    'TBR': 'TB',
    'WAS': 'WSH'
}

def teams_match(team1: str, team2: str) -> bool:
    """Check if two team abbreviations refer to the same team"""
    if not team1 or not team2:
        return False
    
    team1_upper = team1.upper()
    team2_upper = team2.upper()
    
    # Direct match
    if team1_upper == team2_upper:
        return True
    
    # Check if they map to each other
    return (TEAM_MAPPINGS.get(team1_upper) == team2_upper or 
            TEAM_MAPPINGS.get(team2_upper) == team1_upper)

class EnhancedComprehensiveHellraiser:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            script_dir = Path(__file__).parent.absolute()
            self.base_dir = script_dir.parent / "BaseballTracker"
        else:
            self.base_dir = Path(base_dir)
        
        self.output_dir = self.base_dir / "public" / "data" / "hellraiser"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.build_output_dir = self.base_dir / "build" / "data" / "hellraiser"
        self.build_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats_dir = self.base_dir / "public" / "data" / "stats"
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🔥 Enhanced Comprehensive Hellraiser Generator - {self.today}")
        print(f"📊 Processing comprehensive baseball analytics...")
        
        # Data containers
        self.custom_batter_stats = {}
        self.custom_pitcher_stats = {}
        self.exit_velocity_data = {}
        self.pitcher_exit_velocity = {}
        self.handedness_splits = {}
        self.swing_path_data = {}
        self.pitch_arsenal_hitter = {}
        self.pitch_arsenal_pitcher = {}
        
        # Percentile benchmarks for scoring
        self.batter_percentiles = {}
        self.pitcher_percentiles = {}
        
        # BaseballAPI configuration
        self.api_base_url = "http://localhost:8000"
        self.api_available = self._check_api_availability()
        
        # Load all data sources with comprehensive processing
        self._load_all_comprehensive_data()
    
    def _check_api_availability(self) -> bool:
        """Check if BaseballAPI is available"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ BaseballAPI connected - enabling advanced analysis")
                return True
        except:
            print("⚠️ BaseballAPI not available - using CSV-only analysis")
        return False
    
    def _load_all_comprehensive_data(self):
        """Load all data sources with proper processing"""
        print("\n📋 Loading comprehensive baseball data sources...")
        
        start_time = time.time()
        
        # 1. Load custom batter stats (200+ metrics)
        self._load_custom_batter_stats_enhanced()
        
        # 2. Load custom pitcher stats (300+ metrics)  
        self._load_custom_pitcher_stats_enhanced()
        
        # 3. Load detailed exit velocity data
        self._load_exit_velocity_data_enhanced()
        
        # 4. Load pitcher exit velocity data
        self._load_pitcher_exit_velocity_data()
        
        # 5. Load handedness splits (all combinations)
        self._load_comprehensive_handedness_splits()
        
        # 6. Load swing path optimization data
        self._load_swing_path_data_enhanced()
        
        # 7. Load pitch arsenal statistics
        self._load_pitch_arsenal_comprehensive()
        
        # 8. Build percentile benchmarks for dynamic scoring
        self._build_percentile_benchmarks()
        
        load_time = time.time() - start_time
        print(f"✅ Data loading complete: {load_time:.1f} seconds")
        print(f"📊 Loaded: {len(self.custom_batter_stats)} batters, {len(self.custom_pitcher_stats)} pitchers")
    
    def _load_custom_batter_stats_enhanced(self):
        """Load custom batter stats with enhanced processing"""
        batter_file = self.stats_dir / "custom_batter_2025.csv"
        
        try:
            print("📊 Loading custom batter statistics (200+ metrics)...")
            df = pd.read_csv(batter_file, encoding='utf-8-sig')
            
            for _, row in df.iterrows():
                name_str = str(row['last_name, first_name']).strip()
                full_name = self._parse_name_format(name_str)
                
                if not full_name:
                    continue
                
                # Store comprehensive statistics with proper data types
                self.custom_batter_stats[full_name] = {
                    # Basic stats
                    'ab': self._safe_float(row.get('ab', 0)),
                    'pa': self._safe_float(row.get('pa', 0)),
                    'hits': self._safe_float(row.get('hit', 0)),
                    'home_runs': self._safe_float(row.get('home_run', 0)),
                    'doubles': self._safe_float(row.get('double', 0)),
                    'triples': self._safe_float(row.get('triple', 0)),
                    'rbi': self._safe_float(row.get('b_rbi', 0)),
                    'runs': self._safe_float(row.get('r_total_stolen_base', 0)),
                    'strikeouts': self._safe_float(row.get('strikeout', 0)),
                    'walks': self._safe_float(row.get('walk', 0)),
                    
                    # Rate stats
                    'k_percent': self._safe_float(row.get('k_percent', 0)),
                    'bb_percent': self._safe_float(row.get('bb_percent', 0)),
                    'batting_avg': self._safe_float(row.get('batting_avg', 0)),
                    'slg_percent': self._safe_float(row.get('slg_percent', 0)),
                    'on_base_percent': self._safe_float(row.get('on_base_percent', 0)),
                    'ops': self._safe_float(row.get('on_base_plus_slg', 0)),
                    'iso': self._safe_float(row.get('isolated_power', 0)),
                    'babip': self._safe_float(row.get('babip', 0)),
                    
                    # Statcast expected stats
                    'xba': self._safe_float(row.get('xba', 0)),
                    'xslg': self._safe_float(row.get('xslg', 0)),
                    'woba': self._safe_float(row.get('woba', 0)),
                    'xwoba': self._safe_float(row.get('xwoba', 0)),
                    'xobp': self._safe_float(row.get('xobp', 0)),
                    'xiso': self._safe_float(row.get('xiso', 0)),
                    
                    # Contact quality metrics
                    'exit_velocity_avg': self._safe_float(row.get('exit_velocity_avg', 0)),
                    'launch_angle_avg': self._safe_float(row.get('launch_angle_avg', 0)),
                    'sweet_spot_percent': self._safe_float(row.get('sweet_spot_percent', 0)),
                    'barrel': self._safe_float(row.get('barrel', 0)),
                    'barrel_batted_rate': self._safe_float(row.get('barrel_batted_rate', 0)),
                    'hard_hit_percent': self._safe_float(row.get('hard_hit_percent', 0)),
                    'avg_best_speed': self._safe_float(row.get('avg_best_speed', 0)),
                    
                    # Swing metrics
                    'avg_swing_speed': self._safe_float(row.get('avg_swing_speed', 0)),
                    'fast_swing_rate': self._safe_float(row.get('fast_swing_rate', 0)),
                    'attack_angle': self._safe_float(row.get('attack_angle', 0)),
                    'ideal_angle_rate': self._safe_float(row.get('ideal_angle_rate', 0)),
                    
                    # Plate discipline
                    'z_swing_percent': self._safe_float(row.get('z_swing_percent', 0)),
                    'oz_swing_percent': self._safe_float(row.get('oz_swing_percent', 0)),
                    'swing_percent': self._safe_float(row.get('swing_percent', 0)),
                    'whiff_percent': self._safe_float(row.get('whiff_percent', 0)),
                    'oz_contact_percent': self._safe_float(row.get('oz_contact_percent', 0)),
                    
                    # Batted ball profile
                    'pull_percent': self._safe_float(row.get('pull_percent', 0)),
                    'straightaway_percent': self._safe_float(row.get('straightaway_percent', 0)),
                    'opposite_percent': self._safe_float(row.get('opposite_percent', 0)),
                    'groundballs_percent': self._safe_float(row.get('groundballs_percent', 0)),
                    'flyballs_percent': self._safe_float(row.get('flyballs_percent', 0)),
                    'linedrives_percent': self._safe_float(row.get('linedrives_percent', 0)),
                    
                    # Speed metrics
                    'sprint_speed': self._safe_float(row.get('sprint_speed', 0)),
                    'hp_to_1b': self._safe_float(row.get('hp_to_1b', 0))
                }
            
            print(f"✅ Custom batter stats loaded: {len(self.custom_batter_stats)} players")
            
        except Exception as e:
            print(f"❌ Error loading custom batter stats: {e}")
    
    def _load_exit_velocity_data_enhanced(self):
        """Load exit velocity data with correct field mappings"""
        ev_file = self.stats_dir / "hitter_exit_velocity_2025.csv"
        
        try:
            print("📊 Loading hitter exit velocity data...")
            df = pd.read_csv(ev_file, encoding='utf-8-sig')
            
            for _, row in df.iterrows():
                name_str = str(row['last_name, first_name']).strip()
                full_name = self._parse_name_format(name_str)
                
                if not full_name:
                    continue
                
                # CORRECTED field mappings based on actual CSV structure
                self.exit_velocity_data[full_name] = {
                    'avg_hit_speed': self._safe_float(row.get('avg_hit_speed', 0)),
                    'max_hit_speed': self._safe_float(row.get('max_hit_speed', 0)),
                    'brl_percent': self._safe_float(row.get('brl_percent', 0)),
                    'barrels': self._safe_int(row.get('barrels', 0)),
                    'ev95percent': self._safe_float(row.get('ev95percent', 0)),
                    'avg_distance': self._safe_float(row.get('avg_distance', 0)),
                    'avg_hr_distance': self._safe_float(row.get('avg_hr_distance', 0)),
                    'anglesweetspotpercent': self._safe_float(row.get('anglesweetspotpercent', 0))
                }
            
            print(f"✅ Exit velocity data loaded: {len(self.exit_velocity_data)} players")
            
        except Exception as e:
            print(f"❌ Error loading exit velocity data: {e}")
    
    def _load_pitcher_exit_velocity_data(self):
        """Load pitcher exit velocity allowed data"""
        pitcher_ev_file = self.stats_dir / "pitcher_exit_velocity_2025.csv"
        
        try:
            print("📊 Loading pitcher exit velocity data...")
            df = pd.read_csv(pitcher_ev_file, encoding='utf-8-sig')
            
            for _, row in df.iterrows():
                name_str = str(row['last_name, first_name']).strip()
                full_name = self._parse_name_format(name_str)
                
                if not full_name:
                    continue
                
                self.pitcher_exit_velocity[full_name] = {
                    'avg_hit_speed': self._safe_float(row.get('avg_hit_speed', 0)),
                    'max_hit_speed': self._safe_float(row.get('max_hit_speed', 0)),
                    'brl_percent': self._safe_float(row.get('brl_percent', 0)),
                    'barrels': self._safe_int(row.get('barrels', 0)),
                    'ev95percent': self._safe_float(row.get('ev95percent', 0)),
                    'hard_hit_percent': self._safe_float(row.get('hard_hit_percent', 0))
                }
            
            print(f"✅ Pitcher exit velocity data loaded: {len(self.pitcher_exit_velocity)} pitchers")
            
        except Exception as e:
            print(f"❌ Error loading pitcher exit velocity data: {e}")
    
    def _load_custom_pitcher_stats_enhanced(self):
        """Load custom pitcher stats with enhanced processing"""
        pitcher_file = self.stats_dir / "custom_pitcher_2025.csv"
        
        try:
            print("📊 Loading custom pitcher statistics (300+ metrics)...")
            df = pd.read_csv(pitcher_file, encoding='utf-8-sig')
            
            for _, row in df.iterrows():
                name_str = str(row['last_name, first_name']).strip()
                full_name = self._parse_name_format(name_str)
                
                if not full_name:
                    continue
                
                self.custom_pitcher_stats[full_name] = {
                    # Basic pitching stats
                    'era': self._safe_float(row.get('p_era', 0)),
                    'whip': self._safe_float(row.get('p_whip', 0)),
                    'k_percent': self._safe_float(row.get('k_percent', 0)),
                    'bb_percent': self._safe_float(row.get('bb_percent', 0)),
                    'hr_per_9': self._safe_float(row.get('home_run_per_9', 0)),
                    'games': self._safe_float(row.get('p_game', 1)),
                    'innings': self._safe_float(row.get('p_inning', 0)),
                    'strikeouts': self._safe_float(row.get('strikeout', 0)),
                    'walks': self._safe_float(row.get('walk', 0)),
                    'home_runs_allowed': self._safe_float(row.get('home_run', 0)),
                    
                    # Contact quality allowed
                    'exit_velocity_avg': self._safe_float(row.get('exit_velocity_avg', 0)),
                    'launch_angle_avg': self._safe_float(row.get('launch_angle_avg', 0)),
                    'sweet_spot_percent': self._safe_float(row.get('sweet_spot_percent', 0)),
                    'barrel_batted_rate': self._safe_float(row.get('barrel_batted_rate', 0)),
                    'hard_hit_percent': self._safe_float(row.get('hard_hit_percent', 0)),
                    
                    # Pitch arsenal
                    'fastball_avg_speed': self._safe_float(row.get('fastball_avg_speed', 0)),
                    'fastball_avg_spin': self._safe_float(row.get('fastball_avg_spin', 0)),
                    'slider_avg_speed': self._safe_float(row.get('slider_avg_speed', 0)),
                    'changeup_avg_speed': self._safe_float(row.get('changeup_avg_speed', 0)),
                    'curveball_avg_speed': self._safe_float(row.get('curveball_avg_speed', 0)),
                    
                    # Plate discipline against
                    'whiff_percent': self._safe_float(row.get('whiff_percent', 0)),
                    'z_swing_percent': self._safe_float(row.get('z_swing_percent', 0)),
                    'oz_swing_percent': self._safe_float(row.get('oz_swing_percent', 0)),
                    'swing_percent': self._safe_float(row.get('swing_percent', 0)),
                    'oz_contact_percent': self._safe_float(row.get('oz_contact_percent', 0)),
                    
                    # Batted ball profile allowed
                    'groundballs_percent': self._safe_float(row.get('groundballs_percent', 0)),
                    'flyballs_percent': self._safe_float(row.get('flyballs_percent', 0)),
                    'linedrives_percent': self._safe_float(row.get('linedrives_percent', 0)),
                    'pull_percent': self._safe_float(row.get('pull_percent', 0)),
                    'straightaway_percent': self._safe_float(row.get('straightaway_percent', 0)),
                    'opposite_percent': self._safe_float(row.get('opposite_percent', 0))
                }
            
            print(f"✅ Custom pitcher stats loaded: {len(self.custom_pitcher_stats)} pitchers")
            
        except Exception as e:
            print(f"❌ Error loading custom pitcher stats: {e}")
    
    def _load_comprehensive_handedness_splits(self):
        """Load all handedness combinations"""
        handedness_files = [
            ('batters-batted-ball-bat-left-pitch-hand-left-2025.csv', 'LHP_vs_LHB'),
            ('batters-batted-ball-bat-left-pitch-hand-right-2025.csv', 'RHP_vs_LHB'),
            ('batters-batted-ball-bat-right-pitch-hand-left-2025.csv', 'LHP_vs_RHB'),
            ('batters-batted-ball-bat-right-pitch-hand-right-2025.csv', 'RHP_vs_RHB')
        ]
        
        for filename, key in handedness_files:
            file_path = self.stats_dir / filename
            
            try:
                print(f"📊 Loading handedness splits: {key}")
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                self.handedness_splits[key] = {}
                
                for _, row in df.iterrows():
                    player_name = str(row.get('name', '')).strip().strip('"')
                    full_name = self._parse_name_format(player_name)
                    
                    if not full_name:
                        continue
                    
                    self.handedness_splits[key][full_name] = {
                        'woba': self._safe_float(row.get('woba', 0)),
                        'iso': self._safe_float(row.get('iso', 0)),
                        'babip': self._safe_float(row.get('babip', 0)),
                        'gb_percent': self._safe_float(row.get('gb_percent', 0)),
                        'fb_percent': self._safe_float(row.get('fb_percent', 0)),
                        'ld_percent': self._safe_float(row.get('ld_percent', 0)),
                        'hr_fb_percent': self._safe_float(row.get('hr_fb_percent', 0)),
                        'pull_percent': self._safe_float(row.get('pull_percent', 0)),
                        'cent_percent': self._safe_float(row.get('cent_percent', 0)),
                        'oppo_percent': self._safe_float(row.get('oppo_percent', 0))
                    }
                
                print(f"✅ Handedness splits loaded ({key}): {len(self.handedness_splits[key])} players")
                
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    def _load_swing_path_data_enhanced(self):
        """Load swing path optimization data"""
        swing_files = [
            ('batters-swing-path-RHP.csv', 'vs_RHP'),
            ('batters-swing-path-LHP.csv', 'vs_LHP'), 
            ('batters-swing-path-all.csv', 'overall')
        ]
        
        for filename, key in swing_files:
            file_path = self.stats_dir / filename
            
            try:
                print(f"📊 Loading swing path data: {key}")
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                for _, row in df.iterrows():
                    player_name = str(row.get('name', '')).strip().strip('"')
                    full_name = self._parse_name_format(player_name)
                    
                    if not full_name:
                        continue
                    
                    if full_name not in self.swing_path_data:
                        self.swing_path_data[full_name] = {}
                    
                    self.swing_path_data[full_name][key] = {
                        'side': str(row.get('side', 'R')).strip().strip('"'),
                        'avg_bat_speed': self._safe_float(row.get('avg_bat_speed', 0)),
                        'attack_angle': self._safe_float(row.get('attack_angle', 0)),
                        'ideal_attack_angle_rate': self._safe_float(row.get('ideal_attack_angle_rate', 0)),
                        'swing_tilt': self._safe_float(row.get('swing_tilt', 0)),
                        'attack_direction': self._safe_float(row.get('attack_direction', 0))
                    }
                
                player_count = len([p for p in self.swing_path_data.values() if key in p])
                print(f"✅ Swing path data loaded ({key}): {player_count} players")
                
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    def _load_pitch_arsenal_comprehensive(self):
        """Load pitch arsenal statistics"""
        # Load hitter arsenal stats
        hitter_arsenal_file = self.stats_dir / "hitterpitcharsenalstats_2025.csv"
        
        try:
            print("📊 Loading hitter pitch arsenal stats...")
            df = pd.read_csv(hitter_arsenal_file, encoding='utf-8-sig')
            
            for _, row in df.iterrows():
                name_str = str(row.get('last_name, first_name', '')).strip()
                full_name = self._parse_name_format(name_str)
                pitch_type = str(row.get('pitch_type', '')).strip()
                
                if not full_name or not pitch_type:
                    continue
                
                if full_name not in self.pitch_arsenal_hitter:
                    self.pitch_arsenal_hitter[full_name] = {}
                
                self.pitch_arsenal_hitter[full_name][pitch_type] = {
                    'ba': self._safe_float(row.get('ba', 0)),
                    'slg': self._safe_float(row.get('slg', 0)),
                    'woba': self._safe_float(row.get('woba', 0)),
                    'whiff_percent': self._safe_float(row.get('whiff_percent', 0)),
                    'k_percent': self._safe_float(row.get('k_percent', 0)),
                    'hard_hit_percent': self._safe_float(row.get('hard_hit_percent', 0)),
                    'est_ba': self._safe_float(row.get('est_ba', 0)),
                    'est_slg': self._safe_float(row.get('est_slg', 0)),
                    'est_woba': self._safe_float(row.get('est_woba', 0)),
                    'pitch_usage': self._safe_float(row.get('pitch_usage', 0)),
                    'pitches': self._safe_int(row.get('pitches', 0)),
                    'pa': self._safe_int(row.get('pa', 0)),
                    'run_value_per_100': self._safe_float(row.get('run_value_per_100', 0))
                }
            
            print(f"✅ Hitter arsenal stats loaded: {len(self.pitch_arsenal_hitter)} players")
            
        except Exception as e:
            print(f"❌ Error loading hitter arsenal stats: {e}")
        
        # Load pitcher arsenal stats
        pitcher_arsenal_file = self.stats_dir / "pitcherpitcharsenalstats_2025.csv"
        
        try:
            print("📊 Loading pitcher pitch arsenal stats...")
            df = pd.read_csv(pitcher_arsenal_file, encoding='utf-8-sig')
            
            for _, row in df.iterrows():
                name_str = str(row.get('last_name, first_name', '')).strip()
                full_name = self._parse_name_format(name_str)
                pitch_type = str(row.get('pitch_type', '')).strip()
                
                if not full_name or not pitch_type:
                    continue
                
                if full_name not in self.pitch_arsenal_pitcher:
                    self.pitch_arsenal_pitcher[full_name] = {}
                
                self.pitch_arsenal_pitcher[full_name][pitch_type] = {
                    'ba': self._safe_float(row.get('ba', 0)),
                    'slg': self._safe_float(row.get('slg', 0)),
                    'woba': self._safe_float(row.get('woba', 0)),
                    'whiff_percent': self._safe_float(row.get('whiff_percent', 0)),
                    'k_percent': self._safe_float(row.get('k_percent', 0)),
                    'hard_hit_percent': self._safe_float(row.get('hard_hit_percent', 0)),
                    'est_ba': self._safe_float(row.get('est_ba', 0)),
                    'est_slg': self._safe_float(row.get('est_slg', 0)),
                    'est_woba': self._safe_float(row.get('est_woba', 0)),
                    'pitch_usage': self._safe_float(row.get('pitch_usage', 0)),
                    'pitches': self._safe_int(row.get('pitches', 0)),
                    'pa': self._safe_int(row.get('pa', 0)),
                    'run_value_per_100': self._safe_float(row.get('run_value_per_100', 0))
                }
            
            print(f"✅ Pitcher arsenal stats loaded: {len(self.pitch_arsenal_pitcher)} pitchers")
            
        except Exception as e:
            print(f"❌ Error loading pitcher arsenal stats: {e}")
    
    def _build_percentile_benchmarks(self):
        """Build percentile benchmarks for dynamic scoring"""
        print("📊 Building percentile benchmarks for dynamic scoring...")
        
        # Batter percentiles
        if self.custom_batter_stats:
            batter_df = pd.DataFrame(self.custom_batter_stats).T
            
            batter_metrics = [
                'exit_velocity_avg', 'barrel_batted_rate', 'hard_hit_percent', 
                'iso', 'woba', 'ops', 'home_runs', 'avg_swing_speed'
            ]
            
            self.batter_percentiles = self._calculate_percentiles(batter_df, batter_metrics)
        
        # Pitcher percentiles
        if self.custom_pitcher_stats:
            pitcher_df = pd.DataFrame(self.custom_pitcher_stats).T
            
            pitcher_metrics = [
                'era', 'hr_per_9', 'exit_velocity_avg', 'barrel_batted_rate',
                'hard_hit_percent', 'whip', 'k_percent', 'bb_percent'
            ]
            
            self.pitcher_percentiles = self._calculate_percentiles(pitcher_df, pitcher_metrics)
        
        print(f"✅ Percentile benchmarks built for dynamic scoring")
    
    def _calculate_percentiles(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Dict[str, float]]:
        """Calculate percentile benchmarks"""
        percentiles = {}
        
        for col in columns:
            if col in df.columns:
                # Convert to numeric, handling any string values
                series = pd.to_numeric(df[col], errors='coerce').dropna()
                
                if len(series) > 0:
                    percentiles[col] = {
                        'p10': series.quantile(0.10),
                        'p25': series.quantile(0.25),
                        'p50': series.quantile(0.50),
                        'p75': series.quantile(0.75),
                        'p90': series.quantile(0.90),
                        'p95': series.quantile(0.95)
                    }
        
        return percentiles
    
    def _calculate_percentile_score(self, value: float, percentiles: Dict[str, float], 
                                  reverse: bool = False) -> float:
        """Calculate percentile-based score (25-95 range)"""
        if not percentiles or value == 0:
            return 50.0
        
        # Reverse scoring for "bad" stats like ERA (lower is better)
        if reverse:
            if value <= percentiles['p10']:
                return 95
            elif value <= percentiles['p25']:
                return 80 + ((percentiles['p25'] - value) / (percentiles['p25'] - percentiles['p10'])) * 15
            elif value <= percentiles['p50']:
                return 65 + ((percentiles['p50'] - value) / (percentiles['p50'] - percentiles['p25'])) * 15
            elif value <= percentiles['p75']:
                return 45 + ((percentiles['p75'] - value) / (percentiles['p75'] - percentiles['p50'])) * 20
            elif value <= percentiles['p90']:
                return 30 + ((percentiles['p90'] - value) / (percentiles['p90'] - percentiles['p75'])) * 15
            else:
                return 25
        else:
            # Normal scoring for "good" stats (higher is better)
            if value >= percentiles['p95']:
                return 95
            elif value >= percentiles['p90']:
                return 85 + ((value - percentiles['p90']) / (percentiles['p95'] - percentiles['p90'])) * 10
            elif value >= percentiles['p75']:
                return 70 + ((value - percentiles['p75']) / (percentiles['p90'] - percentiles['p75'])) * 15
            elif value >= percentiles['p50']:
                return 50 + ((value - percentiles['p50']) / (percentiles['p75'] - percentiles['p50'])) * 20
            elif value >= percentiles['p25']:
                return 35 + ((value - percentiles['p25']) / (percentiles['p50'] - percentiles['p25'])) * 15
            else:
                return 25
    
    def _parse_name_format(self, name_str: str) -> str:
        """Parse name from various formats"""
        if not name_str or pd.isna(name_str):
            return ""
        
        name_str = str(name_str).strip()
        
        # Handle "Last, First" format
        if ', ' in name_str:
            parts = name_str.split(', ')
            if len(parts) == 2:
                return f"{parts[1].strip()} {parts[0].strip()}"
        
        return name_str
    
    def _safe_float(self, value, default=0.0):
        """Safely convert value to float"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=0):
        """Safely convert value to int"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return default
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    def _get_baseball_api_analysis(self, player_name: str, pitcher_name: str, team: str) -> Optional[Dict]:
        """Get analysis from BaseballAPI if available"""
        if not self.api_available:
            return None
        
        try:
            # Use BaseballAPI bulk analysis endpoint
            response = requests.post(
                f"{self.api_base_url}/analyze/bulk-predictions",
                json={
                    "predictions": [{
                        "player_name": player_name,
                        "pitcher_name": pitcher_name,
                        "team": team
                    }]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('predictions'):
                    return data['predictions'][0]
        
        except Exception as e:
            print(f"⚠️ API call failed for {player_name}: {e}")
        
        return None
    
    def _analyze_rolling_performance_trends(self, player_name: str, days_back: int = 15) -> Dict[str, Any]:
        """Analyze rolling performance from daily JSON files"""
        print(f"🔍 Analyzing {days_back}-day trends for {player_name}")
        
        recent_games = []
        
        # Load recent game data
        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
            year, month, day = date.split('-')
            month_name = datetime.strptime(month, '%m').strftime('%B').lower()
            
            game_file = self.base_dir / "public" / "data" / year / month_name / f"{month_name}_{day.zfill(2)}_{year}.json"
            
            if game_file.exists():
                try:
                    with open(game_file, 'r') as f:
                        daily_data = json.load(f)
                    
                    # Find player's performance
                    for player in daily_data.get('players', []):
                        if self._names_match(player.get('name', ''), player_name):
                            recent_games.append({
                                'date': date,
                                'hits': self._safe_float(player.get('hits', 0)),
                                'at_bats': self._safe_float(player.get('AB', 0)),
                                'home_runs': self._safe_float(player.get('homeRuns', 0)),
                                'rbi': self._safe_float(player.get('RBI', 0)),
                                'avg': self._safe_float(player.get('AVG', 0))
                            })
                            break
                
                except Exception as e:
                    continue
        
        if not recent_games:
            return {'trend_available': False}
        
        # Calculate rolling trends
        recent_3 = recent_games[:3] if len(recent_games) >= 3 else recent_games
        recent_5 = recent_games[:5] if len(recent_games) >= 5 else recent_games
        recent_7 = recent_games[:7] if len(recent_games) >= 7 else recent_games
        
        # Calculate averages
        avg_3 = statistics.mean([g['avg'] for g in recent_3]) if recent_3 else 0
        avg_5 = statistics.mean([g['avg'] for g in recent_5]) if recent_5 else 0
        avg_7 = statistics.mean([g['avg'] for g in recent_7]) if recent_7 else 0
        season_avg = statistics.mean([g['avg'] for g in recent_games]) if recent_games else 0
        
        # HR trends
        hr_3 = sum(g['home_runs'] for g in recent_3)
        hr_7 = sum(g['home_runs'] for g in recent_7)
        
        # Determine trend direction
        if avg_3 > season_avg * 1.3:
            trend = 'very_hot'
            trend_score = 20
        elif avg_3 > season_avg * 1.15:
            trend = 'hot'
            trend_score = 15
        elif avg_3 < season_avg * 0.7:
            trend = 'very_cold'
            trend_score = -15
        elif avg_3 < season_avg * 0.85:
            trend = 'cold'
            trend_score = -10
        else:
            trend = 'stable'
            trend_score = 0
        
        return {
            'trend_available': True,
            'games_analyzed': len(recent_games),
            'recent_3_avg': avg_3,
            'recent_5_avg': avg_5,
            'recent_7_avg': avg_7,
            'season_avg': season_avg,
            'trend_direction': trend,
            'trend_score': trend_score,
            'hr_last_3': hr_3,
            'hr_last_7': hr_7,
            'is_trending_up': avg_3 > avg_7,
            'momentum': 'positive' if avg_3 > avg_7 else 'negative' if avg_3 < avg_7 else 'stable'
        }
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names match with various formats"""
        if not name1 or not name2:
            return False
        
        # Direct match
        if name1.lower() == name2.lower():
            return True
        
        # Normalize both names
        norm1 = re.sub(r'[^\w\s]', '', name1.lower())
        norm2 = re.sub(r'[^\w\s]', '', name2.lower())
        
        if norm1 == norm2:
            return True
        
        # Enhanced matching for abbreviated names (e.g., "S. Ohtani" vs "Shohei Ohtani")
        if self._check_abbreviated_match(norm1, norm2):
            return True
        
        # Check if one contains the other (for partial matches)
        if norm1 in norm2 or norm2 in norm1:
            # Only if the shorter name is at least 5 characters
            if min(len(norm1), len(norm2)) >= 5:
                return True
        
        return False
    
    def _check_abbreviated_match(self, name1: str, name2: str) -> bool:
        """Check if names match in abbreviated format (Initial. Lastname vs Full Name)"""
        parts1 = name1.split()
        parts2 = name2.split()
        
        if len(parts1) != len(parts2):
            return False
        
        for p1, p2 in zip(parts1, parts2):
            # Check if one is abbreviated (single letter) and matches the first letter of the other
            if len(p1) == 1 and len(p2) > 1:
                if p1.lower() != p2[0].lower():
                    return False
            elif len(p2) == 1 and len(p1) > 1:
                if p2.lower() != p1[0].lower():
                    return False
            elif p1.lower() != p2.lower():
                return False
        
        return True
    
    def calculate_comprehensive_player_analysis(self, player_name: str, team: str, 
                                               pitcher_name: str, pitcher_matchup: Dict, 
                                               odds_data: Dict) -> Dict[str, Any]:
        """
        COMPREHENSIVE PLAYER ANALYSIS with all data sources integrated
        This is where the detailed analysis happens
        """
        
        print(f"🔍 Comprehensive analysis: {player_name} vs {pitcher_name}")
        
        analysis = {
            'player_name': player_name,
            'team': team,
            'pitcher_name': pitcher_name,
            'venue': pitcher_matchup['venue'],
            'is_home': pitcher_matchup['is_home'],
            'confidence_score': 0.0,
            'detailed_reasoning': [],
            'component_scores': {},
            'data_sources_used': [],
            'trend_analysis': {},
            'api_analysis': {},
            'launch_angle_masters_data': {},
            'barrel_matchup_data': {}
        }
        
        # 1. COMPREHENSIVE BATTER ANALYSIS (30% weight - reduced from 35%)
        batter_analysis = self._analyze_batter_comprehensive_enhanced(player_name)
        analysis['component_scores']['batter_analysis'] = batter_analysis
        
        if batter_analysis['data_available']:
            analysis['data_sources_used'].extend(['custom_batter_stats', 'exit_velocity_data'])
            
            # Add detailed reasoning
            if batter_analysis['exit_velocity_score'] >= 80:
                analysis['detailed_reasoning'].append(
                    f"Elite exit velocity: {batter_analysis['exit_velocity_avg']:.1f} mph ({batter_analysis['exit_velocity_percentile']:.0f}th percentile)"
                )
            elif batter_analysis['exit_velocity_score'] >= 65:
                analysis['detailed_reasoning'].append(
                    f"Above-average exit velocity: {batter_analysis['exit_velocity_avg']:.1f} mph"
                )
            
            if batter_analysis['barrel_rate_score'] >= 80:
                analysis['detailed_reasoning'].append(
                    f"Elite barrel rate: {batter_analysis['barrel_rate']:.1f}% (crushing the ball consistently)"
                )
            elif batter_analysis['barrel_rate_score'] >= 65:
                analysis['detailed_reasoning'].append(
                    f"Strong barrel rate: {batter_analysis['barrel_rate']:.1f}% (quality contact)"
                )
            
            if batter_analysis['power_score'] >= 75:
                analysis['detailed_reasoning'].append(
                    f"Strong power profile: {batter_analysis['home_runs']} HRs, {batter_analysis['iso']:.3f} ISO"
                )
            
            # Weight batter analysis (30% - reduced from 35%)
            analysis['confidence_score'] += batter_analysis['overall_score'] * 0.30
        
        # 2. COMPREHENSIVE PITCHER ANALYSIS (22% weight - reduced from 25%)
        pitcher_analysis = self._analyze_pitcher_comprehensive_enhanced(pitcher_name)
        analysis['component_scores']['pitcher_analysis'] = pitcher_analysis
        
        if pitcher_analysis['data_available']:
            analysis['data_sources_used'].extend(['custom_pitcher_stats', 'pitcher_exit_velocity'])
            
            # Add detailed reasoning
            if pitcher_analysis['vulnerability_score'] >= 80:
                analysis['detailed_reasoning'].append(
                    f"Highly vulnerable pitcher: {pitcher_analysis['era']:.2f} ERA, {pitcher_analysis['hr_per_9']:.2f} HR/9"
                )
            elif pitcher_analysis['vulnerability_score'] >= 65:
                analysis['detailed_reasoning'].append(
                    f"Vulnerable pitcher: {pitcher_analysis['era']:.2f} ERA"
                )
            
            if pitcher_analysis['contact_quality_score'] >= 75:
                analysis['detailed_reasoning'].append(
                    f"Allows hard contact: {pitcher_analysis['exit_velocity_allowed']:.1f} mph avg, {pitcher_analysis['barrel_rate_allowed']:.1f}% barrels"
                )
            
            # Weight pitcher analysis (22% - reduced from 25%)
            analysis['confidence_score'] += pitcher_analysis['overall_score'] * 0.22
        
        # 3. ROLLING TREND ANALYSIS (12% weight - reduced from 15%)
        trend_analysis = self._analyze_rolling_performance_trends(player_name, 15)
        analysis['trend_analysis'] = trend_analysis
        
        if trend_analysis['trend_available']:
            analysis['data_sources_used'].append('daily_json_files')
            
            if trend_analysis['trend_direction'] == 'very_hot':
                analysis['detailed_reasoning'].append(
                    f"Red-hot recent form: {trend_analysis['recent_3_avg']:.3f} AVG last 3 games vs {trend_analysis['season_avg']:.3f} season"
                )
            elif trend_analysis['trend_direction'] == 'hot':
                analysis['detailed_reasoning'].append(
                    f"Hot recent streak: {trend_analysis['recent_3_avg']:.3f} AVG trending up"
                )
            elif trend_analysis['trend_direction'] == 'cold':
                analysis['detailed_reasoning'].append(
                    f"Recent cold spell: {trend_analysis['recent_3_avg']:.3f} AVG last 3 games"
                )
            
            if trend_analysis['hr_last_7'] >= 2:
                analysis['detailed_reasoning'].append(
                    f"Power surge: {trend_analysis['hr_last_7']} HRs in last 7 games"
                )
            
            # Weight trend analysis (12% - reduced from 15%)
            analysis['confidence_score'] += trend_analysis['trend_score'] * 0.12
        
        # 4. ENHANCED ARSENAL MATCHUP ANALYSIS (18% weight)
        arsenal_analysis = self._analyze_enhanced_arsenal_matchup(player_name, pitcher_name)
        analysis['component_scores']['arsenal_matchup'] = arsenal_analysis
        
        if arsenal_analysis['matchup_available']:
            analysis['data_sources_used'].append('pitch_arsenal_data')
            
            # Add arsenal reasoning
            if arsenal_analysis['overall_advantage'] >= 15:
                analysis['detailed_reasoning'].append(
                    f"Strong arsenal advantage: {arsenal_analysis['advantage_summary']}"
                )
            elif arsenal_analysis['overall_advantage'] >= 8:
                analysis['detailed_reasoning'].append(
                    f"Favorable pitch matchups: {arsenal_analysis['advantage_summary']}"
                )
            elif arsenal_analysis['overall_advantage'] <= -8:
                analysis['detailed_reasoning'].append(
                    f"Challenging matchup: {arsenal_analysis['disadvantage_summary']}"
                )
            
            # Weight arsenal analysis (18% of total score)
            analysis['confidence_score'] += arsenal_analysis['overall_advantage'] * 0.18
        
        # 5. BASEBALLAPI INTEGRATION (8% weight - reduced from 10%)
        if self.api_available:
            api_analysis = self._get_baseball_api_analysis(player_name, pitcher_name, team)
            if api_analysis:
                analysis['api_analysis'] = api_analysis
                analysis['data_sources_used'].append('baseball_api')
                
                # Add API reasoning
                if api_analysis.get('hr_score', 0) >= 80:
                    analysis['detailed_reasoning'].append(
                        f"API advanced analysis: {api_analysis.get('hr_score', 0):.1f}% confidence"
                    )
                
                # Weight API analysis (8% - reduced from 10%)
                analysis['confidence_score'] += (api_analysis.get('hr_score', 50) - 50) * 0.08
        
        # 6. HANDEDNESS MATCHUP ANALYSIS (7% weight - reduced from 10%)
        handedness_analysis = self._analyze_handedness_matchup_enhanced(player_name, pitcher_name)
        analysis['component_scores']['handedness_analysis'] = handedness_analysis
        
        if handedness_analysis['advantage_score'] > 0:
            analysis['data_sources_used'].append('handedness_splits')
            analysis['detailed_reasoning'].append(
                f"Favorable handedness matchup: {handedness_analysis['advantage_description']}"
            )
            analysis['confidence_score'] += handedness_analysis['advantage_score'] * 0.07
        
        # 7. SWING OPTIMIZATION ANALYSIS (3% weight - reduced from 5%)
        swing_analysis = self._analyze_swing_path_optimization(player_name)
        analysis['component_scores']['swing_analysis'] = swing_analysis
        
        if swing_analysis['optimization_score'] >= 70:
            analysis['data_sources_used'].append('swing_path_data')
            analysis['detailed_reasoning'].append(
                f"Optimal swing mechanics: {swing_analysis['optimization_score']:.0f}% efficiency"
            )
            analysis['confidence_score'] += (swing_analysis['optimization_score'] - 50) * 0.03
        
        # 7. VENUE CONTEXT (bonus adjustment)
        venue_analysis = self._analyze_venue_context(pitcher_matchup['venue'], pitcher_matchup['is_home'])
        if venue_analysis['hr_factor'] > 1.05:
            analysis['detailed_reasoning'].append(
                f"Hitter-friendly venue: {pitcher_matchup['venue']} (HR factor: {venue_analysis['hr_factor']:.2f})"
            )
            analysis['confidence_score'] += (venue_analysis['hr_factor'] - 1.0) * 20
        
        # 8. POPULATE CARD-SPECIFIC DATA
        # Launch Angle Masters data
        analysis['launch_angle_masters_data'] = {
            'swing_optimization_score': swing_analysis.get('optimization_score', 50),
            'attack_angle': swing_analysis.get('attack_angle', 0),
            'ideal_angle_rate': swing_analysis.get('ideal_angle_rate', 0),
            'bat_speed': swing_analysis.get('bat_speed', 0)
        }
        
        # Barrel Matchup data
        analysis['barrel_matchup_data'] = {
            'barrel_rate': batter_analysis.get('barrel_rate', 0),
            'exit_velocity_avg': batter_analysis.get('exit_velocity_avg', 0),
            'hard_hit_percent': batter_analysis.get('hard_hit_percent', 0),
            'sweet_spot_percent': batter_analysis.get('sweet_spot_percent', 0)
        }
        
        # Recent form analysis integration
        recent_form = self._analyze_recent_form(player_name)
        analysis['recent_form'] = recent_form
        
        # Calculate composite factors for enhanced classification
        composite_factors = self._calculate_composite_factors(analysis, recent_form)
        
        # Apply recent form boost to confidence
        form_boost = (recent_form['score'] - 5.0) * 2  # Scale to ±10 boost
        analysis['confidence_score'] += form_boost
        
        # Final confidence score
        analysis['confidence_score'] = min(95, max(25, analysis['confidence_score']))
        
        # Enhanced classification with betting value and composite factors
        odds = analysis.get('odds', {}).get('american', '+300')
        if isinstance(odds, str):
            odds_value = int(odds.replace('+', '').replace('-', ''))
        else:
            odds_value = 300
            
        analysis['classification'] = self._classify_prediction(
            analysis['confidence_score'], 
            odds_value, 
            composite_factors
        )
        analysis['pathway'] = self._determine_pathway_enhanced(analysis)
        
        # Enhanced reasoning with all context - replace main reasoning
        enhanced_reasoning = self._generate_enhanced_reasoning(analysis, recent_form, composite_factors)
        if enhanced_reasoning and enhanced_reasoning != analysis.get('reasoning', ''):
            analysis['reasoning'] = enhanced_reasoning  # Replace main reasoning for UI display
            analysis['enhanced_reasoning'] = enhanced_reasoning  # Also keep as separate field
        
        return analysis
    
    def _analyze_batter_comprehensive_enhanced(self, player_name: str) -> Dict[str, Any]:
        """Enhanced batter analysis using multiple data sources"""
        
        # Try multiple name variations
        batter_data = None
        ev_data = None
        
        name_variations = self._generate_name_variations(player_name)
        
        for name in name_variations:
            if name in self.custom_batter_stats:
                batter_data = self.custom_batter_stats[name]
                break
        
        for name in name_variations:
            if name in self.exit_velocity_data:
                ev_data = self.exit_velocity_data[name]
                break
        
        if not batter_data and not ev_data:
            return {'data_available': False, 'overall_score': 50}
        
        # Use best available data source
        if ev_data:
            exit_velo = ev_data['avg_hit_speed']
            barrel_rate = ev_data['brl_percent']
            hard_hit = ev_data['ev95percent']
        elif batter_data:
            exit_velo = batter_data['exit_velocity_avg']
            barrel_rate = batter_data['barrel_batted_rate']
            hard_hit = batter_data['hard_hit_percent']
        else:
            exit_velo = barrel_rate = hard_hit = 0
        
        # Calculate percentile-based scores
        ev_percentiles = self.batter_percentiles.get('exit_velocity_avg', {})
        barrel_percentiles = self.batter_percentiles.get('barrel_batted_rate', {})
        
        exit_velo_score = self._calculate_percentile_score(exit_velo, ev_percentiles)
        barrel_score = self._calculate_percentile_score(barrel_rate, barrel_percentiles)
        
        # Power profile
        iso = batter_data.get('iso', 0) if batter_data else 0
        home_runs = batter_data.get('home_runs', 0) if batter_data else 0
        
        iso_percentiles = self.batter_percentiles.get('iso', {})
        power_score = self._calculate_percentile_score(iso, iso_percentiles)
        
        # Overall weighted score
        overall_score = (
            exit_velo_score * 0.35 +
            barrel_score * 0.30 +
            power_score * 0.35
        )
        
        return {
            'data_available': True,
            'exit_velocity_avg': exit_velo,
            'exit_velocity_score': exit_velo_score,
            'exit_velocity_percentile': self._get_percentile_rank(exit_velo, ev_percentiles),
            'barrel_rate': barrel_rate,
            'barrel_rate_score': barrel_score,
            'hard_hit_percent': hard_hit,
            'iso': iso,
            'home_runs': home_runs,
            'power_score': power_score,
            'overall_score': overall_score,
            'sweet_spot_percent': batter_data.get('sweet_spot_percent', 0) if batter_data else 0,
            'data_source': 'exit_velocity' if ev_data else 'custom_batter'
        }
    
    def _analyze_pitcher_comprehensive_enhanced(self, pitcher_name: str) -> Dict[str, Any]:
        """Enhanced pitcher analysis using multiple data sources"""
        
        # Try multiple name variations
        pitcher_data = None
        pitcher_ev_data = None
        
        name_variations = self._generate_name_variations(pitcher_name)
        
        for name in name_variations:
            if name in self.custom_pitcher_stats:
                pitcher_data = self.custom_pitcher_stats[name]
                break
        
        for name in name_variations:
            if name in self.pitcher_exit_velocity:
                pitcher_ev_data = self.pitcher_exit_velocity[name]
                break
        
        if not pitcher_data and not pitcher_ev_data:
            return {'data_available': False, 'overall_score': 50}
        
        # Use best available data
        era = pitcher_data.get('era', 0) if pitcher_data else 0
        hr_per_9 = pitcher_data.get('hr_per_9', 0) if pitcher_data else 0
        
        if pitcher_ev_data:
            exit_velo_allowed = pitcher_ev_data['avg_hit_speed']
            barrel_allowed = pitcher_ev_data['brl_percent']
        elif pitcher_data:
            exit_velo_allowed = pitcher_data['exit_velocity_avg']
            barrel_allowed = pitcher_data['barrel_batted_rate']
        else:
            exit_velo_allowed = barrel_allowed = 0
        
        # Calculate percentile-based scores (reverse for pitchers - lower is better)
        era_percentiles = self.pitcher_percentiles.get('era', {})
        hr_percentiles = self.pitcher_percentiles.get('hr_per_9', {})
        
        era_score = self._calculate_percentile_score(era, era_percentiles, reverse=True)
        hr_score = self._calculate_percentile_score(hr_per_9, hr_percentiles, reverse=True)
        
        # Contact quality (higher = more vulnerable for pitcher)
        ev_percentiles = self.pitcher_percentiles.get('exit_velocity_avg', {})
        contact_score = self._calculate_percentile_score(exit_velo_allowed, ev_percentiles)
        
        # Overall vulnerability score
        overall_score = (
            era_score * 0.40 +
            hr_score * 0.35 +
            contact_score * 0.25
        )
        
        return {
            'data_available': True,
            'era': era,
            'era_score': era_score,
            'hr_per_9': hr_per_9,
            'hr_score': hr_score,
            'exit_velocity_allowed': exit_velo_allowed,
            'contact_quality_score': contact_score,
            'barrel_rate_allowed': barrel_allowed,
            'vulnerability_score': overall_score,
            'overall_score': overall_score,
            'whip': pitcher_data.get('whip', 0) if pitcher_data else 0,
            'k_percent': pitcher_data.get('k_percent', 0) if pitcher_data else 0,
            'data_source': 'pitcher_exit_velocity' if pitcher_ev_data else 'custom_pitcher'
        }
    
    def _analyze_enhanced_arsenal_matchup(self, batter_name: str, pitcher_name: str) -> Dict[str, Any]:
        """
        Enhanced Arsenal Matchup Analysis
        Cross-references pitcher's pitch usage vs batter's performance against those pitch types
        """
        
        # Try multiple name variations for data lookup
        batter_variations = self._generate_name_variations(batter_name)
        pitcher_variations = self._generate_name_variations(pitcher_name)
        
        batter_arsenal = None
        pitcher_arsenal = None
        
        # Find batter arsenal data
        for name in batter_variations:
            if name in self.pitch_arsenal_hitter:
                batter_arsenal = self.pitch_arsenal_hitter[name]
                break
        
        # Find pitcher arsenal data
        for name in pitcher_variations:
            if name in self.pitch_arsenal_pitcher:
                pitcher_arsenal = self.pitch_arsenal_pitcher[name]
                break
        
        if not batter_arsenal or not pitcher_arsenal:
            return {
                'matchup_available': False,
                'overall_advantage': 0,
                'confidence': 0,
                'pitch_matchups': {},
                'advantage_summary': 'No arsenal data available',
                'disadvantage_summary': 'Limited matchup data'
            }
        
        print(f"🎯 Arsenal matchup: {batter_name} vs {pitcher_name}")
        print(f"   Batter pitches: {list(batter_arsenal.keys())}")
        print(f"   Pitcher pitches: {list(pitcher_arsenal.keys())}")
        
        # Find common pitch types
        common_pitches = set(batter_arsenal.keys()) & set(pitcher_arsenal.keys())
        
        if not common_pitches:
            return {
                'matchup_available': False,
                'overall_advantage': 0,
                'confidence': 0,
                'pitch_matchups': {},
                'advantage_summary': 'No common pitch types found',
                'disadvantage_summary': 'Cannot analyze matchup'
            }
        
        pitch_matchups = {}
        total_weighted_advantage = 0
        total_usage_weight = 0
        
        # Analyze each common pitch type
        for pitch_type in common_pitches:
            batter_stats = batter_arsenal[pitch_type]
            pitcher_stats = pitcher_arsenal[pitch_type]
            
            # Get usage weight (how often pitcher throws this pitch)
            usage_weight = pitcher_stats.get('pitch_usage', 0) / 100.0
            
            # Skip if very low usage or sample size
            if usage_weight < 0.05 or batter_stats.get('pa', 0) < 20:
                continue
            
            # Calculate batter advantage for this pitch type
            batter_slg = batter_stats.get('slg', 0)
            batter_woba = batter_stats.get('woba', 0)
            batter_hard_hit = batter_stats.get('hard_hit_percent', 0)
            batter_whiff = batter_stats.get('whiff_percent', 100)  # Lower is better for batter
            
            # Calculate pitcher vulnerability for this pitch type
            pitcher_ba_allowed = pitcher_stats.get('ba', 0.250)  # League average baseline
            pitcher_slg_allowed = pitcher_stats.get('slg', 0.400)
            pitcher_hard_hit_allowed = pitcher_stats.get('hard_hit_percent', 30)
            pitcher_whiff_rate = pitcher_stats.get('whiff_percent', 20)  # Higher is better for pitcher
            
            # Calculate advantage scores (scale -50 to +50)
            slg_advantage = (batter_slg - 0.400) * 100 - (pitcher_slg_allowed - 0.400) * 100
            woba_advantage = (batter_woba - 0.320) * 100
            hard_hit_advantage = (batter_hard_hit - 30) - (pitcher_hard_hit_allowed - 30)
            whiff_advantage = (25 - batter_whiff) - (pitcher_whiff_rate - 25)  # Lower whiff for batter is good
            
            # Composite advantage for this pitch type
            pitch_advantage = (slg_advantage * 0.4 + woba_advantage * 0.3 + 
                             hard_hit_advantage * 0.2 + whiff_advantage * 0.1)
            
            # Cap advantage between -50 and +50
            pitch_advantage = max(-50, min(50, pitch_advantage))
            
            pitch_matchups[pitch_type] = {
                'batter_slg': batter_slg,
                'pitcher_slg_allowed': pitcher_slg_allowed,
                'batter_woba': batter_woba,
                'batter_hard_hit': batter_hard_hit,
                'pitcher_usage': usage_weight * 100,
                'advantage_score': pitch_advantage,
                'sample_size': batter_stats.get('pa', 0)
            }
            
            # Weight by usage for overall score
            total_weighted_advantage += pitch_advantage * usage_weight
            total_usage_weight += usage_weight
        
        if total_usage_weight == 0:
            return {
                'matchup_available': False,
                'overall_advantage': 0,
                'confidence': 0,
                'pitch_matchups': {},
                'advantage_summary': 'Insufficient data for analysis',
                'disadvantage_summary': 'Low sample sizes'
            }
        
        # Calculate overall advantage score
        overall_advantage = total_weighted_advantage / total_usage_weight
        
        # Calculate confidence based on data quality
        total_pa = sum(matchup.get('sample_size', 0) for matchup in pitch_matchups.values())
        confidence = min(1.0, total_pa / 200.0)  # Full confidence at 200+ PA
        
        # Generate advantage/disadvantage summaries
        best_matchups = [
            f"{pitch_type} ({matchup['advantage_score']:+.1f})"
            for pitch_type, matchup in pitch_matchups.items()
            if matchup['advantage_score'] > 5
        ]
        
        worst_matchups = [
            f"{pitch_type} ({matchup['advantage_score']:+.1f})"
            for pitch_type, matchup in pitch_matchups.items()
            if matchup['advantage_score'] < -5
        ]
        
        advantage_summary = f"Strong vs {', '.join(best_matchups[:2])}" if best_matchups else "Limited advantages found"
        disadvantage_summary = f"Struggles vs {', '.join(worst_matchups[:2])}" if worst_matchups else "No major weaknesses"
        
        print(f"   Overall advantage: {overall_advantage:+.1f} (confidence: {confidence:.2f})")
        print(f"   Key matchups: {list(pitch_matchups.keys())}")
        
        return {
            'matchup_available': True,
            'overall_advantage': overall_advantage,
            'confidence': confidence,
            'pitch_matchups': pitch_matchups,
            'advantage_summary': advantage_summary,
            'disadvantage_summary': disadvantage_summary,
            'total_sample_size': total_pa
        }
    
    def _analyze_handedness_matchup_enhanced(self, batter_name: str, pitcher_name: str) -> Dict[str, Any]:
        """Enhanced handedness matchup analysis"""
        
        # For now, assume RHP vs RHB (could be enhanced with actual handedness detection)
        matchup_key = 'RHP_vs_RHB'
        
        name_variations = self._generate_name_variations(batter_name)
        
        for name in name_variations:
            if matchup_key in self.handedness_splits and name in self.handedness_splits[matchup_key]:
                splits = self.handedness_splits[matchup_key][name]
                
                woba = splits['woba']
                iso = splits['iso']
                hr_fb_percent = splits['hr_fb_percent']
                
                # Calculate advantage
                if woba >= 0.370 and iso >= 0.200:
                    advantage = 20
                    description = "Elite handedness matchup"
                elif woba >= 0.340 and iso >= 0.170:
                    advantage = 15
                    description = "Strong handedness matchup"
                elif woba >= 0.320 and iso >= 0.140:
                    advantage = 10
                    description = "Favorable handedness matchup"
                elif woba >= 0.300:
                    advantage = 5
                    description = "Slight handedness advantage"
                else:
                    advantage = 0
                    description = "Neutral handedness matchup"
                
                return {
                    'matchup_available': True,
                    'matchup_key': matchup_key,
                    'woba': woba,
                    'iso': iso,
                    'hr_fb_percent': hr_fb_percent,
                    'advantage_score': advantage,
                    'advantage_description': description
                }
        
        return {
            'matchup_available': False,
            'advantage_score': 0,
            'advantage_description': 'No handedness data available'
        }
    
    def _analyze_swing_path_optimization(self, player_name: str) -> Dict[str, Any]:
        """Analyze swing path optimization"""
        
        name_variations = self._generate_name_variations(player_name)
        
        for name in name_variations:
            if name in self.swing_path_data:
                # Try vs_RHP first, then overall
                swing_key = 'vs_RHP' if 'vs_RHP' in self.swing_path_data[name] else 'overall'
                
                if swing_key in self.swing_path_data[name]:
                    swing_data = self.swing_path_data[name][swing_key]
                    
                    bat_speed = swing_data['avg_bat_speed']
                    attack_angle = swing_data['attack_angle']
                    ideal_rate = swing_data['ideal_attack_angle_rate']
                    
                    # Calculate optimization score
                    optimization_score = self._calculate_swing_optimization_score(
                        bat_speed, attack_angle, ideal_rate
                    )
                    
                    return {
                        'data_available': True,
                        'bat_speed': bat_speed,
                        'attack_angle': attack_angle,
                        'ideal_angle_rate': ideal_rate,
                        'optimization_score': optimization_score
                    }
        
        return {
            'data_available': False,
            'optimization_score': 50
        }
    
    def _calculate_swing_optimization_score(self, bat_speed: float, attack_angle: float, 
                                          ideal_rate: float) -> float:
        """Calculate swing optimization score"""
        
        if bat_speed <= 0 or attack_angle <= 0 or ideal_rate <= 0:
            return 50
        
        # Bat speed score (normalized 67-79 mph range)
        bat_speed_score = min(100, max(0, (bat_speed - 67) / 12 * 100))
        
        # Attack angle score (5-20 degrees optimal for HR)
        if 8 <= attack_angle <= 18:
            angle_score = 100
        elif 5 <= attack_angle <= 22:
            angle_score = 85
        elif 3 <= attack_angle <= 25:
            angle_score = 70
        elif 0 <= attack_angle <= 30:
            angle_score = 50
        else:
            angle_score = 25
        
        # Ideal rate score
        rate_score = min(100, ideal_rate * 150)  # 0.67 rate = 100 score
        
        # Weighted optimization score
        return (bat_speed_score * 0.35 + angle_score * 0.40 + rate_score * 0.25)
    
    def _analyze_venue_context(self, venue: str, is_home: bool) -> Dict[str, Any]:
        """Analyze venue context"""
        
        # Park factors (comprehensive)
        park_factors = {
            'Coors Field': 1.30,  # Extreme hitter friendly
            'Yankee Stadium': 1.18,
            'Fenway Park': 1.12,
            'Camden Yards': 1.10,
            'Minute Maid Park': 1.08,
            'Citizens Bank Park': 1.06,
            'Great American Ball Park': 1.05,
            'Kauffman Stadium': 0.95,
            'Comerica Park': 0.92,
            'Petco Park': 0.88,
            'Marlins Park': 0.90,
            'Tropicana Field': 0.93
        }
        
        hr_factor = 1.0
        for park, factor in park_factors.items():
            if park in venue:
                hr_factor = factor
                break
        
        return {
            'venue': venue,
            'hr_factor': hr_factor,
            'home_advantage': 0.03 if is_home else 0.0
        }
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate all possible name variations"""
        variations = [name.strip()]
        
        # Handle "Last, First" format
        if ', ' in name:
            parts = name.split(', ')
            if len(parts) == 2:
                variations.append(f"{parts[1].strip()} {parts[0].strip()}")
        
        # Handle "First Last" format  
        elif ' ' in name:
            parts = name.split(' ')
            if len(parts) >= 2:
                variations.append(f"{parts[-1].strip()}, {' '.join(parts[:-1]).strip()}")
        
        # Add lowercase variations
        variations.extend([v.lower() for v in variations])
        
        return list(set(variations))
    
    def _get_percentile_rank(self, value: float, percentiles: Dict[str, float]) -> float:
        """Get percentile rank for a value"""
        if not percentiles or value == 0:
            return 50.0
        
        if value >= percentiles['p95']:
            return 95.0
        elif value >= percentiles['p90']:
            return 90.0
        elif value >= percentiles['p75']:
            return 75.0
        elif value >= percentiles['p50']:
            return 50.0
        elif value >= percentiles['p25']:
            return 25.0
        else:
            return 10.0
    
    def _classify_prediction(self, confidence_score: float, odds: int = 300, composite_factors: Dict = None) -> str:
        """Enhanced classification based on confidence score, betting value, and composite factors"""
        if composite_factors is None:
            composite_factors = {}
        
        # Calculate betting value (expected value)
        betting_value = self._calculate_betting_value(confidence_score / 100, odds)
        
        # Get composite score and negative factors
        composite_score = composite_factors.get('composite_score', 5.0)
        negative_factors = composite_factors.get('negative_factors', 0)
        recent_form_score = composite_factors.get('recent_form_score', 5.0)
        
        # Enhanced classification with realistic thresholds and betting value consideration
        
        # Strong Bet: High confidence + positive EV + good composite score
        if (confidence_score >= 40 and betting_value > 0.05 and 
            composite_score >= 7.0 and negative_factors <= 2 and recent_form_score >= 6.0):
            return 'Strong Bet'
        
        # Solid Bet: Good confidence + decent EV + solid fundamentals  
        elif (confidence_score >= 35 and betting_value > 0.0 and 
              composite_score >= 6.0 and negative_factors <= 3):
            return 'Solid Bet'
        
        # Value Play: Moderate confidence + positive EV OR high composite despite lower confidence
        elif (confidence_score >= 30 and betting_value > -0.02) or (composite_score >= 7.5):
            return 'Value Play'
        
        # Moderate Play: Decent fundamentals even if lower confidence
        elif confidence_score >= 25 and composite_score >= 5.5 and negative_factors <= 4:
            return 'Moderate Play'
        
        # Longshot: Low confidence but still viable (not hopeless)
        elif confidence_score >= 20 and composite_score >= 4.0:
            return 'Longshot'
        
        # Avoid: Very poor fundamentals or extremely low confidence
        else:
            return 'Avoid'

    def _calculate_betting_value(self, confidence: float, odds: int) -> float:
        """Calculate expected value based on confidence vs odds"""
        try:
            # Convert American odds to decimal probability
            if odds > 0:
                implied_probability = 100 / (odds + 100)
            else:
                implied_probability = abs(odds) / (abs(odds) + 100)
            
            # Calculate expected value
            if confidence > implied_probability:
                # Positive EV calculation
                expected_value = (confidence * odds) - ((1 - confidence) * 100)
                return expected_value / 100  # Convert to percentage
            else:
                # Negative EV calculation
                return -((1 - confidence) * 100) / 100
        except:
            return 0.0

    def _analyze_recent_form(self, player_name: str, analysis_date: str = None) -> Dict[str, Any]:
        """Analyze recent form with trend analysis across multiple time windows"""
        try:
            if analysis_date is None:
                analysis_date = self.today
            
            # Load recent form data from BaseballTracker
            rolling_stats = self._load_rolling_stats_data(player_name)
            if not rolling_stats:
                return {'score': 5.0, 'trends': {}, 'context': 'No recent form data available'}
            
            # Analyze different time windows
            windows = {'3_game': 3, '5_game': 5, '7_game': 7, '15_game': 15}
            trends = {}
            
            for window_name, days in windows.items():
                trend_data = self._calculate_trend_for_window(rolling_stats, window_name, days)
                trends[window_name] = trend_data
            
            # Calculate composite form score with weighted windows
            window_weights = {'3_game': 0.4, '5_game': 0.3, '7_game': 0.2, '15_game': 0.1}
            base_score = 5.0  # Neutral baseline
            
            for window, weight in window_weights.items():
                trend = trends.get(window, {})
                direction = trend.get('direction', 'stable')
                strength = trend.get('strength', 0)
                
                if direction == 'trending_up':
                    base_score += weight * 3 * strength
                elif direction == 'trending_down':
                    base_score -= weight * 2 * strength
            
            # Cap between 1-10
            final_score = max(1.0, min(10.0, base_score))
            
            return {
                'score': final_score,
                'trends': trends,
                'context': self._format_recent_form_context(trends, final_score)
            }
            
        except Exception as e:
            print(f"⚠️ Recent form analysis failed for {player_name}: {e}")
            return {'score': 5.0, 'trends': {}, 'context': 'Recent form analysis unavailable'}

    def _load_rolling_stats_data(self, player_name: str) -> Dict:
        """Load rolling statistics data from BaseballTracker"""
        try:
            # Try to load from rolling stats files
            rolling_paths = [
                self.base_dir / "public" / "data" / "rolling_stats" / "rolling_stats_last_7_latest.json",
                self.base_dir / "public" / "data" / "rolling_stats" / "rolling_stats_last_30_latest.json",
                self.base_dir / "public" / "data" / "rolling_stats" / "rolling_stats_season_latest.json"
            ]
            
            for path in rolling_paths:
                if path.exists():
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Handle different BaseballTracker rolling stats structures
                    
                    # Try allPlayerStats structure first
                    all_players = data.get('allPlayerStats', {})
                    if all_players:
                        # Handle both dict and list within allPlayerStats
                        if isinstance(all_players, dict):
                            for key, player in all_players.items():
                                player_data_name = player.get('name', '') or player.get('playerName', '')
                                if self._names_match(player_data_name, player_name):
                                    print(f"✅ Found rolling stats for {player_name} in {path.name} (matched with '{player_data_name}')")
                                    return player
                        elif isinstance(all_players, list):
                            for player in all_players:
                                player_data_name = player.get('name', '') or player.get('playerName', '')
                                if self._names_match(player_data_name, player_name):
                                    print(f"✅ Found rolling stats for {player_name} in {path.name} (matched with '{player_data_name}')")
                                    return player
                    
                    # Also check if data is a direct list format (backup)
                    if isinstance(data, list):
                        for player in data:
                            player_data_name = player.get('name', '') or player.get('playerName', '')
                            if self._names_match(player_data_name, player_name):
                                print(f"✅ Found rolling stats for {player_name} in {path.name} (list format, matched with '{player_data_name}')")
                                return player
            
            print(f"❌ No rolling stats found for {player_name}")
            return {}
            
        except Exception as e:
            print(f"⚠️ Could not load rolling stats for {player_name}: {e}")
            return {}

    def _calculate_trend_for_window(self, rolling_stats: Dict, window_name: str, days: int) -> Dict:
        """Calculate trend direction and strength for a specific time window"""
        try:
            # Extract recent performance data
            game_log = rolling_stats.get('gameLog', [])
            if len(game_log) < 3:
                return {'direction': 'insufficient_data', 'strength': 0}
            
            # Take last N games for this window
            recent_games = game_log[-days:] if len(game_log) >= days else game_log
            
            if len(recent_games) < 2:
                return {'direction': 'insufficient_data', 'strength': 0}
            
            # Calculate performance scores for trend analysis
            performance_scores = []
            for game in recent_games:
                score = (
                    (game.get('H', 0) * 2) +
                    (game.get('HR', 0) * 8) +
                    (game.get('RBI', 0) * 1.5) +
                    (game.get('R', 0) * 1.5) -
                    (game.get('K', 0) * 0.5)
                )
                performance_scores.append(score)
            
            # Simple trend calculation
            if len(performance_scores) >= 3:
                recent_avg = sum(performance_scores[-3:]) / min(3, len(performance_scores))
                earlier_avg = sum(performance_scores[:-3]) / max(1, len(performance_scores) - 3)
                
                if earlier_avg > 0:
                    trend_strength = (recent_avg - earlier_avg) / earlier_avg
                else:
                    trend_strength = 0
                
                if trend_strength > 0.15:
                    return {'direction': 'trending_up', 'strength': min(1.0, trend_strength)}
                elif trend_strength < -0.15:  
                    return {'direction': 'trending_down', 'strength': min(1.0, abs(trend_strength))}
                else:
                    return {'direction': 'stable', 'strength': abs(trend_strength)}
            
            return {'direction': 'stable', 'strength': 0}
            
        except Exception as e:
            return {'direction': 'error', 'strength': 0}

    def _format_recent_form_context(self, trends: Dict, score: float) -> str:
        """Format recent form analysis into readable context"""
        try:
            # Get primary trend (3-game most important)
            primary_trend = trends.get('3_game', {})
            direction = primary_trend.get('direction', 'stable')
            strength = primary_trend.get('strength', 0)
            
            # Trend indicators
            indicators = {
                'trending_up': '📈 Heating up',
                'trending_down': '📉 Cooling off', 
                'stable': '➡️ Consistent',
                'insufficient_data': '❓ Limited data'
            }
            
            primary_indicator = indicators.get(direction, '➡️ Stable')
            
            # Build context
            context_parts = [f"Form: {score:.1f}/10", primary_indicator]
            
            # Add strength context
            if direction in ['trending_up', 'trending_down'] and strength > 0.3:
                context_parts.append(f"(Strong trend: {strength:.1f})")
            elif direction in ['trending_up', 'trending_down'] and strength > 0.15:
                context_parts.append(f"(Moderate trend: {strength:.1f})")
            
            # Add multi-window summary
            window_summary = []
            for window in ['3_game', '7_game', '15_game']:
                trend = trends.get(window, {})
                direction = trend.get('direction', 'stable')
                if direction == 'trending_up':
                    window_summary.append(f"{window.split('_')[0]}G↗")
                elif direction == 'trending_down':
                    window_summary.append(f"{window.split('_')[0]}G↘")
            
            if window_summary:
                context_parts.append(f"Trends: {', '.join(window_summary)}")
            
            return " | ".join(context_parts)
            
        except Exception as e:
            return f"Form: {score:.1f}/10 | Analysis error"

    def _calculate_composite_factors(self, analysis: Dict, recent_form: Dict) -> Dict:
        """Calculate composite factors for enhanced classification"""
        try:
            composite_score = 5.0  # Base score
            negative_factors = 0
            
            # Component scores influence
            batter_score = analysis.get('component_scores', {}).get('batter_analysis', {}).get('overall_score', 50)
            pitcher_score = analysis.get('component_scores', {}).get('pitcher_analysis', {}).get('overall_score', 50)
            
            # Normalize to 1-10 scale
            batter_normalized = (batter_score / 10)
            pitcher_vulnerability = ((100 - pitcher_score) / 10)  # Higher pitcher score = lower vulnerability
            
            composite_score = (batter_normalized * 0.6) + (pitcher_vulnerability * 0.4)
            
            # Recent form influence
            form_score = recent_form.get('score', 5.0)
            if form_score < 3.0:
                negative_factors += 2
            elif form_score < 4.0:
                negative_factors += 1
            elif form_score > 7.0:
                composite_score += 1.0
            
            # Trend analysis
            trends = recent_form.get('trends', {})
            primary_trend = trends.get('3_game', {})
            if primary_trend.get('direction') == 'trending_down':
                negative_factors += 1
            elif primary_trend.get('direction') == 'trending_up':
                if primary_trend.get('strength', 0) > 0.3:
                    composite_score += 1.5
                else:
                    composite_score += 0.5
            
            # Cap composite score
            composite_score = max(1.0, min(10.0, composite_score))
            
            return {
                'composite_score': composite_score,
                'negative_factors': negative_factors,
                'recent_form_score': form_score
            }
            
        except Exception as e:
            return {
                'composite_score': 5.0,
                'negative_factors': 0, 
                'recent_form_score': 5.0
            }

    def _generate_enhanced_reasoning(self, analysis: Dict, recent_form: Dict, composite_factors: Dict) -> str:
        """Generate comprehensive reasoning with all context factors"""
        try:
            reasoning_sections = []
            
            # 1. Core Performance Metrics (what user currently sees)
            batter_analysis = analysis.get('component_scores', {}).get('batter_analysis', {})
            exit_velo = batter_analysis.get('exit_velocity_avg', 0)
            barrel_rate = batter_analysis.get('barrel_rate', 0)
            iso = batter_analysis.get('iso', 0)
            home_runs = batter_analysis.get('home_runs', 0)
            
            core_metrics = []
            if exit_velo > 0:
                if exit_velo >= 95:
                    core_metrics.append(f"Elite exit velocity: {exit_velo:.1f} mph (95th+ percentile)")
                elif exit_velo >= 92:
                    core_metrics.append(f"Strong exit velocity: {exit_velo:.1f} mph (80th+ percentile)")
                elif exit_velo >= 89:
                    core_metrics.append(f"Solid exit velocity: {exit_velo:.1f} mph (average+)")
                else:
                    core_metrics.append(f"Below-average exit velocity: {exit_velo:.1f} mph")
            
            if barrel_rate > 0:
                if barrel_rate >= 15:
                    core_metrics.append(f"Elite barrel rate: {barrel_rate:.1f}% (crushing the ball consistently)")
                elif barrel_rate >= 10:
                    core_metrics.append(f"Strong barrel rate: {barrel_rate:.1f}% (solid contact quality)")
                elif barrel_rate >= 6:
                    core_metrics.append(f"Average barrel rate: {barrel_rate:.1f}%")
                else:
                    core_metrics.append(f"Below-average barrel rate: {barrel_rate:.1f}%")
            
            if iso > 0 and home_runs > 0:
                core_metrics.append(f"Power profile: {home_runs:.0f} HRs, {iso:.3f} ISO")
            
            if core_metrics:
                reasoning_sections.append(" | ".join(core_metrics))
            
            # 2. Season Context Analysis (NEW)
            season_context = self._analyze_season_context(analysis)
            if season_context:
                reasoning_sections.append(season_context)
            
            # 3. Recent Form & Trends (NEW - what user specifically requested)
            form_context = recent_form.get('context', '')
            if form_context and 'No recent form data' not in form_context:
                reasoning_sections.append(f"Recent Form: {form_context}")
            
            # 4. Arsenal Matchup Analysis (NEW - enhanced)
            arsenal_context = self._analyze_arsenal_matchup_context(analysis)
            if arsenal_context:
                reasoning_sections.append(arsenal_context)
            
            # 5. Venue & Situational Context
            venue_context = self._get_venue_context(analysis)
            if venue_context:
                reasoning_sections.append(venue_context)
            
            # 6. Critical Assessment (NEW - better feedback on bet potential)
            critical_assessment = self._generate_critical_assessment(analysis, recent_form, composite_factors)
            if critical_assessment:
                reasoning_sections.append(f"Assessment: {critical_assessment}")
            
            # Combine all sections
            enhanced_reasoning = " | ".join([section for section in reasoning_sections if section])
            
            # Fallback to original if enhancement fails
            if not enhanced_reasoning:
                return analysis.get('reasoning', 'Standard analysis completed')
            
            return enhanced_reasoning
            
        except Exception as e:
            print(f"⚠️ Enhanced reasoning generation failed: {e}")
            return analysis.get('reasoning', 'Analysis completed with limited context')

    def _analyze_season_context(self, analysis: Dict) -> str:
        """Analyze current performance vs season context"""
        try:
            batter_analysis = analysis.get('component_scores', {}).get('batter_analysis', {})
            
            # Get current vs season metrics if available
            current_avg = batter_analysis.get('batting_avg', 0)
            current_slg = batter_analysis.get('slg', 0)
            current_hr_rate = batter_analysis.get('hr_rate', 0)
            
            context_parts = []
            
            # Power trends
            home_runs = batter_analysis.get('home_runs', 0)
            if home_runs > 0:
                if home_runs >= 30:
                    context_parts.append("Elite power (30+ HR pace)")
                elif home_runs >= 20:
                    context_parts.append("Strong power (20+ HR pace)")
                elif home_runs >= 15:
                    context_parts.append("Solid power (15+ HR pace)")
                else:
                    context_parts.append(f"Moderate power ({home_runs} HRs)")
            
            # ISO analysis
            iso = batter_analysis.get('iso', 0)
            if iso > 0:
                if iso >= 0.250:
                    context_parts.append(f"Elite ISO: {iso:.3f}")
                elif iso >= 0.200:
                    context_parts.append(f"Strong ISO: {iso:.3f}")
                elif iso >= 0.150:
                    context_parts.append(f"Average ISO: {iso:.3f}")
                else:
                    context_parts.append(f"Below-average ISO: {iso:.3f}")
            
            if context_parts:
                return f"Season Context: {' | '.join(context_parts)}"
            
            return ""
            
        except Exception as e:
            return ""

    def _analyze_arsenal_matchup_context(self, analysis: Dict) -> str:
        """Analyze pitcher arsenal vs batter handedness matchup"""
        try:
            handedness_analysis = analysis.get('component_scores', {}).get('handedness_analysis', {})
            pitcher_analysis = analysis.get('component_scores', {}).get('pitcher_analysis', {})
            
            context_parts = []
            
            # Handedness advantage
            advantage_desc = handedness_analysis.get('advantage_description', '')
            if advantage_desc and 'No handedness data' not in advantage_desc:
                context_parts.append(f"Handedness: {advantage_desc}")
            
            # Pitcher vulnerability
            pitcher_hr_rate = pitcher_analysis.get('hr_per_9', 0)
            pitcher_era = pitcher_analysis.get('era', 0)
            
            if pitcher_hr_rate > 0:
                if pitcher_hr_rate >= 1.5:
                    context_parts.append(f"Vulnerable pitcher: {pitcher_hr_rate:.2f} HR/9")
                elif pitcher_hr_rate >= 1.2:
                    context_parts.append(f"Moderate pitcher risk: {pitcher_hr_rate:.2f} HR/9")
                else:
                    context_parts.append(f"Tough pitcher: {pitcher_hr_rate:.2f} HR/9")
            
            if pitcher_era > 0:
                if pitcher_era >= 5.00:
                    context_parts.append(f"High ERA: {pitcher_era:.2f}")
                elif pitcher_era >= 4.50:
                    context_parts.append(f"Above-average ERA: {pitcher_era:.2f}")
                elif pitcher_era <= 3.50:
                    context_parts.append(f"Strong ERA: {pitcher_era:.2f}")
            
            if context_parts:
                return f"Matchup: {' | '.join(context_parts)}"
            
            return ""
            
        except Exception as e:
            return ""

    def _get_venue_context(self, analysis: Dict) -> str:
        """Get venue context information"""
        try:
            venue = analysis.get('venue', '')
            if venue:
                # Simple venue analysis (can be enhanced with park factors)
                hitter_friendly_parks = ['Coors Field', 'Great American Ball Park', 'Yankee Stadium', 'Fenway Park']
                pitcher_friendly_parks = ['Marlins Park', 'Petco Park', 'Safeco Field', 'Kauffman Stadium']
                
                if venue in hitter_friendly_parks:
                    return f"Venue: {venue} (Hitter-friendly)"
                elif venue in pitcher_friendly_parks:
                    return f"Venue: {venue} (Pitcher-friendly)"
                else:
                    return f"Venue: {venue}"
            
            return ""
            
        except Exception as e:
            return ""

    def _generate_critical_assessment(self, analysis: Dict, recent_form: Dict, composite_factors: Dict) -> str:
        """Generate critical feedback on bet potential"""
        try:
            assessment_parts = []
            
            # Confidence and betting value assessment
            confidence = analysis['confidence_score']
            odds = analysis.get('odds', {}).get('american', '+300')
            if isinstance(odds, str):
                odds_value = int(odds.replace('+', '').replace('-', ''))
            else:
                odds_value = 300
            
            betting_value = self._calculate_betting_value(confidence / 100, odds_value)
            
            # Overall strength assessment
            composite_score = composite_factors.get('composite_score', 5.0)
            negative_factors = composite_factors.get('negative_factors', 0)
            
            if confidence >= 40 and betting_value > 0.05:
                assessment_parts.append("💰 Strong betting value - high confidence with favorable odds")
            elif confidence >= 35 and betting_value > 0:
                assessment_parts.append("✅ Positive expected value - solid play")
            elif betting_value > -0.02:
                assessment_parts.append("➡️ Near break-even value - manageable risk")
            else:
                assessment_parts.append("⚠️ Negative expected value - higher risk play")
            
            # Recent form warnings/boosts
            form_score = recent_form.get('score', 5.0)
            trends = recent_form.get('trends', {})
            primary_trend = trends.get('3_game', {})
            
            if form_score >= 7.5:
                assessment_parts.append("🔥 Hot recent form supports play")
            elif form_score <= 3.0:
                assessment_parts.append("❄️ Poor recent form - significant concern")
            elif primary_trend.get('direction') == 'trending_up':
                assessment_parts.append("📈 Positive trend building")
            elif primary_trend.get('direction') == 'trending_down':
                assessment_parts.append("📉 Concerning downward trend")
            
            # Risk factors
            if negative_factors >= 3:
                assessment_parts.append("⚠️ Multiple risk factors present")
            elif negative_factors == 0 and composite_score >= 7.0:
                assessment_parts.append("✅ Clean setup with strong fundamentals")
            
            # Composite strength
            if composite_score >= 8.0:
                assessment_parts.append("💪 Elite player/matchup combination")
            elif composite_score <= 4.0:
                assessment_parts.append("🤔 Below-average fundamentals")
            
            return " | ".join(assessment_parts) if assessment_parts else "Standard risk profile"
            
        except Exception as e:
            return "Assessment unavailable"
    
    def _determine_pathway_enhanced(self, analysis: Dict) -> str:
        """Determine prediction pathway"""
        confidence = analysis['confidence_score']
        
        # Check component scores to determine pathway
        batter_score = analysis['component_scores'].get('batter_analysis', {}).get('overall_score', 50)
        pitcher_score = analysis['component_scores'].get('pitcher_analysis', {}).get('overall_score', 50)
        trend_score = analysis['trend_analysis'].get('trend_score', 0)
        
        if confidence >= 85:
            return 'perfectStorm'
        elif batter_score >= 75 and abs(trend_score) >= 10:
            return 'batterDriven'
        elif pitcher_score >= 75:
            return 'pitcherDriven'
        elif batter_score > pitcher_score + 10:
            return 'batterDriven'
        else:
            return 'pitcherDriven'
    
    # Load supporting data methods (odds, lineup, roster)
    def load_current_odds(self) -> List[Dict]:
        """Load current HR odds data"""
        odds_file = self.base_dir / "public" / "data" / "odds" / "mlb-hr-odds-only.csv"
        odds_data = []
        
        try:
            with open(odds_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    odds_data.append({
                        'player_name': row['player_name'],
                        'odds': row['odds'],
                        'last_updated': row.get('last_updated', '')
                    })
            
            print(f"✅ Loaded {len(odds_data)} players with HR odds")
            return odds_data
            
        except FileNotFoundError:
            print("❌ HR odds file not found")
            return []
    
    def load_lineup_data(self, date: str = None) -> Optional[Dict]:
        """Load lineup data"""
        if date is None:
            date = self.today
            
        lineup_file = self.base_dir / "public" / "data" / "lineups" / f"starting_lineups_{date}.json"
        
        try:
            with open(lineup_file, 'r') as f:
                lineup_data = json.load(f)
            
            print(f"✅ Loaded lineup data for {len(lineup_data.get('games', []))} games")
            return lineup_data
            
        except FileNotFoundError:
            print(f"❌ Lineup file not found for {date}")
            return None
    
    def load_roster_data(self) -> List[Dict]:
        """Load roster data for player-team mapping"""
        roster_file = self.base_dir / "public" / "data" / "rosters.json"
        
        try:
            with open(roster_file, 'r') as f:
                roster_data = json.load(f)
            
            print(f"✅ Loaded roster data for {len(roster_data)} players")
            return roster_data
            
        except Exception as e:
            print(f"❌ Error loading roster data: {e}")
            return []
    
    def create_player_team_mapping(self, roster_data: List[Dict]) -> Dict[str, str]:
        """Create player-team mapping"""
        player_team_map = {}
        
        for player in roster_data:
            name = player.get('name', '').strip()
            full_name = player.get('fullName', '').strip()
            team = player.get('team', '').strip()
            
            if team:
                if name:
                    player_team_map[name] = team
                    player_team_map[name.lower()] = team
                
                if full_name:
                    player_team_map[full_name] = team
                    player_team_map[full_name.lower()] = team
        
        return player_team_map
    
    def find_player_team(self, player_name: str, player_team_map: Dict[str, str]) -> Optional[str]:
        """Find team for a player"""
        name_variations = self._generate_name_variations(player_name)
        
        for name in name_variations:
            if name in player_team_map:
                return player_team_map[name]
        
        return None
    
    def get_pitcher_matchup(self, team: str, lineup_data: Dict) -> Optional[Dict]:
        """Get opposing pitcher for a team"""
        if not lineup_data or 'games' not in lineup_data:
            return None
        
        for game in lineup_data['games']:
            teams = game.get('teams', {})
            pitchers = game.get('pitchers', {})
            
            home_team = teams.get('home', {}).get('abbr')
            away_team = teams.get('away', {}).get('abbr')
            
            if teams_match(team, home_team):
                away_pitcher = pitchers.get('away', {})
                if away_pitcher.get('name'):
                    return {
                        'pitcher_name': away_pitcher['name'],
                        'opponent_team': away_team,
                        'venue': game.get('venue', {}).get('name', 'Unknown'),
                        'game_time': game.get('gameTime', ''),
                        'is_home': True
                    }
            elif teams_match(team, away_team):
                home_pitcher = pitchers.get('home', {})
                if home_pitcher.get('name'):
                    return {
                        'pitcher_name': home_pitcher['name'],
                        'opponent_team': home_team,
                        'venue': game.get('venue', {}).get('name', 'Unknown'),
                        'game_time': game.get('gameTime', ''),
                        'is_home': False
                    }
        
        return None
    
    def generate_enhanced_comprehensive_analysis(self, team_filter: List[str] = None) -> Dict:
        """Generate the comprehensive analysis"""
        
        print(f"\n🔥 Generating Enhanced Comprehensive Analysis for {self.today}")
        print("📊 Using ALL available data sources with percentile-based scoring...")
        
        start_time = time.time()
        
        # Load supporting data
        odds_data = self.load_current_odds()
        lineup_data = self.load_lineup_data()
        roster_data = self.load_roster_data()
        
        if not odds_data or not lineup_data:
            return self.create_error_response("Missing required data")
        
        player_team_map = self.create_player_team_mapping(roster_data)
        
        # Process each player with comprehensive analysis
        analysis_picks = []
        processed_count = 0
        
        for odds_player in odds_data:
            player_name = odds_player['player_name']
            
            # Find team
            team = self.find_player_team(player_name, player_team_map)
            if not team:
                continue
            
            # Apply team filter
            if team_filter and team not in team_filter:
                continue
            
            # Get pitcher matchup
            pitcher_matchup = self.get_pitcher_matchup(team, lineup_data)
            if not pitcher_matchup:
                continue
            
            print(f"🔍 Processing: {player_name} ({team}) vs {pitcher_matchup['pitcher_name']}")
            
            # Generate comprehensive analysis
            comprehensive_analysis = self.calculate_comprehensive_player_analysis(
                player_name, team, pitcher_matchup['pitcher_name'], pitcher_matchup, odds_player
            )
            
            # Create analysis pick with full details
            pick = {
                'playerName': player_name,
                'player_name': player_name,
                'team': team,
                'pitcher': f"vs {pitcher_matchup['pitcher_name']}",
                'pitcher_name': pitcher_matchup['pitcher_name'],
                'confidenceScore': comprehensive_analysis['confidence_score'],
                'confidence_score': comprehensive_analysis['confidence_score'],
                'classification': comprehensive_analysis['classification'],
                'pathway': comprehensive_analysis['pathway'],
                'reasoning': '; '.join(comprehensive_analysis['detailed_reasoning']),
                'detailed_reasoning': comprehensive_analysis['detailed_reasoning'],
                'game': f"{pitcher_matchup.get('opponent_team', 'TBD')} @ {team if pitcher_matchup.get('is_home') else pitcher_matchup.get('opponent_team', 'TBD')}",
                'venue': pitcher_matchup['venue'],
                'gameTime': pitcher_matchup.get('game_time', ''),
                'is_home': pitcher_matchup['is_home'],
                'odds': {
                    'american': odds_player['odds'],
                    'decimal': self._american_to_decimal(odds_player['odds']),
                    'source': 'current'
                },
                'component_scores': comprehensive_analysis['component_scores'],
                'trend_analysis': comprehensive_analysis['trend_analysis'],
                'data_sources_used': comprehensive_analysis['data_sources_used'],
                
                # For Launch Angle Masters card
                'swing_optimization_score': comprehensive_analysis['launch_angle_masters_data']['swing_optimization_score'],
                'swing_attack_angle': comprehensive_analysis['launch_angle_masters_data']['attack_angle'],
                'swing_ideal_rate': comprehensive_analysis['launch_angle_masters_data']['ideal_angle_rate'],
                'swing_bat_speed': comprehensive_analysis['launch_angle_masters_data']['bat_speed'],
                
                # For Barrel Matchup card
                'barrel_rate': comprehensive_analysis['barrel_matchup_data']['barrel_rate'],
                'exit_velocity_avg': comprehensive_analysis['barrel_matchup_data']['exit_velocity_avg'],
                'hard_hit_percent': comprehensive_analysis['barrel_matchup_data']['hard_hit_percent'],
                'sweet_spot_percent': comprehensive_analysis['barrel_matchup_data']['sweet_spot_percent']
            }
            
            analysis_picks.append(pick)
            processed_count += 1
        
        processing_time = time.time() - start_time
        
        # Sort by confidence score
        analysis_picks.sort(key=lambda x: x['confidenceScore'], reverse=True)
        
        # Create pathway breakdown
        pathway_breakdown = {
            'perfectStorm': [p for p in analysis_picks if p['pathway'] == 'perfectStorm'],
            'batterDriven': [p for p in analysis_picks if p['pathway'] == 'batterDriven'],
            'pitcherDriven': [p for p in analysis_picks if p['pathway'] == 'pitcherDriven']
        }
        
        # Calculate summary
        total_picks = len(analysis_picks)
        avg_confidence = statistics.mean([p['confidenceScore'] for p in analysis_picks]) if analysis_picks else 0
        
        analysis = {
            'date': self.today,
            'updatedAt': datetime.now().isoformat(),
            'generatedBy': 'enhanced_comprehensive_hellraiser_v6',
            'version': 'enhanced_comprehensive_v6.0',
            'teamFilter': team_filter,
            'picks': analysis_picks,
            'pathwayBreakdown': pathway_breakdown,
            'summary': {
                'totalPicks': total_picks,
                'averageConfidence': round(avg_confidence, 1),
                'personalStraight': len([p for p in analysis_picks if p['classification'] == 'Personal Straight']),
                'longshots': len([p for p in analysis_picks if p['classification'] == 'Longshot']),
                'processingTimeSeconds': round(processing_time, 1)
            },
            'dataQuality': {
                'customBatterStats': len(self.custom_batter_stats),
                'customPitcherStats': len(self.custom_pitcher_stats),
                'exitVelocityData': len(self.exit_velocity_data),
                'pitcherExitVelocityData': len(self.pitcher_exit_velocity),
                'handednessSplits': sum(len(splits) for splits in self.handedness_splits.values()),
                'swingPathData': len(self.swing_path_data),
                'pitchArsenalHitter': len(self.pitch_arsenal_hitter),
                'pitchArsenalPitcher': len(self.pitch_arsenal_pitcher),
                'baseballApiAvailable': self.api_available,
                'percentileBenchmarksBuilt': len(self.batter_percentiles) > 0
            },
            'comprehensiveFeatures': {
                'percentileBasedScoring': True,
                'multiSourceDataIntegration': True,
                'rollingTrendAnalysis': True,
                'baseballApiIntegration': self.api_available,
                'handednessMatchupAnalysis': True,
                'swingPathOptimization': True,
                'launchAngleMastersIntegration': True,
                'barrelMatchupIntegration': True,
                'detailedReasoningGeneration': True
            }
        }
        
        print(f"\n🔥 Enhanced Comprehensive Analysis Complete!")
        print(f"   Processing Time: {processing_time:.1f} seconds")
        print(f"   Total Picks: {total_picks}")
        print(f"   Average Confidence: {avg_confidence:.1f}%")
        print(f"   Score Range: {min(p['confidenceScore'] for p in analysis_picks):.1f}% - {max(p['confidenceScore'] for p in analysis_picks):.1f}%")
        print(f"   Data Sources: {len(comprehensive_analysis['data_sources_used'])} per player")
        
        return analysis
    
    def _american_to_decimal(self, american_odds: str) -> float:
        """Convert American odds to decimal"""
        try:
            if american_odds.startswith('+'):
                value = int(american_odds[1:])
                return round((value / 100) + 1, 2)
            else:
                value = int(american_odds)
                return round((100 / abs(value)) + 1, 2)
        except ValueError:
            return 1.0
    
    def create_error_response(self, error_message: str) -> Dict:
        """Create error response"""
        return {
            'date': self.today,
            'error': error_message,
            'picks': [],
            'pathwayBreakdown': {'perfectStorm': [], 'batterDriven': [], 'pitcherDriven': []},
            'summary': {'totalPicks': 0, 'averageConfidence': 0}
        }
    
    def save_analysis(self, analysis: Dict, team_filter: List[str] = None) -> str:
        """Save comprehensive analysis"""
        
        if team_filter:
            filename = f"hellraiser_analysis_{self.today}_{'_'.join(team_filter)}.json"
        else:
            filename = f"hellraiser_analysis_{self.today}.json"
        
        # Save to both directories
        paths = [
            self.output_dir / filename,
            self.build_output_dir / filename
        ]
        
        for output_path in paths:
            with open(output_path, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print(f"✅ Enhanced comprehensive analysis saved to {output_path}")
        
        return str(paths[0])


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Comprehensive Hellraiser Analysis v6.0')
    parser.add_argument('--teams', nargs='*', help='Filter by specific teams (e.g., NYY BAL)')
    parser.add_argument('--date', help='Analysis date (YYYY-MM-DD, default: today)')
    
    args = parser.parse_args()
    
    print("🔥 Enhanced Comprehensive Hellraiser Generator v6.0")
    print("=" * 70)
    print("🎯 Features:")
    print("  • Percentile-based scoring (no more flat ratings)")
    print("  • Multi-source data integration")
    print("  • Rolling trend analysis from daily JSON files")
    print("  • BaseballAPI integration for advanced analysis")
    print("  • Comprehensive name matching")
    print("  • Launch Angle Masters & Barrel Matchup card integration")
    print("=" * 70)
    
    # Initialize generator
    generator = EnhancedComprehensiveHellraiser()
    
    if args.date:
        generator.today = args.date
    
    # Generate comprehensive analysis
    team_filter = args.teams if args.teams else None
    analysis = generator.generate_enhanced_comprehensive_analysis(team_filter)
    
    # Save analysis
    if analysis.get('error'):
        print(f"❌ Analysis failed: {analysis['error']}")
        sys.exit(1)
    else:
        output_path = generator.save_analysis(analysis, team_filter)
        print(f"\n🔥 Enhanced Comprehensive Analysis completed successfully!")
        print(f"📁 Output: {output_path}")
        print(f"🎯 Launch Angle Masters and Barrel Matchup cards now receive comprehensive data!")
        print(f"⚡ Expected varied confidence scores with detailed reasoning!")


if __name__ == "__main__":
    main()