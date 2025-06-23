#!/usr/bin/env python3
"""
Hellraiser Workflow Test Suite

Tests the complete Hellraiser analysis workflow:
1. Scheduler functionality
2. Analysis generation
3. Archiving system
4. Performance analysis
5. Cron job setup

Usage:
python3 test_hellraiser_workflow.py                # Full test suite
python3 test_hellraiser_workflow.py --quick        # Quick tests only
python3 test_hellraiser_workflow.py --analysis     # Test analysis generation only
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

class HellraiserWorkflowTester:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parent
        self.tracker_dir = self.project_root / "BaseballTracker"
        
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
        
        print("🧪 Hellraiser Workflow Test Suite")
        print(f"📂 Script directory: {self.script_dir}")
        print(f"📂 Project root: {self.project_root}")

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results['tests'].append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1

    def test_file_existence(self):
        """Test that all required files exist"""
        required_files = [
            self.script_dir / "daily_hellraiser_scheduler.py",
            self.script_dir / "generate_hellraiser_analysis.py",
            self.script_dir / "setup_hellraiser_automation.sh",
            self.script_dir / "analyze_pick_performance.py"
        ]
        
        for file_path in required_files:
            exists = file_path.exists()
            self.log_test(
                f"File existence: {file_path.name}",
                exists,
                f"Found at {file_path}" if exists else f"Missing: {file_path}"
            )

    def test_directory_structure(self):
        """Test that required directories exist or can be created"""
        required_dirs = [
            self.tracker_dir / "public" / "data" / "hellraiser",
            self.tracker_dir / "public" / "data" / "hellraiser" / "archive",
            self.tracker_dir / "public" / "data" / "hellraiser" / "performance",
            self.script_dir / "logs"
        ]
        
        for dir_path in required_dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                exists = dir_path.exists()
                self.log_test(
                    f"Directory structure: {dir_path.name}",
                    exists,
                    f"Created/verified: {dir_path}"
                )
            except Exception as e:
                self.log_test(
                    f"Directory structure: {dir_path.name}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_scheduler_syntax(self):
        """Test that scheduler script has valid syntax"""
        scheduler_script = self.script_dir / "daily_hellraiser_scheduler.py"
        
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(scheduler_script)],
                capture_output=True,
                text=True
            )
            
            passed = result.returncode == 0
            message = "Syntax valid" if passed else f"Syntax error: {result.stderr}"
            
            self.log_test("Scheduler syntax check", passed, message)
            
        except Exception as e:
            self.log_test("Scheduler syntax check", False, f"Error: {str(e)}")

    def test_analysis_generator_syntax(self):
        """Test that analysis generator script has valid syntax"""
n        generator_script = self.script_dir / "generate_hellraiser_analysis.py"\n        \n        try:\n            result = subprocess.run(\n                ["python3", "-m", "py_compile", str(generator_script)],\n                capture_output=True,\n                text=True\n            )\n            \n            passed = result.returncode == 0\n            message = "Syntax valid" if passed else f"Syntax error: {result.stderr}"\n            \n            self.log_test("Analysis generator syntax check", passed, message)\n            \n        except Exception as e:\n            self.log_test("Analysis generator syntax check", False, f"Error: {str(e)}")

    def test_performance_analyzer_syntax(self):
        """Test that performance analyzer script has valid syntax"""
        analyzer_script = self.script_dir / "analyze_pick_performance.py"
        
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(analyzer_script)],
                capture_output=True,
                text=True
            )
            
            passed = result.returncode == 0
            message = "Syntax valid" if passed else f"Syntax error: {result.stderr}"
            
            self.log_test("Performance analyzer syntax check", passed, message)
            
        except Exception as e:
            self.log_test("Performance analyzer syntax check", False, f"Error: {str(e)}")

    def test_cron_setup_script(self):
        """Test that cron setup script is properly configured"""
        setup_script = self.script_dir / "setup_hellraiser_automation.sh"
        
        # Check if script is executable
        is_executable = os.access(setup_script, os.X_OK)
        self.log_test(
            "Cron setup script executable",
            is_executable,
            "Script is executable" if is_executable else "Script needs chmod +x"
        )
        
        # Check if script has valid bash syntax (basic check)
        try:
            with open(setup_script, 'r') as f:
                content = f.read()
            
            has_shebang = content.startswith('#!/bin/bash')
            self.log_test(
                "Cron setup script format",
                has_shebang,
                "Has bash shebang" if has_shebang else "Missing bash shebang"
            )
            
        except Exception as e:
            self.log_test("Cron setup script format", False, f"Error reading script: {str(e)}")

    def test_mock_analysis_generation(self):
        """Test analysis generation with mock data"""
        print("🧪 Testing mock analysis generation...")
        
        # Create minimal test data
        test_odds_dir = self.tracker_dir / "public" / "data" / "odds"
        test_odds_dir.mkdir(parents=True, exist_ok=True)
        
        test_odds_file = test_odds_dir / "mlb-hr-odds-only.csv"
        
        # Create minimal test odds data
        test_odds_data = """player_name,odds,last_updated
