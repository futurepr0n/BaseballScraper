#!/bin/bash
"""
Weakspot Analysis Runner
========================

Shell script to integrate weakspot analysis into the existing BaseballScraper
daily automation workflow. This script can be called from daily_update.sh
or run independently.

Usage:
  ./run_weakspot_analysis.sh [options]

Options:
  --force     Force update even if no new data detected
  --test      Run in test mode with sample data
  --verbose   Enable verbose logging
  --help      Show this help message

Integration with existing workflow:
- Call this script after play-by-play data has been scraped
- Outputs go to BaseballData/data/weakspot_analysis/
- JSON files are created for fast frontend loading

Author: BaseballScraper Enhancement System
Date: August 2025
"""

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_PATH="$SCRIPT_DIR/../BaseballData/data"
LOG_FILE="$SCRIPT_DIR/logs/weakspot_analysis.log"
VENV_PATH="$SCRIPT_DIR/venv"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to show help
show_help() {
    echo "Weakspot Analysis Runner"
    echo "========================"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --force     Force update even if no new data detected"
    echo "  --test      Run in test mode with sample data"
    echo "  --verbose   Enable verbose logging"
    echo "  --help      Show this help message"
    echo
    echo "Integration:"
    echo "  Add this script to your daily_update.sh workflow:"
    echo "  ./run_weakspot_analysis.sh"
    echo
    exit 0
}

# Function to check if virtual environment exists and activate it
setup_python_env() {
    if [ ! -d "$VENV_PATH" ]; then
        log_message "WARNING" "Virtual environment not found at $VENV_PATH"
        log_message "INFO" "Attempting to use system Python..."
        return 0
    fi
    
    source "$VENV_PATH/bin/activate"
    if [ $? -eq 0 ]; then
        log_message "INFO" "Activated virtual environment at $VENV_PATH"
        return 0
    else
        log_message "WARNING" "Failed to activate virtual environment, using system Python"
        return 0
    fi
}

# Function to check dependencies
check_dependencies() {
    log_message "INFO" "Checking Python dependencies..."
    
    # Check if required Python packages are available
    python3 -c "import pandas, numpy, json, pathlib" 2>/dev/null
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Required Python packages not found (pandas, numpy)"
        log_message "INFO" "Please install with: pip install pandas numpy"
        return 1
    fi
    
    # Check if weakspot analyzer exists
    if [ ! -f "$SCRIPT_DIR/weakspot_analyzer.py" ]; then
        log_message "ERROR" "Weakspot analyzer script not found at $SCRIPT_DIR/weakspot_analyzer.py"
        return 1
    fi
    
    # Check if data directory exists
    if [ ! -d "$DATA_PATH" ]; then
        log_message "ERROR" "Data directory not found at $DATA_PATH"
        return 1
    fi
    
    log_message "INFO" "Dependencies check passed"
    return 0
}

# Function to run weakspot analysis
run_weakspot_analysis() {
    local force_flag="$1"
    local verbose_flag="$2"
    local test_flag="$3"
    
    log_message "INFO" "Starting weakspot analysis..."
    
    # Build command line arguments
    local python_args="$DATA_PATH"
    
    if [ "$force_flag" = "true" ]; then
        python_args="$python_args --force"
    fi
    
    if [ "$verbose_flag" = "true" ]; then
        python_args="$python_args --verbose"
    fi
    
    # Change to script directory to ensure imports work
    cd "$SCRIPT_DIR"
    
    # Run the analysis
    if [ "$test_flag" = "true" ]; then
        log_message "INFO" "Running in test mode..."
        python3 -c "
import sys
sys.path.append('.')
from weakspot_analyzer import WeakspotAnalyzer

# Test with sample data
try:
    analyzer = WeakspotAnalyzer('$DATA_PATH')
    print('✓ WeakspotAnalyzer initialized successfully')
    
    # Try to load a small amount of data
    processor = analyzer.processor
    games_data = processor.load_playbyplay_files()
    print(f'✓ Loaded {len(games_data)} play-by-play games')
    
    if games_data:
        # Test analysis on first pitcher found
        sample_game = games_data[0]
        plays = sample_game.get('plays', [])
        if plays:
            sample_pitcher_id = plays[0].get('pitcher')
            if sample_pitcher_id:
                print(f'✓ Found sample pitcher: {sample_pitcher_id}')
            
    print('✓ Test completed successfully')
    
except Exception as e:
    print(f'✗ Test failed: {e}')
    sys.exit(1)
"
    else
        # Run full analysis
        python3 daily_weakspot_update.py --data-path "$DATA_PATH" $python_args
    fi
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_message "INFO" "Weakspot analysis completed successfully"
        return 0
    else
        log_message "ERROR" "Weakspot analysis failed with exit code $exit_code"
        return $exit_code
    fi
}

