#!/usr/bin/env python3
"""
Hellraiser Pick Performance Analysis System

Analyzes archived Hellraiser picks to determine:
- Which time periods produce the most successful picks
- How picks change throughout the day (odds movement impact)
- Which pathways (Perfect Storm, Batter-Driven, Pitcher-Driven) are most successful
- Value assessment accuracy (were "Exceptional Value" picks actually good?)
- Player success patterns

This helps refine the Hellraiser methodology and timing strategies.

Usage:
python3 analyze_pick_performance.py                    # Analyze all archived picks
python3 analyze_pick_performance.py --date 2025-06-23  # Specific date
python3 analyze_pick_performance.py --days 7           # Last 7 days
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import argparse

class PickPerformanceAnalyzer:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            script_dir = Path(__file__).parent.absolute()
            self.base_dir = script_dir.parent / "BaseballTracker"
        else:
            self.base_dir = Path(base_dir)
        
        self.archive_dir = self.base_dir / "public" / "data" / "hellraiser" / "archive"
        self.results_dir = self.base_dir / "public" / "data" / "hellraiser" / "performance"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔍 Hellraiser Pick Performance Analyzer")
        print(f"📂 Archive directory: {self.archive_dir}")

    def load_archived_picks(self, date: str = None, days: int = None) -> Dict[str, List[Dict]]:
        """Load archived pick files for analysis"""
        archived_picks = defaultdict(list)
        
        if not self.archive_dir.exists():
            print("❌ Archive directory not found")
            return archived_picks
        
        # Get date range
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            date_range = [target_date]
        elif days:
            end_date = datetime.now().date()
            date_range = [end_date - timedelta(days=i) for i in range(days)]
        else:
            # All available dates
            date_range = None
        
        # Find matching archive files
        for file_path in self.archive_dir.glob("hellraiser_*.json"):
            try:
                # Parse filename: hellraiser_YYYY-MM-DD_HH-MM-SS_run_type.json
                filename = file_path.stem
                parts = filename.split('_')
                if len(parts) >= 3:
                    file_date_str = parts[1]  # YYYY-MM-DD
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                    
                    # Check if file matches date criteria
                    if date_range is None or file_date in date_range:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Extract metadata
                        metadata = {
                            'filename': filename,
                            'date': file_date_str,
                            'timestamp': parts[2] if len(parts) > 2 else 'unknown',
                            'run_type': '_'.join(parts[3:]) if len(parts) > 3 else 'unknown',
                            'archive_metadata': data.get('archiveMetadata', {})
                        }
                        
                        # Add picks with metadata
                        if 'picks' in data and isinstance(data['picks'], list):
                            for pick in data['picks']:
                                pick['_metadata'] = metadata
                            
                            archived_picks[file_date_str].extend(data['picks'])
            
            except Exception as e:
                print(f"⚠️ Error processing {file_path}: {e}")
                continue
        
        total_picks = sum(len(picks) for picks in archived_picks.values())
        print(f"📊 Loaded {total_picks} picks from {len(archived_picks)} days")
        
        return archived_picks

    def analyze_time_patterns(self, archived_picks: Dict[str, List[Dict]]) -> Dict:
        """Analyze which times of day produce different pick patterns"""
        time_analysis = {
            'by_hour': defaultdict(lambda: {'count': 0, 'pathways': defaultdict(int), 'confidence_scores': []}),
            'by_run_type': defaultdict(lambda: {'count': 0, 'avg_confidence': 0, 'pathways': defaultdict(int)})
        }
        
        for date, picks in archived_picks.items():
            for pick in picks:
                metadata = pick.get('_metadata', {})
                run_type = metadata.get('run_type', 'unknown')
                timestamp = metadata.get('timestamp', '00-00-00')
                
                # Extract hour from timestamp (HH-MM-SS)
                try:
                    hour = int(timestamp.split('-')[0])
                except:
                    hour = 0
                
                confidence = pick.get('confidenceScore', 0)
                pathway = pick.get('pathway', 'unknown')
                
                # Time analysis
                time_analysis['by_hour'][hour]['count'] += 1
                time_analysis['by_hour'][hour]['pathways'][pathway] += 1
                time_analysis['by_hour'][hour]['confidence_scores'].append(confidence)
                
                # Run type analysis
                time_analysis['by_run_type'][run_type]['count'] += 1
                time_analysis['by_run_type'][run_type]['pathways'][pathway] += 1
        
        # Calculate averages
        for hour_data in time_analysis['by_hour'].values():
            if hour_data['confidence_scores']:
                hour_data['avg_confidence'] = sum(hour_data['confidence_scores']) / len(hour_data['confidence_scores'])
        
        for run_data in time_analysis['by_run_type'].values():
            # This would need actual results data to calculate avg_confidence properly
            pass
        
        return time_analysis

    def analyze_pick_evolution(self, archived_picks: Dict[str, List[Dict]]) -> Dict:\n        """Analyze how picks change throughout the day"""\n        evolution_analysis = {\n            'player_tracking': defaultdict(list),  # Track same player across different runs\n            'odds_movement': defaultdict(list),    # Track odds changes\n            'confidence_drift': defaultdict(list)  # Track confidence score changes\n        }\n        \n        for date, picks in archived_picks.items():\n            # Group picks by player for each date\n            player_picks = defaultdict(list)\n            \n            for pick in picks:\n                player_name = pick.get('playerName', 'Unknown')\n                metadata = pick.get('_metadata', {})\n                timestamp = metadata.get('timestamp', '00-00-00')\n                \n                player_picks[player_name].append({\n                    'pick': pick,\n                    'timestamp': timestamp,\n                    'metadata': metadata\n                })\n            \n            # Analyze evolution for each player\n            for player, player_data in player_picks.items():\n                if len(player_data) > 1:  # Player appeared in multiple runs\n                    # Sort by timestamp\n                    player_data.sort(key=lambda x: x['timestamp'])\n                    \n                    evolution_analysis['player_tracking'][f\"{date}_{player}\"] = [\n                        {\n                            'timestamp': pd['timestamp'],\n                            'run_type': pd['metadata'].get('run_type', 'unknown'),\n                            'confidence': pd['pick'].get('confidenceScore', 0),\n                            'odds': pd['pick'].get('odds', {}),\n                            'pathway': pd['pick'].get('pathway', 'unknown'),\n                            'market_efficiency': pd['pick'].get('marketEfficiency', {})\n                        }\n                        for pd in player_data\n                    ]\n        \n        return evolution_analysis

    def analyze_pathway_effectiveness(self, archived_picks: Dict[str, List[Dict]]) -> Dict:\n        """Analyze which pathways produce the most confident/successful picks"""\n        pathway_analysis = {\n            'perfectStorm': {'count': 0, 'confidence_scores': [], 'market_assessments': defaultdict(int)},\n            'batterDriven': {'count': 0, 'confidence_scores': [], 'market_assessments': defaultdict(int)},\n            'pitcherDriven': {'count': 0, 'confidence_scores': [], 'market_assessments': defaultdict(int)}\n        }\n        \n        for date, picks in archived_picks.items():\n            for pick in picks:\n                pathway = pick.get('pathway', 'unknown')\n                confidence = pick.get('confidenceScore', 0)\n                market_eff = pick.get('marketEfficiency', {})\n                \n                if pathway in pathway_analysis:\n                    pathway_analysis[pathway]['count'] += 1\n                    pathway_analysis[pathway]['confidence_scores'].append(confidence)\n                    \n                    # Track market assessment\n                    if isinstance(market_eff, dict):\n                        assessment = market_eff.get('assessment', 'Unknown')\n                    else:\n                        assessment = str(market_eff)\n                    \n                    pathway_analysis[pathway]['market_assessments'][assessment] += 1\n        \n        # Calculate averages and insights\n        for pathway, data in pathway_analysis.items():\n            if data['confidence_scores']:\n                data['avg_confidence'] = sum(data['confidence_scores']) / len(data['confidence_scores'])\n                data['max_confidence'] = max(data['confidence_scores'])\n                data['min_confidence'] = min(data['confidence_scores'])\n            else:\n                data['avg_confidence'] = 0\n                data['max_confidence'] = 0\n                data['min_confidence'] = 0\n        \n        return pathway_analysis

    def generate_performance_report(self, analysis_results: Dict) -> str:\n        \"\"\"Generate a comprehensive performance report\"\"\"\n        report_lines = [\n            \"# Hellraiser Pick Performance Analysis Report\",\n            f\"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\",\n            \"\",\n            \"## Time Pattern Analysis\"\n        ]\n        \n        # Time patterns\n        time_analysis = analysis_results.get('time_patterns', {})\n        by_hour = time_analysis.get('by_hour', {})\n        \n        if by_hour:\n            report_lines.extend([\n                \"### Pick Distribution by Hour\",\n                \"| Hour | Pick Count | Avg Confidence | Top Pathway |\",\n                \"|------|------------|----------------|-------------|\"\n            ])\n            \n            for hour in sorted(by_hour.keys()):\n                data = by_hour[hour]\n                avg_conf = data.get('avg_confidence', 0)\n                pathways = data.get('pathways', {})\n                top_pathway = max(pathways.items(), key=lambda x: x[1])[0] if pathways else 'None'\n                \n                report_lines.append(f\"| {hour:02d}:00 | {data['count']} | {avg_conf:.1f} | {top_pathway} |\")\n        \n        # Run type analysis\n        by_run_type = time_analysis.get('by_run_type', {})\n        if by_run_type:\n            report_lines.extend([\n                \"\",\n                \"### Analysis by Run Type\",\n                \"| Run Type | Pick Count | Most Common Pathway |\",\n                \"|----------|------------|--------------------|\"\n            ])\n            \n            for run_type, data in by_run_type.items():\n                pathways = data.get('pathways', {})\n                top_pathway = max(pathways.items(), key=lambda x: x[1])[0] if pathways else 'None'\n                report_lines.append(f\"| {run_type} | {data['count']} | {top_pathway} |\")\n        \n        # Pathway effectiveness\n        pathway_analysis = analysis_results.get('pathway_analysis', {})\n        if pathway_analysis:\n            report_lines.extend([\n                \"\",\n                \"## Pathway Effectiveness Analysis\",\n                \"| Pathway | Count | Avg Confidence | Max Confidence | Top Market Assessment |\",\n                \"|---------|-------|----------------|----------------|-----------------------|\"\n            ])\n            \n            for pathway, data in pathway_analysis.items():\n                assessments = data.get('market_assessments', {})\n                top_assessment = max(assessments.items(), key=lambda x: x[1])[0] if assessments else 'None'\n                \n                report_lines.append(\n                    f\"| {pathway} | {data['count']} | {data['avg_confidence']:.1f} | \"\n                    f\"{data['max_confidence']:.1f} | {top_assessment} |\"\n                )\n        \n        # Pick evolution insights\n        evolution_analysis = analysis_results.get('evolution_analysis', {})\n        player_tracking = evolution_analysis.get('player_tracking', {})\n        \n        if player_tracking:\n            report_lines.extend([\n                \"\",\n                \"## Pick Evolution Insights\",\n                f\"- Found {len(player_tracking)} player instances with multiple daily picks\",\n                \"- This indicates odds/lineup changes affecting analysis throughout the day\"\n            ])\n            \n            # Show some examples\n            example_count = 0\n            for player_key, evolution in player_tracking.items():\n                if example_count >= 3:  # Limit examples\n                    break\n                    \n                if len(evolution) > 1:\n                    date, player = player_key.split('_', 1)\n                    confidence_change = evolution[-1]['confidence'] - evolution[0]['confidence']\n                    \n                    report_lines.append(\n                        f\"- {player} ({date}): {len(evolution)} picks, \"\n                        f\"confidence change: {confidence_change:+.1f}\"\n                    )\n                    example_count += 1\n        \n        # Recommendations\n        report_lines.extend([\n            \"\",\n            \"## Recommendations\",\n            \"Based on this analysis:\"\n        ])\n        \n        # Add specific recommendations based on data\n        if pathway_analysis:\n            best_pathway = max(pathway_analysis.items(), key=lambda x: x[1]['avg_confidence'])[0]\n            report_lines.append(f\"- **{best_pathway}** pathway shows highest average confidence\")\n        \n        if by_hour:\n            peak_hour = max(by_hour.items(), key=lambda x: x[1]['avg_confidence'])[0]\n            report_lines.append(f\"- **{peak_hour:02d}:00** appears to be optimal analysis time\")\n        \n        report_lines.extend([\n            \"- Continue archiving picks to build larger sample size\",\n            \"- Consider weighting analysis runs based on historical performance\",\n            \"- Monitor pick evolution patterns for timing optimization\"\n        ])\n        \n        return \"\\n\".join(report_lines)\n\n    def run_analysis(self, date: str = None, days: int = None) -> Dict:\n        \"\"\"Run complete performance analysis\"\"\"\n        print(f\"🔍 Starting performance analysis...\")\n        \n        # Load archived picks\n        archived_picks = self.load_archived_picks(date, days)\n        \n        if not archived_picks:\n            print(\"❌ No archived picks found\")\n            return {}\n        \n        # Run all analyses\n        analysis_results = {\n            'time_patterns': self.analyze_time_patterns(archived_picks),\n            'evolution_analysis': self.analyze_pick_evolution(archived_picks),\n            'pathway_analysis': self.analyze_pathway_effectiveness(archived_picks),\n            'metadata': {\n                'analysis_date': datetime.now().isoformat(),\n                'date_filter': date,\n                'days_filter': days,\n                'total_days': len(archived_picks),\n                'total_picks': sum(len(picks) for picks in archived_picks.values())\n            }\n        }\n        \n        # Generate report\n        report = self.generate_performance_report(analysis_results)\n        \n        # Save results\n        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n        results_file = self.results_dir / f\"performance_analysis_{timestamp}.json\"\n        report_file = self.results_dir / f\"performance_report_{timestamp}.md\"\n        \n        with open(results_file, 'w') as f:\n            json.dump(analysis_results, f, indent=2, default=str)\n        \n        with open(report_file, 'w') as f:\n            f.write(report)\n        \n        print(f\"✅ Analysis complete!\")\n        print(f\"📊 Results saved: {results_file}\")\n        print(f\"📋 Report saved: {report_file}\")\n        \n        return analysis_results\n\ndef main():\n    parser = argparse.ArgumentParser(description='Analyze Hellraiser pick performance')\n    parser.add_argument('--date', help='Analyze specific date (YYYY-MM-DD)')\n    parser.add_argument('--days', type=int, help='Analyze last N days')\n    parser.add_argument('--base-dir', help='Base directory path')\n    \n    args = parser.parse_args()\n    \n    analyzer = PickPerformanceAnalyzer(args.base_dir)\n    results = analyzer.run_analysis(args.date, args.days)\n    \n    # Print summary\n    if results:\n        metadata = results.get('metadata', {})\n        print(f\"\\n📈 Analysis Summary:\")\n        print(f\"   Total days analyzed: {metadata.get('total_days', 0)}\")\n        print(f\"   Total picks analyzed: {metadata.get('total_picks', 0)}\")\n        \n        pathway_analysis = results.get('pathway_analysis', {})\n        if pathway_analysis:\n            print(f\"\\n🎯 Pathway Performance:\")\n            for pathway, data in pathway_analysis.items():\n                print(f\"   {pathway}: {data['count']} picks, avg confidence {data['avg_confidence']:.1f}\")\n\nif __name__ == \"__main__\":\n    main()