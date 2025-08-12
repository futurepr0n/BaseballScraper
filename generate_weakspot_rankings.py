#!/usr/bin/env python3
"""
Weakspot Rankings Generator
==========================

Generates pre-processed JSON files for fast loading of different weakspot analysis types.
This script creates filterable rankings for:
- Lineup Position Vulnerabilities
- Inning-Specific Patterns  
- Pitch Pattern Predictability
- Overall Weakspot Scores

Designed to run daily/hourly to update rankings as new data becomes available.

Author: BaseballScraper Enhancement System
Date: August 2025
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging
import argparse
from typing import Dict, List, Optional, Tuple, Any

# Add the BaseballScraper directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weakspot_analyzer import WeakspotAnalyzer

class WeakspotRankingsGenerator:
    """Generates comprehensive weakspot rankings for fast frontend loading"""
    
    def __init__(self, base_data_path: str, output_path: str):
        self.base_data_path = Path(base_data_path)
        self.output_path = Path(output_path)
        self.analyzer = WeakspotAnalyzer(base_data_path)
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_lineup_vulnerability_rankings(self, date_range=None) -> str:
        """
        Generate lineup position vulnerability rankings
        
        Args:
            date_range: Optional tuple of (start_date, end_date)
        
        Returns:
            Path to generated JSON file
        """
        self.logger.info("Generating lineup vulnerability rankings...")
        
        rankings = self.analyzer.generate_filterable_rankings('lineup', date_range)
        
        # Enhance with additional analysis
        enhanced_rankings = {
            **rankings,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "lineup_vulnerabilities",
                "description": "Pitcher vulnerability to specific batting order positions",
                "filters_available": [
                    "position_1_through_9",
                    "vulnerability_score",
                    "sample_size",
                    "confidence_level"
                ]
            },
            "summary_stats": self._calculate_summary_stats(rankings.get('rankings', []), 'lineup')
        }
        
        # Add position-specific insights
        for pitcher_data in enhanced_rankings.get('rankings', []):
            position_breakdowns = pitcher_data.get('position_breakdowns', {})
            
            # Find most vulnerable position
            most_vulnerable_pos = None
            max_score = 0
            for pos, data in position_breakdowns.items():
                if data.get('vulnerability_score', 0) > max_score:
                    max_score = data.get('vulnerability_score', 0)
                    most_vulnerable_pos = pos
            
            pitcher_data['most_vulnerable_position'] = most_vulnerable_pos
            pitcher_data['vulnerability_summary'] = f"Most vulnerable to {most_vulnerable_pos} with {max_score}% weakness score"
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_path / f"lineup_vulnerability_rankings_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        # Also create a "latest" version for easy access
        latest_file = self.output_path / "lineup_vulnerability_rankings_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        self.logger.info(f"Lineup vulnerability rankings saved to {output_file}")
        return str(output_file)
    
    def generate_inning_pattern_rankings(self, date_range=None) -> str:
        """
        Generate inning-specific pattern rankings
        
        Args:
            date_range: Optional tuple of (start_date, end_date)
        
        Returns:
            Path to generated JSON file
        """
        self.logger.info("Generating inning pattern rankings...")
        
        rankings = self.analyzer.generate_filterable_rankings('inning', date_range)
        
        # Enhance with additional analysis
        enhanced_rankings = {
            **rankings,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "inning_patterns",
                "description": "Pitcher weakness patterns by inning (fatigue, adjustment periods)",
                "filters_available": [
                    "inning_1_through_9",
                    "vulnerability_score", 
                    "velocity_decline",
                    "pitch_count_stress"
                ]
            },
            "summary_stats": self._calculate_summary_stats(rankings.get('rankings', []), 'inning')
        }
        
        # Add inning-specific insights
        for pitcher_data in enhanced_rankings.get('rankings', []):
            inning_breakdowns = pitcher_data.get('inning_breakdowns', {})
            
            # Find most vulnerable inning
            most_vulnerable_inning = None
            max_score = 0
            for inning, data in inning_breakdowns.items():
                if data.get('vulnerability_score', 0) > max_score:
                    max_score = data.get('vulnerability_score', 0)
                    most_vulnerable_inning = inning
            
            # Analyze fatigue patterns
            velocity_decline = self._calculate_velocity_decline(inning_breakdowns)
            
            pitcher_data['most_vulnerable_inning'] = most_vulnerable_inning
            pitcher_data['velocity_decline_pattern'] = velocity_decline
            pitcher_data['fatigue_indicator'] = "High" if velocity_decline > 2.0 else "Moderate" if velocity_decline > 1.0 else "Low"
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_path / f"inning_pattern_rankings_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        # Also create a "latest" version for easy access
        latest_file = self.output_path / "inning_pattern_rankings_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        self.logger.info(f"Inning pattern rankings saved to {output_file}")
        return str(output_file)
    
    def generate_pitch_pattern_rankings(self, date_range=None) -> str:
        """
        Generate pitch pattern predictability rankings
        
        Args:
            date_range: Optional tuple of (start_date, end_date)
        
        Returns:
            Path to generated JSON file
        """
        self.logger.info("Generating pitch pattern rankings...")
        
        rankings = self.analyzer.generate_filterable_rankings('patterns', date_range)
        
        # Enhance with additional analysis  
        enhanced_rankings = {
            **rankings,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "pitch_patterns",
                "description": "Pitcher predictability based on pitch sequence patterns",
                "filters_available": [
                    "predictability_score",
                    "sequence_frequency",
                    "count_patterns",
                    "total_sequences"
                ]
            },
            "summary_stats": self._calculate_summary_stats(rankings.get('rankings', []), 'patterns')
        }
        
        # Add pattern-specific insights
        for pitcher_data in enhanced_rankings.get('rankings', []):
            pattern_details = pitcher_data.get('pattern_details', {})
            
            # Find most predictable sequence
            sequence_patterns = pattern_details.get('sequence_patterns', {})
            most_common_sequence = max(sequence_patterns, key=sequence_patterns.get) if sequence_patterns else None
            
            # Analyze count-based predictability
            count_patterns = pattern_details.get('count_patterns', {})
            predictable_counts = []
            for count, pitches in count_patterns.items():
                if pitches:
                    most_common_pitch = max(pitches, key=pitches.get)
                    frequency = pitches[most_common_pitch] / sum(pitches.values())
                    if frequency > 0.7:  # 70%+ predictability threshold
                        predictable_counts.append({
                            "count": count,
                            "pitch_type": most_common_pitch,
                            "frequency": round(frequency, 3)
                        })
            
            pitcher_data['most_common_sequence'] = most_common_sequence
            pitcher_data['predictable_counts'] = predictable_counts
            pitcher_data['exploitation_potential'] = "High" if len(predictable_counts) >= 3 else "Moderate" if len(predictable_counts) >= 1 else "Low"
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_path / f"pitch_pattern_rankings_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        # Also create a "latest" version for easy access
        latest_file = self.output_path / "pitch_pattern_rankings_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        self.logger.info(f"Pitch pattern rankings saved to {output_file}")
        return str(output_file)
    
    def generate_overall_weakspot_rankings(self, date_range=None) -> str:
        """
        Generate comprehensive overall weakspot rankings
        
        Args:
            date_range: Optional tuple of (start_date, end_date)
        
        Returns:
            Path to generated JSON file
        """
        self.logger.info("Generating overall weakspot rankings...")
        
        # Get all analysis types
        lineup_rankings = self.analyzer.generate_filterable_rankings('lineup', date_range)
        inning_rankings = self.analyzer.generate_filterable_rankings('inning', date_range)
        pattern_rankings = self.analyzer.generate_filterable_rankings('patterns', date_range)
        
        # Combine into comprehensive rankings
        combined_analysis = {}
        
        # Process lineup vulnerabilities
        for pitcher_data in lineup_rankings.get('rankings', []):
            pitcher = pitcher_data['pitcher']
            if pitcher not in combined_analysis:
                combined_analysis[pitcher] = {'pitcher': pitcher}
            
            combined_analysis[pitcher]['lineup_vulnerability'] = {
                'max_score': pitcher_data.get('max_vulnerability_score', 0),
                'positions_analyzed': len(pitcher_data.get('position_breakdowns', {})),
                'sample_size': pitcher_data.get('total_sample_size', 0)
            }
        
        # Process inning patterns
        for pitcher_data in inning_rankings.get('rankings', []):
            pitcher = pitcher_data['pitcher']
            if pitcher not in combined_analysis:
                combined_analysis[pitcher] = {'pitcher': pitcher}
            
            combined_analysis[pitcher]['inning_vulnerability'] = {
                'max_score': pitcher_data.get('max_vulnerability_score', 0),
                'innings_analyzed': len(pitcher_data.get('inning_breakdowns', {})),
                'sample_size': pitcher_data.get('total_sample_size', 0)
            }
        
        # Process pitch patterns
        for pitcher_data in pattern_rankings.get('rankings', []):
            pitcher = pitcher_data['pitcher']
            if pitcher not in combined_analysis:
                combined_analysis[pitcher] = {'pitcher': pitcher}
            
            combined_analysis[pitcher]['pattern_predictability'] = {
                'predictability_score': pitcher_data.get('predictability_score', 0),
                'sequences_analyzed': pitcher_data.get('total_sequences', 0)
            }
        
        # Calculate composite weakspot scores
        overall_rankings = []
        for pitcher, data in combined_analysis.items():
            lineup_score = data.get('lineup_vulnerability', {}).get('max_score', 0)
            inning_score = data.get('inning_vulnerability', {}).get('max_score', 0)
            pattern_score = data.get('pattern_predictability', {}).get('predictability_score', 0)
            
            # Weighted composite score
            # Lineup vulnerability: 40%, Inning vulnerability: 35%, Pattern predictability: 25%
            composite_score = (lineup_score * 0.4) + (inning_score * 0.35) + (pattern_score * 0.25)
            
            overall_rankings.append({
                **data,
                'composite_weakspot_score': round(composite_score, 2),
                'vulnerability_breakdown': {
                    'lineup_contribution': round(lineup_score * 0.4, 2),
                    'inning_contribution': round(inning_score * 0.35, 2), 
                    'pattern_contribution': round(pattern_score * 0.25, 2)
                }
            })
        
        # Sort by composite score
        overall_rankings.sort(key=lambda x: x.get('composite_weakspot_score', 0), reverse=True)
        
        enhanced_rankings = {
            "analysis_type": "overall_weakspots",
            "analysis_date": datetime.now().isoformat(),
            "analysis_period": date_range or "All available data",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "overall_weakspots",
                "description": "Comprehensive weakspot analysis combining lineup, inning, and pattern vulnerabilities",
                "scoring_weights": {
                    "lineup_vulnerability": "40%",
                    "inning_vulnerability": "35%", 
                    "pattern_predictability": "25%"
                },
                "filters_available": [
                    "composite_score",
                    "lineup_vulnerability",
                    "inning_vulnerability",
                    "pattern_predictability"
                ]
            },
            "rankings": overall_rankings,
            "summary_stats": {
                "total_pitchers_analyzed": len(overall_rankings),
                "avg_composite_score": round(sum(p.get('composite_weakspot_score', 0) for p in overall_rankings) / len(overall_rankings) if overall_rankings else 0, 2),
                "top_10_avg_score": round(sum(p.get('composite_weakspot_score', 0) for p in overall_rankings[:10]) / min(10, len(overall_rankings)) if overall_rankings else 0, 2)
            }
        }
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_path / f"overall_weakspot_rankings_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        # Also create a "latest" version for easy access
        latest_file = self.output_path / "overall_weakspot_rankings_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(enhanced_rankings, f, indent=2)
        
        self.logger.info(f"Overall weakspot rankings saved to {output_file}")
        return str(output_file)
    
    def generate_all_rankings(self, date_range=None) -> Dict[str, str]:
        """
        Generate all ranking types
        
        Args:
            date_range: Optional tuple of (start_date, end_date)
        
        Returns:
            Dictionary mapping analysis type to output file path
        """
        self.logger.info("Generating all weakspot rankings...")
        
        results = {}
        
        try:
            results['lineup_vulnerability'] = self.generate_lineup_vulnerability_rankings(date_range)
        except Exception as e:
            self.logger.error(f"Failed to generate lineup vulnerability rankings: {e}")
        
        try:
            results['inning_patterns'] = self.generate_inning_pattern_rankings(date_range)
        except Exception as e:
            self.logger.error(f"Failed to generate inning pattern rankings: {e}")
        
        try:
            results['pitch_patterns'] = self.generate_pitch_pattern_rankings(date_range)
        except Exception as e:
            self.logger.error(f"Failed to generate pitch pattern rankings: {e}")
        
        try:
            results['overall_weakspots'] = self.generate_overall_weakspot_rankings(date_range)
        except Exception as e:
            self.logger.error(f"Failed to generate overall weakspot rankings: {e}")
        
        return results
    
    def _calculate_summary_stats(self, rankings: List, analysis_type: str) -> Dict:
        """Calculate summary statistics for rankings"""
        if not rankings:
            return {}
        
        if analysis_type == 'lineup':
            scores = [p.get('max_vulnerability_score', 0) for p in rankings]
        elif analysis_type == 'inning':
            scores = [p.get('max_vulnerability_score', 0) for p in rankings]
        elif analysis_type == 'patterns':
            scores = [p.get('predictability_score', 0) for p in rankings]
        else:
            scores = []
        
        if not scores:
            return {}
        
        return {
            "total_pitchers": len(rankings),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "top_10_avg": round(sum(scores[:10]) / min(10, len(scores)), 2)
        }
    
    def _calculate_velocity_decline(self, inning_breakdowns: Dict) -> float:
        """Calculate velocity decline pattern across innings"""
        velocities_by_inning = {}
        
        for inning_key, data in inning_breakdowns.items():
            inning_num = int(inning_key.split('_')[1])
            avg_velocity = data.get('avg_velocity')
            if avg_velocity:
                velocities_by_inning[inning_num] = avg_velocity
        
        if len(velocities_by_inning) < 2:
            return 0.0
        
        # Calculate decline from first to last available inning
        innings = sorted(velocities_by_inning.keys())
        first_inning_velocity = velocities_by_inning[innings[0]]
        last_inning_velocity = velocities_by_inning[innings[-1]]
        
        return round(first_inning_velocity - last_inning_velocity, 2)

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('weakspot_rankings.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Weakspot Rankings Generator')
    parser.add_argument('--analysis-type', choices=['lineup', 'inning', 'patterns', 'overall', 'all'],
                       default='all', help='Type of rankings to generate')
    parser.add_argument('--start-date', help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for analysis (YYYY-MM-DD)')
    parser.add_argument('--data-path', default='../BaseballData/data',
                       help='Path to baseball data directory')
    parser.add_argument('--output-path', default='../BaseballData/data/weakspot_analysis',
                       help='Path to output directory')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        generator = WeakspotRankingsGenerator(args.data_path, args.output_path)
        
        date_range = None
        if args.start_date and args.end_date:
            date_range = (args.start_date, args.end_date)
        
        if args.analysis_type == 'all':
            results = generator.generate_all_rankings(date_range)
            logger.info("Generated all rankings:")
            for analysis_type, output_file in results.items():
                logger.info(f"  {analysis_type}: {output_file}")
        elif args.analysis_type == 'lineup':
            output_file = generator.generate_lineup_vulnerability_rankings(date_range)
            logger.info(f"Generated lineup vulnerability rankings: {output_file}")
        elif args.analysis_type == 'inning':
            output_file = generator.generate_inning_pattern_rankings(date_range)
            logger.info(f"Generated inning pattern rankings: {output_file}")
        elif args.analysis_type == 'patterns':
            output_file = generator.generate_pitch_pattern_rankings(date_range)
            logger.info(f"Generated pitch pattern rankings: {output_file}")
        elif args.analysis_type == 'overall':
            output_file = generator.generate_overall_weakspot_rankings(date_range)
            logger.info(f"Generated overall weakspot rankings: {output_file}")
            
    except Exception as e:
        logger.error(f"Rankings generation failed: {e}")
        raise

if __name__ == "__main__":
    main()