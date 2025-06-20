#!/usr/bin/env python3
"""
Smart Morning Baseball Scraper Run
Intelligent automation for detecting postponements and updating schedules
"""

import subprocess
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

def log_message(message: str, level: str = "INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_enhanced_scraper() -> Dict:
    """
    Run the enhanced scraper and capture results
    Returns dict with execution results
    """
    log_message("Starting enhanced scraper execution")
    
    try:
        # Run the enhanced scraper
        result = subprocess.run([
            sys.executable, 'enhanced_scrape.py'
        ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'execution_time': datetime.now().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        log_message("Enhanced scraper timed out after 1 hour", "ERROR")
        return {
            'success': False,
            'error': 'timeout',
            'execution_time': datetime.now().isoformat()
        }
    except Exception as e:
        log_message(f"Error running enhanced scraper: {e}", "ERROR")
        return {
            'success': False,
            'error': str(e),
            'execution_time': datetime.now().isoformat()
        }

def check_postponement_logs() -> List[Dict]:
    """
    Check for any postponement logs from recent runs
    """
    postponement_files = []
    
    # Look for postponement logs from last few days
    for days_back in range(0, 3):
        date = datetime.now() - timedelta(days=days_back)
        date_str = f"{date.strftime('%B').lower()}_{date.day}_{date.year}"
        log_file = f"postponements_{date_str}.json"
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    postponement_files.append({
                        'file': log_file,
                        'date': date_str,
                        'data': data
                    })
                    log_message(f"Found postponement log: {log_file}")
            except Exception as e:
                log_message(f"Error reading postponement log {log_file}: {e}", "WARNING")
    
    return postponement_files

def analyze_scraper_output(output: str) -> Dict:
    """
    Analyze scraper output to extract key metrics
    """
    analysis = {
        'total_urls': 0,
        'successful_extractions': 0,
        'postponed_games': 0,
        'other_failures': 0,
        'schedule_updated': False,
        'files_moved': False
    }
    
    lines = output.split('\n')
    
    for line in lines:
        if 'Total URLs processed:' in line:
            try:
                analysis['total_urls'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Successful extractions:' in line:
            try:
                analysis['successful_extractions'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Postponed games detected:' in line:
            try:
                analysis['postponed_games'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Other failures:' in line:
            try:
                analysis['other_failures'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Successfully updated next day\'s schedule' in line:
            analysis['schedule_updated'] = True
        elif 'Successfully processed and archived' in line:
            analysis['files_moved'] = True
    
    return analysis

def generate_summary_report(scraper_result: Dict, analysis: Dict, postponements: List[Dict]) -> str:
    """
    Generate a comprehensive summary report
    """
    report = []
    report.append("🏟️ SMART MORNING SCRAPER REPORT")
    report.append("=" * 50)
    report.append(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"✅ Scraper Success: {'Yes' if scraper_result['success'] else 'No'}")
    
    if scraper_result['success']:
        report.append(f"📊 Total Games: {analysis['total_urls']}")
        report.append(f"✅ Successful: {analysis['successful_extractions']}")
        report.append(f"🚨 Postponed: {analysis['postponed_games']}")
        report.append(f"❌ Failed: {analysis['other_failures']}")
        
        if analysis['postponed_games'] > 0:
            report.append("")
            report.append("🚨 POSTPONEMENT ACTIONS:")
            if analysis['schedule_updated']:
                report.append("✅ Next day's schedule updated")
            else:
                report.append("❌ Failed to update next day's schedule")
        
        if analysis['files_moved']:
            report.append("✅ Processed files archived")
    else:
        report.append(f"❌ Scraper failed: {scraper_result.get('error', 'Unknown error')}")
    
    if postponements:
        report.append("")
        report.append("📋 RECENT POSTPONEMENTS:")
        for p in postponements:
            report.append(f"  📅 {p['date']}: {p['data']['total_postponed']} games")
    
    report.append("")
    report.append("🔧 RECOMMENDATIONS:")
    
    if scraper_result['success']:
        if analysis['postponed_games'] > 0:
            report.append("  🔄 Check tomorrow's schedule file for updates")
            report.append("  📊 Monitor for makeup games in coming days")
        if analysis['other_failures'] > 0:
            report.append("  🔍 Review failed extractions manually")
        if analysis['successful_extractions'] > 0:
            report.append("  ✅ Data ready for baseball analysis pipeline")
    else:
        report.append("  🚨 Manual intervention required")
        report.append("  🔍 Check scraper logs for error details")
    
    return "\n".join(report)

def save_morning_run_log(scraper_result: Dict, analysis: Dict, summary: str):
    """
    Save the morning run results to a log file
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'scraper_result': scraper_result,
        'analysis': analysis,
        'summary': summary
    }
    
    date_str = datetime.now().strftime("%Y%m%d")
    log_filename = f"morning_run_{date_str}.json"
    
    try:
        with open(log_filename, 'w') as f:
            json.dump(log_data, f, indent=2)
        log_message(f"Saved morning run log: {log_filename}")
    except Exception as e:
        log_message(f"Error saving morning run log: {e}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description='Smart Morning Baseball Scraper')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without executing')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    args = parser.parse_args()
    
    log_message("🌅 Starting Smart Morning Baseball Scraper")
    
    if args.dry_run:
        log_message("🔍 DRY RUN MODE - No actual execution", "INFO")
        return
    
    # Step 1: Check for recent postponement logs
    log_message("📋 Checking for recent postponement logs")
    postponements = check_postponement_logs()
    
    if postponements:
        log_message(f"Found {len(postponements)} recent postponement logs")
    else:
        log_message("No recent postponement logs found")
    
    # Step 2: Run the enhanced scraper
    log_message("🚀 Executing enhanced scraper")
    scraper_result = run_enhanced_scraper()
    
    if scraper_result['success']:
        log_message("✅ Enhanced scraper completed successfully")
    else:
        log_message("❌ Enhanced scraper failed", "ERROR")
    
    # Step 3: Analyze results
    if scraper_result['success'] and 'stdout' in scraper_result:
        analysis = analyze_scraper_output(scraper_result['stdout'])
        log_message(f"📊 Analysis: {analysis['successful_extractions']} successful, {analysis['postponed_games']} postponed")
    else:
        analysis = {}
        log_message("⚠️ Could not analyze scraper output", "WARNING")
    
    # Step 4: Generate comprehensive report
    summary = generate_summary_report(scraper_result, analysis, postponements)
    
    # Step 5: Display results
    print("\n" + summary)
    
    # Step 6: Save results
    save_morning_run_log(scraper_result, analysis, summary)
    
    # Step 7: Show verbose output if requested
    if args.verbose and scraper_result.get('stdout'):
        print("\n" + "="*50)
        print("DETAILED SCRAPER OUTPUT:")
        print("="*50)
        print(scraper_result['stdout'])
    
    if scraper_result.get('stderr'):
        print("\n" + "="*50)
        print("SCRAPER ERRORS:")
        print("="*50)
        print(scraper_result['stderr'])
    
    # Exit with appropriate code
    exit_code = 0 if scraper_result['success'] else 1
    log_message(f"🏁 Smart morning run completed with exit code {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)