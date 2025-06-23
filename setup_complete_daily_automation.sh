#!/bin/bash

# setup_complete_daily_automation.sh - Complete Daily Baseball Analytics Automation
# Sets up both odds tracking AND Hellraiser analysis to run throughout the day

echo "🚀 Setting up Complete Daily Baseball Analytics Automation..."

# Get the current directory (BaseballScraper)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📂 Script directory: $SCRIPT_DIR"
echo "📂 Project root: $PROJECT_ROOT"

# Make sure all scripts are executable
echo "🔧 Making scripts executable..."
chmod +x "$SCRIPT_DIR/update-odds.sh"
chmod +x "$SCRIPT_DIR/daily_hellraiser_scheduler.py"
chmod +x "$SCRIPT_DIR/generate_hellraiser_analysis.py"
chmod +x "$SCRIPT_DIR/simple_performance_analyzer.py"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Create wrapper scripts for cron execution
echo "📝 Creating cron wrapper scripts..."

# Odds update wrapper
ODDS_WRAPPER="$SCRIPT_DIR/run_odds_cron.sh"
cat > "$ODDS_WRAPPER" << EOF
#!/bin/bash

# Odds Update Cron Wrapper Script
# Ensures proper environment and logging for cron execution

# Set working directory
cd "$SCRIPT_DIR"

# Activate virtual environment (REQUIRED)
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
    echo "\$(date): Virtual environment activated: \$VIRTUAL_ENV" >> logs/odds_cron.log
else
    echo "\$(date): ERROR: No virtual environment found at venv/bin/activate" >> logs/odds_cron.log
    echo "\$(date): Please set up venv: python3 -m venv venv && . venv/bin/activate && pip install requirements" >> logs/odds_cron.log
    exit 1
fi

# Run the odds update script
echo "\$(date): Starting odds update..." >> logs/odds_cron.log
./update-odds.sh >> logs/odds_cron.log 2>&1
EXIT_CODE=\$?

if [ \$EXIT_CODE -eq 0 ]; then
    echo "\$(date): Odds update completed successfully" >> logs/odds_cron.log
else
    echo "\$(date): Odds update failed with exit code \$EXIT_CODE" >> logs/odds_cron.log
fi

# Deactivate virtual environment
if [ -n "\$VIRTUAL_ENV" ]; then
    deactivate
fi

exit \$EXIT_CODE
EOF

# Hellraiser analysis wrapper
HELLRAISER_WRAPPER="$SCRIPT_DIR/run_hellraiser_cron.sh"
cat > "$HELLRAISER_WRAPPER" << EOF
#!/bin/bash

# Hellraiser Analysis Cron Wrapper Script
# Ensures proper environment and logging for cron execution

# Set working directory
cd "$SCRIPT_DIR"

# Activate virtual environment (REQUIRED)
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
    echo "\$(date): Virtual environment activated: \$VIRTUAL_ENV" >> logs/hellraiser_cron.log
else
    echo "\$(date): ERROR: No virtual environment found at venv/bin/activate" >> logs/hellraiser_cron.log
    echo "\$(date): Please set up venv: python3 -m venv venv && . venv/bin/activate && pip install requirements" >> logs/hellraiser_cron.log
    exit 1
fi

# Set Python path for project imports
export PYTHONPATH="\$PYTHONPATH:$PROJECT_ROOT"

# Run the Hellraiser scheduler (use venv's python)
echo "\$(date): Starting Hellraiser scheduler with venv python..." >> logs/hellraiser_cron.log
python daily_hellraiser_scheduler.py >> logs/hellraiser_cron.log 2>&1
EXIT_CODE=\$?

if [ \$EXIT_CODE -eq 0 ]; then
    echo "\$(date): Hellraiser scheduler completed successfully" >> logs/hellraiser_cron.log
else
    echo "\$(date): Hellraiser scheduler failed with exit code \$EXIT_CODE" >> logs/hellraiser_cron.log
fi

# Deactivate virtual environment
if [ -n "\$VIRTUAL_ENV" ]; then
    deactivate
fi

exit \$EXIT_CODE
EOF

chmod +x "$ODDS_WRAPPER"
chmod +x "$HELLRAISER_WRAPPER"

# Create the complete cron jobs configuration
COMPLETE_CRON_FILE="$SCRIPT_DIR/complete_daily_crontab.txt"

