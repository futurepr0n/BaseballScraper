#!/usr/bin/env python3
"""
Daily Weakspot Analysis - Production Script
Generates comprehensive weakspot analysis from all play-by-play data
Designed for integration with daily processing pipeline
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse
from weakspot_analysis_engine import WeakspotAnalysisEngine
from lineup_position_analyzer import add_lineup_analysis_to_engine

class DailyWeakspotAnalyzer:
    def __init__(self, full_analysis=False):
        self.full_analysis = full_analysis
        self.engine = WeakspotAnalysisEngine()
        
    def run_daily_analysis(self):
        """Run the complete daily weakspot analysis"""
        print("🚀 STARTING DAILY WEAKSPOT ANALYSIS")
        print("=" * 60)
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Full analysis mode: {'Yes' if self.full_analysis else 'No (recent games only)'}")
        print("=" * 60)
        
        # Load data based on mode
        if self.full_analysis:
            print("🔄 Loading ALL play-by-play data (full analysis)...")
            self.engine.load_playbyplay_data()
        else:
            print("🔄 Loading recent play-by-play data (quick analysis)...")
            self.engine.load_playbyplay_data(limit_files=500)  # Last ~500 games
            
        if self.engine.games_processed == 0:
            print("❌ No games found to analyze!")
            print("   Check that ../BaseballData/data/play-by-play/ contains JSON files")
            return False
            
        print(f"\n✅ Data loaded successfully!")
        print(f"   📊 Games analyzed: {self.engine.games_processed}")
        print(f"   ⚾ Pitchers tracked: {len(self.engine.pitchers_data)}")
        print(f"   👨‍💼 Batters tracked: {len(self.engine.batters_data)}")
        
        # Generate all analysis reports
        print(f"\n🔍 Running comprehensive analysis...")
        reports = self.engine.generate_analysis_report()
        
        # Add lineup position analysis
        print(f"🎯 Running lineup position analysis...")
        lineup_analyzer, lineup_results = add_lineup_analysis_to_engine(self.engine)
        
        # Generate additional filtering-focused reports
        self._generate_filtering_reports()
        
        # Print summary statistics
        self._print_analysis_summary(reports, lineup_results)
        
        print(f"\n⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 Daily weakspot analysis complete!")
        
        return True
    
    def _generate_filtering_reports(self):
        """Generate additional reports optimized for filtering"""
        print("📝 Generating specialized filtering reports...")
        
        output_dir = Path("../BaseballData/data/weakspot_analysis")
        
        # 1. Top Target Pitchers (worst vulnerabilities across all categories)
        top_targets = self._identify_top_target_pitchers()
        with open(output_dir / 'top_target_pitchers.json', 'w') as f:
            import json
            json.dump({
                'analysis_type': 'top_target_pitchers',
                'timestamp': datetime.now().isoformat(),
                'description': 'Pitchers with multiple exploitable weaknesses',
                'data': top_targets[:25]  # Top 25 targets
            }, f, indent=2, default=str)
        
        # 2. Today's Starter Vulnerabilities (for daily lineup integration)
        starter_vulns = self._analyze_starter_vulnerabilities()
        with open(output_dir / 'starter_vulnerabilities_today.json', 'w') as f:
            import json
            json.dump({
                'analysis_type': 'starter_vulnerabilities',
                'timestamp': datetime.now().isoformat(),
                'description': 'Starting pitcher vulnerabilities for lineup matching',
                'data': starter_vulns
            }, f, indent=2, default=str)
        
        # 3. Situation-Specific Vulnerabilities (clutch spots)
        situational = self._analyze_situational_vulnerabilities()
        with open(output_dir / 'situational_vulnerabilities.json', 'w') as f:
            import json
            json.dump({
                'analysis_type': 'situational_vulnerabilities',
                'timestamp': datetime.now().isoformat(),
                'description': 'High-leverage situation vulnerabilities',
                'data': situational
            }, f, indent=2, default=str)
        
        print("   ✅ Specialized reports generated")
    
    def _identify_top_target_pitchers(self):
        """Identify pitchers with multiple exploitable weaknesses"""
        target_scores = {}
        
        # Score pitchers based on multiple vulnerability types
        for pitcher, data in self.engine.pitchers_data.items():
            score = 0
            vulnerabilities = []
            
            # Check inning vulnerabilities
            for inning_key, plays in data['inning_patterns'].items():
                if len(plays) >= 3:
                    avg_outcome = sum(p['outcome_score'] for p in plays) / len(plays)
                    if avg_outcome < -0.5:
                        score += abs(avg_outcome) * len(plays)
                        vulnerabilities.append(f"Weak in {inning_key}")
            
            # Check count vulnerabilities
            for count, pitches in data['count_patterns'].items():
                if len(pitches) >= 5:
                    outcomes = [self.engine._score_outcome_for_pitcher(p['final_outcome']) for p in pitches]
                    avg_outcome = sum(outcomes) / len(outcomes)
                    if avg_outcome < -0.4:
                        score += abs(avg_outcome) * len(pitches) * 0.5
                        vulnerabilities.append(f"Weak in {count} count")
            
            # Check predictable sequences
            for sequence, outcomes in data['pitch_sequences'].items():
                if len(outcomes) >= 3:
                    avg_outcome = sum(o['outcome_score'] for o in outcomes) / len(outcomes)
                    if avg_outcome < -0.3:
                        score += abs(avg_outcome) * len(outcomes) * 0.3
                        vulnerabilities.append(f"Predictable: {' → '.join(sequence)}")
            
            if score > 5:  # Minimum threshold for targeting
                target_scores[pitcher] = {
                    'total_vulnerability_score': score,
                    'vulnerability_count': len(vulnerabilities),
                    'vulnerabilities': vulnerabilities,
                    'total_appearances': sum(len(plays) for plays in data['inning_patterns'].values())
                }
        
        # Sort by vulnerability score
        return sorted(
            [{'pitcher': p, **stats} for p, stats in target_scores.items()],
            key=lambda x: x['total_vulnerability_score'],
            reverse=True
        )
    
    def _analyze_starter_vulnerabilities(self):
        """Analyze vulnerabilities specific to starting pitchers (early innings)"""
        starter_vulns = {}
        
        for pitcher, data in self.engine.pitchers_data.items():
            # Focus on innings 1-6 for starters
            starter_innings = ['inning_1_top', 'inning_1_bottom', 'inning_2_top', 'inning_2_bottom',
                             'inning_3_top', 'inning_3_bottom', 'inning_4_top', 'inning_4_bottom',
                             'inning_5_top', 'inning_5_bottom', 'inning_6_top', 'inning_6_bottom']
            
            vulnerabilities = {}
            total_starter_plays = 0
            
            for inning in starter_innings:
                if inning in data['inning_patterns'] and len(data['inning_patterns'][inning]) >= 3:
                    plays = data['inning_patterns'][inning]
                    avg_outcome = sum(p['outcome_score'] for p in plays) / len(plays)
                    
                    if avg_outcome < -0.3:  # Vulnerable threshold for starters
                        vulnerabilities[inning] = {
                            'avg_outcome_score': avg_outcome,
                            'appearances': len(plays),
                            'worst_outcomes': [p['outcome'] for p in plays if p['outcome_score'] < -1]
                        }
                    
                    total_starter_plays += len(plays)
            
            # Only include pitchers with meaningful starter data
            if total_starter_plays >= 15 and vulnerabilities:
                starter_vulns[pitcher] = {
                    'vulnerable_starter_innings': vulnerabilities,
                    'total_starter_appearances': total_starter_plays,
                    'starter_vulnerability_rating': sum(abs(v['avg_outcome_score']) * v['appearances'] 
                                                       for v in vulnerabilities.values())
                }
        
        return dict(sorted(starter_vulns.items(), 
                          key=lambda x: x[1]['starter_vulnerability_rating'], 
                          reverse=True)[:30])
    
    def _analyze_situational_vulnerabilities(self):
        """Analyze vulnerabilities in high-leverage situations"""
        situational_vulns = {}
        
        # Focus on high-leverage counts
        clutch_counts = ['3-2', '2-2', '3-1', '2-0', '0-2']
        
        for pitcher, data in self.engine.pitchers_data.items():
            clutch_performance = {}
            
            for count in clutch_counts:
                if count in data['count_patterns'] and len(data['count_patterns'][count]) >= 4:
                    pitches = data['count_patterns'][count]
                    outcomes = [self.engine._score_outcome_for_pitcher(p['final_outcome']) for p in pitches]
                    avg_outcome = sum(outcomes) / len(outcomes)
                    
                    if avg_outcome < -0.3:
                        clutch_performance[count] = {
                            'avg_outcome_score': avg_outcome,
                            'pitch_count': len(pitches),
                            'common_pitch_types': self._get_common_elements([p['pitch_type'] for p in pitches], 2),
                            'bad_outcomes': [p['final_outcome'] for p in pitches 
                                           if self.engine._score_outcome_for_pitcher(p['final_outcome']) < -1]
                        }
            
            if clutch_performance:
                situational_vulns[pitcher] = {
                    'clutch_vulnerabilities': clutch_performance,
                    'clutch_vulnerability_score': sum(abs(v['avg_outcome_score']) * v['pitch_count'] 
                                                     for v in clutch_performance.values())
                }
        
        return dict(sorted(situational_vulns.items(),
                          key=lambda x: x[1]['clutch_vulnerability_score'],
                          reverse=True)[:20])
    
    def _get_common_elements(self, items, top_n=2):
        """Get most common elements from a list"""
        from collections import Counter
        return Counter(items).most_common(top_n)
    
    def _print_analysis_summary(self, reports, lineup_results=None):
        """Print comprehensive analysis summary"""
        print(f"\n📊 DAILY ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"🎯 Inning Vulnerabilities: {len(reports['inning_vulnerabilities'])} pitchers")
        print(f"🔮 Predictable Patterns: {len(reports['pitch_predictability'])} pitchers")
        print(f"📊 Count Weaknesses: {len(reports['count_vulnerabilities'])} pitchers")
        if lineup_results:
            print(f"🏟️ Lineup Vulnerabilities: {lineup_results['vulnerability_rankings']} pitchers")
            print(f"⚾ Batter Optimizations: {lineup_results['batter_optimizations']} batters")
        print(f"📈 Games Analyzed: {reports['games_analyzed']}")
        print(f"⚾ Total Pitchers: {reports['pitchers_analyzed']}")
        print(f"👨‍💼 Total Batters: {reports['batters_analyzed']}")
        
        print(f"\n📁 Files Generated:")
        output_dir = Path("../BaseballData/data/weakspot_analysis")
        json_files = list(output_dir.glob("*.json"))
        for file in json_files:
            file_size_kb = file.stat().st_size / 1024
            print(f"   📄 {file.name} ({file_size_kb:.1f} KB)")
        
        print(f"\n🎯 TOP RECOMMENDATIONS FOR TODAY:")
        print("   1. Check 'top_target_pitchers.json' for high-value targets")
        print("   2. Review 'starter_vulnerabilities_today.json' for lineup matching")
        print("   3. Use 'situational_vulnerabilities.json' for clutch spots")
        print("   4. Review 'lineup_vulnerability_rankings.json' for position-specific targets")
        print("   5. Check 'batter_lineup_optimization.json' for optimal batting order")
        print("   6. Apply findings to daily predictions and strategy")
        print("=" * 60)

def main():
    """Main execution with command line options"""
    parser = argparse.ArgumentParser(description='Daily Weakspot Analysis')
    parser.add_argument('--full', action='store_true', 
                       help='Run full analysis on all data (slower)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick analysis on recent games (faster)')
    
    args = parser.parse_args()
    
    # Default to quick analysis unless specified
    full_analysis = args.full or not args.quick
    
    analyzer = DailyWeakspotAnalyzer(full_analysis=full_analysis)
    success = analyzer.run_daily_analysis()
    
    if success:
        print("\n✅ Analysis complete! Ready for daily predictions.")
        sys.exit(0)
    else:
        print("\n❌ Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()