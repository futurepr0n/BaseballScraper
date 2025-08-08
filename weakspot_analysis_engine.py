#!/usr/bin/env python3
"""
Comprehensive Weakspot Analysis Engine
Analyzes pitcher vulnerabilities, batter matchups, and situational patterns from play-by-play data
"""

import json
import glob
from pathlib import Path
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np

class WeakspotAnalysisEngine:
    def __init__(self, data_dir="../BaseballData/data/play-by-play"):
        self.data_dir = Path(data_dir)
        self.pitchers_data = defaultdict(lambda: {
            'inning_patterns': defaultdict(list),
            'count_patterns': defaultdict(list), 
            'pitch_sequences': defaultdict(list),
            'outcomes_allowed': defaultdict(list),
            'pitch_type_usage': defaultdict(list),
            'velocity_patterns': defaultdict(list)
        })
        self.batters_data = defaultdict(lambda: {
            'vs_pitch_types': defaultdict(list),
            'lineup_position_performance': defaultdict(list),
            'count_success': defaultdict(list)
        })
        self.matchup_data = []
        self.games_processed = 0
        
    def load_playbyplay_data(self, limit_files=None):
        """Load all play-by-play data files"""
        print("🔄 Loading play-by-play data...")
        
        json_files = list(self.data_dir.glob("*.json"))
        
        if limit_files:
            json_files = json_files[:limit_files]
            
        print(f"📊 Found {len(json_files)} play-by-play files")
        
        for i, file_path in enumerate(json_files, 1):
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                
                self._process_game_data(game_data, file_path.name)
                self.games_processed += 1
                
                if i % 100 == 0:
                    print(f"   Processed {i}/{len(json_files)} files...")
                    
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                continue
        
        print(f"✅ Loaded {self.games_processed} games successfully")
        print(f"📈 Tracking {len(self.pitchers_data)} pitchers and {len(self.batters_data)} batters")
        
    def _process_game_data(self, game_data, filename):
        """Process individual game data and extract weakspot patterns"""
        plays = game_data.get('plays', [])
        metadata = game_data.get('metadata', {})
        
        # Extract lineup order from play sequence
        lineup_orders = {}  # batter -> first appearance order
        current_order = 1
        seen_batters = set()
        
        for play in plays:
            batter = play.get('batter', '').strip()
            pitcher = play.get('pitcher', '').strip()
            inning = play.get('inning', 0)
            inning_half = play.get('inning_half', '')
            
            # Skip if essential data missing
            if not batter or not pitcher or batter.startswith(('Batter_', 'Pitcher_')):
                continue
                
            # Track lineup order (approximation based on first appearance)
            if inning_half == 'Top' and batter not in seen_batters:
                lineup_orders[batter] = current_order
                seen_batters.add(batter)
                current_order += 1
                if current_order > 9:  # Reset after 9 batters
                    current_order = 1
                    
            # Extract detailed play data
            play_result = play.get('play_result', '')
            pitch_sequence = play.get('pitch_sequence', [])
            
            # Process pitcher patterns
            self._analyze_pitcher_patterns(pitcher, play, inning, inning_half, filename)
            
            # Process batter patterns
            self._analyze_batter_patterns(batter, play, lineup_orders.get(batter, 0))
            
            # Store matchup data for cross-analysis
            self.matchup_data.append({
                'pitcher': pitcher,
                'batter': batter,
                'inning': inning,
                'inning_half': inning_half,
                'result': play_result,
                'pitch_count': len(pitch_sequence),
                'filename': filename,
                'lineup_position': lineup_orders.get(batter, 0)
            })
    
    def _analyze_pitcher_patterns(self, pitcher, play, inning, inning_half, filename):
        """Analyze pitcher-specific vulnerability patterns"""
        pitch_sequence = play.get('pitch_sequence', [])
        play_result = play.get('play_result', '')
        
        # Inning patterns - track performance by inning
        inning_key = f"inning_{inning}_{inning_half.lower()}"
        outcome_value = self._score_outcome_for_pitcher(play_result)
        self.pitchers_data[pitcher]['inning_patterns'][inning_key].append({
            'outcome': play_result,
            'outcome_score': outcome_value,
            'pitch_count': len(pitch_sequence),
            'filename': filename
        })
        
        # Count-based patterns
        for i, pitch in enumerate(pitch_sequence):
            count_key = f"{pitch.get('balls', 0)}-{pitch.get('strikes', 0)}"
            pitch_type = pitch.get('pitch_type', 'Unknown')
            velocity = pitch.get('velocity', 0)
            pitch_result = pitch.get('result', '')
            
            self.pitchers_data[pitcher]['count_patterns'][count_key].append({
                'pitch_type': pitch_type,
                'velocity': velocity,
                'result': pitch_result,
                'final_outcome': play_result,
                'pitch_in_sequence': i + 1
            })
            
            # Track pitch type usage patterns
            self.pitchers_data[pitcher]['pitch_type_usage'][pitch_type].append({
                'count': count_key,
                'velocity': velocity,
                'result': pitch_result,
                'inning': inning
            })
        
        # Pitch sequences for predictability analysis
        sequence = [p.get('pitch_type', 'Unknown') for p in pitch_sequence]
        if len(sequence) >= 2:
            self.pitchers_data[pitcher]['pitch_sequences'][tuple(sequence)].append({
                'outcome': play_result,
                'outcome_score': outcome_value,
                'inning': inning
            })
    
    def _analyze_batter_patterns(self, batter, play, lineup_position):
        """Analyze batter-specific success patterns"""
        pitch_sequence = play.get('pitch_sequence', [])
        play_result = play.get('play_result', '')
        
        # Success vs pitch types
        for pitch in pitch_sequence:
            pitch_type = pitch.get('pitch_type', 'Unknown')
            pitch_result = pitch.get('result', '')
            
            success_score = self._score_outcome_for_batter(play_result)
            self.batters_data[batter]['vs_pitch_types'][pitch_type].append({
                'result': play_result,
                'success_score': success_score,
                'pitch_result': pitch_result,
                'velocity': pitch.get('velocity', 0)
            })
        
        # Lineup position performance
        if lineup_position > 0:
            success_score = self._score_outcome_for_batter(play_result)
            self.batters_data[batter]['lineup_position_performance'][f"position_{lineup_position}"].append({
                'result': play_result,
                'success_score': success_score,
                'pitch_count': len(pitch_sequence)
            })
    
    def _score_outcome_for_pitcher(self, outcome):
        """Score outcomes from pitcher's perspective (lower is better for pitcher)"""
        outcome_scores = {
            'Single': -1,
            'Double': -2, 
            'Triple': -3,
            'Home Run': -4,
            'Walk': -1,
            'Hit By Pitch': -1,
            'Strikeout': 2,
            'Flyout': 1,
            'Groundout': 1,
            'Popout': 1,
            'Lineout': 0,
            'Foulout': 1,
            'Error': -0.5
        }
        return outcome_scores.get(outcome, 0)
    
    def _score_outcome_for_batter(self, outcome):
        """Score outcomes from batter's perspective (higher is better for batter)"""
        outcome_scores = {
            'Single': 1,
            'Double': 2,
            'Triple': 3, 
            'Home Run': 4,
            'Walk': 0.5,
            'Hit By Pitch': 0.5,
            'Strikeout': -2,
            'Flyout': -1,
            'Groundout': -1,
            'Popout': -1,
            'Lineout': -0.5,
            'Foulout': -1,
            'Error': 0.5
        }
        return outcome_scores.get(outcome, 0)

    def analyze_pitcher_inning_vulnerabilities(self, min_appearances=5):
        """Find pitchers with specific inning weaknesses"""
        print("🎯 Analyzing pitcher inning vulnerabilities...")
        
        vulnerabilities = []
        
        for pitcher, data in self.pitchers_data.items():
            inning_stats = {}
            
            for inning_key, plays in data['inning_patterns'].items():
                if len(plays) < min_appearances:
                    continue
                    
                avg_outcome = np.mean([p['outcome_score'] for p in plays])
                total_plays = len(plays)
                
                # Negative scores are bad for pitcher
                if avg_outcome < -0.5:  # Threshold for vulnerability
                    inning_stats[inning_key] = {
                        'avg_outcome_score': avg_outcome,
                        'total_plays': total_plays,
                        'outcomes': [p['outcome'] for p in plays]
                    }
            
            if inning_stats:
                vulnerabilities.append({
                    'pitcher': pitcher,
                    'vulnerable_innings': inning_stats,
                    'total_appearances': sum(len(plays) for plays in data['inning_patterns'].values())
                })
        
        # Sort by severity of vulnerability
        vulnerabilities.sort(key=lambda x: min(v['avg_outcome_score'] for v in x['vulnerable_innings'].values()))
        
        return vulnerabilities
    
    def analyze_pitch_predictability(self, min_sequences=3):
        """Find predictable pitch sequence patterns"""
        print("🔍 Analyzing pitch predictability patterns...")
        
        predictable_patterns = []
        
        for pitcher, data in self.pitchers_data.items():
            pattern_stats = {}
            
            for sequence, outcomes in data['pitch_sequences'].items():
                if len(outcomes) < min_sequences:
                    continue
                    
                # Calculate how often this sequence leads to poor outcomes for pitcher
                avg_outcome = np.mean([o['outcome_score'] for o in outcomes])
                frequency = len(outcomes)
                
                # Patterns that frequently lead to hits are predictable weaknesses
                if avg_outcome < -0.3 and frequency >= min_sequences:
                    pattern_stats[' → '.join(sequence)] = {
                        'frequency': frequency,
                        'avg_outcome_score': avg_outcome,
                        'outcomes': [o['outcome'] for o in outcomes]
                    }
            
            if pattern_stats:
                predictable_patterns.append({
                    'pitcher': pitcher,
                    'predictable_sequences': pattern_stats,
                    'total_sequences': len(data['pitch_sequences'])
                })
        
        # Sort by predictability (frequency × poor outcome)
        predictable_patterns.sort(key=lambda x: sum(
            p['frequency'] * abs(p['avg_outcome_score']) 
            for p in x['predictable_sequences'].values()
        ), reverse=True)
        
        return predictable_patterns
    
    def analyze_count_vulnerabilities(self, min_counts=5):
        """Find pitcher weaknesses in specific counts"""
        print("📊 Analyzing count-based vulnerabilities...")
        
        count_weaknesses = []
        
        for pitcher, data in self.pitchers_data.items():
            count_stats = {}
            
            for count, pitches in data['count_patterns'].items():
                if len(pitches) < min_counts:
                    continue
                
                # Calculate average outcome in this count
                final_outcomes = [p['final_outcome'] for p in pitches]
                outcome_scores = [self._score_outcome_for_pitcher(outcome) for outcome in final_outcomes]
                avg_outcome = np.mean(outcome_scores)
                
                # Find counts where pitcher struggles
                if avg_outcome < -0.4:
                    count_stats[count] = {
                        'avg_outcome_score': avg_outcome,
                        'pitch_count': len(pitches),
                        'most_common_pitch': Counter([p['pitch_type'] for p in pitches]).most_common(1)[0],
                        'outcomes': final_outcomes
                    }
            
            if count_stats:
                count_weaknesses.append({
                    'pitcher': pitcher,
                    'weak_counts': count_stats,
                    'total_pitches': sum(len(pitches) for pitches in data['count_patterns'].values())
                })
        
        # Sort by severity of count weaknesses
        count_weaknesses.sort(key=lambda x: min(w['avg_outcome_score'] for w in x['weak_counts'].values()))
        
        return count_weaknesses
    
    def generate_analysis_report(self, output_dir="../BaseballData/data/weakspot_analysis"):
        """Generate comprehensive weakspot analysis reports"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"📝 Generating analysis reports in {output_path}...")
        
        # Generate individual analysis reports
        inning_vulns = self.analyze_pitcher_inning_vulnerabilities()
        predictable = self.analyze_pitch_predictability()
        count_vulns = self.analyze_count_vulnerabilities()
        
        reports = {
            'inning_vulnerabilities': inning_vulns[:50],  # Top 50
            'pitch_predictability': predictable[:30],     # Top 30
            'count_vulnerabilities': count_vulns[:40],    # Top 40
            'generation_timestamp': datetime.now().isoformat(),
            'games_analyzed': self.games_processed,
            'pitchers_analyzed': len(self.pitchers_data),
            'batters_analyzed': len(self.batters_data)
        }
        
        # Save comprehensive report
        with open(output_path / 'weakspot_analysis_comprehensive.json', 'w') as f:
            json.dump(reports, f, indent=2, default=str)
        
        # Save individual focused reports for filtering
        with open(output_path / 'inning_vulnerabilities.json', 'w') as f:
            json.dump({
                'analysis_type': 'inning_vulnerabilities',
                'timestamp': datetime.now().isoformat(),
                'data': inning_vulns
            }, f, indent=2, default=str)
            
        with open(output_path / 'pitch_predictability.json', 'w') as f:
            json.dump({
                'analysis_type': 'pitch_predictability', 
                'timestamp': datetime.now().isoformat(),
                'data': predictable
            }, f, indent=2, default=str)
            
        with open(output_path / 'count_vulnerabilities.json', 'w') as f:
            json.dump({
                'analysis_type': 'count_vulnerabilities',
                'timestamp': datetime.now().isoformat(), 
                'data': count_vulns
            }, f, indent=2, default=str)
        
        print(f"✅ Generated {len(reports)} analysis reports")
        return reports
    
    def print_summary(self):
        """Print analysis summary to console"""
        print("\n" + "="*60)
        print("📊 WEAKSPOT ANALYSIS ENGINE SUMMARY")
        print("="*60)
        print(f"🎮 Games processed: {self.games_processed}")
        print(f"⚾ Pitchers analyzed: {len(self.pitchers_data)}")
        print(f"👨‍💼 Batters analyzed: {len(self.batters_data)}")
        print(f"🎭 Total matchups: {len(self.matchup_data)}")
        
        # Sample top findings
        print(f"\n🎯 Top Analysis Categories Available:")
        print(f"   📅 Inning Vulnerability Analysis")
        print(f"   🔮 Pitch Sequence Predictability")
        print(f"   📊 Count-Based Weaknesses")
        print(f"   🏟️ Situational Pattern Analysis")
        
        print("\n💾 Ready for JSON export and frontend integration")
        print("="*60)

def main():
    """Main execution function"""
    print("🚀 STARTING WEAKSPOT ANALYSIS ENGINE")
    print("="*60)
    
    # Initialize engine
    engine = WeakspotAnalysisEngine()
    
    # Load data (can limit for testing)
    engine.load_playbyplay_data(limit_files=None)  # Set to 50 for testing
    
    # Generate reports
    reports = engine.generate_analysis_report()
    
    # Print summary
    engine.print_summary()
    
    print("\n🎉 Analysis complete! Check ../BaseballData/data/weakspot_analysis/ for results")

if __name__ == "__main__":
    main()