cat > "$COMPLETE_CRON_FILE" << EOF
# Complete Daily Baseball Analytics Automation
# Combines odds tracking and Hellraiser analysis throughout the day

# ========================================
# ODDS TRACKING - Every 30 minutes from 6:30 AM to 11:30 PM
# ========================================
30 6-23 * * * $ODDS_WRAPPER

# ========================================  
# HELLRAISER ANALYSIS - Strategic timing based on game schedules
# ========================================

# Major analysis runs every 2 hours during active period
0 6,8,10,12,14,16,18,20,22 * * * $HELLRAISER_WRAPPER

# Additional targeted runs before typical game times
30 12 * * * $HELLRAISER_WRAPPER   # Before early afternoon games (1 PM)
30 18 * * * $HELLRAISER_WRAPPER   # Before evening games (7 PM)
15 19 * * * $HELLRAISER_WRAPPER   # Final check before 7:30 PM games

# ========================================
# DAILY MAINTENANCE - Weekly performance analysis
# ========================================
0 7 * * 1 cd $SCRIPT_DIR && . venv/bin/activate && python simple_performance_analyzer.py --days 7 >> logs/weekly_performance.log 2>&1

EOF

echo "✅ Created wrapper scripts:"
echo "   - $ODDS_WRAPPER"
echo "   - $HELLRAISER_WRAPPER"
echo "✅ Created complete cron configuration: $COMPLETE_CRON_FILE"

echo ""
echo "📋 Proposed complete automation schedule:"
echo "   ODDS TRACKING:"
echo "     - Every 30 minutes from 6:30 AM to 11:30 PM"
echo "     - Captures real-time line movement throughout the day"
echo "     - Syncs to both development and production directories"
echo ""
echo "   HELLRAISER ANALYSIS:"
echo "     - Major runs: 6 AM, 8 AM, 10 AM, 12 PM, 2 PM, 4 PM, 6 PM, 8 PM, 10 PM"
echo "     - Targeted runs: 12:30 PM, 6:30 PM, 7:15 PM"
echo "     - Archives every analysis for performance tracking"
echo ""
echo "   PERFORMANCE ANALYSIS:"
echo "     - Weekly summary every Monday at 7 AM"

echo ""
echo "🔧 To install the complete automation:"
echo "   1. Review the cron jobs: cat $COMPLETE_CRON_FILE"
echo "   2. Install them: crontab $COMPLETE_CRON_FILE"
echo "   3. Verify installation: crontab -l"

echo ""
echo "📊 To monitor the automation:"
echo "   - Odds updates: tail -f $SCRIPT_DIR/logs/odds_cron.log"
echo "   - Hellraiser analysis: tail -f $SCRIPT_DIR/logs/hellraiser_cron.log"
echo "   - Performance reports: tail -f $SCRIPT_DIR/logs/weekly_performance.log"

echo ""
echo "🧪 To test before installing:"
echo "   - Test odds update: $ODDS_WRAPPER"
echo "   - Test Hellraiser: $HELLRAISER_WRAPPER"
echo "   - Run performance analysis: cd $SCRIPT_DIR && . venv/bin/activate && python simple_performance_analyzer.py"

echo ""
echo "📁 Directory structure created:"
echo "   $SCRIPT_DIR/logs/ - All automation logs"
echo "   $PROJECT_ROOT/BaseballTracker/public/data/odds/ - Development odds data"
echo "   $PROJECT_ROOT/BaseballTracker/build/data/odds/ - Production odds data"
echo "   $PROJECT_ROOT/BaseballTracker/public/data/hellraiser/archive/ - Analysis archives"
echo "   $PROJECT_ROOT/BaseballTracker/public/data/hellraiser/performance/ - Performance reports"

echo ""
echo "⚠️ Important Notes:"
echo "   - Ensure virtual environment is set up: python3 -m venv venv && . venv/bin/activate"
echo "   - Verify DraftKings API access (odds data source)"
echo "   - Monitor logs for the first few days to ensure proper operation"
echo "   - Archive files will accumulate - consider monthly cleanup"

echo ""
echo "🔥 Complete daily automation setup ready!"
echo "   This provides comprehensive odds tracking + Hellraiser analysis throughout each day"
echo "   with full archiving and performance monitoring."