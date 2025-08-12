#!/usr/bin/env python3
"""
Pitcher Name Mapping System
===========================

Comprehensive system to map anonymous pitcher IDs from play-by-play data
to actual pitcher names using multiple cross-referenced data sources.

This system solves the critical issue where play-by-play data contains
anonymous IDs like "Pitcher_4346118" that need to be resolved to actual
names like "Jacob deGrom" for usable weakspot analysis.

Strategy:
1. Build master player database from roster.json
2. Create game-date-team context from lineup files  
3. Cross-reference with CSV game files for validation
4. Use statistical data for verification
5. Generate high-confidence mapping with fallbacks

Author: BaseballScraper Enhancement System
Date: August 2025
"""

import json
import csv
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple, Set
import re

class PitcherNameMapper:
    """
    Comprehensive pitcher name mapping system using multiple data sources
    """
    
    def __init__(self, base_data_path: str):
        self.base_data_path = Path(base_data_path)
        self.logger = logging.getLogger(__name__)
        
        # Core mapping data structures
        self.master_player_map = {}  # playerId -> player info
        self.game_context_map = {}   # game context -> pitcher info
        self.anonymous_to_name = {}  # Pitcher_XXXXX -> real name
        self.name_variations = {}    # Different name formats
        self.confidence_scores = {}  # Mapping confidence levels
        
        # Data sources
        self.roster_data = []
        self.lineup_files = []
        self.csv_files = []
        self.hellraiser_data = []
        
    def load_all_data_sources(self):
        """Load all available data sources for mapping"""
        self.logger.info("Loading all data sources for pitcher mapping...")
        
        try:
            self._load_roster_data()
            self._load_lineup_files()
            self._load_csv_files()
            self._load_hellraiser_files()
            self._load_custom_stats()
        except Exception as e:
            self.logger.error(f"Error loading data sources: {e}")
            
    def _load_roster_data(self):
        """Load master roster file"""
        roster_file = self.base_data_path / "rosters.json"
        if roster_file.exists():
            try:
                with open(roster_file, 'r') as f:
                    self.roster_data = json.load(f)
                
                # Build master player map
                for player in self.roster_data:
                    if player.get('type') == 'pitcher':
                        player_id = player.get('playerId')
                        if player_id:
                            self.master_player_map[str(player_id)] = {
                                'short_name': player.get('name', ''),
                                'full_name': player.get('fullName', ''),
                                'team': player.get('team', ''),
                                'handedness': player.get('ph', ''),
                                'player_id': player_id
                            }
                            
                            # Add name variations
                            short_name = player.get('name', '')
                            full_name = player.get('fullName', '')
                            if short_name:
                                self.name_variations[short_name.lower()] = str(player_id)
                            if full_name:
                                self.name_variations[full_name.lower()] = str(player_id)
                
                self.logger.info(f"Loaded {len([p for p in self.roster_data if p.get('type') == 'pitcher'])} pitchers from roster")
            except Exception as e:
                self.logger.error(f"Error loading roster data: {e}")
    
    def _load_lineup_files(self):
        """Load daily lineup files for game context"""
        lineup_dir = self.base_data_path / "lineups"
        if lineup_dir.exists():
            lineup_files = list(lineup_dir.glob("starting_lineups_2025-*.json"))
            
            for lineup_file in lineup_files:
                try:
                    with open(lineup_file, 'r') as f:
                        lineup_data = json.load(f)
                    
                    # Extract date from filename
                    date_match = re.search(r'2025-(\d{2})-(\d{2})', lineup_file.name)
                    if date_match:
                        month, day = date_match.groups()
                        file_date = f"2025-{month}-{day}"
                        
                        # Process each game in the lineup file
                        for game in lineup_data.get('games', []):
                            game_id = game.get('originalId', '')
                            
                            # Extract pitcher information
                            pitchers = game.get('pitchers', {})
                            home_pitcher = pitchers.get('home', {})
                            away_pitcher = pitchers.get('away', {})
                            
                            # Store game context
                            if home_pitcher.get('name'):
                                context_key = f"{file_date}_{game.get('homeTeam', '')}_{game_id}"
                                self.game_context_map[context_key] = {
                                    'name': home_pitcher.get('name'),
                                    'id': home_pitcher.get('id'),
                                    'team': game.get('homeTeam', ''),
                                    'game_id': game_id,
                                    'date': file_date,
                                    'venue': game.get('venue', '')
                                }
                                
                            if away_pitcher.get('name'):
                                context_key = f"{file_date}_{game.get('awayTeam', '')}_{game_id}"
                                self.game_context_map[context_key] = {
                                    'name': away_pitcher.get('name'),
                                    'id': away_pitcher.get('id'),
                                    'team': game.get('awayTeam', ''),
                                    'game_id': game_id,
                                    'date': file_date,
                                    'venue': game.get('venue', '')
                                }
                
                except Exception as e:
                    self.logger.warning(f"Error processing lineup file {lineup_file}: {e}")
            
            self.logger.info(f"Loaded {len(self.game_context_map)} game contexts from lineup files")
    
    def _load_csv_files(self):
        """Load CSV game files for additional context"""
        csv_backup_dir = Path("../BaseballData/BACKUP_CSV")
        if not csv_backup_dir.exists():
            csv_backup_dir = self.base_data_path / "CSV_BACKUPS"
        
        if csv_backup_dir.exists():
            pitching_files = list(csv_backup_dir.glob("*_pitching_*.csv"))
            
            # Sample some files to avoid overwhelming processing
            sample_files = pitching_files[:100] if len(pitching_files) > 100 else pitching_files
            
            for csv_file in sample_files:
                try:
                    df = pd.read_csv(csv_file)
                    
                    # Extract game info from filename
                    # Format: TEAM_pitching_DATE_GAMEID.csv
                    filename_parts = csv_file.stem.split('_')
                    if len(filename_parts) >= 4:
                        team = filename_parts[0]
                        game_id = filename_parts[-1]
                        date_part = filename_parts[2:-1] if len(filename_parts) > 4 else []
                        
                        # Get pitcher names from CSV (using 'player' column as seen in sample)
                        name_col = None
                        for col in ['player', 'Name', 'Player']:
                            if col in df.columns:
                                name_col = col
                                break
                        
                        if name_col:
                            pitchers = df[name_col].dropna().tolist()
                            
                            # Store CSV context with enhanced info
                            for pitcher_name in pitchers:
                                csv_key = f"csv_{team}_{game_id}_{pitcher_name}"
                                self.game_context_map[csv_key] = {
                                    'name': pitcher_name,
                                    'team': team.upper(),
                                    'game_id': game_id,
                                    'date_parts': date_part,
                                    'source': 'csv'
                                }
                
                except Exception as e:
                    self.logger.warning(f"Error processing CSV file {csv_file}: {e}")
                    
            self.logger.info(f"Processed {len(sample_files)} CSV files for additional context")
    
    def _load_hellraiser_files(self):
        """Load hellraiser analysis files for current pitcher context"""
        hellraiser_dir = self.base_data_path / "hellraiser"
        if hellraiser_dir.exists():
            hellraiser_files = list(hellraiser_dir.glob("hellraiser_analysis_2025-*.json"))
            
            for hellraiser_file in sorted(hellraiser_files)[-10:]:  # Last 10 files
                try:
                    with open(hellraiser_file, 'r') as f:
                        hellraiser_data = json.load(f)
                    
                    # Extract pitcher names from analysis
                    date_str = hellraiser_file.stem.split('_')[-1]  # Get date part
                    
                    for analysis in hellraiser_data.get('analysis', []):
                        pitcher_name = analysis.get('pitcher', '')
                        if pitcher_name:
                            hellraiser_key = f"hellraiser_{date_str}_{pitcher_name}"
                            self.game_context_map[hellraiser_key] = {
                                'name': pitcher_name,
                                'date': date_str,
                                'source': 'hellraiser'
                            }
                
                except Exception as e:
                    self.logger.warning(f"Error processing hellraiser file {hellraiser_file}: {e}")
            
            self.logger.info(f"Loaded pitcher names from recent hellraiser files")
    
    def _load_custom_stats(self):
        """Load custom pitcher statistics for additional validation"""
        stats_dir = self.base_data_path / "stats"
        if stats_dir.exists():
            custom_pitcher_file = stats_dir / "custom_pitcher_2025.csv"
            if custom_pitcher_file.exists():
                try:
                    df = pd.read_csv(custom_pitcher_file)
                    
                    # Process pitcher names and IDs
                    for _, row in df.iterrows():
                        name = row.get('Name', '') or row.get('player_name', '')
                        player_id = row.get('player_id', '') or row.get('mlb_id', '')
                        
                        if name and player_id:
                            stats_key = f"stats_{name}_{player_id}"
                            self.game_context_map[stats_key] = {
                                'name': name,
                                'player_id': str(player_id),
                                'source': 'custom_stats'
                            }
                            
                            # Add to name variations
                            self.name_variations[name.lower()] = str(player_id)
                
                except Exception as e:
                    self.logger.warning(f"Error loading custom stats: {e}")
    
    def build_anonymous_mapping(self, playbyplay_files: List[Path]) -> Dict[str, Dict]:
        """
        Build mapping from anonymous IDs to real names using game context
        
        Args:
            playbyplay_files: List of play-by-play files to analyze
            
        Returns:
            Dictionary mapping anonymous IDs to pitcher information
        """
        self.logger.info("Building anonymous ID to real name mapping...")
        
        anonymous_ids = set()
        game_contexts = {}
        
        # First pass: collect all anonymous IDs and their game contexts
        for pbp_file in playbyplay_files:
            try:
                with open(pbp_file, 'r') as f:
                    pbp_data = json.load(f)
                
                game_id = pbp_data.get('metadata', {}).get('game_id', '')
                home_team = pbp_data.get('metadata', {}).get('home_team', '')
                away_team = pbp_data.get('metadata', {}).get('away_team', '')
                
                # Extract date from filename or metadata
                file_date = self._extract_date_from_filename(pbp_file.name)
                
                # Collect anonymous pitcher IDs
                for play in pbp_data.get('plays', []):
                    pitcher_id = play.get('pitcher', '')
                    if pitcher_id and pitcher_id.startswith('Pitcher_'):
                        anonymous_ids.add(pitcher_id)
                        
                        # Store context for this anonymous ID
                        if pitcher_id not in game_contexts:
                            game_contexts[pitcher_id] = []
                        
                        game_contexts[pitcher_id].append({
                            'game_id': game_id,
                            'home_team': home_team,
                            'away_team': away_team,
                            'date': file_date,
                            'inning': play.get('inning', 1),
                            'inning_half': play.get('inning_half', '')
                        })
            
            except Exception as e:
                self.logger.warning(f"Error processing play-by-play file {pbp_file}: {e}")
        
        self.logger.info(f"Found {len(anonymous_ids)} anonymous pitcher IDs to map")
        
        # Second pass: map anonymous IDs to real names
        mapping_results = {}
        
        for anonymous_id in anonymous_ids:
            contexts = game_contexts.get(anonymous_id, [])
            mapping_result = self._resolve_anonymous_id(anonymous_id, contexts)
            
            if mapping_result:
                mapping_results[anonymous_id] = mapping_result
        
        self.anonymous_to_name = mapping_results
        return mapping_results
    
    def _extract_date_from_filename(self, filename: str) -> str:
        """Extract date from play-by-play filename"""
        # Format: TEAM_vs_TEAM_playbyplay_month_day_year_gameId.json
        try:
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 6:
                month = parts[-4]
                day = parts[-3] 
                year = parts[-2]
                
                # Convert month name to number
                month_map = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12'
                }
                
                month_num = month_map.get(month.lower(), '01')
                return f"{year}-{month_num}-{day.zfill(2)}"
                
        except Exception:
            pass
        
        return "unknown"
    
    def _resolve_anonymous_id(self, anonymous_id: str, contexts: List[Dict]) -> Optional[Dict]:
        """
        Resolve anonymous ID to real pitcher name using context analysis
        
        Args:
            anonymous_id: Anonymous pitcher ID like "Pitcher_4346118"
            contexts: List of game contexts where this ID appeared
            
        Returns:
            Mapping result with confidence score, or None if no match
        """
        if not contexts:
            return None
        
        # Extract numeric ID
        numeric_id = anonymous_id.split('_')[-1] if '_' in anonymous_id else anonymous_id
        
        # Strategy 1: Direct numeric ID match in roster
        if numeric_id in self.master_player_map:
            return {
                'real_name': self.master_player_map[numeric_id]['full_name'],
                'short_name': self.master_player_map[numeric_id]['short_name'],
                'team': self.master_player_map[numeric_id]['team'],
                'confidence': 0.95,
                'method': 'direct_id_match',
                'sources': ['roster']
            }
        
        # Strategy 2: Game context matching
        candidate_names = Counter()
        teams_seen = Counter()
        dates_seen = Counter()
        
        # Collect context information first
        for context in contexts:
            game_id = context.get('game_id', '')
            home_team = context.get('home_team', '')
            away_team = context.get('away_team', '')
            date = context.get('date', '')
            inning_half = context.get('inning_half', '')
            
            teams_seen[home_team] += 1
            teams_seen[away_team] += 1 
            dates_seen[date] += 1
        
        # Determine which team this pitcher belongs to based on inning patterns
        pitcher_team = None
        top_innings = sum(1 for ctx in contexts if ctx.get('inning_half') == 'Top')
        bottom_innings = sum(1 for ctx in contexts if ctx.get('inning_half') == 'Bottom')
        
        # If pitcher appears more in bottom innings, they're likely home team
        if bottom_innings > top_innings * 1.5:
            pitcher_team = contexts[0].get('home_team') if contexts else None
        elif top_innings > bottom_innings * 1.5:
            pitcher_team = contexts[0].get('away_team') if contexts else None
        
        # Now match with CSV and lineup data
        most_likely_date = dates_seen.most_common(1)[0][0] if dates_seen else ''
        
        # Strategy 2a: Match with CSV data for same game
        for context_key, csv_info in self.game_context_map.items():
            if csv_info.get('source') == 'csv':
                csv_game_id = csv_info.get('game_id', '')
                csv_team = csv_info.get('team', '')
                
                # Check if this CSV matches our game context
                game_matches = any(ctx.get('game_id') == csv_game_id for ctx in contexts)
                team_matches = (pitcher_team and csv_team == pitcher_team) or csv_team in [ctx.get('home_team', '') for ctx in contexts] or csv_team in [ctx.get('away_team', '') for ctx in contexts]
                
                if game_matches and team_matches:
                    pitcher_name = csv_info.get('name', '')
                    if pitcher_name:
                        # Heavy weight for exact game + team match
                        candidate_names[pitcher_name] += 10.0
        
        # Strategy 2b: Match with lineup data
        for context in contexts:
            game_id = context.get('game_id', '')
            date = context.get('date', '')
            
            # Look for lineup matches
            for context_key, lineup_info in self.game_context_map.items():
                if lineup_info.get('source') != 'csv' and (game_id in context_key or 
                    (date in context_key and pitcher_team and pitcher_team in context_key)):
                    
                    pitcher_name = lineup_info.get('name', '')
                    if pitcher_name:
                        # Weight by context relevance
                        weight = 1.0
                        if game_id and game_id in context_key:
                            weight += 2.0  # Exact game match
                        if date and date in context_key:
                            weight += 1.0  # Date match
                        
                        candidate_names[pitcher_name] += weight
        
        # Strategy 3: Statistical validation
        most_likely_team = teams_seen.most_common(1)[0][0] if teams_seen else ''
        most_likely_date = dates_seen.most_common(1)[0][0] if dates_seen else ''
        
        # Find best candidate
        if candidate_names:
            best_candidate = candidate_names.most_common(1)[0][0]
            candidate_score = candidate_names[best_candidate]
            total_contexts = len(contexts)
            
            # Calculate confidence based on consistency
            confidence = min(0.9, candidate_score / (total_contexts * 2))
            
            # Validate candidate exists in roster
            candidate_lower = best_candidate.lower()
            player_id = self.name_variations.get(candidate_lower)
            
            if player_id and player_id in self.master_player_map:
                player_info = self.master_player_map[player_id]
                
                # Team validation
                if most_likely_team and player_info.get('team') == most_likely_team:
                    confidence += 0.1
                
                return {
                    'real_name': player_info['full_name'],
                    'short_name': player_info['short_name'],
                    'team': player_info['team'],
                    'confidence': min(0.95, confidence),
                    'method': 'context_matching',
                    'sources': ['lineup', 'roster'],
                    'contexts_analyzed': len(contexts),
                    'candidate_score': candidate_score
                }
            else:
                # Name found but not in roster - lower confidence
                return {
                    'real_name': best_candidate,
                    'short_name': best_candidate.split()[-1] if ' ' in best_candidate else best_candidate,
                    'team': most_likely_team,
                    'confidence': min(0.7, confidence),
                    'method': 'context_matching_unverified',
                    'sources': ['lineup'],
                    'contexts_analyzed': len(contexts),
                    'candidate_score': candidate_score
                }
        
        # Strategy 4: Partial matching fallback
        # Look for patterns in numeric ID or other characteristics
        return self._fallback_mapping(anonymous_id, numeric_id, most_likely_team, most_likely_date, len(contexts))
    
    def _fallback_mapping(self, anonymous_id: str, numeric_id: str, team: str, date: str, context_count: int) -> Optional[Dict]:
        """Fallback mapping strategies when direct matching fails"""
        
        # Try substring matching in player IDs
        for player_id, player_info in self.master_player_map.items():
            if (numeric_id in player_id or player_id in numeric_id) and len(numeric_id) > 4:
                return {
                    'real_name': player_info['full_name'],
                    'short_name': player_info['short_name'],
                    'team': player_info['team'],
                    'confidence': 0.4,
                    'method': 'substring_match',
                    'sources': ['roster'],
                    'numeric_id': numeric_id
                }
        
        # Return anonymous ID with context info if available
        if team or date:
            return {
                'real_name': f"Unknown Pitcher ({anonymous_id})",
                'short_name': anonymous_id,
                'team': team,
                'confidence': 0.1,
                'method': 'anonymous_with_context',
                'sources': ['context'],
                'contexts_analyzed': context_count
            }
        
        return None
    
    def get_pitcher_name(self, anonymous_id: str, default: str = None) -> str:
        """
        Get real pitcher name from anonymous ID
        
        Args:
            anonymous_id: Anonymous pitcher ID like "Pitcher_4346118"
            default: Default value if no mapping found
            
        Returns:
            Real pitcher name or default
        """
        mapping = self.anonymous_to_name.get(anonymous_id)
        if mapping:
            return mapping.get('real_name', default or anonymous_id)
        
        return default or anonymous_id
    
    def get_mapping_info(self, anonymous_id: str) -> Optional[Dict]:
        """Get complete mapping information for anonymous ID"""
        return self.anonymous_to_name.get(anonymous_id)
    
    def save_mapping_cache(self, cache_file: str):
        """Save mapping results to cache file for reuse"""
        cache_data = {
            'anonymous_to_name': self.anonymous_to_name,
            'generated_at': datetime.now().isoformat(),
            'total_mappings': len(self.anonymous_to_name),
            'high_confidence_count': len([m for m in self.anonymous_to_name.values() if m.get('confidence', 0) >= 0.8]),
            'mapping_summary': {
                'direct_id_match': len([m for m in self.anonymous_to_name.values() if m.get('method') == 'direct_id_match']),
                'context_matching': len([m for m in self.anonymous_to_name.values() if m.get('method') == 'context_matching']),
                'fallback_methods': len([m for m in self.anonymous_to_name.values() if 'fallback' in m.get('method', '')])
            }
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        self.logger.info(f"Saved mapping cache to {cache_file}")
    
    def load_mapping_cache(self, cache_file: str) -> bool:
        """Load mapping results from cache file"""
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            self.anonymous_to_name = cache_data.get('anonymous_to_name', {})
            self.logger.info(f"Loaded {len(self.anonymous_to_name)} mappings from cache")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not load mapping cache: {e}")
            return False
    
    def generate_mapping_report(self) -> Dict:
        """Generate comprehensive mapping report"""
        total_mappings = len(self.anonymous_to_name)
        if total_mappings == 0:
            return {'error': 'No mappings generated'}
        
        confidence_levels = [m.get('confidence', 0) for m in self.anonymous_to_name.values()]
        methods_used = Counter([m.get('method', 'unknown') for m in self.anonymous_to_name.values()])
        
        high_confidence = len([c for c in confidence_levels if c >= 0.8])
        medium_confidence = len([c for c in confidence_levels if 0.5 <= c < 0.8])
        low_confidence = len([c for c in confidence_levels if c < 0.5])
        
        return {
            'total_anonymous_ids': total_mappings,
            'confidence_breakdown': {
                'high_confidence_80_plus': high_confidence,
                'medium_confidence_50_79': medium_confidence,
                'low_confidence_below_50': low_confidence
            },
            'confidence_percentages': {
                'high': round(high_confidence / total_mappings * 100, 1),
                'medium': round(medium_confidence / total_mappings * 100, 1),
                'low': round(low_confidence / total_mappings * 100, 1)
            },
            'mapping_methods': dict(methods_used),
            'average_confidence': round(sum(confidence_levels) / len(confidence_levels), 3),
            'data_sources_loaded': {
                'roster_entries': len(self.roster_data) if self.roster_data else 0,
                'game_contexts': len(self.game_context_map),
                'name_variations': len(self.name_variations)
            }
        }

def main():
    """Test the mapping system"""
    logging.basicConfig(level=logging.INFO)
    
    mapper = PitcherNameMapper("../BaseballData/data")
    
    # Load all data sources
    mapper.load_all_data_sources()
    
    # Test with sample play-by-play files
    playbyplay_dir = Path("../BaseballData/data/play-by-play")
    if playbyplay_dir.exists():
        pbp_files = list(playbyplay_dir.glob("*_vs_*_playbyplay_*.json"))[:20]  # Sample
        
        print(f"Testing with {len(pbp_files)} play-by-play files...")
        
        # Build mapping
        mapping_results = mapper.build_anonymous_mapping(pbp_files)
        
        # Generate report
        report = mapper.generate_mapping_report()
        print(json.dumps(report, indent=2))
        
        # Show sample mappings
        print("\nSample Mappings:")
        for i, (anon_id, mapping) in enumerate(mapping_results.items()):
            if i >= 10:
                break
            print(f"{anon_id} -> {mapping.get('real_name')} (confidence: {mapping.get('confidence', 0):.2f})")
        
        # Save cache
        mapper.save_mapping_cache("pitcher_mapping_cache.json")
        
    else:
        print("Play-by-play directory not found")

if __name__ == "__main__":
    main()