#!/bin/bash

# setup_hellraiser_automation.sh - Set up Hellraiser analysis automation
# This script sets up cron jobs to run Hellraiser analysis throughout the day

echo "🔥 Setting up Hellraiser Analysis Automation..."

# Get the current directory (BaseballScraper)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📂 Script directory: $SCRIPT_DIR"
echo "📂 Project root: $PROJECT_ROOT"

# Make sure our scripts are executable
chmod +x "$SCRIPT_DIR/daily_hellraiser_scheduler.py"
chmod +x "$SCRIPT_DIR/generate_hellraiser_analysis.py"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Create a wrapper script for cron execution
CRON_WRAPPER="$SCRIPT_DIR/run_hellraiser_cron.sh"

cat > "$CRON_WRAPPER" << EOF
#!/bin/bash

# Hellraiser Cron Wrapper Script
# This ensures proper environment and logging for cron execution

# Set working directory
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "\$(date): Virtual environment activated" >> logs/hellraiser_cron.log
else
    echo "\$(date): Warning: No virtual environment found, using system Python" >> logs/hellraiser_cron.log
fi

# Set Python path
export PYTHONPATH="\$PYTHONPATH:$PROJECT_ROOT"

# Run the scheduler with logging
echo "\$(date): Starting Hellraiser scheduler..." >> logs/hellraiser_cron.log
python3 daily_hellraiser_scheduler.py >> logs/hellraiser_cron.log 2>&1
EXIT_CODE=\$?

if [ \$EXIT_CODE -eq 0 ]; then
    echo "\$(date): Hellraiser scheduler completed successfully" >> logs/hellraiser_cron.log
else
    echo "\$(date): Hellraiser scheduler failed with exit code \$EXIT_CODE" >> logs/hellraiser_cron.log
fi

# Deactivate virtual environment
if [ -f "venv/bin/activate" ]; then
    deactivate
fi

exit \$EXIT_CODE
EOF

chmod +x "$CRON_WRAPPER"

# Create the cron job entries
CRON_JOBS_FILE="$SCRIPT_DIR/hellraiser_crontab.txt"

cat > "$CRON_JOBS_FILE" << EOF
# Hellraiser Analysis Automation
# Runs throughout the day to capture changing odds and lineups

# Every 2 hours from 6 AM to 10 PM (captures different game start times)
0 6,8,10,12,14,16,18,20,22 * * * $CRON_WRAPPER

# Additional runs before typical game times
30 12 * * * $CRON_WRAPPER   # Before early afternoon games
30 18 * * * $CRON_WRAPPER   # Before evening games

EOF

echo "✅ Created cron wrapper script: $CRON_WRAPPER"
echo "✅ Created cron jobs file: $CRON_JOBS_FILE"

echo ""
echo "📋 Proposed cron schedule:"
echo "   - Every 2 hours from 6 AM to 10 PM"
echo "   - Additional runs at 12:30 PM and 6:30 PM"
echo "   - Total: ~10 analysis runs per day"

echo ""
echo "🔧 To install the cron jobs:"
echo "   1. Review the cron jobs: cat $CRON_JOBS_FILE"
echo "   2. Install them: crontab $CRON_JOBS_FILE"
echo "   3. Verify installation: crontab -l"

echo ""
echo "📊 To monitor the automation:"
echo "   - View scheduler logs: tail -f $SCRIPT_DIR/logs/hellraiser_scheduler.log"
echo "   - View cron logs: tail -f $SCRIPT_DIR/logs/hellraiser_cron.log"
echo "   - Check archives: ls -la $PROJECT_ROOT/BaseballTracker/public/data/hellraiser/archive/"

echo ""
echo "🧪 To test manually:"
echo "   - Run scheduler: $CRON_WRAPPER"
echo "   - Generate analysis: cd $SCRIPT_DIR && python3 generate_hellraiser_analysis.py"

echo ""
echo "⚠️ Important Notes:"
echo "   - Make sure your virtual environment is set up: python3 -m venv venv && source venv/bin/activate"
echo "   - Ensure odds data is being updated: check update-odds.sh cron job"
echo "   - Archive files will accumulate - consider periodic cleanup"

echo ""
echo "🔥 Hellraiser automation setup complete!"