# Function to show results summary
show_results_summary() {
    local output_dir="$DATA_PATH/weakspot_analysis"
    
    if [ ! -d "$output_dir" ]; then
        log_message "WARNING" "Output directory not found: $output_dir"
        return
    fi
    
    log_message "INFO" "=== WEAKSPOT ANALYSIS RESULTS SUMMARY ==="
    
    # Check for latest ranking files
    local lineup_file="$output_dir/lineup_vulnerability_rankings_latest.json"
    local inning_file="$output_dir/inning_pattern_rankings_latest.json"
    local pattern_file="$output_dir/pitch_pattern_rankings_latest.json"
    local overall_file="$output_dir/overall_weakspot_rankings_latest.json"
    local today_file="$output_dir/todays_opportunities_latest.json"
    
    if [ -f "$lineup_file" ]; then
        local lineup_count=$(python3 -c "import json; data=json.load(open('$lineup_file')); print(len(data.get('rankings', [])))" 2>/dev/null || echo "0")
        log_message "INFO" "✓ Lineup Vulnerability Rankings: $lineup_count pitchers analyzed"
    fi
    
    if [ -f "$inning_file" ]; then
        local inning_count=$(python3 -c "import json; data=json.load(open('$inning_file')); print(len(data.get('rankings', [])))" 2>/dev/null || echo "0")
        log_message "INFO" "✓ Inning Pattern Rankings: $inning_count pitchers analyzed"
    fi
    
    if [ -f "$pattern_file" ]; then
        local pattern_count=$(python3 -c "import json; data=json.load(open('$pattern_file')); print(len(data.get('rankings', [])))" 2>/dev/null || echo "0")
        log_message "INFO" "✓ Pitch Pattern Rankings: $pattern_count pitchers analyzed"
    fi
    
    if [ -f "$overall_file" ]; then
        local overall_count=$(python3 -c "import json; data=json.load(open('$overall_file')); print(len(data.get('rankings', [])))" 2>/dev/null || echo "0")
        log_message "INFO" "✓ Overall Weakspot Rankings: $overall_count pitchers analyzed"
    fi
    
    if [ -f "$today_file" ]; then
        local today_games=$(python3 -c "import json; data=json.load(open('$today_file')); print(len(data.get('games', [])))" 2>/dev/null || echo "0")
        log_message "INFO" "✓ Today's Opportunities: $today_games games analyzed"
    fi
    
    log_message "INFO" "Results saved to: $output_dir"
    log_message "INFO" "=========================================="
}

# Main execution
main() {
    local force_flag="false"
    local verbose_flag="false"
    local test_flag="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_flag="true"
                shift
                ;;
            --verbose)
                verbose_flag="true"
                shift
                ;;
            --test)
                test_flag="true"
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                log_message "ERROR" "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    log_message "INFO" "Starting weakspot analysis runner..."
    
    # Setup Python environment
    setup_python_env
    
    # Check dependencies
    if ! check_dependencies; then
        log_message "ERROR" "Dependency check failed"
        exit 1
    fi
    
    # Run analysis
    if ! run_weakspot_analysis "$force_flag" "$verbose_flag" "$test_flag"; then
        log_message "ERROR" "Weakspot analysis failed"
        exit 1
    fi
    
    # Show results summary
    if [ "$test_flag" != "true" ]; then
        show_results_summary
    fi
    
    log_message "INFO" "Weakspot analysis runner completed successfully"
}

# Run main function with all arguments
main "$@"