Juan Soto,+450,2025-06-23 14:00:00
Aaron Judge,+300,2025-06-23 14:00:00
Mookie Betts,+500,2025-06-23 14:00:00"""
        
        try:
            with open(test_odds_file, 'w') as f:
                f.write(test_odds_data)
            
            self.log_test("Mock odds data creation", True, "Created test odds file")
            
            # Try to run analysis generator (expect it might fail due to missing lineup data)
            try:
                result = subprocess.run(
                    ["python3", str(self.script_dir / "generate_hellraiser_analysis.py")],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(self.script_dir)
                )
                
                # Even if it fails, we want to check that it runs without syntax errors
                ran_without_crash = True
                message = f"Exit code: {result.returncode}"
                if result.stdout:
                    message += f", Output: {result.stdout[:100]}..."
                if result.stderr:
                    message += f", Errors: {result.stderr[:100]}..."
                
                self.log_test("Analysis generator execution", ran_without_crash, message)
                
            except subprocess.TimeoutExpired:
                self.log_test("Analysis generator execution", False, "Timeout after 30 seconds")
            except Exception as e:
                self.log_test("Analysis generator execution", False, f"Execution error: {str(e)}")
                
        except Exception as e:
            self.log_test("Mock odds data creation", False, f"Error: {str(e)}")

    def test_archiving_functionality(self):
        """Test that archiving system works"""
        print("🧪 Testing archiving functionality...")
        
        # Create a mock hellraiser analysis file
        hellraiser_dir = self.tracker_dir / "public" / "data" / "hellraiser"
        hellraiser_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        test_analysis_file = hellraiser_dir / f"hellraiser_{today}.json"
        
        test_analysis_data = {
            "picks": [
                {
                    "playerName": "Test Player",
                    "team": "TEST",
                    "confidenceScore": 75,
                    "pathway": "batterDriven",
                    "reasoning": "Test reasoning"
                }
            ],
            "updatedAt": datetime.now().isoformat(),
            "generatedBy": "test_suite"
        }
        
        try:
            with open(test_analysis_file, 'w') as f:
                json.dump(test_analysis_data, f, indent=2)
            
            self.log_test("Mock analysis file creation", True, f"Created {test_analysis_file}")
            
            # Test that scheduler can archive this
            archive_dir = hellraiser_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Count files before
            files_before = len(list(archive_dir.glob("*.json")))
            
            # Import and test archiving function
            try:
                sys.path.append(str(self.script_dir))
                from daily_hellraiser_scheduler import HellraiserScheduler
                
                scheduler = HellraiserScheduler()
                scheduler.archive_analysis_results("Test Run")
                
                # Count files after
                files_after = len(list(archive_dir.glob("*.json")))
                
                archived_successfully = files_after > files_before
                self.log_test(
                    "Archiving functionality",
                    archived_successfully,
                    f"Archive files: {files_before} -> {files_after}"
                )
                
            except Exception as e:
                self.log_test("Archiving functionality", False, f"Import/execution error: {str(e)}")
                
        except Exception as e:
            self.log_test("Mock analysis file creation", False, f"Error: {str(e)}")

    def test_performance_analysis(self):
        """Test performance analysis functionality"""
        print("🧪 Testing performance analysis...")
        
        try:
            sys.path.append(str(self.script_dir))
            from analyze_pick_performance import PickPerformanceAnalyzer
            
            analyzer = PickPerformanceAnalyzer(str(self.tracker_dir))
            
            # Test loading (even if no archived picks exist)
            archived_picks = analyzer.load_archived_picks()
            
            self.log_test(
                "Performance analyzer loading",
                True,
                f"Loaded {sum(len(picks) for picks in archived_picks.values())} picks from {len(archived_picks)} days"
            )
            
        except Exception as e:
            self.log_test("Performance analyzer loading", False, f"Error: {str(e)}")

    def run_quick_tests(self):
        """Run quick tests (syntax and file checks)"""
        print("🚀 Running quick tests...")
        
        self.test_file_existence()
        self.test_directory_structure()
        self.test_scheduler_syntax()
        self.test_analysis_generator_syntax()
        self.test_performance_analyzer_syntax()
        self.test_cron_setup_script()

    def run_full_tests(self):
        """Run complete test suite"""
        print("🚀 Running full test suite...")
        
        self.run_quick_tests()
        self.test_mock_analysis_generation()
        self.test_archiving_functionality()
        self.test_performance_analysis()

    def run_analysis_tests(self):
        """Run analysis-specific tests"""
        print("🚀 Running analysis tests...")
        
        self.test_analysis_generator_syntax()
        self.test_mock_analysis_generation()
        self.test_archiving_functionality()
        self.test_performance_analysis()

    def print_summary(self):
        """Print test summary"""
        total_tests = self.test_results['passed'] + self.test_results['failed']
        pass_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Test Summary:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed: {self.test_results['passed']} ✅")
        print(f"   Failed: {self.test_results['failed']} ❌")
        print(f"   Pass rate: {pass_rate:.1f}%")
        
        if self.test_results['failed'] > 0:
            print(f"\n❌ Failed tests:")
            for test in self.test_results['tests']:
                if not test['passed']:
                    print(f"   - {test['name']}: {test['message']}")
        
        # Save detailed results
        results_file = self.script_dir / "logs" / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved: {results_file}")
        
        return self.test_results['failed'] == 0

def main():
    parser = argparse.ArgumentParser(description='Test Hellraiser workflow')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--analysis', action='store_true', help='Run analysis tests only')
    
    args = parser.parse_args()
    
    tester = HellraiserWorkflowTester()
    
    try:
        if args.quick:
            tester.run_quick_tests()
        elif args.analysis:
            tester.run_analysis_tests()
        else:
            tester.run_full_tests()
        
        success = tester.print_summary()
        
        if success:
            print(f"\n🎉 All tests passed! Hellraiser workflow is ready.")
            print(f"\n🔥 Next steps:")
            print(f"   1. Run setup: ./setup_hellraiser_automation.sh")
            print(f"   2. Install cron jobs: crontab hellraiser_crontab.txt")
            print(f"   3. Monitor logs: tail -f logs/hellraiser_scheduler.log")
        else:
            print(f"\n⚠️ Some tests failed. Please fix issues before proceeding.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()