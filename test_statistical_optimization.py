#!/usr/bin/env python3
"""
Test Script for Statistical Hellraiser Optimization
Tests the solution to the flat 50% confidence score issue

This script validates:
1. That predictions have proper variance (not flat 50%)
2. Statistical approaches are working correctly
3. Data quality impacts are properly handled
4. Model performance meets target requirements
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics
import traceback

# Import the optimized statistical analyzer
from optimized_hellraiser_statistical import OptimizedHellraiserStatistical

class HellraiserTestSuite:
    """Comprehensive test suite for statistical optimization"""
    
    def __init__(self):
        self.analyzer = OptimizedHellraiserStatistical()
        self.test_results = {}
        
    def run_comprehensive_tests(self, test_date: str = None) -> Dict:
        """Run comprehensive test suite"""
        if test_date is None:
            test_date = datetime.now().strftime('%Y-%m-%d')
        
        print("🔬 Hellraiser Statistical Optimization Test Suite")
        print("=" * 60)
        print(f"🎯 Primary Goal: Fix flat 50% confidence score issue")
        print(f"📅 Test Date: {test_date}")
        print("=" * 60)
        
        tests = [
            ('variance_test', self.test_prediction_variance),
            ('distribution_test', self.test_score_distribution),
            ('data_quality_test', self.test_data_quality_impact),
            ('feature_engineering_test', self.test_feature_engineering),
            ('uncertainty_quantification_test', self.test_uncertainty_quantification),
            ('comparison_test', self.test_vs_baseline),
            ('robustness_test', self.test_statistical_robustness)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name.replace('_', ' ').title()}...")
            try:
                result = test_func(test_date)
                self.test_results[test_name] = result
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                print(f"{status} {test_name}: {result['summary']}")
                
                if not result['passed']:
                    print(f"   Issue: {result['details']}")
                    
            except Exception as e:
                self.test_results[test_name] = {
                    'passed': False,
                    'summary': f"Test failed with error: {str(e)[:100]}",
                    'details': traceback.format_exc(),
                    'critical': True
                }
                print(f"❌ ERROR {test_name}: {str(e)[:100]}")
        
        # Overall assessment
        self.print_test_summary()
        return self.test_results
    
    def test_prediction_variance(self, test_date: str) -> Dict:
        """Test 1: Critical - Ensure predictions have proper variance"""
        try:
            results = self.analyzer.analyze_date_statistical(test_date)
            
            if results.get('error'):
                return {
                    'passed': False,
                    'summary': f"Analysis failed: {results['error']}",
                    'details': "Could not generate predictions to test variance",
                    'critical': True
                }
            
            picks = results.get('picks', [])
            if not picks:
                return {
                    'passed': False,
                    'summary': "No predictions generated",
                    'details': "Cannot test variance with no predictions",
                    'critical': True
                }
            
            confidence_scores = [p.get('confidenceScore', 50) for p in picks]
            variance = statistics.variance(confidence_scores) if len(confidence_scores) > 1 else 0
            std_dev = statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0
            
            # Check for flat 50% issue
            flat_scores = len([s for s in confidence_scores if abs(s - 50) < 2])
            flat_percentage = (flat_scores / len(confidence_scores)) * 100
            
            variance_threshold = self.analyzer.VARIANCE_THRESHOLD
            passed = std_dev >= variance_threshold and flat_percentage < 50
            
            return {
                'passed': passed,
                'summary': f"Std Dev: {std_dev:.2f}, Flat: {flat_percentage:.1f}%",
                'details': {
                    'standard_deviation': std_dev,
                    'variance': variance,
                    'flat_percentage': flat_percentage,
                    'threshold_met': std_dev >= variance_threshold,
                    'score_range': (min(confidence_scores), max(confidence_scores)),
                    'total_predictions': len(confidence_scores)
                },
                'critical': True,
                'metrics': {
                    'std_dev': std_dev,
                    'variance': variance,
                    'flat_pct': flat_percentage
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Test execution failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': True
            }
    
    def test_score_distribution(self, test_date: str) -> Dict:
        """Test 2: Ensure score distribution is reasonable"""
        try:
            results = self.analyzer.analyze_date_statistical(test_date)
            picks = results.get('picks', [])
            
            if not picks:
                return {
                    'passed': False,
                    'summary': "No predictions to analyze distribution",
                    'details': "Cannot test distribution without predictions",
                    'critical': True
                }
            
            confidence_scores = [p.get('confidenceScore', 50) for p in picks]
            
            # Distribution analysis
            bins = {
                'very_low': len([s for s in confidence_scores if s < 30]),
                'low': len([s for s in confidence_scores if 30 <= s < 45]),
                'medium': len([s for s in confidence_scores if 45 <= s < 55]),
                'high': len([s for s in confidence_scores if 55 <= s < 70]),
                'very_high': len([s for s in confidence_scores if s >= 70])
            }
            
            total = len(confidence_scores)
            distribution = {k: (v/total)*100 for k, v in bins.items()}
            
            # Check for reasonable distribution
            # Should not have >80% in medium range (45-55)
            medium_heavy = distribution['medium'] > 80
            # Should have some spread
            has_extremes = distribution['very_low'] + distribution['very_high'] > 5
            
            passed = not medium_heavy and has_extremes
            
            return {
                'passed': passed,
                'summary': f"Distribution: Low: {distribution['low']:.1f}%, Med: {distribution['medium']:.1f}%, High: {distribution['high']:.1f}%",
                'details': {
                    'distribution_percentages': distribution,
                    'bins_count': bins,
                    'medium_heavy': medium_heavy,
                    'has_extremes': has_extremes,
                    'total_predictions': total
                },
                'critical': False
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Distribution test failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': False
            }
    
    def test_data_quality_impact(self, test_date: str) -> Dict:
        """Test 3: Ensure data quality affects predictions appropriately"""
        try:
            results = self.analyzer.analyze_date_statistical(test_date)
            data_quality = results.get('data_quality', {})
            
            overall_score = data_quality.get('overall_score', 0)
            sources_available = data_quality.get('sources_available', 0)
            sources_expected = data_quality.get('sources_expected', 6)
            availability_ratio = sources_available / sources_expected
            
            # Check if data quality is being tracked
            quality_tracked = overall_score > 0 and 'completeness_scores' in data_quality
            
            # Check if low quality affects uncertainty
            picks = results.get('picks', [])
            if picks:
                avg_variance = statistics.mean([p.get('prediction_variance', 10) for p in picks])
                # Lower quality should mean higher uncertainty
                appropriate_uncertainty = avg_variance > 8 if overall_score < 0.6 else True
            else:
                appropriate_uncertainty = True
            
            passed = quality_tracked and appropriate_uncertainty
            
            return {
                'passed': passed,
                'summary': f"Quality: {overall_score:.2f}, Sources: {sources_available}/{sources_expected}",
                'details': {
                    'overall_score': overall_score,
                    'availability_ratio': availability_ratio,
                    'quality_tracked': quality_tracked,
                    'appropriate_uncertainty': appropriate_uncertainty,
                    'completeness_scores': data_quality.get('completeness_scores', {})
                },
                'critical': False
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Data quality test failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': False
            }
    
    def test_feature_engineering(self, test_date: str) -> Dict:
        """Test 4: Verify feature engineering from available data"""
        try:
            results = self.analyzer.analyze_date_statistical(test_date)
            feature_importance = results.get('feature_importance', {})
            
            # Check if features are engineered
            engineered_features = [f for f in feature_importance.keys() if 'engineered' in f]
            bayesian_features = [f for f in feature_importance.keys() if 'bayesian' in f]
            
            # Check feature diversity
            active_features = len([f for f, importance in feature_importance.items() if importance > 0.05])
            
            feature_engineering_working = len(engineered_features) > 0 or len(bayesian_features) > 0
            sufficient_diversity = active_features >= 3
            
            passed = feature_engineering_working and sufficient_diversity
            
            return {
                'passed': passed,
                'summary': f"Active features: {active_features}, Engineered: {len(engineered_features)}",
                'details': {
                    'feature_importance': feature_importance,
                    'engineered_features': engineered_features,
                    'bayesian_features': bayesian_features,
                    'active_features': active_features,
                    'sufficient_diversity': sufficient_diversity
                },
                'critical': False
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Feature engineering test failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': False
            }
    
    def test_uncertainty_quantification(self, test_date: str) -> Dict:
        """Test 5: Verify uncertainty quantification is working"""
        try:
            results = self.analyzer.analyze_date_statistical(test_date)
            picks = results.get('picks', [])
            
            if not picks:
                return {
                    'passed': False,
                    'summary': "No predictions to test uncertainty",
                    'details': "Cannot test uncertainty without predictions",
                    'critical': False
                }
            
            # Check if confidence intervals are present
            intervals_present = len([p for p in picks if 'confidence_interval_lower' in p])
            variance_present = len([p for p in picks if 'prediction_variance' in p])
            uncertainty_classified = len([p for p in picks if 'uncertainty_level' in p])
            
            intervals_ratio = intervals_present / len(picks)
            variance_ratio = variance_present / len(picks)
            
            # Check interval properties
            if intervals_present > 0:
                interval_widths = []
                for pick in picks:
                    if 'confidence_interval_lower' in pick and 'confidence_interval_upper' in pick:
                        width = pick['confidence_interval_upper'] - pick['confidence_interval_lower']
                        interval_widths.append(width)
                
                avg_interval_width = statistics.mean(interval_widths) if interval_widths else 0
                reasonable_intervals = 10 <= avg_interval_width <= 60  # Reasonable width
            else:
                reasonable_intervals = False
                avg_interval_width = 0
            
            passed = intervals_ratio >= 0.8 and variance_ratio >= 0.8 and reasonable_intervals
            
            return {
                'passed': passed,
                'summary': f"Intervals: {intervals_ratio:.1%}, Avg width: {avg_interval_width:.1f}",
                'details': {
                    'intervals_present': intervals_present,
                    'variance_present': variance_present,
                    'uncertainty_classified': uncertainty_classified,
                    'intervals_ratio': intervals_ratio,
                    'variance_ratio': variance_ratio,
                    'avg_interval_width': avg_interval_width,
                    'reasonable_intervals': reasonable_intervals
                },
                'critical': False
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Uncertainty test failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': False
            }
    
    def test_vs_baseline(self, test_date: str) -> Dict:
        """Test 6: Compare against baseline flat predictions"""
        try:
            # Get statistical results
            results = self.analyzer.analyze_date_statistical(test_date)
            picks = results.get('picks', [])
            
            if not picks:
                return {
                    'passed': False,
                    'summary': "No predictions for comparison",
                    'details': "Cannot compare without predictions",
                    'critical': True
                }
            
            confidence_scores = [p.get('confidenceScore', 50) for p in picks]
            
            # Statistical analysis
            mean_score = statistics.mean(confidence_scores)
            std_dev = statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0
            
            # Compare to flat baseline
            flat_baseline_std = 0  # Flat 50% predictions
            improvement_factor = std_dev / max(flat_baseline_std, 0.1)  # Avoid division by zero
            
            # Check target performance (12.7% improvement over 0% baseline)
            target_variance = 5.0  # Minimum acceptable variance
            meets_target = std_dev >= target_variance
            
            # Check if predictions are meaningfully different from 50%
            mean_deviation = abs(mean_score - 50)
            meaningful_deviation = mean_deviation > 3 or std_dev > target_variance
            
            passed = meets_target and meaningful_deviation
            
            return {
                'passed': passed,
                'summary': f"Std dev: {std_dev:.2f} vs 0.0 baseline, Mean: {mean_score:.1f}",
                'details': {
                    'mean_score': mean_score,
                    'std_dev': std_dev,
                    'improvement_factor': improvement_factor,
                    'meets_target': meets_target,
                    'meaningful_deviation': meaningful_deviation,
                    'target_variance': target_variance,
                    'baseline_comparison': f"{std_dev:.2f} vs 0.0"
                },
                'critical': True
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Baseline comparison failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': True
            }
    
    def test_statistical_robustness(self, test_date: str) -> Dict:
        """Test 7: Statistical robustness and validation"""
        try:
            results = self.analyzer.analyze_date_statistical(test_date)
            
            # Run internal validation
            validation_results = self.analyzer._validate_statistical_approach(results)
            
            # Count passed tests
            critical_tests = [test for test, result in validation_results.items() 
                            if result.get('critical', False)]
            critical_passed = [test for test in critical_tests 
                             if validation_results[test]['passed']]
            
            total_tests = len(validation_results)
            total_passed = len([test for test, result in validation_results.items() 
                              if result['passed']])
            
            # Statistical robustness requires all critical tests to pass
            critical_success_rate = len(critical_passed) / max(len(critical_tests), 1)
            overall_success_rate = total_passed / max(total_tests, 1)
            
            passed = critical_success_rate >= 1.0 and overall_success_rate >= 0.7
            
            return {
                'passed': passed,
                'summary': f"Critical: {len(critical_passed)}/{len(critical_tests)}, Overall: {total_passed}/{total_tests}",
                'details': {
                    'validation_results': validation_results,
                    'critical_tests': critical_tests,
                    'critical_passed': critical_passed,
                    'critical_success_rate': critical_success_rate,
                    'overall_success_rate': overall_success_rate
                },
                'critical': True
            }
            
        except Exception as e:
            return {
                'passed': False,
                'summary': f"Robustness test failed: {str(e)}",
                'details': traceback.format_exc(),
                'critical': True
            }
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🔬 TEST SUMMARY - Statistical Hellraiser Optimization")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results.values() if t['passed']])
        critical_tests = len([t for t in self.test_results.values() if t.get('critical', False)])
        critical_passed = len([t for t in self.test_results.values() 
                              if t['passed'] and t.get('critical', False)])
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        print(f"🚨 Critical Tests: {critical_passed}/{critical_tests} passed")
        
        # Success assessment
        if critical_passed == critical_tests and passed_tests >= total_tests * 0.8:
            print("✅ SUCCESS: Flat confidence issue appears to be RESOLVED")
            print("🎯 Statistical optimization is working correctly")
        elif critical_passed == critical_tests:
            print("⚠️  PARTIAL SUCCESS: Critical issues fixed, minor issues remain")
            print("🔧 Consider additional optimization for non-critical areas")
        else:
            print("❌ FAILURE: Critical issues remain unresolved")
            print("🚨 Flat confidence issue may still be present")
        
        print("\n📋 Individual Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            critical = " (CRITICAL)" if result.get('critical', False) else ""
            print(f"  {status} {test_name.replace('_', ' ').title()}{critical}")
            print(f"      {result['summary']}")
        
        # Performance metrics summary
        variance_test = self.test_results.get('variance_test', {})
        if variance_test.get('metrics'):
            metrics = variance_test['metrics']
            print(f"\n📈 Key Performance Metrics:")
            print(f"  • Standard Deviation: {metrics['std_dev']:.2f} (Target: ≥5.0)")
            print(f"  • Prediction Variance: {metrics['variance']:.2f}")
            print(f"  • Flat Prediction %: {metrics['flat_pct']:.1f}% (Target: <30%)")
        
        print("=" * 60)
    
    def generate_test_report(self, output_file: str = None) -> str:
        """Generate detailed test report"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"hellraiser_test_report_{timestamp}.json"
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'test_suite_version': '1.0',
            'purpose': 'Validate fix for flat 50% confidence score issue',
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len([t for t in self.test_results.values() if t['passed']]),
                'critical_tests': len([t for t in self.test_results.values() if t.get('critical', False)]),
                'critical_passed': len([t for t in self.test_results.values() 
                                      if t['passed'] and t.get('critical', False)])
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed test report saved: {output_file}")
        return output_file


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Statistical Hellraiser Optimization')
    parser.add_argument('--date', type=str, help='Date to test (YYYY-MM-DD)', 
                       default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--save-report', action='store_true', help='Save detailed test report')
    parser.add_argument('--quick', action='store_true', help='Run quick validation only')
    
    args = parser.parse_args()
    
    # Initialize test suite
    test_suite = HellraiserTestSuite()
    
    if args.quick:
        # Quick validation - just check variance
        print("🚀 Quick Validation: Testing prediction variance...")
        result = test_suite.test_prediction_variance(args.date)
        
        if result['passed']:
            print("✅ QUICK TEST PASSED: Predictions have proper variance")
            print(f"📊 Standard Deviation: {result['metrics']['std_dev']:.2f}")
            print(f"📈 Flat Predictions: {result['metrics']['flat_pct']:.1f}%")
        else:
            print("❌ QUICK TEST FAILED: Flat confidence issue may still exist")
            print(f"⚠️  Issue: {result['summary']}")
        
        return
    
    # Full test suite
    test_results = test_suite.run_comprehensive_tests(args.date)
    
    # Save report if requested
    if args.save_report:
        test_suite.generate_test_report()
    
    # Return appropriate exit code
    critical_issues = [t for t in test_results.values() 
                      if not t['passed'] and t.get('critical', False)]
    
    if critical_issues:
        print(f"\n🚨 Exiting with error due to {len(critical_issues)} critical failures")
        sys.exit(1)
    else:
        print(f"\n✅ All critical tests passed - optimization appears successful")
        sys.exit(0)


if __name__ == "__main__":
    main()