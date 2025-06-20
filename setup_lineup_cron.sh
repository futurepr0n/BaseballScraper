#!/bin/bash
# Setup MLB Lineup Cron Job

echo "🔄 Setting up MLB Lineup Auto-Refresh Cron Job"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "fetch_starting_lineups.py" ]; then
    echo "❌ Error: Must run from BaseballScraper directory"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Run 'python3 -m venv venv' first"
    exit 1
fi

# Get current crontab
echo "📋 Current crontab:"
crontab -l 2>/dev/null || echo "(no crontab found)"

echo ""
echo "🔧 Installing new cron job..."

# Install the cron job
crontab lineup_crontab.txt

if [ $? -eq 0 ]; then
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "📅 Schedule: Every 30 minutes from 9 AM to 11:30 PM"
    echo "📁 Updates both dev and production directories:"
    echo "   - /app/BaseballTracker/public/data/lineups/"
    echo "   - /app/BaseballTracker/build/data/lineups/"
    echo ""
    echo "📊 Logs will be saved to:"
    echo "   - logs/lineup_cron.log"
    echo ""
    echo "🔍 To check current crontab: crontab -l"
    echo "🛑 To remove cron job: crontab -r"
    echo "📋 To view logs: tail -f logs/lineup_cron.log"
else
    echo "❌ Failed to install cron job"
    exit 1
fi