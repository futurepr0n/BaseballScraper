#!/usr/bin/env python3
"""
Simple Hellraiser Performance Analyzer

A simplified version that analyzes archived Hellraiser picks.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import argparse

class SimplePerformanceAnalyzer:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            script_dir = Path(__file__).parent.absolute()
            self.base_dir = script_dir.parent / "BaseballTracker"
        else:
            self.base_dir = Path(base_dir)
        
        self.archive_dir = self.base_dir / "public" / "data" / "hellraiser" / "archive"
        self.results_dir = self.base_dir / "public" / "data" / "hellraiser" / "performance"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔍 Simple Hellraiser Performance Analyzer")

    def load_archived_picks(self, days: int = 7) -> List[Dict]:
        """Load recent archived pick files"""
        all_picks = []
        
        if not self.archive_dir.exists():
            print("❌ Archive directory not found")
            return all_picks
        
        # Find archive files from last N days
        for file_path in self.archive_dir.glob("hellraiser_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if 'picks' in data and isinstance(data['picks'], list):
                    for pick in data['picks']:
                        pick['_archive_file'] = file_path.name
                    all_picks.extend(data['picks'])
                    
            except Exception as e:
                print(f"⚠️ Error processing {file_path}: {e}")
                continue
        
        print(f"📊 Loaded {len(all_picks)} total picks from archive")
        return all_picks

    def analyze_pathways(self, picks: List[Dict]) -> Dict:
        """Analyze pathway effectiveness"""
        pathway_stats = defaultdict(lambda: {
            'count': 0, 
            'confidence_scores': [], 
            'players': set()
        })
        
        for pick in picks:
            pathway = pick.get('pathway', 'unknown')
            confidence = pick.get('confidenceScore', 0)
            player = pick.get('playerName', 'Unknown')
            
            pathway_stats[pathway]['count'] += 1
            pathway_stats[pathway]['confidence_scores'].append(confidence)
            pathway_stats[pathway]['players'].add(player)
        
        # Calculate averages
        for pathway, stats in pathway_stats.items():
            if stats['confidence_scores']:
                stats['avg_confidence'] = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
                stats['max_confidence'] = max(stats['confidence_scores'])
            else:
                stats['avg_confidence'] = 0
                stats['max_confidence'] = 0
            stats['unique_players'] = len(stats['players'])
            stats['players'] = list(stats['players'])  # Convert set to list for JSON serialization
        
        return dict(pathway_stats)

    def analyze_top_players(self, picks: List[Dict]) -> Dict:
        """Analyze most frequently picked players"""
        player_stats = defaultdict(lambda: {
            'count': 0,
            'confidence_scores': [],
            'pathways': defaultdict(int)
        })
        
        for pick in picks:
            player = pick.get('playerName', 'Unknown')
            confidence = pick.get('confidenceScore', 0)
            pathway = pick.get('pathway', 'unknown')
            
            player_stats[player]['count'] += 1
            player_stats[player]['confidence_scores'].append(confidence)
            player_stats[player]['pathways'][pathway] += 1
        
        # Calculate averages and sort by frequency
        for player, stats in player_stats.items():
            if stats['confidence_scores']:
                stats['avg_confidence'] = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
            else:
                stats['avg_confidence'] = 0
            stats['pathways'] = dict(stats['pathways'])
        
        # Return top 20 most picked players
        sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        return dict(sorted_players[:20])

    def generate_summary_report(self, pathway_analysis: Dict, player_analysis: Dict) -> str:
        """Generate a simple summary report"""
        report_lines = [
            "# Hellraiser Performance Summary",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Pathway Analysis"
        ]
        
        if pathway_analysis:
            report_lines.extend([
                "| Pathway | Pick Count | Avg Confidence | Unique Players |",
                "|---------|------------|----------------|----------------|"
            ])
            
            for pathway, stats in pathway_analysis.items():
                report_lines.append(
                    f"| {pathway} | {stats['count']} | {stats['avg_confidence']:.1f} | {stats['unique_players']} |"
                )
        
        report_lines.extend([
            "",
            "## Top Players (by pick frequency)"
        ])
        
        if player_analysis:
            report_lines.extend([
                "| Player | Pick Count | Avg Confidence | Top Pathway |",
                "|--------|------------|----------------|-------------|"
            ])
            
            for player, stats in list(player_analysis.items())[:10]:  # Top 10
                top_pathway = max(stats['pathways'].items(), key=lambda x: x[1])[0] if stats['pathways'] else 'None'
                report_lines.append(
                    f"| {player} | {stats['count']} | {stats['avg_confidence']:.1f} | {top_pathway} |"
                )
        
        return "\n".join(report_lines)

    def run_analysis(self, days: int = 7) -> Dict:
        """Run simplified performance analysis"""
        print(f"🔍 Starting performance analysis for last {days} days...")
        
        picks = self.load_archived_picks(days)
        
        if not picks:
            print("❌ No archived picks found")
            return {}
        
        pathway_analysis = self.analyze_pathways(picks)
        player_analysis = self.analyze_top_players(picks)
        
        results = {
            'pathway_analysis': pathway_analysis,
            'player_analysis': player_analysis,
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'days_analyzed': days,
                'total_picks': len(picks)
            }
        }
        
        # Generate report
        report = self.generate_summary_report(pathway_analysis, player_analysis)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"simple_analysis_{timestamp}.json"
        report_file = self.results_dir / f"simple_report_{timestamp}.md"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"✅ Analysis complete!")
        print(f"📊 Results saved: {results_file}")
        print(f"📋 Report saved: {report_file}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Simple Hellraiser pick performance analysis')
    parser.add_argument('--days', type=int, default=7, help='Analyze last N days (default: 7)')
    parser.add_argument('--base-dir', help='Base directory path')
    
    args = parser.parse_args()
    
    analyzer = SimplePerformanceAnalyzer(args.base_dir)
    results = analyzer.run_analysis(args.days)
    
    if results:
        metadata = results.get('metadata', {})
        print(f"\n📈 Analysis Summary:")
        print(f"   Total picks analyzed: {metadata.get('total_picks', 0)}")
        
        pathway_analysis = results.get('pathway_analysis', {})
        if pathway_analysis:
            print(f"\n🎯 Pathway Performance:")
            for pathway, data in pathway_analysis.items():
                print(f"   {pathway}: {data['count']} picks, avg confidence {data['avg_confidence']:.1f}")

if __name__ == "__main__":
    main()